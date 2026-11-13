#!/usr/bin/env python3
"""Prepare a separate prospective source-disjoint gap study; zero model calls."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import shutil

from scoring import numeric

ROOT = Path(__file__).resolve().parent
MODELS = ['gemma-4-31b-it', 'deepseek-v4-flash']
VARIANTS = ['numeric', 'paraphrase', 'p1_i0', 'p1_i1']
ROLE = 'replication'
N_FAMILIES, BATCH_SIZE, N_BLOCKS = 30, 3, 10
N_TASKS, N_REQUESTS = 120, 80
RUNNER_SHA = 'c280811c5f685cdc5b254d5097946835428cd87de6ea58218de1e2cad537fe5e'
INSTRUCTION = '''Solve each arithmetic word problem independently. Return only one JSON object mapping every provided ID to its final numerical answer as a string. Use exact integers, finite decimals, or an exact fraction a/b. Do not include units or explanations. If you cannot solve an item, use the string ABSTAIN. Include every ID exactly once and no extra keys. Do not browse or use tools.'''
IMPLEMENTATION = ['prepare_manifest.py','scoring.py','capture_math.py','gate_admission.py',
                  'analyze_gap.py','gap_bounds.py','test_runtime.py','test_gap_analysis.py',
                  'test_gap_bounds.py','README.md']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()

def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as out:
        json.dump(value,out,indent=2,ensure_ascii=False,allow_nan=False);out.write('\n')

def prepare(args):
    output=args.output_dir.resolve()
    inputs={
        'selected_data.json':args.selected_data,
        'source_manifest.json':args.source_manifest,
        'source_disposition.json':args.source_disposition,
        'selection_plan.json':args.selection_plan,
        'primary_spec.json':args.primary_spec,
        'prospective_design.md':args.prospective_design,
    }
    for name,path in inputs.items():
        if path is None or not path.is_file():
            raise FileNotFoundError('Missing required preparation input: '+name)
    if not args.runner.is_file() or sha(args.runner)!=RUNNER_SHA:
        raise ValueError('Exact frozen native SSE runner required')
    for name in IMPLEMENTATION:
        if not (ROOT/name).is_file():raise FileNotFoundError('Required implementation: '+name)
    from analyze_gap import validate_spec
    validate_spec(json.loads(args.primary_spec.read_text()))
    source=json.loads(args.selected_data.read_text())
    if source.get('source_validation_status',source.get('status'))!='accepted_source_reviewed':
        raise ValueError('Strict source-review acceptance required before preparation')
    families=sorted(source['families'],key=lambda f:f['selection_slot'])
    if len(families)!=N_FAMILIES or len({f['source_family_id'] for f in families})!=N_FAMILIES:
        raise ValueError('Need exactly30 unique accepted source families')
    if [f['selection_slot'] for f in families]!=list(range(1,31)):
        raise ValueError('Expected exact slots1..30')
    if Counter(f['analysis_role'] for f in families)!={ROLE:N_FAMILIES}:
        raise ValueError('All30 families must belong to the single replication role')
    for family in families:
        if family.get('source_validation_status')!='accepted':raise ValueError('Every family requires strict source admission')
        if family['batch_block']!=(family['selection_slot']-1)//BATCH_SIZE+1:
            raise ValueError('Source priority/common batch partition changed')
        variants={x['variant']:x for x in family['variants']}
        if len(family['variants'])!=4 or set(variants)!=set(VARIANTS):raise ValueError('Wrong variant set')
        for item in variants.values():
            if not isinstance(item['question'],str) or not item['question'].strip():raise ValueError('Empty source question')
            numeric(item['gold_answer'])
    for filename,field in (('source_disposition.json','source_disposition_sha256'),('selection_plan.json','selection_plan_sha256')):
        if source.get(field) and source[field]!=sha(inputs[filename]):raise ValueError('Source-review proof digest mismatch: '+filename)
    # Validate all external inputs before creating any generated scientific output.
    output.mkdir(parents=True,exist_ok=True)
    for n in ('manifest.jsonl','task_key.json','protocol.json','admission'):
        if (output/n).exists():raise FileExistsError('Refusing to overwrite prepared cohort: '+n)
    for name,path in inputs.items():
        target=output/name
        if target.resolve()==path.resolve():continue
        if target.exists():
            if sha(target)!=sha(path):raise FileExistsError('Conflicting preparation input: '+name)
        else:shutil.copyfile(path,target)
    ids=[f'T{i:04d}' for i in range(1,N_TASKS+1)]
    random.Random(20261113120).shuffle(ids)
    tasks,lookup=[],{}
    for family in families:
        by_variant={x['variant']:x for x in family['variants']}
        for variant in VARIANTS:
            item=by_variant[variant]
            row={'task_id':ids[len(tasks)],'family_id':family['source_family_id'],
                 'selection_slot':family['selection_slot'],'analysis_role':ROLE,
                 'batch_block':family['batch_block'],'variant':variant,
                 'gold_answer':item['gold_answer'],'question_sha256':hashlib.sha256(item['question'].encode()).hexdigest()}
            tasks.append(row);lookup[family['source_family_id'],variant]=row
    write_new(output/'task_key.json',{'rows':tasks})
    requests=[]
    for model in MODELS:
        for variant in VARIANTS:
            for block in range(1,N_BLOCKS+1):
                batch=[f for f in families if f['batch_block']==block]
                if len(batch)!=BATCH_SIZE:raise ValueError('Expected3 unrelated families in every block')
                items=[]
                for f in batch:
                    item=next(v for v in f['variants'] if v['variant']==variant)
                    items.append({'id':lookup[f['source_family_id'],variant]['task_id'],'question':item['question']})
                payload={'model':model,'input':INSTRUCTION+'\n\n'+json.dumps(items,ensure_ascii=False),
                         'stream':True,'temperature':0,'max_output_tokens':8192,
                         'tools':[],'tool_choice':'none','agentic_memory':False,'store':False}
                requests.append({'requested_model':model,'analysis_role':ROLE,'variant':variant,'batch_block':block,
                    'item_ids':[v['id'] for v in items],'family_ids':[f['source_family_id'] for f in batch],
                    'request_payload':payload,'request_sha256':hashlib.sha256(canonical(payload)).hexdigest()})
    random.Random(20261113121).shuffle(requests)
    for i,row in enumerate(requests,1):row.update(trial_id=f'GR-{i:03d}',execution_order=i)
    with (output/'manifest.jsonl').open('x',encoding='utf-8',newline='\n') as out:
        for row in requests:out.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    admission=output/'admission';admission.mkdir(exist_ok=False)
    neutral=[{'id':'A001','question':'A box contains 2 red balls and 3 blue balls. How many balls are in the box?'},
             {'id':'A002','question':'A pencil costs 4 dollars. What is the cost of 3 pencils?'},
             {'id':'A003','question':'Mira has 9 cards and gives away 2 cards. How many cards remain?'}]
    with (admission/'manifest.jsonl').open('x',encoding='utf-8',newline='\n') as out:
        for i,model in enumerate(MODELS,1):
            payload={'model':model,'input':INSTRUCTION+'\n\n'+json.dumps(neutral,ensure_ascii=False),
                'stream':True,'temperature':0,'max_output_tokens':8192,'tools':[],
                'tool_choice':'none','agentic_memory':False,'store':False}
            row={'trial_id':f'AD-{i:02d}','requested_model':model,'item_ids':[x['id'] for x in neutral],
                 'admission_only':True,'request_payload':payload,'request_sha256':hashlib.sha256(canonical(payload)).hexdigest()}
            out.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    pins={name:sha(output/name) for name in inputs}
    pins.update({name:sha(output/name) for name in ('task_key.json','manifest.jsonl','admission/manifest.jsonl')})
    protocol={
      'id':'source-disjoint-prospective-gap-replication30-20261113',
      'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'status':'prepared_before_new_replication_model_outputs',
      'models':MODELS,
      'candidate_selection':'Same fixed pair as the completed math30 pilot; the replication hypothesis and pair are informed by that pilot. This is not performance-blind model discovery. Aliases do not pin provider weights.',
      'source_sha256':pins,'implementation_sha256':{n:sha(ROOT/n) for n in IMPLEMENTATION},
      'runner_sha256':RUNNER_SHA,
      'allocation':{'families':30,'replication':30,'variants_per_family':4,'models':2,'batch_size':3,'requests':80,'classifications':240},
      'admission':{'requests':2,'items_per_request':3,'directory':'admission',
        'gate':'Strict capture plus exact JSON IDs and numeric/ABSTAIN representation only; never arithmetic correctness',
        'failure':'Stop before all80 main calls if either fixed model fails; no retry or replacement',
        'maximum_total_requests':82,'maximum_total_requested_output_tokens':671744},
      'randomization':{'source_priority_seed':20261113117,'task_id_seed':20261113120,
        'request_order_seed':20261113121,'common_batch_blocks':'Priorityslots groupedby3; allvariants/models share10 fixed blocks'},
      'inference':{'temperature':0,'max_output_tokens':8192,'concurrency':2,'socket_timeout_seconds':120,
        'attempts_per_request':1,'maximum_requested_output_tokens':655360,
        'tools':[],'agentic_memory':False,'store':False,'history':'none'},
      'parse':{'final':'EntireJSON object; optional single outer fence; exact requested IDs once,noextras/duplicates',
        'answers':'Frozen numeric codec unchanged from math30: JSONstrings exactinteger/decimal/exponent/fraction; ABSTAINvalidwrong',
        'unknown':'Incompletecapture,invalidbatchJSONorinvalidnumericitem retains[0,1]; norepair,noimputedwrong'},
      'scoring':{'primary':'D=(DeepSeek-Gemma meanaccuracygap on P1instances0and1) minus(samegap on numericalsubstitution/paraphrase)',
        'model_a':MODELS[0],'model_b':MODELS[1],
        'comparison_variants':['p1_i0','p1_i1'],'target_variants':['numeric','paraphrase'],
        'variant_weights':'Eachpackage uses1/2 pervariant; all30sourcefamiliesequallyweighted',
        'meaningful_replication_threshold':'1/10','meaningful_replication_rule':'exactsharpDlower>=1/10',
        'positive_identified_rule':'exactsharpDlower>0',
        'bounds':'Combineidenticalcandidate/variantoutcomecoefficientsbefore sharp independent[0,1]box bounds',
        'secondary':'Modelrankingchange,pervariantaccuracyandtargetjointaccuracy; nosuccessrescue'},
      'bootstrap':{'repeats':10000,'family_seed':20261113118,'batch_block_seed':20261113119,
        'units':['source_family','common_three_family_batch_block'],
        'scope':'Conditionaldescriptivepercentileboundenvelopes on thisfixedcohort;notpopulationCIs or significance'},
      'stopping':'All80frozenmainrequests once after2formatcontrols; noadditionalfamilies/models,earlysuccessstop,retry,repairorautomaticresume',
      'evidence_scope':'Newsource-disjointselectedcohort and prospective endpoint. P1instances0/1 differ from previous P1/P2 package. No population claim or isolated causal claim about addedclauses; publicpretrainingexposure and immutableweights unproved.'}
    write_new(output/'protocol.json',protocol)
    print(json.dumps({'prepared':str(output),'requests':len(requests),'admission_requests':2,'tasks':len(tasks),'inference_calls':0,'protocol_sha256':sha(output/'protocol.json')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('selected-data','source-manifest','source-disposition','selection-plan','primary-spec','prospective-design','runner'):
        p.add_argument('--'+flag,type=Path,required=True)
    p.add_argument('--output-dir',type=Path,default=ROOT)
    prepare(p.parse_args())
