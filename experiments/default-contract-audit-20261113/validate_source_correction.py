"""Full-source regression/causal checks of the proposed typed source adapter."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

import audit_contracts as audit
from source_contracts import UnscorableSource, normalize_record, evaluation_contract

def main():
    BenchInfo, Runner=audit.load_components()
    dispositions=json.loads((audit.CAPTURE/'DATASET_DISPOSITIONS.json').read_text())
    results=[]
    with tempfile.TemporaryDirectory() as temporary:
        path=Path(temporary)/'rows.jsonl'
        for source in dispositions:
            if source['status']!='captured':continue
            raw=gzip.decompress((audit.CAPTURE/source['rows_file']).read_bytes())
            source_rows=[json.loads(x) for x in raw.splitlines()]
            for permute in (False,True):
                normalized=[];errors={}
                for index,row in enumerate(source_rows):
                    try:normalized.append(normalize_record(source['bench'],row,source['rows_sha256']+'|'+str(index),permute=permute))
                    except UnscorableSource as error:errors[str(error)]=errors.get(str(error),0)+1
                if errors:
                    results.append({'bench':source['bench'],'split':source['split'],'permuted':permute,
                                    'status':'benchmark_rejected_before_inference','source_rows':len(source_rows),
                                    'errors':errors,'score':None})
                    continue
                for predictor in ('semantic_oracle','constant_A'):
                    rows=[];truths=[]
                    for row in normalized:
                        value=row['_contract_reference'] if predictor=='semantic_oracle' else '<answer>A</answer>'
                        rows.append({**row,'generated_ans':value})
                        truths.append(1 if predictor=='semantic_oracle' else int(row['_contract_reference']=='<answer>A</answer>'))
                    path.write_text(''.join(audit.compact(x)+'\n' for x in rows))
                    bench=BenchInfo(bench_name=source['bench'],meta={'artifact_paths':{'records':str(path)},'pred_key':'generated_ans','ref_key':'_contract_reference'})
                    result=Runner(max_workers=2).run_bench_with_contract(bench,evaluation_contract())['primary_metric_result']
                    assert result['scored_samples']==len(rows) and result['invalid_references']==0
                    assert abs(result['score']-sum(truths)/len(truths))<1e-12
                    results.append({'bench':source['bench'],'split':source['split'],'permuted':permute,
                                    'status':'verified','predictor':predictor,'rows':len(rows),
                                    'score':result['score'],'invalid_references':0,
                                    'choice_counts':sorted({len(x['choices']) for x in rows})})
    report={'scope':'Proposed explicit source adapter with original scorer. Generation orchestration is not changed or deployed. References canonicalized before inference; missing-gold source is rejected as a whole.',
            'results':results,'real_model_calls':0}
    (audit.ROOT/'results/SOURCE_CORRECTION_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'verified':sum(x['status']=='verified' for x in results),
                      'rejected_missing_gold_configurations':sum(x['status']=='benchmark_rejected_before_inference' for x in results)},indent=2))

if __name__=='__main__':main()
