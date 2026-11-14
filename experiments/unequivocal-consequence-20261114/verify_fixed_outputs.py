"""Independent raw-capture/source check, separate from native metric replay."""
from pathlib import Path
from collections import defaultdict
import json,re,hashlib
ROOT=Path(__file__).resolve().parent
capture=ROOT/'review/model-capture'
cases={r['case_id']:r for r in json.loads((capture/'cases.json').read_bytes())}
manifest=[json.loads(x) for x in (capture/'manifest.jsonl').read_text().splitlines()]
responses={r['trial_id']:r for r in map(json.loads,(capture/'responses.jsonl').read_text().splitlines())}
def compact(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
groups=defaultdict(list);proof=[]
for trial in manifest:
    if trial['bench']!='winogrande':continue
    case=cases[trial['case_id']];response=responses[trial['trial_id']]
    raw=response['output_text'] or ''
    assert hashlib.sha256(raw.encode()).hexdigest()==response['output_text_sha256']
    assert hashlib.sha256(compact(case['source_row']).encode()).hexdigest()==case['source_row_sha256']
    assert response['request_sha256']==trial['request_sha256']
    assert response['request_payload']==trial['request_payload']
    row=case['source_row'];assert row['answer'] in ['1','2']
    gold=['A','B'][int(row['answer'])-1]
    assert gold==case['gold_letter']==trial['gold_letter']
    assert case['displayed_choices']==[row['option1'],row['option2']]
    assert row['sentence'] in case['prompt']
    tags=re.findall(r'<answer>\s*([A-Za-z])\s*</answer>',raw)
    parsed=tags[0].upper() if response['completed_nonempty'] and len(tags)==1 and tags[0].upper() in ['A','B'] else None
    proof.append(dict(trial_id=trial['trial_id'],case_id=trial['case_id'],model=trial['request_payload']['model'],
                      source_row_sha256=case['source_row_sha256'],output_text_sha256=response['output_text_sha256'],
                      source_gold=gold,parsed=parsed,unknown=parsed is None,correct=parsed==gold if parsed else None))
    groups[trial['request_payload']['model']].append(proof[-1])
summary={}
for model,rows in groups.items():
    assert len(rows)==12 and sum(r['source_gold']=='B' for r in rows)==6
    known=sum(r['correct'] is True for r in rows);unknown=sum(r['unknown'] for r in rows)
    assert known>=11 and known>6
    summary[model]=dict(n=12,known_correct=known,unknown=unknown,source_correct_bounds=[known/12,(known+unknown)/12],
                        constant_B_correct=6,constant_B_accuracy=0.5,model_strictly_better_for_every_unknown_assignment=True)
result=dict(status='PASS',raw_output_checks=len(proof),source_gold_derived_from_original_one_based_answer=True,
            request_payloads_unchanged=True,models=summary,
            scope='Independent artifact and semantic-tag check by root; native scoring route tested separately. No new generation or human labels.')
(ROOT/'ROOT_FIXED_OUTPUT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'FIXED_OUTPUT_ROWS.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(result,indent=2))
