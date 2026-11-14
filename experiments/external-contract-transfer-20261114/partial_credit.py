"""Exploratory SQuAD token-overlap sensitivity on the fixed source panel."""
from collections import Counter
import json
from pathlib import Path
from design import MODELS
from scoring import final_text, squad_norm

def f1(a,b):
    x=squad_norm(a).split();y=squad_norm(b).split()
    overlap=sum((Counter(x)&Counter(y)).values())
    return 2*overlap/(len(x)+len(y)) if overlap else 0.

def main(root,waves):
    cases=json.loads((root/"cases.json").read_bytes())
    result={}
    received={}
    for path in sorted((root/"capture").glob("*/attempts.jsonl")):
        for a in map(json.loads,path.read_bytes().splitlines()):
            received[a["case"],a["model"],a["arm"]]=a
    for m in MODELS:
        bounds=[0.,0.];n=0
        for i,c in enumerate(cases[:25*waves]):
            if c["dataset"]!="squad":continue
            n+=1
            for arm,sign in [("choice_clear",1),("choice_none",-1)]:
                a=received.get((i,m,arm),{})
                if a.get("eligible"):
                    score=max(f1(final_text(a["text"])[0],g) for g in c["gold"])
                    bounds[0]+=sign*score;bounds[1]+=sign*score
                else:
                    bounds[0]+=min(0,sign);bounds[1]+=max(0,sign)
        result[m]=[round(100*v/n,3) for v in bounds]
    out=dict(questions=n,source='Rajpurkar et al., 2016, section 6.1: maximum token F1 over human references.',
        definition='Exploratory F1 change, choice_clear minus choice_none. Unknowns bounded over [0,1].',
        by_model=result,equal_weight_across_four=[round(sum(v[i] for v in result.values())/4,3) for i in [0,1]])
    (root/"results"/f"token-f1-{waves}-waves.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out))

if __name__=="__main__":
    import sys
    main(Path(__file__).resolve().parent,int(sys.argv[1]))
