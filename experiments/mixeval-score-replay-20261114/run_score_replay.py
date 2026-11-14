"""Frozen controlled-output replay, native choice rescoring vs official rule mode."""
import ast, copy, gzip, hashlib, json, logging, os, random, re, sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'reviewer'/'upstream'))
sys.path.insert(0,str(P))
import native_scaffold
canonical=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def dump(name,v): (P/name).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,list):return [clean(x) for x in v]
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def load_official():
    names={'find_all_sub','parse_multi_choice_response_rule','check_is_number','normalize_str','extract_numbers','parse_freeform_response_rule','eval_multi_choice','eval_freeform_rule'}
    src=P/'official/mix_eval/utils/metric_utils.py'
    tree=ast.parse(src.read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(nodes)==len(names)
    class TrackedRandom:
        def __init__(self):self.rng=random.Random(42);self.calls=0
        def choice(self,x):self.calls+=1;return self.rng.choice(x)
    rng=TrackedRandom();ns={'re':re,'np':np,'random':rng}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(src),'exec'),ns)
    return ns,rng
def fixtures(record,split):
    if split=='free_form':correct=record['target'][0];wrong='ZXQ_UNRELATED_SENTINEL'
    else:
        idx=record['target'][0];assert isinstance(idx,int) and 0<=idx<len(record['options'])
        correct=chr(65+idx);wrong=chr(65+(idx+1)%len(record['options']))
    return {'source_first_reference':correct,'explicit_wrong':wrong,'empty':'','always_A':'A'}
def main():
    protocol=json.loads((P/'PROTOCOL.json').read_text())
    assert hashlib.sha256((P/'SELECTED.jsonl.gz').read_bytes()).hexdigest()==protocol['inputs']['SELECTED.jsonl.gz']
    selected=[json.loads(x) for x in gzip.decompress((P/'SELECTED.jsonl.gz').read_bytes()).splitlines()]
    gallery=json.loads((P/'GALLERY_ENTRY.json').read_text())
    precls,_=native_scaffold.load_native_classes();precls._rescore_choice_single.__globals__['os']=os
    pre=precls.__new__(precls)
    official,rng=load_official();args=SimpleNamespace(model_type='ChatModel')
    captures=[];summaries=[];errors=[]
    out=P/'captures';out.mkdir(exist_ok=True)
    for split in ['free_form','multiple_choice']:
        cases=[s for s in selected if s['split']==split]
        source_frame,mapping=pre._preprocess_dataframe(pd.DataFrame([s['record'] for s in cases]),'mixeval',copy.deepcopy(gallery['meta']['key_mapping']),eval_type='key3_q_choices_a')
        for family in protocol['constructed_output_families']:
            responses=[fixtures(s['record'],split)[family] for s in cases]
            for condition in protocol['conditions']:
                key=split+'__'+family+'__'+condition
                rows=[];stats={};fallbacks_before=rng.calls
                try:
                    if condition!='official_rule_type_dispatch':
                        frame=source_frame.copy(deep=True);frame['generated_ans']=responses
                        if condition=='singleton_reference_only':
                            frame['target']=frame['target'].map(lambda t:t[0] if len(t)==1 else t)
                        frame['eval_score']=None
                        step=out/(key+'.jsonl');frame.to_json(step,orient='records',lines=True,force_ascii=False)
                        stats=pre._rescore_choice_single(str(step),str(out/(key+'.stats.json')),{},'generated_ans',mapping['input_label_key'],gallery['meta']['evaluation']['parser'])
                        rows=pd.read_json(step,lines=True).to_dict('records')
                        stats['interpretation']='UNSCORABLE' if stats.get('valid_samples')==0 else 'SCORABLE_DIAGNOSTIC'
                    else:
                        for s,response in zip(cases,responses):
                            r=s['record'];before=rng.calls
                            if split=='free_form':
                                parsed=official['parse_freeform_response_rule'](args,response)
                                score=official['eval_freeform_rule'](r['target'],parsed)
                            else:
                                labels=[chr(65+i) for i in range(len(r['options']))]
                                parsed=official['parse_multi_choice_response_rule'](args,response,labels,dict(zip(labels,r['options'])))
                                score=official['eval_multi_choice'](labels[r['target'][0]],parsed)
                            rows.append(dict(generated_ans=response,target=r['target'],eval_score=int(score),eval_valid=True,eval_error='',parsed=parsed,random_fallback=rng.calls>before))
                        stats=dict(total_samples=len(rows),valid_samples=len(rows),accuracy=sum(r['eval_score'] for r in rows)/len(rows),invalid_references=0,interpretation='OFFICIAL_RULE_MODE_CONSTRUCTED_CONTROLS')
                    stats.update(split=split,condition=condition,output_family=family,random_fallback_calls=rng.calls-fallbacks_before)
                    summaries.append(clean(stats))
                    for s,response,row in zip(cases,responses,rows):
                        captures.append(clean(dict(split=split,source_index=s['source_index'],source_sha256=hashlib.sha256(canonical(s['record'])).hexdigest(),condition=condition,output_family=family,constructed_response=response,result=row)))
                except Exception as e:errors.append(dict(panel=key,error=repr(e)))
    raw=b''.join(canonical(c)+b'\n' for c in captures);(P/'SCORING_CAPTURES.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0))
    report=dict(status='completed' if not errors else 'partial',source_rows=len(selected),condition_records=len(captures),panels=summaries,errors=errors,new_model_calls=0,scope=protocol['official_scope'],native_execution=protocol['provenance'])
    dump('SUMMARY.json',report);print(json.dumps(report))
if __name__=='__main__':main()
