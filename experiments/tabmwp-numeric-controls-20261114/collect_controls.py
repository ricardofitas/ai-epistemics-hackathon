from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from decimal import Decimal
from fractions import Fraction
import gzip
import json
import os
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"external-contract-transfer-20261114"
if not BASE.exists():BASE=HERE.parent/"src"
sys.path.insert(0,str(BASE))
from design import MODELS, RATES, canonical, digest, payload
from scoring import final_text, number
from run_panel import append, fetch, output_text

def make():
    cases=json.loads((BASE/"cases.json").read_bytes())
    items=[(i,r) for i,r in enumerate(cases) if 150<=i<200 and r["dataset"]=="tabmwp"]
    assert len(items)==25
    items.sort(key=lambda x:digest(("20261114-numeric-option-v1|"+x[1]["id"]).encode()))
    tasks=[]
    for i,r in items[:24]:
        truth=r["gold"][0]
        norm=number(truth,r["unit"])
        if "/" in truth:
            wrong=str(norm+1)
        else:
            wrong=format(Decimal(truth.replace(",","").strip("$"))+1,"f")
        assert number(wrong,r["unit"])==norm+1
        for m in MODELS:
            for arm,value in (("correct",truth),("wrong",wrong)):
                p=payload(r,m,"choice_none",i)
                assert p["input"].count("Options:\nA. None")==1
                p["input"]=p["input"].replace("Options:\nA. None","Options:\nA. "+value)
                row={"key":f"tab-{r['id']}-{MODELS.index(m)}-{arm}","case":i,"model":m,
                     "arm":arm,"request_sha":digest(canonical(p)),"value":value}
                tasks.append((row,p))
    tasks.sort(key=lambda x:digest(("20261114-option-order|"+x[0]["key"]).encode()))
    assert len({r["request_sha"] for r,p in tasks})==192
    limit=sum(3*((len(p["input"].encode())+1024)*RATES[r["model"]][0]+p["max_output_tokens"]*RATES[r["model"]][1])/1e6 for r,p in tasks)
    assert limit<9
    return cases,tasks,limit

def capture(tasks):
    folder=HERE/"capture"
    (folder/"terminal").mkdir(parents=True,exist_ok=False)
    pending=tasks; key=os.environ["ADAPTION_API_KEY"]
    for attempt in (1,2,3):
        again=[]
        with ThreadPoolExecutor(max_workers=3) as pool:
            for pos in range(0,len(pending),3):
                futures={}; delay=0.
                for row,p in pending[pos:pos+3]:
                    append(folder/"intent.jsonl",dict(key=row["key"],attempt=attempt,request_sha=row["request_sha"]))
                    futures[pool.submit(fetch,row,p,attempt,key,folder)]=(row,p)
                    time.sleep(0.7)
                for f in as_completed(futures):
                    a=f.result()
                    append(folder/"attempts.jsonl",a)
                    if a.get("http") in (401,402,403,404) or a.get("returned_model") not in (None,a["model"]):
                        raise RuntimeError("provider identity or access")
                    if a.get("http")==429 and attempt<3:
                        again.append(futures[f]);delay=max(delay,a.get("retry_after_seconds",0),6)
                if delay:time.sleep(delay)
        pending=again
        if not pending:break

def summarize(cases,tasks,limit):
    folder=HERE/"capture"
    get={r["key"]:(r,p) for r,p in tasks}
    intents={(a["key"],a["attempt"]):a["request_sha"] for a in map(json.loads,(folder/"intent.jsonl").read_bytes().splitlines())}
    last={};ids=set();attempts=0;cost=0.;rejected=0
    for a in map(json.loads,(folder/"attempts.jsonl").read_bytes().splitlines()):
        attempts+=1;row,p=get[a["key"]]
        assert intents[a["key"],a["attempt"]]==a["request_sha"]==digest(canonical(p))
        if a["key"] in last:assert last[a["key"]]["http"]==429
        last[a["key"]]=a
        if a.get("terminal_sha"):
            b=gzip.decompress((folder/"terminal"/f"{a['key']}-{a['attempt']}.json.gz").read_bytes())
            assert digest(b)==a["terminal_sha"]
            raw=json.loads(b)
            assert raw["model"]==row["model"] and raw["id"]==a["response_id"] and raw["id"] not in ids
            ids.add(raw["id"])
            assert (output_text(raw) or raw.get("output_text") or "")==a["text"]
        rejected+=a["http"]==429;cost+=(a.get("usage") or {}).get("cost",0)
    assert len(intents)==attempts
    results={m:{a:Counter() for a in ("correct","wrong")} for m in MODELS}
    for r,p in tasks:
        a=last.get(r["key"],{});c=results[r["model"]][r["arm"]];c["n"]+=1
        if not a.get("eligible"):c["unknown"]+=1;continue
        case=cases[r["case"]]
        v=number(final_text(a["text"])[0],case["unit"])
        c["says_option"]+=int(v==number(r["value"],case["unit"]))
        c["factually_correct"]+=int(v==number(case["gold"][0],case["unit"]))
        c["complete"]+=1
    out=dict(planned=len(tasks),terminal_objects=len(ids),attempts=attempts,http_429=rejected,
             provider_cost=cost,maximum_reservation_including_retries=limit,results=results,
             source_indices=sorted({r["case"] for r,p in tasks}))
    (HERE/"summary.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("NUMERIC_CONTROLS "+json.dumps(out,separators=(",",":")))

if __name__=="__main__":
    cases,tasks,limit=make()
    print("DESIGN",len(tasks),round(limit,5),flush=True)
    if "--check" not in sys.argv:
        assert os.environ.get("GITHUB_RUN_ATTEMPT")=="1"
        capture(tasks);summarize(cases,tasks,limit)
