"""Original public run_eval, disk storage and evaluator; constant serving only."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import threading
import time
import traceback
from types import SimpleNamespace
import unicodedata

import pandas as pd
from word2number import w2n

from audit_positions import HERE, LOG, ConstantServing, class_from, gpqa_frame, hf_frame, load_native


def forbidden(*args, **kwargs):
    raise AssertionError("An out-of-scope heavy inference/math dependency was reached")


def support_classes(ns):
    ns.update(copy=copy, threading=threading, time=time, traceback=traceback,
              unicodedata=unicodedata, w2n=w2n, DataFlowStorage=object,
              AnswerJudgePrompt=object, parse=forbidden, verify=forbidden,
              LocalModelLLMServing_vllm=type("UnavailableLocalModelServing", (), {}))
    LOG.success = LOG.info
    receipts = {}
    wheel = ns["wheel_sources"]
    for path, names in [
        ("dataflow/utils/reasoning/AnswerExtraction.py", ["StringProcessor", "UnitTextManager", "StringCleaner", "AnswerExtractor"]),
        ("dataflow/utils/storage.py", ["FileStorage"]),
        ("dataflow/operators/core_text/eval/unified_bench_dataset_evaluator.py", ["UnifiedBenchDatasetEvaluator"]),
    ]:
        source = wheel[path]
        receipts[path] = hashlib.sha256(source.encode()).hexdigest()
        for name in names:
            class_from(source, name, ns)
    return receipts


def execute(name, original, config, native, letters):
    _, _, Tool, Runner, Report, _, ns = native
    folder = HERE / "entrypoint_records" / name
    folder.mkdir(parents=True, exist_ok=True)
    source_path = folder / "source.jsonl"
    original.to_json(source_path, orient="records", lines=True, force_ascii=False)
    # The native entry point itself reads this JSONL; use its materialized types below.
    expected = pd.read_json(source_path, lines=True)
    expected.to_json(folder / "source-before-native.jsonl", orient="records", lines=True, force_ascii=False)
    mapping = config["meta"]["key_mapping"]
    gold_positions = []
    for row in expected.to_dict("records"):
        keys = mapping["input_choices_key"]
        choices = [str(row[k]) for k in keys] if isinstance(keys, list) else [str(c) for c in row[keys]]
        label = row[mapping["input_label_key"]]
        gold_positions.append(int(label) if name == "mmlu" else choices.index(str(label)))
    result = {}
    for letter in letters:
        label_folder = folder / f"constant-{letter}"
        label_folder.mkdir(exist_ok=True)
        serving = ConstantServing(letter)
        model = SimpleNamespace(is_api=True, model_name_or_path=f"constant-{letter}")
        Tool._cached_llm_serving = serving
        Tool._cached_model_config = model
        bench = SimpleNamespace(**copy.deepcopy(config), dataset_cache=str(source_path))
        tool = Tool(output_root=str(label_folder))
        native_result = tool.run_eval(bench, model)
        records = pd.read_json(native_result["detail_path"], lines=True)
        assert len(records) == len(expected) == len(serving.prompts)
        # pandas' repeated JSON materialization can change binary floating metadata
        # at sub-serialization precision. Compare the canonical persisted fields,
        # while requiring exact task-field text independently below.
        source_canonical = expected.to_json(orient="records", lines=True, force_ascii=False)
        output_canonical = records[expected.columns].to_json(orient="records", lines=True, force_ascii=False)
        assert source_canonical == output_canonical, "The native pipeline changed serialized source fields"
        task_keys = [mapping["input_question_key"], mapping["input_label_key"]]
        task_keys += mapping["input_choices_key"] if isinstance(mapping["input_choices_key"], list) else [mapping["input_choices_key"]]
        assert all(records[k].tolist() == expected[k].tolist() for k in task_keys), "A source task field changed"
        assert records["generated_ans"].eq(f"<answer>{letter}</answer>").all()
        prompt_rows = [dict(row=i, question_present=str(expected.iloc[i][mapping["input_question_key"]]) in text,
                            prompt_sha256=hashlib.sha256(text.encode()).hexdigest())
                       for i, text in enumerate(serving.prompts)]
        (label_folder / "captured-prompts.jsonl").write_text("".join(json.dumps(dict(row=i, prompt=t), ensure_ascii=False)+"\n" for i,t in enumerate(serving.prompts)))
        (label_folder / "prompt-index.jsonl").write_text("".join(json.dumps(x)+"\n" for x in prompt_rows))
        bench.meta.update(pred_key="eval_pred", ref_key=mapping["input_label_key"],
                          eval_result=native_result["stats"], artifact_paths={"records_path": native_result["detail_path"]})
        metrics = Runner(max_workers=1).run_bench(bench, [{"name":"choice_accuracy", "priority":"primary"}])
        report = Report()
        report_score, report_source = report._resolve_report_score(bench, metrics, "choice_accuracy")
        counterfactual = copy.deepcopy(bench)
        counterfactual.meta.pop("eval_result", None)
        other_score, other_source = report._resolve_report_score(counterfactual, metrics, "choice_accuracy")
        (label_folder / "native-return.json").write_text(json.dumps(native_result, indent=2, default=str)+"\n")
        (label_folder / "metric-return.json").write_text(json.dumps(metrics, indent=2, default=str)+"\n")
        result[letter] = dict(native_stats=native_result["stats"],
            report_score=report_score, report_source=report_source,
            ordinary_metric_score=metrics["metrics"]["choice_accuracy"]["score"],
            diagnostic_removed_report_score=other_score, diagnostic_removed_report_source=other_source,
            own_question_present=sum(x["question_present"] for x in prompt_rows), rows=len(records),
            correct_rows=int(records["eval_score"].eq(1).sum()), valid_rows=int(records["eval_valid"].sum()),
            result_sha256=hashlib.sha256(Path(native_result["detail_path"]).read_bytes()).hexdigest())
    from collections import Counter
    return dict(source_rows=len(expected), source_jsonl_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                gold_position_counts=dict(Counter(gold_positions)), baselines=result)


def main():
    plan = json.loads((HERE/"sources.json").read_text())
    native = load_native(plan)
    receipts = support_classes(native[-1])
    gallery = json.loads(native[0]["one_eval/utils/bench_table/bench_gallery.json"])["benches"]
    results, provenance = {}, {}
    sources = plan["dataset_sources"] + [dict(name="mmlu", hf="cais/mmlu", split="test", prefix="all/")]
    for source in sources:
        name = source["name"]
        if "hf" in source:
            frame, provenance[name] = hf_frame(source["hf"], source["split"], source.get("prefix"))
        else:
            frame, provenance[name] = gpqa_frame(plan)
        config = next(b for b in gallery if b["bench_name"] == name)
        results[name] = execute(name, frame, config, native, "A" if name == "mmlu" else "AB")
        print("ENTRYPOINT_DATASET "+json.dumps({name:results[name]}, separators=(",", ":")), flush=True)
    summary = dict(one_eval_revision=plan["one_eval_revision"], datasets=results, source_provenance=provenance,
                   dataflow=native[5], added_source_sha256=receipts, new_model_calls=0,
                   boundary="Original complete DataFlowEvalTool.run_eval, FileStorage, generator, UnifiedBenchDatasetEvaluator, rescorer, MetricRunner and report score selector; source-loaded registration/base dependencies and constant-serving cache. No installed CLI or LLM-generated report.")
    (HERE/"entrypoint-summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print("ENTRYPOINT_SUMMARY "+json.dumps(summary, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
