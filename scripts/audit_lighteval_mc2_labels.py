"""Scan pinned actual TruthfulQA labels and execute unchanged Lighteval metric/adapter."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import urllib.request

import numpy as np
import pyarrow.parquet as pq

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("source_dir",type=Path,help="Contains pinned truthful_qa.py and truthfulqa_task.py")
parser.add_argument("dataset_path",type=Path,help="Pinned parquet, downloaded if absent")
parser.add_argument("--output",type=Path)
args=parser.parse_args()
ROOT = args.source_dir
expected={"truthful_qa.py":"b21e160903f4e813394b01c2f1b0296434fe568b5d89236bebc2584fdbea9c59","truthfulqa_task.py":"94ea5abd4a88da94d3980ff6816f5fc3658c3afbaf06781284918fb762eb15af"}
for name,digest in expected.items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError("Pinned source mismatch: "+name)
REVISION = "741b8276f2d1982aa3d5b832d3ee81ed3b896490"
URL = f"https://huggingface.co/datasets/truthfulqa/truthful_qa/resolve/{REVISION}/multiple_choice/validation-00000-of-00001.parquet"
path = args.dataset_path
if not path.exists():
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(urllib.request.urlopen(URL, timeout=60).read())
if hashlib.sha256(path.read_bytes()).hexdigest()!="23f08e230ca4ed66babf3a72419af7cbde1f3d734dd396ac4cf6d088bd162afd":raise ValueError("Pinned dataset mismatch")
rows = pq.read_table(path).to_pylist()

metric_source = (ROOT / "truthful_qa.py").read_text()
metric_node = next(n for n in ast.parse(metric_source).body if isinstance(n, ast.ClassDef) and n.name == "TruthfulqaMCMetrics")
namespace = {"np":np, "SampleLevelComputation":object, "Doc":SimpleNamespace,
             "ModelResponse":SimpleNamespace, "as_list": lambda x:x if isinstance(x,list) else [x]}
exec(compile(ast.Module(body=[metric_node], type_ignores=[]), "pinned_metric", "exec"),namespace)
metric = namespace["TruthfulqaMCMetrics"]()
task_source = (ROOT / "truthfulqa_task.py").read_text()
task_node = next(n for n in ast.parse(task_source).body if isinstance(n, ast.FunctionDef) and n.name == "truthful_qa_multiple_choice_prompt")
exec(compile(ast.Module(body=[task_node],type_ignores=[]), "pinned_adapter", "exec"),namespace)
adapter = namespace["truthful_qa_multiple_choice_prompt"]

def evaluate(row):
    doc = adapter(row)
    response = SimpleNamespace(logprobs=[0.] * len(doc.choices))
    actual = float(metric.compute(doc,response)["truthfulqa_mc2"])
    labels = row["mc2_targets"]["labels"]
    expected = sum(labels)/len(labels)
    return actual, expected

nonprefix=[]; wrong=[]; permuted_wrong=[]
for i,row in enumerate(rows):
    labels=row["mc2_targets"]["labels"]
    if labels != [1]*sum(labels)+[0]*(len(labels)-sum(labels)):
        nonprefix.append(i)
    a,e=evaluate(row)
    if abs(a-e)>1e-12: wrong.append(dict(index=i,labels=labels,actual=a,expected=e))
    order=list(range(len(labels)))
    # Move the first false answer before all true answers, preserving every pair.
    false_ix=next((j for j,x in enumerate(labels) if x==0),None)
    if false_ix is not None:
        order.remove(false_ix); order.insert(0,false_ix)
        newrow=dict(row)
        newrow["mc2_targets"]={"choices":[row["mc2_targets"]["choices"][j] for j in order],"labels":[labels[j] for j in order]}
        b,_=evaluate(newrow)
        if abs(b-e)>1e-12:
            permuted_wrong.append(dict(index=i,labels_before=labels,labels_after=newrow["mc2_targets"]["labels"],actual_before=a,actual_after=b,expected=e))

example=rows[0]
out={"dataset_revision":REVISION,"dataset_url":URL,"dataset_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
     "lighteval_commit":"b97a6533bec22c4184b88526366fdf5d73d502c9","numpy_version":np.__version__,
     "rows":len(rows),"nonprefix_labels":len(nonprefix),"nonprefix_indices":nonprefix,
     "original_uniform_score_mismatches":len(wrong),"original_examples":wrong[:10],
     "false_first_permuted_score_mismatches":len(permuted_wrong),"permuted_examples":permuted_wrong[:3],
     "row0_question":example["question"],"note":"Uniform constructed likelihoods, real labels/adapter; no real model inference. Permutation preserves answer-label pairs; current original-order incidence is reported separately."}
if args.output:
    args.output.write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
