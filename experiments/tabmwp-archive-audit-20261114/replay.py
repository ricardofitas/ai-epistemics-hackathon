"""Independent replay and prespecified tie-break sensitivity on authors' released outputs."""
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path
import collections
import hashlib
import json
import re
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "external-contract-transfer-20261114"
if not STUDY.exists():
    STUDY = HERE.parent / "src"
sys.path.insert(0, str(STUDY))
from scoring import number


def download(item, revision):
    path, expected = item
    url = f"https://raw.githubusercontent.com/lupantech/PromptPG/{revision}/{path}"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    git_blob = b"blob " + str(len(data)).encode() + b"\0" + data
    if hashlib.sha1(git_blob).hexdigest() != expected:
        raise ValueError(f"Unverified input: {path}")
    return path, json.loads(data)


def similarity(answer, output):
    if answer == output:
        return 3
    def clean(value):
        value = value.replace('"', "").replace("'", "")
        return re.sub(r"[{}^\\`\u2047<]", " ", value)
    answer, output = clean(answer), clean(output)
    if answer == output:
        return 2
    if " " in answer or " " in output:
        a, b = answer.split(" "), output.split(" ")
        return len(set(a) & set(b)) / max(len(a), len(b))
    return 0


def native_normal(value, unit):
    value = re.sub(r"^[\$]", "", value)
    value = re.sub(r"[,.\/]$", "", value)
    if re.fullmatch(r"[-+]?[\d,./]+", value):
        value = value.replace(",", "")
        if re.fullmatch(r"[-+]?\d+", value):
            val = int(value)
        elif "/" in value:
            numerator, denominator = value.split("/")[:2]
            val = round(float(numerator) / float(denominator), 3)
        else:
            val = round(float(value), 3)
        return re.sub(r"\.[0]+$", "", str(val)).lower()
    return (value.replace(unit, "").strip() if unit else value).lower()


def replay(path, archive, source, panel):
    rows = archive["results"]
    assert rows.keys() == source.keys()
    c = collections.Counter()
    zero_ids, credited_ids = set(), set()
    for key, row in rows.items():
        item = source[key]
        unit, gold, opts = item["unit"], item["answer"], item["choices"]
        assert gold == row["answer"]
        official = row["true_false"]
        assert isinstance(official, bool)
        assert official == (native_normal(row["prediction"], unit) == native_normal(gold, unit))
        c["correct"] += official
        c["strict_panel_rows"] += key in panel
        if key in panel:
            assert not opts and panel[key]["gold"] == [gold]
            target = number(gold, panel[key]["unit"])
            assert target is not None
            strict = number(row["prediction"], panel[key]["unit"]) == target
            c["strict_panel_correct"] += strict
            c["official_panel_correct"] += official
            c["panel_disagreements"] += strict != official
        if not opts:
            continue
        c["choice_rows"] += 1
        scores = [similarity(opt, row["output"]) for opt in opts]
        selected = scores.index(max(scores))
        assert opts[selected] == row["prediction"]
        if max(scores) == 0 and len(opts) >= 2:
            zero_ids.add(key)
            if official:
                credited_ids.add(key)
            last = native_normal(opts[-1], unit) == native_normal(gold, unit)
            c["zero_first_correct"] += official
            c["zero_last_correct"] += last
            c["zero_changed_flags"] += last != official
    n = len(rows)
    assert c["strict_panel_rows"] == 100
    assert n == archive["count"] and c["correct"] == archive["correct"]
    assert abs(archive["acc"] - 100 * c["correct"]/n) < 1e-8
    abstain = c["correct"] - c["zero_first_correct"]
    counts = {key: c[key] for key in (
        "choice_rows", "zero_first_correct", "zero_last_correct", "zero_changed_flags",
        "official_panel_correct", "strict_panel_correct", "panel_disagreements")}
    counts.update(total=n, original=c["correct"], zero_rows=len(zero_ids), abstain=abstain,
                  last=abstain+c["zero_last_correct"])
    return counts, zero_ids, credited_ids


def main():
    manifest = json.loads((HERE / "sources.json").read_text())
    with ThreadPoolExecutor(4) as pool:
        inputs = dict(pool.map(lambda item: download(item, manifest["source_rev"]),
                               manifest["blobs"].items()))
    source = inputs.pop("data/tabmwp/problems_test.json")
    panel = {case["id"]:case for case in json.loads((STUDY/"cases.json").read_text())
             if case["dataset"] == "tabmwp"}
    assert len(panel) == 100
    scores, affected, awarded = {}, set(), set()
    for path, archive in sorted(inputs.items()):
        scores[path], zero_ids, credited_ids = replay(path, archive, source, panel)
        affected.update(zero_ids)
        awarded.update(credited_ids)
    inverted = {}
    for alternative in ("last", "abstain"):
        inverted[alternative] = [[a,b] for a,b in combinations(scores,2)
             if (scores[a]["original"]-scores[b]["original"])
                * (scores[a][alternative]-scores[b][alternative]) < 0]
    result = dict(source_revision=manifest["source_rev"],files=scores,
                  unique_test_items=len(source),unique_zero_tie_items=len(affected),
                  unique_items_credited_by_zero_tie=len(awarded),strict_inversions=inverted)
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print("ARCHIVE_SUMMARY " + json.dumps(result, sort_keys=True, separators=(",",":")))


if __name__ == "__main__":
    main()
