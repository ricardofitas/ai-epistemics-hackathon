"""Offline, source-authenticated consequence audit. No model or judge calls."""
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction
import argparse, hashlib, importlib.util, json, re, unicodedata
import numpy as np

HERE=Path(__file__).resolve().parent
BASE_T='results/tapex/exp1_tapex-base.json'
BASE_U='results/t5/exp2_pretrained_unifiedqa_base.json'
LARGE_T='results/tapex/exp3_tapex-large.json'
LARGE_U='results/t5/exp3_pretrained_unifiedqa_large.json'
HEAD_T='results/gpt3_rl/exp1_test_TQ-SA_2_seed_2.json'
HEAD_U='results/gpt3/exp4_test_TQ-SA_2_seed_2.json'
MODES=['original','explicit_only','residual_zero','residual_uniform','residual_lexicographic']

def norm(text):
    return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def selected_function(path,name):
    # The GPT-3 entrypoint imports unavailable provider dependencies. Extract only
    # its unchanged normalization function; record this bounded scope explicitly.
    import ast
    tree=ast.parse(path.read_text())
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
    namespace={'re':re}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    return namespace[name]

def independent_similarity(answer,output):
    if answer==output: return 3.0
    def clean(x): return re.sub(r'[{}^\\`\u2047<]',' ',x.replace('"','').replace("'",''))
    answer,output=clean(answer),clean(output)
    if answer==output: return 2.0
    if ' ' in answer or ' ' in output:
        a,b=answer.split(' '),output.split(' ')
        return len(set(a)&set(b))/max(len(a),len(b))
    return 0.0

class TracedNP:
    def __init__(self): self.scores=None
    def argmax(self,scores):
        assert self.scores is None
        self.scores=list(scores)
        return np.argmax(scores)

class TracedRandom:
    def __init__(self): self.candidates=None
    def choice(self,seq):
        self.candidates=list(seq)
        return self.candidates[0]

def gpt_clean(output):
    output=re.sub(r'\$?\\frac\{([\d\.\,\-]+)\}\{([\d\.\,]+)\}\$?',r'\1/\2',output)
    output=re.sub(r'(?<![AP]\.M)\.$','',output)
    output=re.sub(r'(?<=\d)[\=](?=[\-\$\d])',' = ',output)
    return re.sub(r'\u2212','-',output)

def number_category(text):
    return 'numeric_or_currency' if re.fullmatch(r'\s*[$€£]?\s*[-+]?\d[\d,. /%]*\s*',text) else 'other_text'

