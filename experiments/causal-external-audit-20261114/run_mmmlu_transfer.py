"""Acquire the pinned official FR_FR CSV and test the frozen binding prediction."""

import csv
import datetime
import gzip
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

import audit_shared_causes as audit


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "transfer"


def main():
    protocol = json.loads((ROOT / "MMMLU_PROTOCOL.json").read_text())
    metadata = json.loads((OUT / "OFFICIAL_METADATA.json").read_text())
    revision = metadata["sha"]
    source_path = "test/mmlu_FR-FR.csv"
    assert source_path in {item["rfilename"] for item in metadata["siblings"]}
    url = "https://huggingface.co/datasets/openai/MMMLU/resolve/" + revision + "/" + source_path
    with urlopen(Request(url, headers={"User-Agent": "epistemics-research-source-audit"}), timeout=45) as response:
        payload = response.read()
    (OUT / "mmlu_FR-FR.csv").write_bytes(payload)
    receipt_path = OUT / "ACQUISITION_ORDER.json"
    receipts = json.loads(receipt_path.read_text())
    receipts.append({"url": url, "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    receipt_path.write_text(json.dumps(receipts, indent=2) + "\n")
    records = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    canonical = lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    order = sorted(range(len(records)), key=lambda index: (hashlib.sha256(canonical(records[index]).encode()).hexdigest(), index))
    cases = []
    source_errors = []
    for index in order[:100]:
        row = records[index]
        try:
            choices = [row[key] for key in ("A", "B", "C", "D")]
            gold = "ABCD".index(row["Answer"].strip())
            cases.append({"bench": "mmmlu", "split": "test", "source_index": index, "record": row, "expected_choices": choices, "gold_index": gold})
        except (KeyError, ValueError) as error:
            source_errors.append({"source_index": index, "error": repr(error)})
    gallery = json.loads((ROOT / "GALLERY_FULL.json").read_text())
    entry = next(item for item in gallery["benches"] if item["bench_name"] == "mmmlu")
    for name, expected in json.loads((ROOT / "UPSTREAM_HASHES.json").read_text()).items():
        assert hashlib.sha256((ROOT / "upstream" / name).read_bytes()).hexdigest() == expected
    preprocessor, generator = audit.load_native_classes()
    panels = {}
    captures = []
    errors = list(source_errors)
    for condition in protocol["conditions"]:
        try:
            result, rows = audit.run_condition(preprocessor, generator, entry, cases, condition)
            panels[condition] = result
            captures.extend(rows)
        except Exception as error:
            errors.append({"condition": condition, "error": repr(error)})
    report = {
        "status": "complete" if not errors else "partial",
        "source_repository": "openai/MMMLU", "source_revision": revision,
        "config": "FR_FR", "split": "test", "source_file": source_path,
        "source_rows": len(records), "selected_rows": min(100, len(records)),
        "source_rows_evaluable": len(cases), "condition_records": len(captures),
        "source_file_sha256": hashlib.sha256(payload).hexdigest(),
        "provider_model_requests": 0, "errors": errors, "panels": panels,
        "scope": protocol["scope"], "prior_exposure": protocol["prior_exposure"],
    }
    (OUT / "SUMMARY.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    for name, items in (("SELECTED.jsonl.gz", cases), ("CAPTURES.jsonl.gz", captures)):
        data = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items).encode()
        (OUT / name).write_bytes(gzip.compress(data, mtime=0))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
