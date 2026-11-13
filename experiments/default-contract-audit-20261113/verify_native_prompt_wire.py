"""Data-only replay of locked native generator and formatter, no model calls."""
import ast
import copy
import gzip
import hashlib
import inspect
import json
import logging
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
import pandas as pd
import audit_contracts as audit

SUPPORT=audit.ROOT.parent/'default_contract_locked_support_v2_20261113'/'locked_support'

def load_class(path,name,namespace,remove_bases=False):
    tree=ast.parse(path.read_text())
    node=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==name)
    node.decorator_list=[]  # Registration/type-check decorators do not change method bodies.
    if remove_bases:node.bases=[]
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    module=ast.fix_missing_locations(ast.Module(body=[future,node],type_ignores=[]))
    exec(compile(module,str(path),'exec'),namespace)
    return namespace[name]

class RecordedServing:
    def __init__(self):self.prompts=[];self.calls=0
    def generate_from_input(self,user_inputs,system_prompt=None):
        self.calls+=1;self.prompts=list(user_inputs)
        return ['<answer>A</answer>']*len(user_inputs)

class FrameStorage:
    def __init__(self,frame):self.frame=frame.copy();self.writes=0
    def read(self,*args,**kwargs):return self.frame.copy()
    def write(self,frame):self.frame=frame.copy();self.writes+=1;return 'in_memory_fixture'

def main():
    BenchInfo,_=audit.load_components()
    namespace={'Any':Any,'Dict':Dict,'List':List,'Literal':Literal,'Optional':Optional,'Union':Union,
               'pd':pd,'np':np,'json':json,'inspect':inspect,'get_logger':logging.getLogger}
    base=load_class(SUPPORT/'dataflow/core/prompt.py','PromptABC',namespace)
    formatter=load_class(SUPPORT/'dataflow/prompts/core_text.py','FormatStrPrompt',namespace)
    generator=load_class(audit.CAPTURE/'dataflow_wheel__dataflow__operators__core_text__generate__bench_answer_generator.py','BenchAnswerGenerator',namespace,remove_bases=True)
    preprocessor=audit.load_preprocessor()
    preprocessor._resolve_prompt_template.__globals__.update({'FormatStrPrompt':formatter,'hashlib':hashlib})
    gallery=json.loads(gzip.decompress((audit.CAPTURE/'one_eval__utils__bench_table__bench_gallery.json.gz').read_bytes()))
    gallery={x['bench_name']:x for x in gallery['benches']}
    dispositions=json.loads((audit.CAPTURE/'DATASET_DISPOSITIONS.json').read_text())
    summaries=[];hash_rows=[];examples=[]
    for source in dispositions:
        if source['status']!='captured':continue
        name=source['bench'];entry=gallery[name]
        rows=[json.loads(x) for x in gzip.decompress((audit.CAPTURE/source['rows_file']).read_bytes()).splitlines()]
        mapping=copy.deepcopy(entry['meta']['key_mapping'])
        frame,mapping=preprocessor._preprocess_dataframe(pd.DataFrame(rows),name,mapping,eval_type='key3_q_choices_a')
        bench=BenchInfo(bench_name=name,bench_dataflow_eval_type='key3_q_choices_a',meta=copy.deepcopy(entry['meta']))
        prompt_template,meta=preprocessor._resolve_prompt_template(bench,'key3_q_choices_a')
        choices_key=mapping['input_choices_key']
        if isinstance(choices_key,list):choices_key=choices_key[0]  # Exact run_eval fallback.
        serving=RecordedServing();storage=FrameStorage(frame)
        operator=generator(eval_type='key3_q_choices_a',llm_serving=serving,prompt_template=prompt_template,force_generate=True)
        produced=operator.run(storage=storage,input_question_key=mapping['input_question_key'],
                              input_context_key=mapping.get('input_context_key'),input_choices_key=choices_key,
                              output_key='generated_ans')
        if not serving.prompts:
            summaries.append({'bench':name,'split':source['split'],'rows':len(rows),
                              'status':'blocked_before_serving','serving_calls':serving.calls,
                              'choice_key_missing':choices_key not in frame.columns,'generator_return':produced})
            continue
        assert len(serving.prompts)==len(rows)
        counts={'question_present':0,'question_mutation_changes_prompt':0,
                'nonempty_context_rows':0,'context_present':0,'context_mutation_changes_prompt':0,
                'unresolved_template_field_rows':0}
        for index,(row,prompt) in enumerate(zip(frame.to_dict('records'),serving.prompts)):
            question=str(row[mapping['input_question_key']])
            context=operator._normalize_context(row.get(mapping.get('input_context_key'))) if mapping.get('input_context_key') else None
            choices=operator._ensure_list(row[choices_key])
            changed_question=operator._build_prompt(eval_type='key3_q_choices_a',question='AUDIT_QUESTION_NONCE_'+str(index),context=context,choices=choices)
            changed_context=operator._build_prompt(eval_type='key3_q_choices_a',question=question,context='AUDIT_CONTEXT_NONCE_'+str(index),choices=choices)
            unresolved=re.findall(r'\{\{[A-Za-z_][A-Za-z0-9_]*\}\}',prompt)
            counts['question_present']+=question in prompt
            counts['question_mutation_changes_prompt']+=changed_question!=prompt
            counts['nonempty_context_rows']+=bool(context)
            counts['context_present']+=bool(context) and context in prompt
            counts['context_mutation_changes_prompt']+=bool(context) and changed_context!=prompt
            counts['unresolved_template_field_rows']+=bool(unresolved)
            hash_rows.append({'bench':name,'split':source['split'],'row':index,
                              'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                              'question_mutation_changed':changed_question!=prompt,
                              'context_mutation_changed':changed_context!=prompt,'unresolved_fields':unresolved})
            if index<2:examples.append({'bench':name,'split':source['split'],'row':index,'native_prompt':prompt,
                                        'source_question':question,'unresolved_fields':unresolved})
        summaries.append({'bench':name,'split':source['split'],'rows':len(rows),'status':'native_generator_replayed',
                          'serving_calls':serving.calls,'generator_return':produced,**counts,'prompt_metadata':meta})
        print(name,source['split'],counts,flush=True)
    report={'scope':'Original One-Eval preprocessing/prompt-resolution methods and locked open-dataflow1.0.10 generator/formatter methods. Registry/type-check decorators and unused generator base removed; in-memory storage and fixed diagnostic serving replace I/O/backend. No model inference.',
            'comparison_to_model_smoke':'The prospective model smoke deliberately renders the intended gallery template directly; it is a scorer-layer experiment and does not include these native formatter failures.',
            'rows':summaries}
    audit.dump(audit.ROOT/'results/NATIVE_PROMPT_WIRE_AUDIT.json',report)
    (audit.ROOT/'results/NATIVE_PROMPT_WIRE_HASHES.jsonl.gz').write_bytes(gzip.compress((''.join(audit.compact(x)+'\n' for x in hash_rows)).encode(),mtime=0))
    (audit.ROOT/'results/NATIVE_PROMPT_WIRE_EXAMPLES.jsonl.gz').write_bytes(gzip.compress((''.join(audit.compact(x)+'\n' for x in examples)).encode(),mtime=0))

if __name__=='__main__':main()
