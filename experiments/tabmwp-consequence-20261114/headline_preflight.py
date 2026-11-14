"""Check released GPT-3 archives before attributing policy effects to source code."""
from pathlib import Path
import json
from collections import Counter
from analyze import module, selected_function, TracedNP, TracedRandom

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'upstream'
source=json.loads((ROOT/'data/tabmwp/problems_test.json').read_bytes())
gpt=module(ROOT/'run_gpt3/utilities.py','gpt_preflight')
pg=module(ROOT/'run_gpt3_rl/utilities.py','pg_preflight')
normal=selected_function(ROOT/'run_gpt3/run_gpt3.py','normalize_answer')
result={}
for path in sorted(ROOT.glob('results/gpt*/**/*.json')):
    archive=json.loads(path.read_bytes())
    assert source.keys()==archive['results'].keys()
    ev=pg if path.parent.name=='gpt3_rl' else gpt
    nf=pg.normalize_answer if ev is pg else normal
    counts=Counter(); witnesses=[]
    for pid,row in archive['results'].items():
        item=source[pid];opts=item['choices'];unit=item['unit']
        assert item['answer']==row['answer']
        gold=nf(item['answer'],unit).lower()
        assert (nf(row['prediction'],unit).lower()==gold)==row['true_false']
        counts['stored_flag_checks']+=1
        tr=TracedNP(); rd=TracedRandom();ev.np=tr;ev.random=rd
        pred=ev.extract_prediction(row['output'],opts,archive['args']['option_inds'])
        if rd.candidates is not None:
            assert row['prediction'] in [opts[i] for i in rd.candidates]
            counts['stochastic_fallbacks']+=1
            continue
        counts['deterministic_prediction_checks']+=1
        if pred!=row['prediction']:
            counts['prediction_mismatches']+=1
            counts['flag_mismatches']+=(nf(pred,unit).lower()==gold)!=row['true_false']
            if len(witnesses)<12:
                witnesses.append(dict(id=pid,raw=row['output'],stored_prediction=row['prediction'],
                                      replay_prediction=pred,gold=item['answer'],stored_correct=row['true_false'],
                                      replay_correct=nf(pred,unit).lower()==gold,choices=opts))
    assert sum(r['true_false'] for r in archive['results'].values())==archive['correct']
    result[str(path.relative_to(ROOT))]=dict(status='STOP_UNSUPPORTED_PARSER_ATTRIBUTION' if counts['prediction_mismatches'] else 'PASS',
             counts=dict(counts),correct=archive['correct'],n=archive['count'],accuracy=archive['acc'],
             metadata_seed=archive['args'].get('seed'),witnesses=witnesses)
out=HERE/'results';out.mkdir(exist_ok=True)
(out/'headline-preflight.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({p:{k:v for k,v in row.items() if k!='witnesses'} for p,row in result.items()},indent=2))
