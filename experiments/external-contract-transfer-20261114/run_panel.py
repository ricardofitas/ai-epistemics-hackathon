"""Paced standalone Adaption generations for an immutable 2x2 external panel."""
import argparse
from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

from design import CAP, MODELS, RATES, audit, canonical, digest, payload, trials
from scoring import report

ROOT=Path(__file__).resolve().parent
TRANSPORT=ROOT.parent/"mixeval-factorial-20261114"
if not TRANSPORT.exists():
    TRANSPORT=ROOT.parent/"work"
sys.path.insert(0,str(TRANSPORT))
try:
    from run_adaption_stream_pilot import SSEFrameDecoder, NoRedirect, output_text, sanitize
except ModuleNotFoundError:
    from transport import SSEFrameDecoder, NoRedirect, output_text, sanitize

BASE="https://api.prod.adaptionlabs.ai/api/v1"
SHARD_LIMIT=10.
TERMINAL={"response.completed","response.incomplete","response.failed","response.cancelled"}
def utc():
    return datetime.now(timezone.utc).isoformat()

def retry_time(value):
    if not value:return 0.
    try:return max(0.,float(value))
    except ValueError:
        try:return max(0.,parsedate_to_datetime(value).timestamp()-time.time())
        except (ValueError,TypeError,OverflowError):return 0.

def charge(row, pay):
    ip,op=RATES[row["model"]]
    return ((len(pay["input"].encode())+1024)*ip+pay["max_output_tokens"]*op)/1e6

def output_usage(raw):
    data=raw.get("usage") or {}
    if not isinstance(data,dict):
        return {}
    keep={}
    for k in ("input_tokens","output_tokens","total_tokens","cost"):
        value=data.get(k)
        if isinstance(value,(int,float)) and not isinstance(value,bool) and value>=0:
            keep[k]=value
    return keep

def fetch(row, pay, attempt, key, folder):
    start=time.monotonic()
    rec={"key":row["key"],"attempt":attempt,"model":row["model"],"arm":row["arm"],"case":row["case"],
         "request_sha":digest(canonical(pay)),"start":utc(),"http":None,"eligible":False,
         "status":"transport_error","retry_after_seconds":0.,"usage":{}}
    if row["request_sha"]!=rec["request_sha"]:
        raise ValueError("payload changed")
    req=urllib.request.Request(BASE+"/responses",data=canonical(pay),method="POST",headers={
        "Authorization":"Bearer "+key,"Content-Type":"application/json","Accept":"text/event-stream"})
    terminal={}; event=None; wire=hashlib.sha256(); frame_count=0
    try:
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=100) as response:
            rec["http"]=response.status
            rec["request_id"]=response.headers.get("x-request-id") or response.headers.get("request-id")
            if response.headers.get_content_type()=="application/json":
                data=response.read();wire.update(data);terminal=json.loads(data);event="json_object"
            else:
                decoder=SSEFrameDecoder()
                for line in response:
                    if time.monotonic()-start>200:
                        raise TimeoutError("response deadline")
                    wire.update(line)
                    frame=decoder.feed(line)
                    if frame is None:continue
                    frame_count+=1
                    value=frame.get("data")
                    if not isinstance(value,dict):continue
                    kind=value.get("type") or frame["event"]
                    if kind in TERMINAL and isinstance(value.get("response"),dict):
                        terminal=value["response"];event=kind;break
                    if kind=="error":
                        rec["status"]="provider_stream_error"
                        break
    except urllib.error.HTTPError as err:
        rec["http"]=err.code;rec["status"]="http_"+str(err.code)
        rec["retry_after_seconds"]=retry_time(err.headers.get("Retry-After"))
        rec["request_id"]=err.headers.get("x-request-id") or err.headers.get("request-id")
        msg=err.read(4096)
        try:
            detail=json.loads(msg)
            detail=detail.get("error",{}) if isinstance(detail,dict) else {}
            if isinstance(detail,dict):rec["error_code"]=str(detail.get("code") or detail.get("type") or "")[:120]
        except (ValueError,TypeError):pass
    except (OSError,ValueError,TimeoutError) as err:
        rec["failure_type"]=type(err).__name__
    if isinstance(terminal,dict) and terminal:
        # Save terminal data independently of the derived answer or scoring.
        terminal=sanitize(terminal,key)
        termbytes=canonical(terminal)
        target=folder/"terminal"/f"{row['key']}-{attempt}.json.gz"
        with target.open("xb") as f:f.write(gzip.compress(termbytes,compresslevel=3,mtime=0))
        text=output_text(terminal) or terminal.get("output_text") or ""
        if not isinstance(text,str):text=""
        rec.update(terminal_sha=digest(termbytes),text=text,output_sha=digest(text.encode()),
                   returned_model=terminal.get("model"),response_id=terminal.get("id"),usage=output_usage(terminal),
                   status=terminal.get("status") or "missing_status",incomplete_details=terminal.get("incomplete_details"))
        rec["eligible"]=(rec["http"]==200 and event in {"response.completed","json_object"} and rec["status"]=="completed"
                         and rec["returned_model"]==row["model"] and bool(rec["response_id"]) and bool(text.strip()))
    elif rec["http"]==200 and rec["status"]=="transport_error":
        rec["status"]="missing_terminal"
    rec.update(terminal_event=event,stream_sha=wire.hexdigest(),frames=frame_count,end=utc(),seconds=round(time.monotonic()-start,3))
    return rec

