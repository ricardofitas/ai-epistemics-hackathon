"""Replay archived model likelihoods through unchanged Lighteval MC2 adapter/scorer.

No new model inference is performed. These are cross-implementation metric inputs,
not a claim to reproduce native Lighteval prompts or inference.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("source_dir",type=Path,help="Contains pinned truthful_qa.py and truthfulqa_task.py")
parser.add_argument("trace_root",type=Path,help="Contains download_manifest.json and downloaded data/")
parser.add_argument("--output",type=Path)
args=parser.parse_args()
ROOT=args.source_dir
TRACE_ROOT=args.trace_root
expected={"truthful_qa.py":"b21e160903f4e813394b01c2f1b0296434fe568b5d89236bebc2584fdbea9c59","truthfulqa_task.py":"94ea5abd4a88da94d3980ff6816f5fc3658c3afbaf06781284918fb762eb15af"}
for name,digest in expected.items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError("Pinned source mismatch: "+name)
manifest=json.loads((TRACE_ROOT/"download_manifest.json").read_text())
namespace={"np":np,"SampleLevelComputation":object,"Doc":SimpleNamespace,
           "ModelResponse":SimpleNamespace,"as_list":lambda x:x if isinstance(x,list) else [x]}
for filename,name,kind in [("truthful_qa.py","TruthfulqaMCMetrics",ast.ClassDef),("truthfulqa_task.py","truthful_qa_multiple_choice_prompt",ast.FunctionDef)]:
    source=(ROOT/filename).read_text()
    node=next(n for n in ast.parse(source).body if isinstance(n,kind) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),filename,"exec"),namespace)
metric=namespace["TruthfulqaMCMetrics"]()
adapter=namespace["truthful_qa_multiple_choice_prompt"]

files=[]; all_affected=[]; reference_docs=None
for entry in manifest["files"]:
    path=TRACE_ROOT/"data"/entry["path"]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]:raise ValueError("Trace hash mismatch")
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    if reference_docs is None: reference_docs={r['doc_id']:r['doc'] for r in rows}
    matching_docs=sum(r['doc']==reference_docs.get(r['doc_id']) for r in rows)
    if matching_docs != len(rows):raise ValueError('Trace document changes')
    old_scores=[]; new_scores=[]; affected=[]
    for r in rows:
        row=r["doc"]; doc=adapter(row)
        ll=np.array([x[0] for x in r["filtered_resps"]],dtype=float)
        labels=np.array(row["mc2_targets"]["labels"])
        if len(ll)!=len(labels) or not np.isfinite(ll).all():raise ValueError("Invalid likelihood shape")
        # MC1 likelihoods do not affect MC2. Supply placeholders for that slice only.
        response=SimpleNamespace(logprobs=[0.]*doc.specific["len_mc1"]+ll.tolist())
        old=float(metric.compute(doc,response)["truthfulqa_mc2"])
        weights=np.exp(ll-ll.max()); new=float(weights[labels==1].sum()/weights.sum())
        old_scores.append(old); new_scores.append(new)
        if abs(old-new)>1e-12:
            affected.append({"doc_id":r["doc_id"],"question":row["question"],"labels":labels.tolist(),
                "log_likelihoods":ll.tolist(),"lighteval_score":old,"intended_score":new,"difference":new-old})
    item={"path":entry["path"],"url":entry["url"],"trace_sha256":entry["sha256"],"rows":len(rows),
          "changed_beyond_1e_minus_12":len(affected),"matching_reference_docs":matching_docs,"lighteval_mean":float(np.mean(old_scores)),
          "intended_mean":float(np.mean(new_scores)),"mean_difference_pp":100*float(np.mean(new_scores)-np.mean(old_scores)),
          "max_item_difference":max((x["difference"] for x in affected),default=0.),"affected":affected}
    files.append(item)
    all_affected.extend((entry["path"],x) for x in affected)
old_order=[f["path"] for f in sorted(files,key=lambda x:x["lighteval_mean"],reverse=True)]
new_order=[f["path"] for f in sorted(files,key=lambda x:x["intended_mean"],reverse=True)]
out={"lighteval_commit":"b97a6533bec22c4184b88526366fdf5d73d502c9",
     "trace_repo":manifest["repo"],"trace_revision":manifest["revision"],
     "files":files,"total_items":sum(x["rows"] for x in files),
     "affected_items":len(all_affected),"replayed_checkpoint_order_changed":old_order!=new_order,
     "source_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['truthful_qa.py','truthfulqa_task.py']},
     "old_order":old_order,"new_order":new_order,
     "note":"Original archived MC2 labels/likelihoods; unchanged Lighteval adapter/scorer replay. Dummy MC1 likelihoods affect MC1 only. No native Lighteval inference or published result correction claimed."}
if args.output:
    args.output.write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({"files":len(files),"total_items":out["total_items"],"affected_items":out["affected_items"],"ranking_changed":out["replayed_checkpoint_order_changed"],"max_item":max(x["max_item_difference"] for x in files),"max_mean_diff_pp":max(x["mean_difference_pp"] for x in files)},indent=2))
