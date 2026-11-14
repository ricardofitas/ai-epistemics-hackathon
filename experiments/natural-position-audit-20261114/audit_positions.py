"""Execute pinned native methods on unchanged public source records and constant baselines."""
import ast
from collections import Counter
import concurrent.futures
import copy
import csv
import gzip
import hashlib
from io import BytesIO, StringIO
import inspect
import json
import logging
import math
import os
from pathlib import Path
import random
import re
from types import SimpleNamespace
import urllib.request
import zipfile

import jinja2
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
logging.basicConfig(level=logging.WARNING)
LOG = logging.getLogger("native-position-audit")


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "natural-benchmark-audit/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def git_file(repo, revision, path, expected):
    data = get(f"https://raw.githubusercontent.com/{repo}/{revision}/{path}")
    assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == expected, path
    return data


def class_from(source, name, ns, methods=None):
    cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == name)
    cls.decorator_list = []  # Registration has no role in these native methods.
    if methods is not None:
        cls.body = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in methods]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), cls], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<verified native source>", "exec"), ns)
    return ns[name]


def hf_frame(repo, split, prefix=None):
    metadata = json.loads(get(f"https://huggingface.co/api/datasets/{repo}"))
    revision = metadata["sha"]
    entries = json.loads(get(f"https://huggingface.co/api/datasets/{repo}/tree/{revision}?recursive=true"))
    files = [f for f in entries if f.get("type") == "file" and f["path"].endswith(".parquet")
             and Path(f["path"]).name.startswith(split + "-")
             and (prefix is None or f["path"].startswith(prefix))]
    assert files, (repo, split)
    frames, receipts = [], []
    for item in sorted(files, key=lambda r: r["path"]):
        data = get(f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{item['path']}")
        sha = hashlib.sha256(data).hexdigest()
        declared = (item.get("lfs") or {}).get("oid")
        if declared:
            assert sha == declared.removeprefix("sha256:"), item["path"]
        frames.append(pd.read_parquet(BytesIO(data)))
        receipts.append(dict(path=item["path"], sha256=sha, bytes=len(data), declared_lfs_sha256=declared))
    return pd.concat(frames, ignore_index=True), dict(repo=repo, revision=revision, split=split, files=receipts)


def gpqa_frame(plan, member_basename="gpqa_main.csv"):
    data = git_file("Idavidrein/gpqa", plan["gpqa_author_revision"], "dataset.zip", plan["gpqa_archive_git_blob"])
    readme = git_file("Idavidrein/gpqa", plan["gpqa_author_revision"], "README.md", plan["gpqa_readme_git_blob"]).decode()
    match = re.search(r"password[^`]*`([^`]+)`", readme, re.I)
    assert match, "Author-provided archive password not located"
    with zipfile.ZipFile(BytesIO(data)) as archive:
        member = next(name for name in archive.namelist() if Path(name).name == member_basename)
        contents = archive.read(member, pwd=match[1].encode())
    records = list(csv.DictReader(StringIO(contents.decode("utf-8-sig"))))
    return pd.DataFrame(records), dict(repo="Idavidrein/gpqa", revision=plan["gpqa_author_revision"],
        archive_git_blob=plan["gpqa_archive_git_blob"], archive_sha256=hashlib.sha256(data).hexdigest(),
        member=member, member_sha256=hashlib.sha256(contents).hexdigest())


class Storage:
    def __init__(self, frame, path):
        self.frame = frame
        self.path = path

    def read(self, *args, **kwargs):
        return self.frame.copy(deep=True)

    def write(self, frame, *args, **kwargs):
        self.frame = frame.copy(deep=True)
        self.frame.to_json(self.path, orient="records", lines=True, force_ascii=False)
        return str(self.path)


class ConstantServing:
    def __init__(self, label):
        self.label = label
        self.prompts = []

    def generate_from_input(self, user_inputs, **kwargs):
        self.prompts.extend(user_inputs)
        return [f"<answer>{self.label}</answer>" for _ in user_inputs]


def load_native(plan):
    sources = {path: git_file("OpenDCAI/One-Eval", plan["one_eval_revision"], path, sha)
               for path, sha in plan["one_eval_files"].items()}
    native_root = HERE / "native"
    for name in ("one_eval/__init__.py", "one_eval/metrics/__init__.py", "one_eval/utils/__init__.py"):
        path = native_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    for name, data in sources.items():
        path = native_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    import sys
    sys.path.insert(0, str(native_root))
    from one_eval.metrics.parsers import parse_value
    from one_eval.utils.extractor import extract_choice
    ns = dict(pd=pd, np=np, re=re, json=json, os=os, Path=Path, hashlib=hashlib, math=math,
              concurrent=concurrent, cpu_count=lambda: 2, log=LOG, get_logger=lambda *a: LOG,
              parse_value=parse_value, extract_choice=extract_choice, inspect=inspect,
              OperatorABC=object, DIYPromptABC=object, PromptABC=object, jinja2=jinja2, Template=jinja2.Template,
              Environment=jinja2.Environment, StrictUndefined=jinja2.StrictUndefined,
              NON_PARALLEL_METRICS={"choice_accuracy"})
    wheel_info = json.loads(get("https://pypi.org/pypi/open-dataflow/1.0.10/json"))
    wheel = next(w for w in wheel_info["urls"] if w["filename"].endswith(".whl"))
    data = get(wheel["url"])
    assert hashlib.sha256(data).hexdigest() == wheel["digests"]["sha256"]
    with zipfile.ZipFile(BytesIO(data)) as archive:
        prompt_file = next(p for p in archive.namelist() if p.startswith("dataflow/prompts/") and p.endswith(".py") and b"class FormatStrPrompt" in archive.read(p))
        prompt_source = archive.read(prompt_file).decode()
        generator_file = "dataflow/operators/core_text/generate/bench_answer_generator.py"
        generator_source = archive.read(generator_file).decode()
        ns["wheel_sources"] = {p: archive.read(p).decode() for p in archive.namelist()
            if p in {"dataflow/utils/storage.py", "dataflow/utils/reasoning/AnswerExtraction.py",
                     "dataflow/operators/core_text/eval/unified_bench_dataset_evaluator.py"}}
    class_from(prompt_source, "FormatStrPrompt", ns)
    generator = class_from(generator_source, "BenchAnswerGenerator", ns)
    tool = class_from(sources["one_eval/toolkits/dataflow_eval_tool.py"].decode(), "DataFlowEvalTool", ns)
    nodes = []
    for node in ast.parse(sources["one_eval/metrics/common/general.py"].decode()).body:
        if isinstance(node, ast.FunctionDef) and node.name in {"compute_choice_accuracy", "_compute_choice_accuracy_with_parser"}:
            node.decorator_list = []
            nodes.append(node)
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)] + nodes, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<native registered metric>", "exec"), ns)
    ns["get_metric_fn"] = lambda name: ns["compute_choice_accuracy"] if name == "choice_accuracy" else None
    runner = class_from(sources["one_eval/metrics/runner.py"].decode(), "MetricRunner", ns)
    # The original class base is unrelated to these two score-selection methods.
    report_tree = ast.parse(sources["one_eval/agents/report_gen_agent.py"].decode())
    report_cls = next(c for c in report_tree.body if isinstance(c, ast.ClassDef) and c.name == "ReportGenAgent")
    report_cls.bases = []
    report = class_from(ast.unparse(report_cls), "ReportGenAgent", ns, methods={"_safe_float", "_resolve_report_score"})
    receipt = dict(pypi_version="1.0.10", wheel=wheel["filename"], wheel_sha256=wheel["digests"]["sha256"],
                   prompt_source=prompt_file, prompt_sha256=hashlib.sha256(prompt_source.encode()).hexdigest(),
                   generator_source=generator_file, generator_sha256=hashlib.sha256(generator_source.encode()).hexdigest())
    return sources, generator, tool, runner, report, receipt, ns


