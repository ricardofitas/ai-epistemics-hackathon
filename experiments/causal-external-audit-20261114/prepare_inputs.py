"""Select previously captured source records for the frozen causal diagnosis."""

import gzip
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
OLD = WORK / "source-audit"
CAPTURE = OLD / "default_contract_source_capture_20261113" / "capture"
HOLDOUT = WORK / "holdout" / "artifact" / "capture"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_rows(path):
    return [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]


def source_answer(bench, row):
    if bench == "sciq":
        return [row[key] for key in ("correct_answer", "distractor1", "distractor2", "distractor3")], 0
    if bench == "winogrande":
        return [row["option1"], row["option2"]], int(row["answer"]) - 1
    if bench == "lab-bench-language-agent-biology-benchmark":
        return [row["ideal"], *row["distractors"]], 0
    if bench == "medmcqa":
        return [row[key] for key in ("opa", "opb", "opc", "opd")], int(row["cop"])
    if bench == "mmlu":
        return row["choices"], int(row["answer"])
    return row["choices"]["text"], row["choices"]["label"].index(row["answerKey"])


def main():
    protocol = json.loads((ROOT / "PROTOCOL.json").read_text())
    gallery_path = CAPTURE / "one_eval__utils__bench_table__bench_gallery.json.gz"
    gallery_bytes = gzip.decompress(gallery_path.read_bytes())
    gallery_blob = hashlib.sha1(b"blob " + str(len(gallery_bytes)).encode() + b"\0" + gallery_bytes).hexdigest()
    assert gallery_blob == "67e88a261cf481933df1464aef2c60502931d8f7"
    gallery = {entry["bench_name"]: entry for entry in json.loads(gallery_bytes)["benches"]}
    dispositions = json.loads((CAPTURE / "DATASET_DISPOSITIONS.json").read_text())
    inputs = []
    provenance = []
    for panel in protocol["source_cases"]:
        bench = panel["bench"]
        if bench in ("arc-challenge", "openbookqa", "mmlu"):
            selected_path = HOLDOUT / bench / "SELECTED.jsonl.gz"
            source_path = HOLDOUT / bench / "SOURCE_ROWS.jsonl.gz"
            source_rows = read_rows(source_path)
            selected = read_rows(selected_path)
            for item in selected:
                assert item["record"] == source_rows[item["source_index"]]
        else:
            disposition = next(item for item in dispositions if item["bench"] == bench and item["split"] == panel["split"])
            source_path = CAPTURE / disposition["rows_file"]
            source_bytes = gzip.decompress(source_path.read_bytes())
            assert hashlib.sha256(source_bytes).hexdigest() == disposition["rows_sha256"]
            source_rows = [json.loads(line) for line in source_bytes.splitlines()]
            order = sorted(range(len(source_rows)), key=lambda index: (hashlib.sha256(canonical(source_rows[index]).encode()).hexdigest(), index))
            selected = [{"source_index": index, "record": source_rows[index]} for index in order[:panel["max_rows"]]]
        for item in selected:
            choices, gold = source_answer(bench, item["record"])
            assert 0 <= gold < len(choices)
            inputs.append({"bench": bench, "split": panel["split"], "source_index": item["source_index"], "record": item["record"], "expected_choices": choices, "gold_index": gold})
        provenance.append({"bench": bench, "rows_selected": len(selected), "source_rows": len(source_rows), "source_compressed_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(), "prior_captured_sources": True})
    payload = "".join(canonical(item) + "\n" for item in inputs).encode()
    (ROOT / "INPUTS.jsonl.gz").write_bytes(gzip.compress(payload, mtime=0))
    (ROOT / "GALLERY_SELECTED.json").write_text(json.dumps({item["bench"]: gallery[item["bench"]] for item in protocol["source_cases"]}, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "INPUT_PROVENANCE.json").write_text(json.dumps({"source_rows_reused": len(inputs), "gallery_git_blob": gallery_blob, "panels": provenance}, indent=2) + "\n")
    upstream = ROOT / "upstream"
    upstream.mkdir(exist_ok=True)
    sources = {
        "dataflow_eval_tool.py": OLD / "default_contract_audit_20261113" / "upstream" / "dataflow_eval_tool.py",
        "core_prompt.py": OLD / "default_contract_locked_support_v2_20261113" / "locked_support" / "dataflow" / "core" / "prompt.py",
        "core_text.py": OLD / "default_contract_locked_support_v2_20261113" / "locked_support" / "dataflow" / "prompts" / "core_text.py",
        "bench_answer_generator.py": CAPTURE / "dataflow_wheel__dataflow__operators__core_text__generate__bench_answer_generator.py",
        "LICENSE_DATAFLOW": OLD / "default_contract_audit_20261113" / "DATAFLOW_APACHE_LICENSE",
    }
    hashes = {}
    for name, path in sources.items():
        shutil.copyfile(path, upstream / name)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / "UPSTREAM_HASHES.json").write_text(json.dumps(hashes, indent=2) + "\n")
    print(json.dumps({"source_rows_reused": len(inputs), "panels": provenance}, indent=2))


if __name__ == "__main__":
    main()
