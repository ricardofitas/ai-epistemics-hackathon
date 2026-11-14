"""Validate design, paired contrasts, reference scorers and unknown handling before the API run."""
import json
from collections import Counter
from pathlib import Path
from design import ARMS, MODELS, audit, digest, payload, trials
from scoring import grade, summarize

def verify():
    root=Path(__file__).resolve().parent
    cases=json.loads((root/"cases.json").read_bytes());rows=trials(cases)
    assert audit(cases,rows)==json.loads((root/"design_receipt.json").read_bytes())
    assert all(grade(c,"<answer>"+c["gold"][0]+"</answer>")[0] for c in cases)
    assert all(grade(c,"<answer>A. None</answer>")[:2]==(0,1) for c in cases)
    for ds in ("squad","tabmwp"):
        assert Counter(payload(c,MODELS[0],ARMS[0],i)["max_output_tokens"] for i,c in enumerate(cases) if c["dataset"]==ds)=={4096:50,6144:50}
    assert all(len({k for k in (payload(c,MODELS[0],a,i)["input"] for a in ARMS)})==4 for i,c in enumerate(cases))
    group={(MODELS[0],"tabmwp",0):{"free_clear":(1,0,"tag"),"free_none":(1,0,"tag"),
                                   "choice_clear":(1,0,"tag"),"choice_none":(None,None,None)}}
    effects=summarize(group)[MODELS[0]]["tabmwp"]["contrasts"]
    assert effects["interaction"]["lower_pp"]==effects["choice_carrier"]["lower_pp"]==0
    assert effects["interaction"]["upper_pp"]==effects["choice_carrier"]["upper_pp"]==100
    x={"dataset":"tabmwp","gold":["1/2"],"unit":"kg"}
    assert grade(x,"First 17.\n<answer>0.5 kg</answer>")[0]==1 and grade(x,"<answer>0.51 kg</answer>")[0]==0
    print("Verified source and request hashes, distinct cells, balanced caps, 200 gold controls, 200 dummy controls and unknown bounds.")
if __name__=="__main__":verify()