def difference(rows,a,b):
    constant=0
    variables=Counter()
    for pid in rows[a]:
        for path,sign in [(a,1),(b,-1)]:
            row=rows[path][pid]
            if row['residual']:
                variables[(pid,norm(row['output']))]+=sign
            else: constant+=sign*row['scores']['residual_zero']
    lower=constant+sum(min(0,c) for c in variables.values())
    upper=constant+sum(max(0,c) for c in variables.values())
    totals={m:sum(r['scores'][m] for r in rows[a].values())-sum(r['scores'][m] for r in rows[b].values()) for m in MODES}
    return dict(a=a,b=b,n=len(rows[a]),differences=totals,
                difference_bounds_residual_unknown=[lower,upper],
                shared_normalized_residual_groups=sum(c==0 for c in variables.values()),
                net_residual_correct_to_tie_from_zero=-constant,
                net_residual_correct_to_make_a_better=-constant+1,
                order_under_scoped_residual_uncertainty= 'a' if lower>0 else 'b' if upper<0 else 'unidentified',
                boundary_scope='Only residual zero-similarity outputs treated as unknown; all other historical grading fixed. Not full semantic gold.')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--inputs-dir',type=Path,default=HERE.parent/'upstream')
    p.add_argument('--prior-dir',type=Path,default=HERE.parent/'tabmwp-archive-audit-20261114')
    p.add_argument('--out-dir',type=Path,default=HERE/'results')
    args=p.parse_args(); args.out_dir.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((HERE/'acquisition.json').read_text())
    authenticated=[]
    for path,expected in manifest['blobs'].items():
        data=(args.inputs_dir/path).read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert actual==expected,(path,actual,expected)
        authenticated.append(dict(path=path,git_blob_sha=actual,bytes=len(data)))
    source=json.loads((args.inputs_dir/'data/tabmwp/problems_test.json').read_bytes())
    assert len(source)==7686
    tapex=module(args.inputs_dir/'run_tapex/eval.py','original_tapex_eval')
    t5=module(args.inputs_dir/'run_t5/eval.py','original_t5_eval')
    gpt=module(args.inputs_dir/'run_gpt3/utilities.py','original_gpt_utils')
    pg=module(args.inputs_dir/'run_gpt3_rl/utilities.py','original_pg_utils')
    gpt_normal=selected_function(args.inputs_dir/'run_gpt3/run_gpt3.py','normalize_answer')
    scores={};rows={};stochastic=[];witnesses=[]
    flag_checks=prediction_checks=baseline_choice_checks=0
    preflight=json.loads((args.out_dir/'headline-preflight.json').read_text())
    stopped={path:entry for path,entry in preflight.items() if entry['status']!='PASS'}
    result_paths=sorted(path for path in manifest['blobs'] if path.startswith('results/') and path not in stopped)
    for path in result_paths:
        archive=json.loads((args.inputs_dir/path).read_bytes())
        assert archive['results'].keys()==source.keys(),path
        baseline=path.startswith('results/t5/') or path.startswith('results/tapex/')
        evaluator=t5 if path.startswith('results/t5/') else tapex if baseline else pg if path.startswith('results/gpt3_rl/') else gpt
        normalize=evaluator.normalize_answer if baseline or evaluator is pg else gpt_normal
        summary=Counter(); detail={}; sums=Counter()
        for pid,row in archive['results'].items():
            item=source[pid];opts=item['choices'];unit=item['unit']
            assert item['answer']==row['answer']
            gold=normalize(item['answer'],unit).lower()
            stored=normalize(row['prediction'],unit).lower()==gold
            assert isinstance(row['true_false'],bool) and stored==row['true_false'],(path,pid,'flag')
            flag_checks+=1
            trace=TracedNP(); randomness=TracedRandom()
            evaluator.np=trace
            if not baseline: evaluator.random=randomness
            predicted=evaluator.extract_prediction(row['output'],opts) if baseline else evaluator.extract_prediction(row['output'],opts,archive['args']['option_inds'])
            if randomness.candidates is not None:
                assert row['prediction'] in [opts[i] for i in randomness.candidates]
                stochastic.append(dict(path=path,id=pid,candidate_indices=randomness.candidates))
            else:
                assert predicted==row['prediction'],(path,pid,'prediction',predicted,row['prediction'])
                prediction_checks+=1
            if baseline and opts:
                independent=[independent_similarity(o,row['output']) for o in opts]
                assert independent==trace.scores
                assert opts[independent.index(max(independent))]==row['prediction']
                baseline_choice_checks+=1
            # Only the actual fallback path qualifies; recognized GPT letters are protected.
            zero=bool(opts and trace.scores is not None and max(trace.scores)==0)
            text=row['output'] if baseline else gpt_clean(row['output'])
            explicit=[i for i,o in enumerate(opts or []) if norm(o)==norm(text)] if zero else []
            unique=len(explicit)==1
            residual=zero and not unique
            vals={m:int(stored) for m in MODES}
            if unique:
                valid=int(normalize(opts[explicit[0]],unit).lower()==gold)
                for m in MODES[1:]: vals[m]=valid
                summary['unique_explicit']+=1
                summary['explicit_flag_changes']+=valid!=stored
            if residual:
                vals['residual_zero']=0
                vals['residual_uniform']=sum(Fraction(int(normalize(o,unit).lower()==gold),len(opts)) for o in opts)
                selected=min(range(len(opts)),key=lambda i:(norm(opts[i]),opts[i],i))
                vals['residual_lexicographic']=int(normalize(opts[selected],unit).lower()==gold)
                summary['residual']+=1
                summary['residual_original_credits']+=stored
                summary['residual_'+number_category(row['output'])]+=1
            summary['zero_fallback']+=zero
            summary['choice_rows']+=bool(opts)
            for mode,value in vals.items(): sums[mode]+=value
            detail[pid]=dict(output=row['output'],residual=residual,zero=zero,unique=unique,
                            invalid_letter_random_fallback=randomness.candidates is not None,scores=vals)
            if zero and len(witnesses)<50 and baseline and path==BASE_T:
                witnesses.append(dict(id=pid,question=item['question'],table=item['table'],options=opts,
                                      raw_output=row['output'],original_prediction=row['prediction'],
                                      original_correct=stored,unique_explicit=unique,residual=residual))
        assert sums['original']==archive['correct'] and len(detail)==archive['count']
        assert abs(float(sums['original'])*100/len(detail)-archive['acc'])<1e-8
        scores[path]=dict(n=len(detail),counts=dict(summary),correct={k:float(v) for k,v in sums.items()},
                          percent={k:float(v)*100/len(detail) for k,v in sums.items()},
                          residual_unknown_bounds=[int(sums['residual_zero']),int(sums['residual_zero'])+summary['residual']],
                          reported_args_seed=archive['args'].get('seed'),archive_accuracy=archive['acc'])
        rows[path]=detail
    prior=json.loads((args.prior_dir/'exact_results.json').read_text())
    for path,row in prior['files'].items():
        for old,new in [('original','original'),('only_exact_override','explicit_only'),('exact_first_then_abstain','residual_zero')]:
            assert scores[path]['correct'][new]==row[old],(path,old)
    pairs={
        'primary_base':difference(rows,BASE_T,BASE_U),
        'large_control':difference(rows,LARGE_T,LARGE_U),
        'released_headline_seed':difference(rows,HEAD_T,HEAD_U),
        'tapex_size':difference(rows,LARGE_T,BASE_T),
        'unifiedqa_size':difference(rows,LARGE_U,BASE_U),
    }
    # Exploratory stricter stress: also treat out-of-range option-letter fallbacks
    # as unknown, retaining shared response labels on the same source question.
    constant=0;variables=Counter()
    for pid in source:
        for path,sign in [(HEAD_T,1),(HEAD_U,-1)]:
            row=rows[path][pid]
            if row['residual'] or row['invalid_letter_random_fallback']:
                variables[(pid,norm(row['output']))]+=sign
            else:constant+=sign*row['scores']['residual_zero']
    pairs['released_headline_seed']['exploratory_zero_plus_invalid_letter_unknown_bounds']=[
        constant+sum(min(0,c) for c in variables.values()),
        constant+sum(max(0,c) for c in variables.values())]
    # Common question-level order across models, stable without reliance on RNG versions.
    permutations=[]
    for seed in range(256):
        totals={path:int(sum(row['scores']['residual_zero'] for row in detail.values())) for path,detail in rows.items()}
        for pid,item in source.items():
            opts=item['choices']
            if not opts: continue
            order=sorted(range(len(opts)),key=lambda i:(hashlib.sha256(f'TABMWP-CONSEQUENCE-V1|{seed}|{pid}|{i}'.encode()).digest(),i))
            selected=opts[order[0]]
            correct=tapex.normalize_answer(selected,item['unit']).lower()==tapex.normalize_answer(item['answer'],item['unit']).lower()
            for path,detail in rows.items():
                if detail[pid]['residual']: totals[path]+=correct
        permutations.append(dict(seed=seed,correct=totals))
    for name,pair in pairs.items():
        deltas=[p['correct'][pair['a']]-p['correct'][pair['b']] for p in permutations]
        pair['common_permutations_256']=dict(min=min(deltas),max=max(deltas),mean=sum(deltas)/len(deltas),
             a_better=sum(x>0 for x in deltas),ties=sum(x==0 for x in deltas),b_better=sum(x<0 for x in deltas),
             scope='Monte Carlo scoring sensitivity on fixed outputs. Not new model experiments or a benchmark confidence interval.')
    results=dict(status='PASS',source_revision=manifest['source_rev'],source_questions=len(source),
                 released_archives=len(result_paths),authenticated_files=authenticated,
                 verification=dict(original_flag_checks=flag_checks,deterministic_prediction_checks=prediction_checks,
                     baseline_independent_choice_checks=baseline_choice_checks,stochastic_fallback_count=len(stochastic)),
                 scores=scores,pairs=pairs,
                 unsupported_archives={path:dict(status=row['status'],counts=row['counts']) for path,row in stopped.items()},
                 headline_scope='One released seed-2 PromptPG/few-shot-CoT pair, not three-run headline average. Zero-shot-CoT filename seed_2 has args.seed=1 and six extraction mismatches; stopped, not silently rescored.',
                 judge_calls=0,model_calls=0,human_labels=0,
                 semantic_boundary='Intervals vary only unresolved zero-fallback outputs and preserve all other historical labels. Partial source audit, not comprehensive semantic correction.')
    def default(x):
        if isinstance(x,Fraction): return float(x)
        raise TypeError(type(x))
    for name,obj in [('results.json',results),('permutations.json',permutations),('stochastic-fallbacks.json',stochastic),('witnesses.json',witnesses)]:
        (args.out_dir/name).write_text(json.dumps(obj,indent=2,default=default)+'\n')
    print(json.dumps(dict(status=results['status'],verification=results['verification'],pairs=pairs),indent=2,default=default))

if __name__=='__main__':main()
