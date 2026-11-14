from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path
import json
import os
import re
import sys
import time

from make_sample import MODELS, pay
HERE=Path(__file__).resolve().parent
STUDY=HERE.parent/"external-contract-transfer-20261114"
if not STUDY.exists():
    STUDY=HERE.parent/"src"
sys.path.insert(0,str(STUDY))
from run_panel import append, fetch, output_text, persist
from design import RATES, canonical, digest

def capture():
    rows = json.loads((HERE/"cases.json").read_bytes())
    folder = HERE/"capture"
    (folder/"terminal").mkdir(parents=True,exist_ok=False)
    prepared = []
    reserved = 0.
    for idx,row in enumerate(rows):
        for j,model in enumerate(MODELS):
            p=pay(row,model)
            request={"key":row["key"]+"-m"+str(j),"case":idx,"model":model,
                     "arm":"blinded","request_sha":digest(canonical(p))}
            tin,tout=RATES[model]
            worst=((len(p["input"].encode())+1024)*tin+4096*tout)/1e6
            reserved+=3*worst
            prepared.append((request,p,worst))
    assert len(prepared)==224 and reserved<=10
    key=os.environ["ADAPTION_API_KEY"]
    def work(job):
        request, p, worst = job
        return fetch(request,p,job_attempt,key,folder)
    pending=prepared
    for job_attempt in (1,2,3):
        again=[]
        with ThreadPoolExecutor(max_workers=2) as pool:
            for pos in range(0,len(pending),2):
                jobs=pending[pos:pos+2]; fs={}
                for job in jobs:
                    req,p,worst=job
                    append(folder/"intent.jsonl",dict(key=req["key"],attempt=job_attempt,
                           request_sha=req["request_sha"],reserved=worst))
                    fs[pool.submit(work,job)]=job
                    time.sleep(1.0)
                delay=0
                for f in as_completed(fs):
                    record=f.result()
                    append(folder/"attempts.jsonl",record)
                    if record.get("http") in (401,402,403,404):
                        raise RuntimeError("provider status "+str(record["http"]))
                    if record.get("returned_model") not in (None,record["model"]):
                        raise RuntimeError("unverified model identity")
                    if record.get("http")==429 and job_attempt<3:
                        again.append(fs[f]);delay=max(delay,record.get("retry_after_seconds",0),6)
                if delay:time.sleep(delay)
        pending=again
        if not pending:break

def summarize():
    import gzip
    rows=json.loads((HERE/"cases.json").read_bytes())
    folder=HERE/"capture"
    attempts=[json.loads(s) for s in (folder/"attempts.jsonl").read_bytes().splitlines()]
    intents={(t["key"],t["attempt"]):t["request_sha"] for t in map(json.loads,(folder/"intent.jsonl").read_bytes().splitlines())}
    assert len(intents)==len(attempts)
    terminal_ids=set();out={};ledger=0.
    for a in attempts:
        row=rows[a["case"]];model=a["model"]
        assert intents[a["key"],a["attempt"]]==a["request_sha"]==digest(canonical(pay(row,model)))
        if a.get("response_id"):
            assert a["response_id"] not in terminal_ids
            terminal_ids.add(a["response_id"])
        if a.get("terminal_sha"):
            data=gzip.decompress((folder/"terminal"/f"{a['key']}-{a['attempt']}.json.gz").read_bytes())
            assert digest(data)==a["terminal_sha"]
            original=json.loads(data)
            assert original["id"]==a["response_id"] and original["model"]==model
            assert (output_text(original) or original.get("output_text") or "")==a["text"]
        ledger+=(a.get("usage") or {}).get("cost",0)
        value=None
        if a["eligible"]:
            tags=re.findall(r"<answer>\s*(UNRESOLVED|[0-9]+)\s*</answer>",a["text"],re.I)
            if tags:
                tag=tags[-1].upper()
                if tag=="UNRESOLVED":value=tag
                elif 1<=int(tag)<=len(row["options"]):value=row["options"][int(tag)-1]
        out[row["key"],model]=value
    counts={k:Counter() for k in ("first_credited","first_wrong","control")}
    per_controls={m:Counter() for m in MODELS}
    for r in rows:
        vals=[out.get((r["key"],m)) for m in MODELS]
        agreement=vals[0] is not None and vals[0]==vals[1]
        group=counts[r["group"]]
        if not agreement:group["unknown"]+=1
        elif r["group"]=="control":
            group["valid" if vals[0]==r["control"] else "wrong"]+=1
        elif vals[0]=="UNRESOLVED":group["unresolved"]+=1
        else:group["gold_option" if vals[0]==r["gold"] else "other_option"]+=1
        if r["group"]=="control":
            for model,val in zip(MODELS,vals):
                per_controls[model]["correct" if val==r["control"] else "failed"]+=1
    result=dict(planned=224,terminals=len(terminal_ids),eligible=sum(bool(a.get("eligible")) for a in attempts),
                http_429=sum(a["http"]==429 for a in attempts),attempts=len(attempts),
                consensus=counts,control_by_judge=per_controls,reported_cost=ledger)
    (HERE/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("BLINDED_SUMMARY "+json.dumps(result,separators=(",",":")))

if __name__=="__main__":
    if os.environ.get("GITHUB_RUN_ATTEMPT")!="1":raise RuntimeError("no duplicate captures")
    capture();summarize()
