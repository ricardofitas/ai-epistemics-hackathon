"""Audit the installed unmodified EvalScope package; no inference backend calls."""
import argparse
import copy
from collections import Counter
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent

def compact(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str)
def write(path,x):path.write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str)+'\n')
def compressed(path,rows):path.write_bytes(gzip.compress((''.join(compact(x)+'\n' for x in rows)).encode(),mtime=0))

def visible(sample,adapter):
    if isinstance(sample.input,str):return adapter.process_sample_input(sample,'default')
    texts=[]
    for message in sample.input:
        content=message.content
        if isinstance(content,str):texts.append(content)
        else:texts.extend(getattr(piece,'text','') for piece in content)
    return '\n'.join(texts)

def expected_reference(name,record):
    if name=='winogrande':return chr(65+int(record['answer'])-1)
    if name=='hellaswag':return chr(65+int(record['label']))
    if name=='boolq':
        assert isinstance(record['answer'],bool)
        return 'A' if record['answer'] else 'B'
    if name=='pubmedqa':return str(record['answer']).upper()
    return record['answer']

def child(name,hub):
    os.environ['EVALSCOPE_CACHE']=str(ROOT/'dataset_cache'/hub/name)
    import evalscope.benchmarks
    import evalscope.metrics
    from evalscope.api.registry import get_benchmark
    from evalscope.config import TaskConfig
    from evalscope.api.dataset import Sample
    from evalscope.api.dataset.dataset import MemoryDataset
    from evalscope.api.evaluator import TaskState
    from evalscope.api.model import ModelOutput
    out=ROOT/'evidence'/(name+'__'+hub);out.mkdir(parents=True,exist_ok=True)
    config=TaskConfig(model='constructed-contract-control',datasets=[name],eval_type='openai_api',dataset_hub=hub,
                      dataset_args={name:{'few_shot_num':0}},seed=42)
    adapter=get_benchmark(name,config)
    assert not adapter.use_llm_judge,'This audit does not permit an LLM judge'
    original=adapter.record_to_sample
    raw=[];before=[]
    def observe(record):
        sample=original(record)
        raw.append(copy.deepcopy(record));before.append(sample.model_dump(mode='json'))
        return sample
    adapter.record_to_sample=observe  # Transparent recorder, return value unchanged.
    loading=adapter.load_dataset()
    datasets=adapter.test_dataset if adapter.test_dataset is not None else loading
    after=[s for key in datasets.keys() for s in datasets[key]]
    assert len(raw)==len(before)==len(after) and before,'Native record observer did not capture the whole dataset'
    compressed(out/'RAW_RECORDS.jsonl.gz',raw)
    compressed(out/'NATIVE_PRE_FORMAT_SAMPLES.jsonl.gz',before)
    compressed(out/'NATIVE_READY_SAMPLES.jsonl.gz',[s.model_dump(mode='json') for s in after])
    setup={'name':name,'hub':hub,'dataset_id':adapter.dataset_id,'dataset_revision':adapter.dataset_revision,
           'eval_split':adapter.eval_split,'source_default_shuffle_choices':adapter.shuffle_choices,
           'few_shot_num':adapter.few_shot_num,'samples':len(before),'package_version':importlib.metadata.version('evalscope'),
           'source_commit':'59bb367bd8565f347266a48ac1230af0b5131b97','new_model_calls':0}
    write(out/'SETUP.json',setup)
    source_checks=[]
    for index,(record,sample_json,ready) in enumerate(zip(raw,before,after)):
        sample=Sample.model_validate(sample_json)
        assert sample.target==expected_reference(name,record)
        wire=visible(sample,adapter);ready_wire=visible(ready,adapter) if not isinstance(ready.input,str) else ready.input
        assert wire.strip()==ready_wire.strip(),'Manual native formatting diverged from loaded inference-ready sample'
        q_key='sentence' if name=='winogrande' else 'ctx_a' if name=='hellaswag' else 'question'
        altered={**record,q_key:'SOURCE_QUESTION_NONCE_'+str(index)}
        changed=visible(original(altered),adapter)
        context_key='passage' if name=='boolq' else 'context' if name=='pubmedqa' else None
        context_changed=None
        if context_key:
            context_changed=visible(original({**record,context_key:'SOURCE_CONTEXT_NONCE_'+str(index)}),adapter)!=wire
        source_checks.append({'row':index,'reference_matches_source':True,'question_mutation_changes_prompt':changed!=wire,
                              'context_mutation_changes_prompt':context_changed,'wire_sha256':hashlib.sha256(wire.encode()).hexdigest()})
    compressed(out/'SOURCE_CHECKS.jsonl.gz',source_checks)
    all_scores=[]
    for shuffle in (False,True):
        samples=[Sample.model_validate(x) for x in before]
        dataset=MemoryDataset(samples=samples)
        if shuffle:dataset.shuffle_choices(seed=42)
        for old,new in zip(before,samples):
            if old.get('choices'):
                assert old['choices'][ord(old['target'])-65]==new.choices[ord(new.target)-65]
        counts=Counter(str(s.target) for s in samples)
        options=['YES','NO','MAYBE'] if name=='pubmedqa' else [chr(65+i) for i in range(max(len(s.choices or []) for s in samples))]
        for predictor in ['oracle',*options]:
            values=[];statuses=Counter()
            for index,sample in enumerate(samples):
                answer=sample.target if predictor=='oracle' else predictor
                completion=str(answer) if name=='pubmedqa' else 'ANSWER: '+str(answer)
                state=TaskState(model='constructed-control',sample=sample,output=ModelOutput.from_content(model='constructed-control',content=completion))
                filtered=adapter.filter_prediction(completion,state)
                score=adapter.match_score(completion,filtered,str(sample.target),state)
                value=score.main_value
                if value is None and len(score.value)==1:value=next(iter(score.value.values()))
                assert isinstance(value,(float,int)),score
                statuses[str(score.status)]+=1
                values.append(float(value))
            expected=1.0 if predictor=='oracle' else counts[predictor]/len(samples)
            actual=sum(values)/len(values)
            assert abs(actual-expected)<1e-12,(name,predictor,shuffle,actual,expected)
            all_scores.append({'predictor':predictor,'shuffle_choices':shuffle,'score':actual,'expected_from_source_targets':expected,
                               'rows':len(values),'target_counts':dict(counts),'statuses':dict(statuses)})
    write(out/'NATIVE_SCORES.json',all_scores)
    write(out/'COMPLETE.json',{'status':'complete','source_rows':len(raw),'source_reference_checks':len(source_checks),
         'question_dependency_failures':sum(not r['question_mutation_changes_prompt'] for r in source_checks),
         'context_dependency_failures':sum(r['context_mutation_changes_prompt'] is False for r in source_checks),
         'score_conditions':len(all_scores),'model_inference_calls':0})
    print(name,hub,'complete',len(raw),flush=True)

