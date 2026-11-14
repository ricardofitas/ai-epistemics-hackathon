"""Post-replay sensitivity: retain explicit option text after case/space normalization."""
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path
from collections import Counter
import json
import unicodedata

from replay import HERE, download, similarity

def norm(text):
    return " ".join(unicodedata.normalize("NFKC",text).casefold().split())

def main():
    manifest=json.loads((HERE/"sources.json").read_bytes())
    with ThreadPoolExecutor(4) as pool:
        raw=dict(pool.map(lambda item:download(item,manifest["source_rev"]),
                          manifest["blobs"].items()))
    source=raw.pop("data/tabmwp/problems_test.json")
    prior=json.loads((HERE/"result.json").read_bytes())
    scores, evidence, ids={},[],set()
    for path,archive in sorted(raw.items()):
        count=Counter()
        for pid,row in archive["results"].items():
            item=source[pid];opts=item["choices"]
            if not opts or max(similarity(opt,row["output"]) for opt in opts)>0:
                continue
            count["zeros"]+=1
            matches=[opt for opt in opts if norm(opt)==norm(row["output"])]
            if len(matches)!=1:
                continue
            count["explicit"]+=1
            correct=(norm(matches[0])==norm(item["answer"]))
            count["explicit_correct"]+=correct
            if row["true_false"]!=correct:
                name="gain" if correct else "loss"
                count[name]+=1
                evidence.append(dict(archive=path,id=pid,raw=row["output"],unique_match=matches[0],
                                  source_answer=item["answer"],original_prediction=row["prediction"],direction=name))
                ids.add(pid)
        old=prior["files"][path]
        assert count["zeros"]==old["zero_rows"]
        scores[path]=dict(total=old["total"],original=old["original"],zero_rows=count["zeros"],
             unique_equivalent=count["explicit"],changed_to_correct=count["gain"],changed_to_wrong=count["loss"],
             only_exact_override=old["original"]+count["gain"]-count["loss"],
             exact_first_then_abstain=old["abstain"]+count["explicit_correct"])
    flips={}
    for mode in ["only_exact_override","exact_first_then_abstain"]:
        flips[mode]=[[a,b] for a,b in combinations(scores,2)
                     if (scores[a]["original"]-scores[b]["original"])*(scores[a][mode]-scores[b][mode])<0]
    result=dict(scope="post-replay, third-party raw outputs; zero similarity only",files=scores,
                changed_flags=len(evidence),unique_source_ids_changed=len(ids),strict_inversions=flips)
    (HERE/"exact_results.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (HERE/"exact_witnesses.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in evidence))
    print("EXACT_SUMMARY "+json.dumps(result,sort_keys=True,separators=(",",":")))

if __name__=="__main__":
    main()
