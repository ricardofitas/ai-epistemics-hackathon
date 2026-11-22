"""Freeze source item IDs without running inference."""
import argparse
import csv
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parents[1] / "evidence"

sys.path.insert(0, str(EVIDENCE / "scienceqa-20261115"))
from audit_wino import digest


def group_id(row):
    return digest(sorted(row[key].strip().casefold() for key in ("option1", "option2")))


def source_items(archive, protocol):
    with ZipFile(archive) as source:
        raw = source.read(protocol["dataset_member"])
        labels = source.read("winogrande_1.1/dev-labels.lst").decode().splitlines()
    items = {}
    groups = defaultdict(list)
    for index, line in enumerate(raw.splitlines()):
        row = json.loads(line)
        qid = row.pop("qID")
        assert set(row) == {"sentence", "option1", "option2", "answer"}
        assert row["answer"] == labels[index]
        assert row["answer"] in {"1", "2"} and row["sentence"].count("_") == 1
        assert row["option1"].strip().casefold() != row["option2"].strip().casefold()
        key = digest(row)
        assert key not in items
        item = dict(row, id=key, index=index, qid=qid)
        items[key] = item
        groups[group_id(row)].append(item)
    assert len(items) == len(labels) == 1267
    assert len({item["qid"] for item in items.values()}) == len(items)

    return items, groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    protocol = json.loads((ROOT / "pilot.json").read_text())
    items, groups = source_items(args.archive, protocol)
    earlier = EVIDENCE / "scienceqa-20261115" / "previous_wino_hashes.txt"
    excluded = set(earlier.read_text().splitlines())
    with (EVIDENCE / "paper-20261115" / "winogrande_scores.csv").open() as handle:
        paper = {(r["source_sha256"], int(r["source_index"])) for r in csv.DictReader(handle)}
    assert all(items[key]["index"] == index for key, index in paper)
    excluded.update(key for key, _ in paper)
    assert excluded <= items.keys()
    excluded_groups = {group_id(items[key]) for key in excluded}
    pairs = {}
    for group in groups.keys() - excluded_groups:
        eligible = []
        for first, second in itertools.combinations(groups[group], 2):
            if first["qid"].rsplit("-", 1)[0] != second["qid"].rsplit("-", 1)[0]:
                continue
            if first["answer"] == second["answer"]:
                continue
            if (first["option1"], first["option2"]) != (second["option1"], second["option2"]):
                continue
            a, b = first["sentence"].split(), second["sentence"].split()
            if len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1:
                eligible.append(sorted([first["id"], second["id"]]))
        if eligible:
            keys = min(eligible, key=digest)
            pairs[digest(keys)] = keys
    ordered = sorted(pairs.items())
    limit = protocol["pair_limit"]
    assert len(ordered) >= 2 * limit, len(ordered)
    result = {
        "validation_rows": len(items),
        "prior_prompted_item_ids": len(excluded),
        "excluded_option_groups": len(excluded_groups),
        "eligible_pairs": len(ordered),
        "pilot": dict(ordered[:limit]),
        "heldout": dict(ordered[limit:2 * limit]),
    }
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
