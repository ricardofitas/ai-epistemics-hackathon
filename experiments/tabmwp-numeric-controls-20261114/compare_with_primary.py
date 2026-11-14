"""Combine observed normalized wrong answers, letter-only endorsements, and primary conditions on matched items."""
from collections import Counter
from pathlib import Path
import json
import re
import sys

from collect_controls import BASE, MODELS, make
from scoring import final_text, grade, number

def option_letter(text):
    ans=final_text(text)[0]
    return bool(re.fullmatch(r"(?:option\s+)?(?:\(a\)|\[a\]|a)[.:]?",ans.strip(),re.I))

def read(folder,pattern):
    found={}
    for f in sorted(folder.glob(pattern)):
        for a in map(json.loads,f.read_bytes().splitlines()):
            if a["key"] in found:assert found[a["key"]]["http"]==429
            found[a["key"]]=a
    return found

def compare(numeric_folder, primary):
    cases,tasks,_=make()
    extra=read(numeric_folder,"capture/attempts.jsonl")
    sources={row["case"] for row,p in tasks}
    groups={m:{arm:Counter() for arm in ["numeric_correct","numeric_wrong","free_clear","free_none","choice_clear","choice_none"]} for m in MODELS}
    for row,p in tasks:
        counts=groups[row["model"]]["numeric_"+row["arm"]];counts["n"]+=1
        a=extra.get(row["key"],{});case=cases[row["case"]]
        if not a.get("eligible"):counts["unknown"]+=1;continue
        value=number(final_text(a["text"])[0],case["unit"])
        counts["explicitly_says_displayed_number"]+=int(value==number(row["value"],case["unit"]))
        counts["option_A_only"]+=int(option_letter(a["text"]))
        counts["source_accurate"]+=int(value==number(case["gold"][0],case["unit"]))
    orig=read(primary,"capture/*/attempts.jsonl")
    for a in orig.values():
        if a["case"] not in sources:continue
        counts=groups[a["model"]][a["arm"]];counts["observed"]+=1
        if not a.get("eligible"):counts["unknown"]+=1;continue
        acc,dummy,_=grade(cases[a["case"]],a["text"])
        counts["source_accurate"]+=acc;counts["dummy"]+=dummy
    for data in groups.values():
        for arm in ["free_clear","free_none","choice_clear","choice_none"]:
            g=data[arm];g["planned"]=24;g["unstarted"]=24-g["observed"]
    (numeric_folder/"matched-primary-comparison.json").write_text(json.dumps(groups,indent=2,sort_keys=True)+"\n")
    return groups

if __name__=="__main__":
    print(json.dumps(compare(Path(sys.argv[1]),Path(sys.argv[2])),sort_keys=True))
