"""Frozen prospective model-response analysis; all planned calls retained."""
import copy
import gzip
import json
from pathlib import Path
import re
import tempfile

import pandas as pd
import audit_contracts as audit

ROOT=audit.ROOT

def strict_answer(text, choices):
    if not isinstance(text,str):return None
    matches=re.findall(r'<answer>\s*([A-Za-z])\s*</answer>',text)
    if len(matches)!=1:return None
    result=matches[0].upper()
    return result if result in choices else None

def main():
    capture=ROOT.parent/'default_contract_model_capture_20261113'
    cases=json.loads((capture/'cases.json').read_text())
    by_case={x['case_id']:x for x in cases}
    manifest=[json.loads(x) for x in (capture/'manifest.jsonl').read_text().splitlines()]
    response_rows=[json.loads(x) for x in (capture/'responses.jsonl').read_text().splitlines()]
    responses={x['trial_id']:x for x in response_rows}
    assert len(manifest)==96 and len(responses)==len(response_rows)==96
    gallery=json.loads((ROOT/'GALLERY_SELECTED.json').read_text())
    gallery={b['bench_name']:b for b in gallery['benches']}
    BenchInfo,Runner=audit.load_components()
    source_counts={};rows=[]
    for request in manifest:
        case=by_case[request['case_id']];response=responses[request['trial_id']]
        completed=bool(response.get('completed_nonempty'))
        parsed=strict_answer(response.get('output_text'),[chr(65+i) for i in range(len(case['displayed_choices']))]) if completed else None
        correct=None if parsed is None else int(parsed==case['gold_letter'])
        rows.append({'trial_id':request['trial_id'],'case_id':case['case_id'],'bench':case['bench'],
                     'variant':case['variant'],'model':request['request_payload']['model'],
                     'completed_nonempty':completed,'http_status':response.get('http_status'),
                     'response_status':response.get('response_status'),'parsed_answer':parsed,
                     'gold_letter':case['gold_letter'],'correct':correct,
                     'output_text_sha256':response.get('output_text_sha256')})
    results=[]
    with tempfile.TemporaryDirectory() as temporary:
        path=Path(temporary)/'rows.jsonl'
        groups=sorted({(x['bench'],x['variant'],x['model']) for x in rows})
        for bench,variant,model in groups:
            selected=[x for x in rows if (x['bench'],x['variant'],x['model'])==(bench,variant,model)]
            assert len(selected)==12
            source=[]
            for x in selected:
                case=by_case[x['case_id']]
                row=copy.deepcopy(case['source_row']);row['generated_ans']=responses[x['trial_id']].get('output_text') or ''
                row['_canonical_gold']='<answer>'+case['gold_letter']+'</answer>'
                row['_displayed_choices']=case['displayed_choices']
                source.append(row)
            frame,mapping=audit.load_preprocessor()._preprocess_dataframe(pd.DataFrame(source),bench,copy.deepcopy(gallery[bench]['meta']['key_mapping']),eval_type='key3_q_choices_a')
            native_rows=frame.to_dict('records');path.write_text(''.join(audit.compact(x)+'\n' for x in native_rows))
            native_bench=BenchInfo(bench_name=bench,meta={'artifact_paths':{'records':str(path)},'pred_key':'generated_ans','ref_key':mapping['input_label_key']})
            native_contract=gallery[bench]['meta']['evaluation']
            native=Runner(max_workers=2).run_bench_with_contract(native_bench,native_contract)['primary_metric_result']
            repaired_bench=BenchInfo(bench_name=bench,meta={'artifact_paths':{'records':str(path)},'pred_key':'generated_ans','ref_key':'_canonical_gold'})
            repaired_contract=copy.deepcopy(native_contract)
            repaired_contract['parser']={'type':'choice_letter','choices':'A-'+chr(64+len(source[0]['_displayed_choices'])),'choices_key':'_displayed_choices'}
            repaired=Runner(max_workers=2).run_bench_with_contract(repaired_bench,repaired_contract)['primary_metric_result']
            known_correct=sum(x['correct']==1 for x in selected);unknown=sum(x['correct'] is None for x in selected)
            constant='B' if bench=='winogrande' else 'A'
            baseline_accuracy=sum(x['gold_letter']==constant for x in selected)/len(selected)
            record={'bench':bench,'variant':variant,'model':model,'planned':12,
                    'completed_nonempty':sum(x['completed_nonempty'] for x in selected),
                    'strict_tag_parsed':12-unknown,'correct':known_correct,'unknown':unknown,
                    'semantic_accuracy_bounds':[known_correct/12,(known_correct+unknown)/12],
                    'native_scorer_score':native['score'],'native_scored_samples':native['scored_samples'],
                    'corrected_scorer_score':repaired['score'],'corrected_scored_samples':repaired['scored_samples'],
                    'constant_baseline':constant,'constant_baseline_semantic_accuracy':baseline_accuracy,
                    'native_scoring_scope':'Original reference/parser replay; for balanced SciQ the native reference/parser is intentionally left unchanged as a diagnostic and is not a valid estimator of displayed-option correctness.'}
            if unknown==0:
                assert abs(repaired['score']-known_correct/12)<1e-12
            # Score the constant baseline through the same native and corrected routes.
            for row in native_rows:row['generated_ans']='<answer>'+constant+'</answer>'
            path.write_text(''.join(audit.compact(x)+'\n' for x in native_rows))
            native_constant=Runner(max_workers=2).run_bench_with_contract(native_bench,native_contract)['primary_metric_result']
            corrected_constant=Runner(max_workers=2).run_bench_with_contract(repaired_bench,repaired_contract)['primary_metric_result']
            assert abs(corrected_constant['score']-baseline_accuracy)<1e-12
            record['constant_baseline_native_score']=native_constant['score']
            record['constant_baseline_corrected_score']=corrected_constant['score']
            record['robust_model_vs_constant_reversal']=(native['score']<native_constant['score']-1e-12 and known_correct/12>baseline_accuracy+1e-12)
            results.append(record)
    output=ROOT/'results'
    audit.dump(output/'MODEL_SMOKE_ROW_AUDIT.json',rows)
    audit.dump(output/'MODEL_SMOKE_RESULTS.json',{'models':sorted({x['model'] for x in rows}),
        'planned_calls':96,'recorded_calls':len(rows),'complete':sum(x['completed_nonempty'] for x in rows),
        'unparsed_or_incomplete':sum(x['correct'] is None for x in rows),'results':results,
        'scope':'Prospective small smoke:12 source rows/benchmark/model, source-stratified, intended gallery prompt rendering, no full One-Eval generation orchestration. Finite within-benchmark baseline comparisons; not representative population model scores.'})
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
