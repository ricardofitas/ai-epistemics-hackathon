"""Stratified descriptive bounds over the 1,238 all-zero-similarity TAPEX base replies."""
import json
from pathlib import Path

def calculate(summary):
    groups=summary["consensus"]
    weight={"first_credited":443/1238,"first_wrong":795/1238}
    out={}
    for label in ("gold_option","unresolved","other_option"):
        low=high=0.
        for g,w in weight.items():
            counts=groups[g]
            n=sum(counts.values())
            assert n==50
            val=counts.get(label,0)/n
            low+=w*val
            high+=w*(val+counts.get("unknown",0)/n)
        out[label]=[round(100*low,2),round(100*high,2)]
    return {"estimated_percentage_in_zero_tie_population":out,
            "weights":{"first_credited":"443/1238", "first_wrong":"795/1238"},
            "type":"Stratified sample estimates conditional on model consensus, bounded over disagreements. Sampling uncertainty and shared judge error not covered."}

if __name__=="__main__":
    import sys
    folder=Path(sys.argv[1])
    x=calculate(json.loads((folder/"summary.json").read_bytes()))
    (folder/"stratified-estimate.json").write_text(json.dumps(x,indent=2)+"\n")
    print(json.dumps(x))