def main():
    protocol=json.loads((ROOT/'PROTOCOL.json').read_text());dispositions=[]
    for name in protocol['panel']:
        for hub in protocol['backend_order']:
            started=time.monotonic()
            try:
                result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',name,'--hub',hub],cwd=ROOT,
                                      stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
                                      timeout=protocol['per_backend_timeout_seconds'])
                out=ROOT/'evidence'/(name+'__'+hub);out.mkdir(parents=True,exist_ok=True)
                (out/'RUN.log').write_text(result.stdout)
                record={'name':name,'hub':hub,'return_code':result.returncode,'status':'complete' if result.returncode==0 else 'failed',
                        'elapsed_seconds':time.monotonic()-started}
            except subprocess.TimeoutExpired as error:
                out=ROOT/'evidence'/(name+'__'+hub);out.mkdir(parents=True,exist_ok=True)
                (out/'RUN.log').write_bytes(error.stdout or b'')
                record={'name':name,'hub':hub,'status':'timeout','elapsed_seconds':time.monotonic()-started}
            dispositions.append(record);write(ROOT/'DISPOSITIONS.json',dispositions)
            print(json.dumps(record),flush=True)
            if record['status']=='complete':break
    freeze=subprocess.run([sys.executable,'-m','pip','freeze'],capture_output=True,text=True)
    (ROOT/'INSTALLED_VERSIONS.txt').write_text(freeze.stdout)
    write(ROOT/'EXECUTION.json',{'python':sys.version,'model_inference_calls':0,'dispositions':dispositions})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--child');parser.add_argument('--hub');args=parser.parse_args()
    if args.child:child(args.child,args.hub)
    else:main()
