"""Preserve the original 40 blinded cases and add 24 diagnostic review cases."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
STUDY = Path(os.environ.get("EPISTEMICS_REVIEW_INPUTS", str(ROOT.parent))).resolve()
sys.path.insert(0, str(STUDY / "controls"))
from collect_controls import make, final_text
from compare_with_primary import read
from interpret_options import interpret


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def records(path):
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def build():
    prior = STUDY / "judge" / "human-packet"
    old = records(prior / "blind.jsonl")
    old_keys = {r["id"]: r for r in records(prior / "key.jsonl")}
    assert len(old) == 40
    public = list(old)
    keys = [{**old_keys[r["id"]], "panel": "original_40"} for r in old]
    used_sources = {r["source_question"] for r in keys}
    sources = json.loads((STUDY / "work" / "tab").read_bytes())
    witness_rows = records(STUDY / "archived" / "exact_witnesses.jsonl")
    for direction in ("gain", "loss"):
        selected = 0
        for row in sorted(witness_rows, key=lambda r: digest("review64-historic|" + r["archive"] + "|" + r["id"])):
            pid = row["id"]
            if row["direction"] != direction or pid not in sources or pid in used_sources:
                continue
            used_sources.add(pid)
            source = sources[pid]
            ident = digest("review64|historical|" + row["archive"] + "|" + pid)[:12]
            public.append(dict(id=ident, question=source["question"], options=source["choices"],
                               archived_reply=row["raw"], reader_option_or_unresolved=None))
            keys.append(dict(id=ident, source_question=pid, panel="historical_exact", direction=direction,
                             archive=row["archive"], official_answer=row["source_answer"],
                             expected_interpretation=row["unique_match"], original_prediction=row["original_prediction"]))
            selected += 1
            if selected == 6:
                break
        assert selected == 6

    cases, tasks, _ = make()
    final = read(STUDY / "controls", "capture/attempts.jsonl")
    tasks.sort(key=lambda t: digest("review64-numeric|" + t[0]["key"]))
    plan = {"correct": {"letter": 2, "letter_and_number": 2, "number": 1},
            "wrong": {"letter": 2, "letter_and_number": 1, "number": 1, "other_text": 2}}
    chosen = []
    used_tasks = set()
    for arm, formats in plan.items():
        for form, required in formats.items():
            n = 0
            for row, payload in tasks:
                record = final.get(row["key"], {})
                if row["arm"] != arm or not record.get("eligible") or row["key"] in used_tasks:
                    continue
                kind, value = interpret(row, cases[row["case"]], record["text"])
                if kind != form:
                    continue
                chosen.append((row, record, kind))
                used_tasks.add(row["key"])
                n += 1
                if n == required:
                    break
            assert n == required, (arm, form)
        if arm == "correct":
            for row, payload in tasks:
                record = final.get(row["key"], {})
                if row["arm"] == arm and row["key"] not in used_tasks and record.get("eligible"):
                    kind, value = interpret(row, cases[row["case"]], record["text"])
                    chosen.append((row, record, kind))
                    used_tasks.add(row["key"])
                    break
    assert len(chosen) == 12
    for row, record, kind in chosen:
        source = cases[row["case"]]
        ident = digest("review64|numeric|" + row["key"])[:12]
        public.append(dict(id=ident, question=source["question"], options=["A. " + row["value"]],
                           archived_reply=final_text(record["text"])[0], reader_option_or_unresolved=None))
        keys.append(dict(id=ident, source_question=source["id"], panel="numeric_control", arm=row["arm"],
                         model=row["model"], request_key=row["key"], supplied_value=row["value"],
                         official_answer=source["gold"][0], expected_format=kind,
                         response_id=record["response_id"], output_sha=record["output_sha"]))
    public.sort(key=lambda r: digest("review64-order|" + r["id"]))
    assert len(public) == len(keys) == len({r["id"] for r in public}) == 64
    assert all(set(r) == {"id", "question", "options", "archived_reply", "reader_option_or_unresolved"} for r in public)
    assert all(r["reader_option_or_unresolved"] is None for r in public)
    assert {r["id"] for r in old} <= {r["id"] for r in public}
    ROOT.mkdir(exist_ok=True)
    (ROOT / "blind.json").write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "coordinator-key.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keys))
    receipt = dict(cases=64, original_cases=40, additional_historical=12, additional_numeric=12,
                   historical_direction_counts=dict(Counter(r.get("direction") for r in keys if r["panel"] == "historical_exact")),
                   original_controls=8, reader_fields_blank=True,
                   original_source_sha256=digest((prior / "blind.jsonl").read_text()),
                   blind_sha256=digest((ROOT / "blind.json").read_text()))
    (ROOT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    build()
