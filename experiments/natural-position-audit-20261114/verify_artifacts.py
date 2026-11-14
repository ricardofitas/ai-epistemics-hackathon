"""Independent JSON/hash verifier; imports none of the audited evaluator code."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile


def rows(archive, path):
    # splitlines() also splits Unicode line separators inside JSON strings.
    return [json.loads(line) for line in archive.read(path).decode().split("\n") if line]


def verify(entrypoint_path, repair_path, repair_sha256):
    result = {}
    native_hash = hashlib.sha256(Path(entrypoint_path).read_bytes()).hexdigest()
    assert native_hash == "0fff22307ea63ae0bbe15a9e03088344ce9479cf5d64d4d196e03efa2ed9871b"
    with zipfile.ZipFile(entrypoint_path) as z:
        summary = json.loads(z.read("entrypoint-summary.json"))
        source_cases = rows(z, "entrypoint_records/cupcase/source-before-native.jsonl")
        for name, dataset in summary["datasets"].items():
            result[name] = {}
            source = rows(z, f"entrypoint_records/{name}/source-before-native.jsonl")
            for label, baseline in dataset["baselines"].items():
                prefix = f"entrypoint_records/{name}/constant-{label}/"
                record_path = next(n for n in z.namelist() if n.startswith(prefix) and n.endswith("step_step2.jsonl"))
                assert hashlib.sha256(z.read(record_path)).hexdigest() == baseline["result_sha256"]
                records = rows(z, record_path)
                prompts = rows(z, prefix + "captured-prompts.jsonl")
                index = rows(z, prefix + "prompt-index.jsonl")
                assert len(records) == len(prompts) == len(source) == dataset["source_rows"]
                assert all(r["generated_ans"] == f"<answer>{label}</answer>" for r in records)
                valid = sum(bool(r["eval_valid"]) for r in records)
                correct = sum(r["eval_score"] == 1 for r in records if r["eval_valid"])
                qkey = {"cupcase":"clean_case_presentation", "sciq":"question", "gpqa":"Question", "mmlu":"question"}[name]
                present = sum(s[qkey] in p["prompt"] for s,p in zip(source,prompts))
                assert (valid,correct,present) == (baseline["valid_rows"],baseline["correct_rows"],baseline["own_question_present"])
                assert abs(correct/valid - baseline["report_score"]) < 1e-12
                assert all(hashlib.sha256(p["prompt"].encode()).hexdigest() == i["prompt_sha256"] for p,i in zip(prompts,index))
                result[name][label] = dict(rows=len(records),valid=valid,correct=correct,question_present=present,report_score=baseline["report_score"])
    assert hashlib.sha256(Path(repair_path).read_bytes()).hexdigest() == repair_sha256
    with zipfile.ZipFile(repair_path) as z:
        summary = json.loads(z.read("repair-summary.json"))
        dataset = summary["repaired_cupcase"]
        source = rows(z, "entrypoint_records/cupcase-repaired/source-before-native.jsonl")
        fields = ["clean_case_presentation","correct_diagnosis","distractor1","distractor2","distractor3"]
        assert len(source) == len(source_cases) == 3562
        for before,after in zip(source_cases,source):
            assert all(before[k] == after[k] for k in fields)
            assert sorted(after["neutral_choices"]) == sorted(before[k] for k in fields[1:])
        result["cupcase_repaired"] = {}
        for label,baseline in dataset["baselines"].items():
            prefix = f"entrypoint_records/cupcase-repaired/constant-{label}/"
            record_path = next(n for n in z.namelist() if n.startswith(prefix) and n.endswith("step_step2.jsonl"))
            assert hashlib.sha256(z.read(record_path)).hexdigest() == baseline["result_sha256"]
            records = rows(z,record_path)
            prompts = rows(z,prefix+"captured-prompts.jsonl")
            assert len(records) == len(prompts) == 3562
            reference_drifts = []
            independent_correct = 0
            for row_id,(before,record,prompt) in enumerate(zip(source_cases,records,prompts)):
                assert all(record[k] == before[k] for k in fields)
                assert before["clean_case_presentation"] in prompt["prompt"]
                assert record["generated_ans"] == f"<answer>{label}</answer>"
                expected_label = "ABCD"[record["neutral_choices"].index(before["correct_diagnosis"])]
                independent_correct += label == expected_label
                if record["eval_ref_choice"] != expected_label:
                    # Preserve observed residual scorer drift instead of forcing
                    # the preregistered corrected-baseline prediction to pass.
                    import re
                    normalize = lambda x: re.sub(r"\s+", " ", str(x).strip()).casefold()
                    distinct = list(dict.fromkeys(normalize(c) for c in record["neutral_choices"]))
                    deduplicated_label = "ABCD"[distinct.index(normalize(before["correct_diagnosis"]))]
                    assert record["eval_ref_choice"] == deduplicated_label
                    reference_drifts.append(dict(row=row_id,displayed_gold=expected_label,parser_gold=deduplicated_label))
                assert record["eval_score"] == float(label == record["eval_ref_choice"])
            correct = sum(r["eval_score"] == 1 for r in records)
            assert correct == {"A":905,"B":888}[label] == baseline["correct_rows"]
            assert independent_correct == {"A":905,"B":882}[label]
            assert len(reference_drifts) == 21
            result["cupcase_repaired"][label] = dict(rows=3562,valid=3562,correct=correct,
                independent_displayed_choice_correct=independent_correct,
                preregistered_prediction_met=correct == independent_correct,
                residual_gold_reference_drifts=reference_drifts,
                question_present=3562,report_score=correct/3562)
    return dict(status="PASS_EVIDENCE_RECOUNTS_WITH_RESIDUAL_REFERENCE_DRIFT_RETAINED", entrypoint_artifact_sha256=native_hash,repair_artifact_sha256=repair_sha256,
                new_model_calls=0,all_source_CUPCase_questions_labels_and_option_multisets_exact=True,results=result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("entrypoint_zip")
    parser.add_argument("repair_zip")
    parser.add_argument("repair_sha256")
    args = parser.parse_args()
    print(json.dumps(verify(args.entrypoint_zip,args.repair_zip,args.repair_sha256),indent=2))
