"""Prespecified final-answer endpoint, scored against source annotations."""
import csv
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
import re
import string
import sys
from pathlib import Path

from design import ARMS, MODELS, canonical, digest, payload, trials

ANSWER = re.compile(r"<answer\b[^>]*>(.*?)</answer\s*>", re.I | re.S)
NUMBER = re.compile(r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:/\d+)?")
def final_text(text):
    matches=ANSWER.findall(text)
    if matches:
        return matches[-1].strip(), "tag"
    lines=[l.strip() for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return "", "empty"
    line=lines[-1]
    return re.sub(r"^(?:final answer|answer)\s*:\s*", "", line, flags=re.I).strip(), "last_line"

def squad_norm(s):
    s=s.lower().translate(str.maketrans("", "", string.punctuation))
    return " ".join(re.sub(r"\b(a|an|the)\b", " ", s).split())

def number(s, unit):
    s=s.strip().strip("*").strip().removesuffix(".").strip().replace("−","-")
    if unit.startswith("$"):
        s=s.removeprefix("$").strip()
    suffix=unit.strip().lstrip("$, ").strip()
    if suffix and s.casefold().endswith(" "+suffix.casefold()):
        s=s[:-len(suffix)].strip()
    if not NUMBER.fullmatch(s):
        return None
    try:
        return Fraction(s.replace(",",""))
    except (ValueError,ZeroDivisionError):
        return None

def grade(case, text):
    ans, extraction=final_text(text)
    if case["dataset"]=="squad":
        gold={squad_norm(g) for g in case["gold"]}
        # Preserve literal articles as valid aliases when normalization empties both strings.
        correct=bool(ans) and squad_norm(ans) in gold
    else:
        gold={number(g,case["unit"]) for g in case["gold"]}
        if None in gold:
            raise ValueError("unparseable numeric reference")
        value=number(ans,case["unit"]);correct=value is not None and value in gold
    option=bool(re.fullmatch(r"(?:[\(\[]?a[\)\].:]?(?:\s*[-:.)]?\s*none(?: of the above)?)?|none(?: of the above)?)\s*[.!]?",ans,re.I))
    return int(correct), int(option), extraction

def stats(cases, planned, final):
    groups=defaultdict(dict)
    for row in planned:
        k=row["key"]; c=cases[row["case"]]
        s=final.get(k,{})
        if s.get("eligible"):
            if (s.get("returned_model")!=row["model"] or s.get("request_sha")!=row["request_sha"]
                    or s.get("output_sha")!=digest(s["text"].encode())):
                raise ValueError("scoring provenance mismatch")
            value=grade(c,s["text"])
        else:
            value=(None,None,None)
        groups[(row["model"],c["dataset"],row["case"])][row["arm"]]=value
    return groups

def summarize(groups):
    by_model={}
    contrasts={"choice_carrier":["choice_clear","choice_none"],
               "free_carrier":["free_clear","free_none"],
               "interaction":["choice_clear","choice_none","free_none","free_clear"]}
    for m in MODELS:
        by_model[m]={}
        for ds in ("squad","tabmwp"):
            source=[v for (model,d,_),v in groups.items() if (model,d)==(m,ds)]
            if not source:continue
            scores={}
            for arm in ARMS:
                a=[d[arm] for d in source]
                scores[arm]={"n":len(a),"correct":sum(v[0]==1 for v in a),
                             "unknown":sum(v[0] is None for v in a),"dummy":sum(v[1]==1 for v in a),
                             "fallback":sum(v[2]=="last_line" for v in a)}
            effects={}
            for name,arms in contrasts.items():
                intervals=[];cc=[]
                for v in source:
                    low=high=0;ok=True
                    for j,arm in enumerate(arms):
                        sign=1 if j%2==0 else -1
                        x=v[arm][0]
                        if x is None:
                            low+=min(0,sign);high+=max(0,sign);ok=False
                        else:
                            low+=sign*x;high+=sign*x
                    intervals.append((low,high))
                    if ok:cc.append(low)
                n=len(source)
                effects[name]={"n":n,"lower_pp":round(100*sum(v[0] for v in intervals)/n,3),
                               "upper_pp":round(100*sum(v[1] for v in intervals)/n,3),
                               "complete_pairs_or_sets":len(cc),"complete_only_pp":round(100*sum(cc)/len(cc),3) if cc else None}
            by_model[m][ds]={"scores":scores,"contrasts":effects}
    return by_model

def report(folder, case_path, subset):
    cases=json.loads(Path(case_path).read_bytes())
    manifest=trials(cases)
    planned=[r for r in manifest if r["case"] in subset]
    keys={r["key"] for r in planned}
    attempts=[]
    for p in sorted(folder.rglob("attempts.jsonl")):
        attempts.extend(json.loads(s) for s in p.read_bytes().splitlines() if s.strip())
    seen=set();final={};response_ids=set()
    for a in attempts:
        ident=(a["key"],a["attempt"])
        if ident in seen or a["key"] not in keys:raise ValueError("duplicate or unexpected attempt")
        seen.add(ident)
        if a.get("response_id"):
            if a["response_id"] in response_ids:raise ValueError("duplicate response id")
            response_ids.add(a["response_id"])
        if a["key"] in final and final[a["key"]].get("http")!=429:raise ValueError("duplicate nonrejected request")
        final[a["key"]]=a
    groups=stats(cases,planned,final)
    statuses=dict(Counter(a["status"] for a in final.values()))
    return dict(planned=len(keys), started_unique=len(final),attempts=len(attempts),
                eligible=sum(bool(a.get("eligible")) for a in final.values()),status=statuses,
                explicit_429=sum(a.get("http")==429 for a in attempts),unstarted=len(keys)-len(final),
                input_tokens=sum((a.get("usage") or {}).get("input_tokens",0) for a in attempts),
                output_tokens=sum((a.get("usage") or {}).get("output_tokens",0) for a in attempts),
                reported_cost=sum(float((a.get("usage") or {}).get("cost",0) or 0) for a in attempts),
                models=summarize(groups))
