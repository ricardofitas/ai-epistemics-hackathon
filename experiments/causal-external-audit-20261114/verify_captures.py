"""Reconcile captured prompt text with source rows without the native renderer."""

from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_gzip(path):
    return [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]


def main():
    gallery = json.loads((ROOT / "GALLERY_SELECTED.json").read_text())
    inputs = {(row["bench"], row["source_index"]): row for row in read_gzip(ROOT / "INPUTS.jsonl.gz")}
    captures = read_gzip(ROOT / "CAPTURES.jsonl.gz")
    counts = defaultdict(Counter)
    for capture in captures:
        key = capture["bench"], capture["source_index"]
        source = inputs[key]
        mapping = gallery[capture["bench"]]["meta"]["key_mapping"]
        question = str(source["record"][mapping["input_question_key"]])
        expected = [str(choice).strip() for choice in source["expected_choices"]]
        displayed = [str(choice).strip() for choice in capture["displayed_choices"]]
        assert hashlib.sha256(capture["prompt"].encode()).hexdigest() == capture["prompt_sha256"]
        assert (question in capture["prompt"]) == capture["question_bound"]
        assert (displayed == expected) == capture["choices_preserved"]
        assert (expected[source["gold_index"]] in displayed) == capture["gold_present"]
        assert all(choice in capture["prompt"] for choice in displayed)
        panel = counts[(capture["bench"], capture["condition"])]
        panel["rows"] += 1
        for field in ("question_bound", "choices_preserved", "gold_present"):
            panel[field] += capture[field]
    summary = json.loads((ROOT / "SUMMARY.json").read_text())
    for (bench, condition), values in counts.items():
        for field, value in values.items():
            assert summary["panels"][bench][condition][field] == value
    transfer = ROOT / "transfer"
    raw = (transfer / "mmlu_FR-FR.csv").read_bytes()
    transfer_summary = json.loads((transfer / "SUMMARY.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == transfer_summary["source_file_sha256"]
    official = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    canonical = lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    order = sorted(range(len(official)), key=lambda index: (hashlib.sha256(canonical(official[index]).encode()).hexdigest(), index))[:100]
    selected = read_gzip(transfer / "SELECTED.jsonl.gz")
    assert [row["source_index"] for row in selected] == order
    sources = {row["source_index"]: row for row in selected}
    paired = defaultdict(dict)
    for capture in read_gzip(transfer / "CAPTURES.jsonl.gz"):
        source = sources[capture["source_index"]]
        row = official[capture["source_index"]]
        assert row == source["record"]
        assert capture["displayed_choices"] == [row[key] for key in ("A", "B", "C", "D")]
        assert source["gold_index"] == "ABCD".index(row["Answer"].strip())
        assert (row["Question"] in capture["prompt"]) == capture["question_bound"]
        assert capture["choices_preserved"] and capture["gold_present"]
        assert hashlib.sha256(capture["prompt"].encode()).hexdigest() == capture["prompt_sha256"]
        paired[capture["source_index"]][capture["condition"]] = capture
    for index, conditions in paired.items():
        native, repaired = conditions["native"], conditions["bind_source_symbols"]
        assert "{{Question}}" in native["prompt"]
        predicted = native["prompt"].replace("{{Question}}", "{" + official[index]["Question"] + "}")
        assert predicted == repaired["prompt"]
        assert not native["question_bound"] and repaired["question_bound"]
    assert set(paired) == set(sources)
    assert len(paired) == transfer_summary["selected_rows"] == 100
    assert transfer_summary["panels"]["native"]["question_bound"] == 0
    assert transfer_summary["panels"]["bind_source_symbols"]["question_bound"] == 100
    result = {
        "status": "PASS", "root_source_rows_reused": len(inputs),
        "root_condition_records": len(captures), "new_native_contract_source_rows": len(selected),
        "transfer_condition_records": 2 * len(paired),
        "transfer_exact_predicted_prompt_substitutions": len(paired),
        "verification_method": "Source/capture/hash/selection reconciliation with direct string substitution, without loading the native renderer.",
        "limits": "Single executor reconciliation. The study uses previously known mechanisms and one new native contract. MMMLU translates MMLU, so source meaning may overlap prior English MMLU items. No global blind validation, model accuracy or external-impact validation.",
    }
    (ROOT / "VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
