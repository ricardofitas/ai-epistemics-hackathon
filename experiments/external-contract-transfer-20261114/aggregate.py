"""Recompute the prospective contrasts and decision transfer on all planned cases."""
from collections import Counter,defaultdict
import gzip
import json
from pathlib import Path
from datetime import datetime
from design import ARMS,MODELS,digest,canonical,payload,trials
from scoring import report,grade

def aggregate(root):
    cases=json.loads((root/"cases.json").read_bytes()); manifest=trials(cases);index={r["key"]:r for r in manifest}
    capture=root/"capture"; result=report(capture,root/"cases.json",set(range(len(cases))))
    attempts=[];verified=0;capcounts=defaultdict(Counter); credit_est=0.
    from design import RATES
    starts=[];ends=[]
    for p in sorted(capture.glob("*/attempts.jsonl")):
        intents={(t["key"],t["attempt"]):t for t in map(json.loads,(p.parent/"intent.jsonl").read_bytes().splitlines())}
        for a in map(json.loads,p.read_bytes().splitlines()):
            r=index[a["key"]]; ident=(a["key"],a["attempt"])
            assert ident in intents and intents[ident]["request_sha"]==r["request_sha"]==a["request_sha"]
            if a.get("start"):starts.append(datetime.fromisoformat(a["start"]))
            if a.get("end"):ends.append(datetime.fromisoformat(a["end"]))
            if a.get("terminal_sha"):
                b=gzip.decompress((p.parent/"terminal"/f"{a['key']}-{a['attempt']}.json.gz").read_bytes())
                assert digest(b)==a["terminal_sha"]; v=json.loads(b)
                assert v.get("id")==a.get("response_id") and v.get("model")==a.get("returned_model") and v.get("status")==a.get("status")
                ts=[x["text"] for o in (v.get("output") or []) if o.get("type")=="message" and o.get("role","assistant")=="assistant" for x in (o.get("content") or []) if x.get("type")=="output_text" and isinstance(x.get("text"),str)]
                assert ("\n".join(ts) or v.get("output_text") or "")==a["text"]
                if a["eligible"]:assert v.get("status")=="completed" and v.get("model")==r["model"] and a["http"]==200
                verified+=1
            use=a.get("usage") or {};pin,pout=RATES[r["model"]]
            credit_est+=(use.get("input_tokens",0)*pin+use.get("output_tokens",0)*pout)/1e6
            if a.get("http")==200:
                cap=payload(cases[r["case"]],r["model"],r["arm"],r["case"])["max_output_tokens"]
                c=capcounts[(r["model"],cap)];c["received"]+=1;c["complete"]+=int(a["eligible"]);c["max_output_tokens"]+=int((a.get("incomplete_details") or {}).get("reason")=="max_output_tokens")
            attempts.append(a)
    result.update(terminal_objects_verified=verified,rate_card_credits_without_cached_discount=round(credit_est,7),
                  cap_comparison={f"{m}:{cap}":v for (m,cap),v in capcounts.items()})
    if starts and ends:
        hrs=(max(ends)-min(starts)).total_seconds()/3600
        result.update(elapsed_hours=round(hrs,4),complete_responses_per_hour=round(result["eligible"]/hrs,2) if hrs>0 else None)
    choices={}
    for condition in ("choice_none","free_clear"):
        source={m:result["models"][m]["squad"]["scores"][condition] for m in MODELS}
        target={m:result["models"][m]["tabmwp"]["scores"]["free_clear"] for m in MODELS}
        highlow=max(s["correct"] for s in source.values())
        cand=[m for m,s in source.items() if s["correct"]+s["unknown"]>=highlow]
        bounds={}
        for m in cand:
            lo=target[m]["correct"];hi=lo+target[m]["unknown"]
            competitors=[(s["correct"],s["correct"]+s["unknown"]) for n,s in target.items() if n!=m]
            # Target stratum has exactly 100 source cases, so counts equal percentage points.
            bounds[m]=[max(0,max(x[0] for x in competitors)-hi),max(0,max(x[1] for x in competitors)-lo)]
        choices[condition]={"admissible_winners":cand,"target_clean_regret_pp":bounds}
    result["decision_transfer"]=choices
    out=root/"results";out.mkdir(exist_ok=True)
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps({k:v for k,v in result.items() if k not in ("models","cap_comparison")}))
if __name__=="__main__":aggregate(Path(__file__).resolve().parent)
