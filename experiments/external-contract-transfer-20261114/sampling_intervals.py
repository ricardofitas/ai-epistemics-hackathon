"""Exploratory uncertainty for the prospective panel, resampling source questions or SQuAD articles."""
from collections import defaultdict
import json
import math
from pathlib import Path
import random
from scoring import MODELS, stats
from design import trials

def percentile(values, p):
    values=sorted(values)
    at=(len(values)-1)*p
    i=math.floor(at); mix=at-i
    return (1-mix)*values[i]+mix*values[min(i+1,len(values)-1)]

def main():
    root=Path(__file__).resolve().parent
    cases=json.loads((root/"cases.json").read_bytes())
    final={}
    for f in sorted((root/"capture").glob("s*/attempts.jsonl")):
        for line in f.read_bytes().splitlines():
            a=json.loads(line)
            if a["key"] in final:
                assert final[a["key"]]["http"]==429
            final[a["key"]]=a
    planned=trials(cases)
    groups=stats(cases, planned, final)
    scores={}
    for model in MODELS:
        scores[model]={}
        for ds in ("squad","tabmwp"):
            cluster=defaultdict(list)
            for (m,d,idx),arms in groups.items():
                if m!=model or d!=ds:continue
                vals=[arms[a][0] for a in ("choice_clear","choice_none","free_none","free_clear")]
                def bounds(n):
                    low=high=0
                    for j,v in enumerate(vals[:n]):
                        sign=1 if j%2==0 else -1
                        low+=(min(0,sign) if v is None else sign*v)
                        high+=(max(0,sign) if v is None else sign*v)
                    return low,high
                label=cases[idx]["group"] if ds=="squad" else cases[idx]["id"]
                cluster[label].append((*bounds(2),*bounds(4)))
            sums=[(len(rows),*[sum(x[j] for x in rows) for j in range(4)]) for rows in cluster.values()]
            rng=random.Random(20261114)
            boots=[[],[],[],[]]
            for rep in range(5000):
                draw=rng.choices(sums,k=len(sums))
                size=sum(x[0] for x in draw)
                for j in range(4):
                    boots[j].append(100*sum(x[1+j] for x in draw)/size)
            scores[model][ds]={"questions":sum(x[0] for x in sums),"clusters":len(sums),
                "choice_carrier_outer_percentiles_pp":[round(percentile(boots[0],.025),2),round(percentile(boots[1],.975),2)],
                "interaction_outer_percentiles_pp":[round(percentile(boots[2],.025),2),round(percentile(boots[3],.975),2)]}
    result=dict(method="Exploratory 5000-resample descriptive percentile envelope. Cluster SQuAD by article and resample TabMWP questions. Bound each unavailable per-source response in each resample. Pointwise, conditional on source selection, no multiplicity or universe-wide coverage claim.",scores=scores)
    (root/"results"/"sampling-intervals.json").write_text(json.dumps(result,indent=2)+"\n")

if __name__=="__main__":
    main()
