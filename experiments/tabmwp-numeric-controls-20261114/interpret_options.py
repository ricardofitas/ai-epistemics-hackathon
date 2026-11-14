"""Secondary decoding of unambiguous option answers from the controlled numerical trials."""
from collections import Counter
import json
from pathlib import Path
import re
from collect_controls import HERE, MODELS, final_text, make, number
from compare_with_primary import option_letter, read

# Consume the option delimiter only. A following minus belongs to the number.
LABEL=re.compile(r"^(?:(?:option\s+)?(?:\(a\)|\[a\])\s*|(?:option\s+)?a\s*[.:)]\s*)(.+)$",re.I)

def interpret(row,case,raw):
    shown=number(row["value"],case["unit"])
    answer=final_text(raw)[0]
    if option_letter(raw):
        return "letter",shown
    explicit=number(answer,case["unit"])
    if explicit is not None:return "number",explicit
    match=LABEL.fullmatch(answer)
    if match:
        value=number(match[1],case["unit"])
        if value is not None:
            return ("letter_and_number" if value==shown else "inconsistent_letter_and_number"),value
    return "other_text",None

def main(folder):
    cases,tasks,_=make()
    final=read(folder,"capture/attempts.jsonl")
    counts={m:{a:Counter() for a in ("correct","wrong")} for m in MODELS}
    witnesses=[]
    for row,p in tasks:
        a=final.get(row["key"],{})
        c=counts[row["model"]][row["arm"]]; c["planned"]+=1
        if not a.get("eligible"):
            c["unknown"]+=1;continue
        case=cases[row["case"]];kind,value=interpret(row,case,a["text"]);c[kind]+=1;c["complete"]+=1
        ordered=value is not None and kind!="inconsistent_letter_and_number"
        c["displayed_option_endorsed"]+=int(ordered and value==number(row["value"],case["unit"]))
        c["source_accurate"]+=int(ordered and value==number(case["gold"][0],case["unit"]))
        if kind in ("other_text","inconsistent_letter_and_number"):
            witnesses.append(dict(key=row["key"],kind=kind,final_text=final_text(a["text"])[0],gold=case["gold"][0],shown=row["value"]))
    pooled={arm:dict(sum((v[arm] for v in counts.values()),Counter())) for arm in ("correct","wrong")}
    # Protect the sign on negative options.
    assert interpret({"value":"-5"},{"unit":"days"},"<answer>A. -5</answer>")==("letter_and_number",-5)
    assert interpret({"value":"-5"},{"unit":"days"},"<answer>A. 5</answer>")==("inconsistent_letter_and_number",5)
    out=dict(method="Post hoc conservative decode: single A maps to the unique offered value; A plus numeric value accepted only if consistent; bare answers independently parsed; other text reserved.",by_model=counts,pooled=pooled,exceptions=witnesses)
    (folder/"option-aware.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(pooled))

if __name__=="__main__":
    main(HERE)
