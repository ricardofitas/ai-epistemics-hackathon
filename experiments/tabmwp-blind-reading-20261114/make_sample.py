from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "tabmwp-archive-audit-20261114"
if not ARCHIVE.exists():
    ARCHIVE = HERE.parent / "archived"
sys.path.insert(0, str(ARCHIVE))
from replay import download, similarity

MODELS = ("qwen3.8-27b", "glm-5.2")
SALT = "TabMWP-frozen-interpretation-v1"
def h(*args):
    return sha256(json.dumps(args, ensure_ascii=False, separators=(",",":")).encode()).hexdigest()

def pay(row, model):
    opts = row["options"]
    text = ("You are transcribing the meaning of an archived model reply, not solving its original question. "
            "Read the question only to understand what each option means. Identify a single option only if the reply "
            "itself indicates it unambiguously (including trivial spelling or case differences). "
            "If there is no such option, respond UNRESOLVED. Never guess. Your entire final output must be "
            "<answer>N</answer> using the displayed option number or <answer>UNRESOLVED</answer>.\n\n"
            + "Question: " + row["question"] + "\nOptions:\n"
            + "\n".join(f"{i+1}. {s}" for i,s in enumerate(opts))
            + "\nArchived reply (JSON string): " + json.dumps(row["raw"], ensure_ascii=False))
    return dict(model=model,input=text,temperature=0,max_output_tokens=4096,stream=True,tools=[],
                agentic_memory=False,store=False,tool_choice="none")

def main():
    manifest = json.loads((ARCHIVE/"sources.json").read_bytes())
    sourcefile = "data/tabmwp/problems_test.json"
    modelpath = "results/tapex/exp1_tapex-base.json"
    files = {p: download((p,manifest["blobs"][p]),manifest["source_rev"])[1] for p in (sourcefile,modelpath)}
    orig, preds = files[sourcefile], files[modelpath]["results"]
    strata = {"first_credited":[], "first_wrong":[]}
    for pid, r in preds.items():
        opts = orig[pid]["choices"]
        if len(opts or []) >= 2 and not any(similarity(s,r["output"]) for s in opts):
            strata["first_credited" if r["true_false"] else "first_wrong"].append(pid)
    assert sorted(map(len,strata.values())) == [443,795]
    rows = []
    def add(pid,group,suffix,raw,ctl):
        item = orig[pid]
        opts = item["choices"]
        order = sorted(range(len(opts)),key=lambda i:h(SALT,"order",pid,suffix,i))
        rows.append(dict(key=f"{pid}-{suffix}",pid=pid,group=group,question=item["question"],
                  options=[opts[i] for i in order],raw=raw,gold=item["answer"],control=ctl))
    for group, ids in strata.items():
        for pid in sorted(ids,key=lambda k:h(SALT,"sample",k))[:50]:
            add(pid, group, "study", preds[pid]["output"], None)
    chosen = {r["pid"] for r in rows}
    rest = sorted([k for k,v in orig.items() if k not in chosen and len(v["choices"] or [])>=2],
                  key=lambda k:h(SALT,"control",k))[:12]
    for j,pid in enumerate(rest):
        opts=orig[pid]["choices"]
        selected = opts[int(h(SALT,"target",pid),16)%len(opts)] if j%2==0 else None
        add(pid,"control","control",selected or "I cannot determine which option applies.",
            selected or "UNRESOLVED")
    rows.sort(key=lambda r:h(SALT,"tasks",r["key"]))
    assert Counter(x["group"] for x in rows)=={"first_credited":50,"first_wrong":50,"control":12}
    return rows

if __name__=="__main__":
    rows=main()
    (HERE/"cases.json").write_text(json.dumps(rows,ensure_ascii=False,sort_keys=True)+"\n")