def append(file,entry):
    with file.open("a",encoding="utf-8") as f:
        f.write(json.dumps(entry,ensure_ascii=False,allow_nan=False)+"\n")
        f.flush();os.fsync(f.fileno())

def persist(path,data):
    temp=path.with_suffix(".tmp")
    temp.write_bytes(canonical(data));temp.replace(path)

def run(shard, section, key):
    cases=json.loads((ROOT/"cases.json").read_bytes())
    all_rows=trials(cases)
    receipt=audit(cases,all_rows)
    pinned=json.loads((ROOT/"design_receipt.json").read_bytes())
    if receipt!=pinned:raise ValueError("frozen design mismatch")
    if os.environ.get("GITHUB_RUN_ATTEMPT")!="1":raise ValueError("rerun disabled for previously started slots")
    req=urllib.request.Request(BASE+"/models",headers={"Authorization":"Bearer "+key})
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=40) as r:
        offered={v["id"] for v in json.load(r)["data"]}
    if not set(MODELS)<=offered:raise RuntimeError("model catalogue changed")
    first=shard*25
    subset=set(range(first,first+4) if section=="front" else range(first+4,first+25))
    planned=[r for r in all_rows if r["case"] in subset]
    pending=deque((r,1) for r in planned)
    # Each front receives 1.60 credits and each back 8.40. All eight waves stay below 80.
    ceiling=SHARD_LIMIT*len(subset)/25
    out=ROOT/"capture"/f"s{shard}-{section}"
    out.mkdir(parents=True,exist_ok=False);(out/"terminal").mkdir()
    started=time.monotonic();next_start=started;cool_until=started
    gap=1.0;capacity=2;streak=0
    spent=0.;reserved=0.;count=Counter();tokens=Counter();flights={}
    schedule=[];stop=None
    def transition(why):
        event=dict(elapsed_s=round(time.monotonic()-started,2),window=capacity,start_gap=round(gap,3),reason=why)
        schedule.append(event)
        print("PACING",json.dumps(event),flush=True)
    def checkpoint():
        summary=dict(shard=shard,section=section,planned=len(planned),unique_started=count["unique_started"],
                     attempts=count["attempts"],completed=count["complete"],http_429=count["429"],
                     elapsed_s=round(time.monotonic()-started,2),tokens=dict(tokens),
                     reserved_or_spent_credits=round(spent+reserved,6),ceiling_credits=ceiling,stop=stop)
        persist(out/"progress.json",summary)
        print("PROGRESS",json.dumps(summary),flush=True)
    transition("initial")
    with ThreadPoolExecutor(max_workers=8) as pool:
        while pending or flights:
            now=time.monotonic()
            if (pending and not stop and len(flights)<capacity and now>=max(next_start,cool_until)):
                r,num=pending.popleft()
                pay=payload(cases[r["case"]],r["model"],r["arm"],r["case"]);worst=charge(r,pay)
                if spent+reserved+worst>ceiling:
                    stop="credit_ceiling";pending.clear();continue
                append(out/"intent.jsonl",{"key":r["key"],"attempt":num,"request_sha":r["request_sha"],"at":utc(),"reserved":worst})
                f=pool.submit(fetch,r,pay,num,key,out);flights[f]=(r,num,worst)
                reserved+=worst;count["attempts"]+=1;count["unique_started"]+=int(num==1)
                next_start=now+gap
            if not flights:
                if not pending or stop:break
                time.sleep(max(.02,min(2,max(cool_until,next_start)-time.monotonic())))
                continue
            can_add=bool(pending) and not stop and len(flights)<capacity
            timeout=max(0.02,min(2., max(next_start,cool_until)-time.monotonic())) if can_add else 2.
            done,_=wait(flights,timeout=timeout,return_when=FIRST_COMPLETED)
            for f in done:
                row,num,worst=flights.pop(f)
                try:result=f.result()
                except Exception as exc:
                    result={"key":row["key"],"case":row["case"],"model":row["model"],"arm":row["arm"],"attempt":num,
                            "request_sha":row["request_sha"],"eligible":False,"http":None,"usage":{},"status":"local_failure","failure_type":type(exc).__name__}
                append(out/"attempts.jsonl",result);reserved-=worst
                usage=result.get("usage") or {}
                ip,op=RATES[row["model"]]
                explicit_429=result.get("http")==429
                if all(k in usage for k in ("input_tokens","output_tokens")):
                    billed=max(usage.get("cost",0),(usage["input_tokens"]*ip+usage["output_tokens"]*op)/1e6)
                    spent+=billed
                    tokens["input"]+=usage["input_tokens"];tokens["output"]+=usage["output_tokens"]
                    if billed>worst+1e-8 or usage["output_tokens"]>CAP:stop="unexpected_usage"
                else:spent+=worst
                if result.get("returned_model") not in (None,row["model"]):stop="model_identity"
                if result.get("http") in (401,402,403,404) or result.get("status")=="local_failure":stop="provider_or_storage"
                if explicit_429:
                    count["429"]+=1
                    delay=max(4.,result.get("retry_after_seconds",0))
                    cool_until=max(cool_until,time.monotonic()+delay)
                    capacity=max(2,capacity//2);gap=min(5.5,max(1.25,1.55*gap));streak=0
                    transition("HTTP_429")
                    if num<3 and not stop:pending.append((row,num+1))
                elif result.get("http")==200:
                    streak+=1
                    if streak>=24:
                        capacity=min(8,capacity*2);gap=max(.35,gap*.8);streak=0
                        transition("24_accepted")
                count["complete"]+=int(result.get("eligible") is True)
                count["recorded"]+=1
                if count["recorded"]%32==0:checkpoint()
                if stop:pending.clear()
    checkpoint()
    stat=report(out,ROOT/"cases.json",subset)
    persist(out/"summary.json",stat);persist(out/"schedule.json",schedule)
    print("FINAL",json.dumps({k:v for k,v in stat.items() if k!="models"}),flush=True)
    if stop:raise RuntimeError(stop)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("shard",type=int,choices=range(8));p.add_argument("section",choices=["front","back"])
    a=p.parse_args();run(a.shard,a.section,os.environ["ADAPTION_API_KEY"])
