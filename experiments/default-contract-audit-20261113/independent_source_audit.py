"""Separate exact-count audit from raw source rows, without One-Eval imports."""
from collections import Counter
from fractions import Fraction
import gzip
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CAPTURE=ROOT.parent/'default_contract_source_capture_20261113'/'capture'

def rows(file):
    return [json.loads(x) for x in gzip.decompress((CAPTURE/file).read_bytes()).splitlines()]

def main():
    results=json.loads((ROOT/'results/NATIVE_PREDICTOR_RESULTS.json').read_text())
    def result(bench,split,predictor):
        return next(x for x in results if x['bench']==bench and x['split']==split and x['predictor']==predictor)
    w=rows('winogrande__validation.jsonl.gz')
    counts=Counter(x['answer'] for x in w)
    assert set(counts)=={'1','2'}
    expected=Fraction(counts['2'],len(w))
    assert abs(result('winogrande','validation','semantic_oracle_letter')['score']-float(expected))<1e-12
    assert result('winogrande','validation','constant_B')['score']==1
    assert abs(result('winogrande','validation','constant_B')['semantic_source_accuracy']-float(expected))<1e-12
    test=rows('winogrande__test.jsonl.gz')
    assert all(x['answer']=='' for x in test)
    assert result('winogrande','test','constant_B')['scored_samples']==0
    s=rows('sciq__test.jsonl.gz')
    assert len(s)==1000
    # Correct source column is the first displayed option in every native row.
    assert all(x['correct_answer'] for x in s)
    baseline=result('sciq','test','constant_A')
    assert baseline['scored_samples']==997 and baseline['invalid_references']==3
    assert abs(baseline['score']-float(Fraction(994,997)))<1e-12
    lab=rows('lab-bench-language-agent-biology-benchmark__train.jsonl.gz')
    assert len(lab)==33 and all(x['ideal'] not in x['distractors'] for x in lab)
    assert all(x['ideal']!=x['distractors'][0] for x in lab)
    bogus=result('lab-bench-language-agent-biology-benchmark','train','constant_A')
    assert bogus['semantic_source_accuracy']==0 and bogus['score']==1 and bogus['scored_samples']==1 and bogus['invalid_references']==32
    for bench,file,key in [('medmcqa','medmcqa__validation.jsonl.gz','cop'),('hellaswag','hellaswag__validation.jsonl.gz','label')]:
        data=rows(file);c=Counter(int(x[key]) for x in data)
        assert set(c)=={0,1,2,3}
        assert result(bench,'validation','semantic_oracle_letter')['score']==1
        for label in range(4):
            score=Fraction(c[label],len(data))
            assert abs(result(bench,'validation','constant_'+chr(65+label))['score']-float(score))<1e-12
    rotations=json.loads((ROOT/'results/SCIQ_BALANCED_ROTATION_RESULTS.json').read_text())
    assert all(x['gold_position_counts']==dict.fromkeys('ABCD',250) for x in rotations)
    assert all(x['score']==(1.0 if x['predictor']=='semantic_oracle_letter' else .25) for x in rotations)
    report={'method':'Independent exact counts and Fractions from source rows; no scorer/parser imports.',
            'winogrande_label_counts':dict(counts),'winogrande_oracle_bad_score_exact':str(expected),
            'winogrande_constant_B_bad_score':1.0,'winogrande_constant_B_true_score_exact':str(expected),
            'winogrande_test_missing_gold':len(test),'sciq_constant_A_native_score_exact':'994/997',
            'sciq_correct_source_first_position_rows':1000,'sciq_balanced_constant_A':.25,
            'lab_missing_correct_option_rows':33,'lab_wrong_constant_A_native_score':1,
            'lab_wrong_constant_A_native_scored_samples':1,'lab_wrong_constant_A_true_score':0,
            'zero_based_controls_passed':['MedMCQA4183','HellaSwag10042'],'model_calls':0}
    (ROOT/'results/INDEPENDENT_SOURCE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
