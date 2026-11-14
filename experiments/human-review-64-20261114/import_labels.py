"""Validate a filled reader workbook against the frozen 64-case packet."""
import argparse
from collections import Counter
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def cell_text(cell, shared):
    if cell is None:
        return ""
    if cell.get("t") == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(f"{{{NS}}}t"))
    value = cell.find(f"{{{NS}}}v")
    if value is None:
        return ""
    if cell.get("t") == "s":
        return shared[int(value.text)]
    return value.text or ""


def parse(path):
    expected = {r["id"]: r for r in json.loads((ROOT / "blind.json").read_bytes())}
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(t.text or "" for t in item.iter(f"{{{NS}}}t"))
                      for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet = next(s for s in book.findall(f"{{{NS}}}sheets/{{{NS}}}sheet") if s.get("name") == "Revisao")
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels if r.get("Id") == sheet.get(f"{{{REL}}}id"))
        name = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
        tree = ET.fromstring(archive.read(name))
        cells = {c.get("r"): c for c in tree.iter(f"{{{NS}}}c")}
        labels = []
        seen = set()
        for row in tree.iter(f"{{{NS}}}row"):
            n = int(row.get("r"))
            if n < 12:
                continue
            ident = cell_text(cells.get(f"A{n}"), shared)
            if not ident:
                continue
            if ident not in expected or ident in seen:
                raise ValueError("Unexpected or duplicate review identifier")
            seen.add(ident)
            ref = expected[ident]
            original = [ref["question"], "\n".join(f"{i+1}) {s}" for i, s in enumerate(ref["options"])), ref["archived_reply"]]
            observed = [cell_text(cells.get(f"{col}{n}"), shared) for col in "BCD"]
            if original != observed:
                raise ValueError(f"Source text changed for case {ident}")
            value = cell_text(cells.get(f"E{n}"), shared).strip().upper()
            allowed = {str(i+1) for i in range(len(ref["options"]))} | {"INDETERMINADA", ""}
            if value not in allowed:
                raise ValueError(f"Invalid option for case {ident}")
            labels.append(dict(id=ident, selection=value or None,
                               other_result=cell_text(cells.get(f"F{n}"), shared)))
        if seen != expected.keys():
            raise ValueError("Review source rows are missing")
        person = cell_text(cells.get("B4"), shared).strip()
    counts = Counter("pending" if r["selection"] is None else "indeterminate" if r["selection"] == "INDETERMINADA" else "option" for r in labels)
    return dict(reviewer=person, planned=64, classified=64-counts["pending"], counts=counts, labels=labels)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("workbook", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = parse(args.workbook)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "labels"}))