def audit(name, frame, config, native):
    sources, Generator, Tool, Runner, Report, receipt, ns = native
    folder = HERE / "records" / name
    folder.mkdir(parents=True, exist_ok=True)
    tool = Tool(output_root=str(folder))
    mapping = copy.deepcopy(config["meta"]["key_mapping"])
    original = frame.copy(deep=True)
    frame, mapping = tool._preprocess_dataframe(frame.copy(deep=True), name, mapping, eval_type=config["bench_dataflow_eval_type"])
    qkey = mapping["input_question_key"]
    label_key = mapping["input_label_key"]
    choices_key = mapping["input_choices_key"]
    assert frame[original.columns].equals(original), "Preprocessing altered source fields"
    positions = [row[choices_key].index(str(row[label_key])) for row in frame.to_dict("records")]
    bench = SimpleNamespace(bench_name=name, meta=copy.deepcopy(config["meta"]), bench_prompt_template=config.get("bench_prompt_template"))
    template, prompt_receipt = tool._resolve_prompt_template(bench, config["bench_dataflow_eval_type"])
    results = {}
    captured = []
    for label in "ABCD":
        path = folder / f"constant-{label}.jsonl"
        storage = Storage(frame, path)
        serving = ConstantServing(label)
        generator = Generator(eval_type=config["bench_dataflow_eval_type"], llm_serving=serving,
                              prompt_template=template, force_generate=True)
        generator.run(storage=storage, input_question_key=qkey, input_choices_key=choices_key, output_key="generated_ans")
        assert len(serving.prompts) == len(frame)
        if label == "A":
            for i, text in enumerate(serving.prompts):
                question = str(frame.iloc[i][qkey])
                captured.append(dict(row=i, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    own_question_present=question in text,
                    first_choice_present=str(frame.iloc[i][choices_key][0]) in text))
        stats = tool._rescore_choice_single(str(path), str(folder / f"stats-{label}.json"), {}, "generated_ans", label_key, bench.meta["evaluation"]["parser"])
        stats = tool._mark_stats_diagnostic(stats)
        # Key choice follows the exact key3_q_choices_a assignment in the native DataFlowEvalNode.
        bench.meta.update(pred_key="eval_pred", ref_key=label_key, eval_result=stats,
                          artifact_paths={"records_path": str(path)})
        metrics = Runner(max_workers=1).run_bench(bench, [{"name": "choice_accuracy", "priority": "primary"}])
        contract = Runner(max_workers=1).run_bench_with_contract(bench, bench.meta["evaluation"])
        report_score, report_source = Report()._resolve_report_score(bench, metrics, "choice_accuracy")
        results[label] = dict(native_diagnostic_score=stats["score"], native_valid=stats["valid_samples"],
            invalid_references=stats["invalid_references"], ordinary_metric=metrics["metrics"],
            contract_metric=contract.get("primary_metric_result"), report_score=report_score, report_source=report_source)
    shuffled_positions = []
    rng = random.Random(20261114)
    for row in original.to_dict("records"):
        choices = [str(row[k]) for k in config["meta"]["key_mapping"]["input_choices_key"]]
        rng.shuffle(choices)
        shuffled_positions.append(choices.index(str(row[label_key])))
    (folder / "prompt_index.jsonl").write_text("".join(json.dumps(r) + "\n" for r in captured))
    source_hashes = [hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest() for row in original.to_dict("records")]
    (folder / "source_row_hashes.json").write_text(json.dumps(source_hashes) + "\n")
    return dict(source_rows=len(frame), gold_position_counts=dict(Counter(positions)),
        native_question_present=sum(r["own_question_present"] for r in captured), native_choices_present=sum(r["first_choice_present"] for r in captured),
        baseline_results=results, prompt=prompt_receipt,
        seeded_shuffled_control=dict(gold_position_counts=dict(Counter(shuffled_positions)), constant_A_correct=sum(p == 0 for p in shuffled_positions),
                                    scope="Reference control using the authors' documented shuffle operation; no model generations."))


def main():
    plan = json.loads((HERE / "sources.json").read_bytes())
    native = load_native(plan)
    gallery = json.loads(native[0]["one_eval/utils/bench_table/bench_gallery.json"])["benches"]
    result, provenance = {}, {}
    for source in plan["dataset_sources"]:
        name = source["name"]
        if "hf" in source:
            frame, provenance[name] = hf_frame(source["hf"], source["split"])
        else:
            frame, provenance[name] = gpqa_frame(plan)
        config = next(b for b in gallery if b["bench_name"] == name)
        result[name] = audit(name, frame, config, native)
        print("POSITION_DATASET " + json.dumps({name: result[name]}, separators=(",", ":")), flush=True)
    summary = dict(one_eval_revision=plan["one_eval_revision"], datasets=result, source_provenance=provenance,
        dataflow=native[5], new_model_calls=0,
        boundary="Original native preprocessing, generator, choice-rescoring, MetricRunner, report score-selection methods. Source-loaded classes, pandas storage and constant serving adapters; no complete CLI or LLM report generation.")
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("POSITION_SUMMARY " + json.dumps(summary, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
