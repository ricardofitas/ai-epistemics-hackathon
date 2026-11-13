#!/usr/bin/env python3
"""Frozen prospective finite-cohort performance-gap contrast; no inference/repair."""
import argparse
from collections import Counter,defaultdict
import datetime as dt
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import random

from gap_bounds import family_gap_bounds,mean_family_bounds
from scoring import score_answer

MODELS=('gemma-4-31b-it','deepseek-v4-flash')
VARIANTS=('numeric','paraphrase','p1_i0','p1_i1')
PACKAGES={'comparison':('p1_i0','p1_i1'),'target':('numeric','paraphrase')}
ALLOCATION={'families':30,'replication':30,'variants_per_family':4,'models':2,'batch_size':3,'requests':80,'classifications':240}
GAP_SPEC=dict(model_a=MODELS[0],model_b=MODELS[1],comparison_weights={'p1_i0':'1/2','p1_i1':'1/2'},target_weights={'numeric':'1/2','paraphrase':'1/2'})

def require(ok,message):
    if not ok:raise ValueError(message)

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def jsonl(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def write(path,value):
    with path.open('x',encoding='utf-8') as out:json.dump(value,out,indent=2,ensure_ascii=False,allow_nan=False);out.write('\n')

def exact_result(lower,upper):
    return {'lower_fraction':str(lower),'upper_fraction':str(upper),
            'lower':float(lower),'upper':float(upper),'lower_pp':float(100*lower),'upper_pp':float(100*upper),
            'point':float(lower) if lower==upper else None}

def finite_mean(rows):
    pairs=list(rows);require(pairs,'Empty finite mean')
    lo=sum(Fraction(a) for a,b in pairs)/len(pairs);hi=sum(Fraction(b) for a,b in pairs)/len(pairs)
    out=exact_result(lo,hi);out.update(n=len(pairs),known=sum(a==b for a,b in pairs));return out

def winner(scores):
    selected=[m for m in MODELS if all(Fraction(scores[m]['lower_fraction'])>Fraction(scores[n]['upper_fraction']) for n in MODELS if n!=m)]
    return selected[0] if len(selected)==1 else None

def validate_spec(spec):
    require(spec.get('models')==list(MODELS) and spec.get('variants')==list(VARIANTS),'Changed fixed models/variants in primaryspec')
    require(spec.get('role')=='replication' and spec.get('main_requests')==80 and spec.get('task_count')==120 and spec.get('intended_task_answers')==240,'Changed primaryspec allocation')
    require(spec.get('attempts_per_request')==1 and spec.get('retries')==0,'Changed request policy')
    primary=spec.get('primary',{})
    require(primary.get('id')=='gap_distortion' and primary.get('D')==MODELS[1] and primary.get('G')==MODELS[0], 'Changed contrast orientation')
    require(primary.get('meaningful_threshold_fraction')=='1/10' and primary.get('unknown_correctness_interval')==[0,1], 'Changed exact criterion/unknown policy')
    require(primary.get('population_claim') is False and primary.get('p_value') is False and primary.get('bounds_are_confidence_intervals') is False,'Unsupported inferential claim in primaryspec')
    b=spec.get('bootstrap',{})
    require(b.get('repeats')==10000 and b.get('family_seed')==20261113118 and b.get('batch_block_seed')==20261113119,'Changed bootstrap pins')

def validate_sources(directory):
    protocol=load(directory/'protocol.json')
    require(protocol.get('allocation')==ALLOCATION,'Changed exact allocation')
    require(protocol.get('models')==list(MODELS),'Changed fixed candidate orientation')
    pins=protocol.get('source_sha256',{})
    required={'selected_data.json','task_key.json','manifest.jsonl','admission/manifest.jsonl','source_manifest.json','source_disposition.json','selection_plan.json','primary_spec.json','prospective_design.md'}
    require(required<=set(pins),'Missing required source/primary pins')
    for table in ('source_sha256','implementation_sha256'):
        require(isinstance(protocol.get(table),dict) and protocol[table],'Missing provenance table')
        for relative,expected in protocol[table].items():
            rel=Path(relative)
            require(not rel.is_absolute() and '..' not in rel.parts,'Unsafe pinned input path')
            p=directory/rel
            require(p.is_file() and sha(p)==expected,table+' hash mismatch: '+relative)
    validate_spec(load(directory/'primary_spec.json'))
    source=load(directory/'selected_data.json')
    require(source.get('source_validation_status',source.get('status'))=='accepted_source_reviewed','Source-review gate absent')
    selected=sorted(source['families'],key=lambda f:f['selection_slot'])
    require(len(selected)==30 and len({f['source_family_id'] for f in selected})==30,'Need30 source families')
    require([f['selection_slot'] for f in selected]==list(range(1,31)),'Changed source slot allocation')
    family={f['source_family_id']:f for f in selected}
    for f in selected:
        require(f.get('source_validation_status')=='accepted' and f.get('analysis_role')=='replication','Unaccepted or wrong-role family')
        require(f['batch_block']==(f['selection_slot']-1)//3+1,'Changed batch block')
        require(len(f['variants'])==4 and {v['variant'] for v in f['variants']}==set(VARIANTS),'Changed source variant set')
    keys=load(directory/'task_key.json')['rows']
    require(len(keys)==120 and len({r['task_id'] for r in keys})==120,'Expected120 unique tasks')
    tasks={r['task_id']:r for r in keys}
    require(len({(r['family_id'],r['variant']) for r in keys})==120,'Repeated family/variant task')
    for r in keys:
        require(r['family_id'] in family and r['variant'] in VARIANTS,'Unknown task linkage')
        f=family[r['family_id']];item=next(v for v in f['variants'] if v['variant']==r['variant'])
        require(r['analysis_role']=='replication' and r['selection_slot']==f['selection_slot'] and r['batch_block']==f['batch_block'],'Changed task family allocation')
        require(r['gold_answer']==item['gold_answer'] and r['question_sha256']==hashlib.sha256(item['question'].encode()).hexdigest(),'Changed task question/gold')
    manifest=jsonl(directory/'manifest.jsonl')
    require(len(manifest)==80 and [r['execution_order'] for r in manifest]==list(range(1,81)) and [r['trial_id'] for r in manifest]==[f'GR-{i:03d}' for i in range(1,81)],'Changed exact80request execution sequence')
    seen=Counter()
    for row in manifest:
        require(row['requested_model'] in MODELS and row['request_payload']['model']==row['requested_model'],'Changed request model')
        ids=row['item_ids'];require(len(ids)==len(set(ids))==3 and set(ids)<=set(tasks),'Invalid3item batch')
        linked=[tasks[i] for i in ids]
        require(len({r['family_id'] for r in linked})==3,'Related variants share request')
        require(row['family_ids']==[r['family_id'] for r in linked],'Changed request family order')
        for field in ('analysis_role','variant','batch_block'):
            require(all(r[field]==row[field] for r in linked),'Mixed role/variant/block')
        require(row['request_sha256']==hashlib.sha256(canonical(row['request_payload'])).hexdigest(),'Changed payload hash')
        source_items=[]
        for task in linked:
            f=family[task['family_id']];item=next(v for v in f['variants'] if v['variant']==task['variant'])
            source_items.append({'id':task['task_id'],'question':item['question']})
        from prepare_manifest import INSTRUCTION
        require(row['request_payload']['input']==INSTRUCTION+'\n\n'+json.dumps(source_items,ensure_ascii=False),'Changed exact question-only prompt')
        seen.update((row['requested_model'],tid) for tid in ids)
    require(seen==Counter({(m,tid):1 for m in MODELS for tid in tasks}),'Missing/repeated candidate task')
    admission=directory/'admission';gate=load(admission/'GATE.json');controls=jsonl(admission/'manifest.jsonl')
    require(len(controls)==2 and {r['requested_model'] for r in controls}==set(MODELS) and {r['trial_id'] for r in controls}=={'AD-01','AD-02'},'Changed format controls')
    require(gate.get('status')=='pass' and gate.get('gate_passed') is True and gate.get('arithmetic_correctness_checked') is False and gate.get('planned_requests')==2 and gate.get('protocol_sha256')==sha(directory/'protocol.json') and gate.get('manifest_sha256')==sha(admission/'manifest.jsonl'),'Format-only admission failed or provenance differs')
    reports=gate.get('rows',[]);require(len(reports)==2 and {r['trial_id'] for r in reports}=={'AD-01','AD-02'},'Changed admission reports')
    for r in reports:
        require(r.get('capture_complete') is True and r.get('format_valid') is True and r.get('arithmetic_correctness_checked') is False,'Invalid format-only admission')
        for folder,suffix,field in (('api_artifacts','.json','artifact_sha256'),('stream_journals','.jsonl','journal_sha256')):
            p=admission/folder/(r['trial_id']+suffix)
            require(p.is_file() and r[field]==sha(p),'Changed admission raw evidence')
    return protocol,selected,tasks

def validate_predictions(directory,protocol,tasks):
    path=directory/'prediction_rows.jsonl';integrity=load(directory/'capture_integrity.json')
    require(integrity.get('status')=='capture_verified' and integrity.get('protocol_sha256')==sha(directory/'protocol.json') and integrity.get('manifest_sha256')==sha(directory/'manifest.jsonl') and integrity.get('prediction_rows_sha256')==sha(path),'Prediction provenance mismatch')
    require(integrity.get('planned_requests')==80 and integrity.get('predictions')==240,'Changed capture allocation')
    rows=jsonl(path);require(len(rows)==240,'Expected240 candidate task predictions');found={}
    for row in rows:
        key=row.get('model'),row.get('task_id')
        require(key[0] in MODELS and key[1] in tasks and key not in found,'Unknown/repeated prediction')
        a,b=row.get('score_lower'),row.get('score_upper')
        require(type(a) is int and type(b) is int and a in (0,1) and b in (0,1) and a<=b,'Invalid exact correctness bounds')
        require(type(row.get('capture_complete')) is bool and type(row.get('format_valid')) is bool,'Missing capture/format flags')
        require('raw_answer' in row,'Retained raw answer required')
        expected=score_answer(row['raw_answer'],tasks[key[1]]['gold_answer'])
        if not row['capture_complete']:
            expected={'label':'unknown','parsed_answer':None,'score_lower':0,'score_upper':1,'format_valid':False}
        require(all(row.get(k)==v for k,v in expected.items()),'Prediction differs from pinned answer-codec replay')
        if row['label'] in ('valid','wrong','abstain'):require(row['capture_complete'] and row['format_valid'],'Known correctness requires complete valid capture')
        found[key]=row
    require(set(found)==set(itertools.product(MODELS,tasks)),'Missing candidate task')
    return found,integrity

def percentile(values,p):
    ordered=sorted(values);index=(len(ordered)-1)*p;lo,hi=math.floor(index),math.ceil(index)
    return ordered[lo]*(hi-index)+ordered[hi]*(index-lo) if lo!=hi else ordered[lo]

def bootstrap(rows,unit,repeats,seed):
    groups=defaultdict(list)
    for row in rows:groups[row['family_id'] if unit=='source_family' else row['batch_block']].append(row)
    keys=sorted(groups,key=str);rng=random.Random(seed);lower=[];upper=[]
    for _ in range(repeats):
        sample=list(itertools.chain.from_iterable(groups[keys[rng.randrange(len(keys))]] for _ in keys))
        lower.append(sum(float(Fraction(r['gap_distortion']['lower_fraction'])) for r in sample)/len(sample))
        upper.append(sum(float(Fraction(r['gap_distortion']['upper_fraction'])) for r in sample)/len(sample))
    envelope=[percentile(lower,.025),percentile(upper,.975)]
    return {'unit':unit,'unit_count':len(keys),'repeats':repeats,'seed':seed,
      'bound_envelope95':envelope,'point_interval95':envelope if all(r['gap_distortion']['lower_fraction']==r['gap_distortion']['upper_fraction'] for r in rows) else None,
      'scope':'Conditional descriptive sensitivity of the fixed screened cohort/modelpair; not a population confidenceinterval or significance test'}

def analyze(directory):
    directory=directory.resolve();output=directory/'analysis'
    require(not output.exists(),'Analysis output exists; no overwrite')
    protocol,selected,tasks=validate_sources(directory)
    prediction,integrity=validate_predictions(directory,protocol,tasks)
    by_family={(r['family_id'],r['variant']):tid for tid,r in tasks.items()};rows=[]
    for f in selected:
        fid=f['source_family_id'];row={'family_id':fid,'analysis_role':'replication','batch_block':f['batch_block'],'variants':{}}
        pp={}
        for variant in VARIANTS:
            row['variants'][variant]={}
            for m in MODELS:
                p=prediction[m,by_family[fid,variant]];bounds=[p['score_lower'],p['score_upper']]
                row['variants'][variant][m]=bounds;pp[m,variant]=bounds
        for package,variants in PACKAGES.items():
            row[package]={m:[sum(row['variants'][v][m][k] for v in variants)/2 for k in (0,1)] for m in MODELS}
        row['joint_target']={m:[math.prod(row['variants'][v][m][k] for v in PACKAGES['target']) for k in (0,1)] for m in MODELS}
        row['gap_distortion']=exact_result(*family_gap_bounds(pp,**GAP_SPEC));rows.append(row)
    dl,dh=mean_family_bounds((Fraction(r['gap_distortion']['lower_fraction']),Fraction(r['gap_distortion']['upper_fraction'])) for r in rows)
    primary=exact_result(dl,dh)
    primary.update(definition='(DeepSeek-Gemma gap on mean P1_i0/P1_i1) minus (same gap on mean numeric/paraphrase)',
      meaningful_threshold_fraction='1/10',meaningful_replication=dl>=Fraction(1,10),positive_identified=dl>0,
      nonpositive_identified=dh<=0,meaningful_replication_ruled_out=dh<Fraction(1,10),
      direction_identified='positive' if dl>0 else 'nonpositive' if dh<=0 else 'unidentified',
      criterion_scope='Prespecified exact finite-cohort unknown-scorebox criterion, not a population inference',bounds_are_confidence_intervals=False)
    scores={package:{m:finite_mean(r[package][m] for r in rows) for m in MODELS} for package in ('comparison','target','joint_target')}
    scores['per_variant']={v:{m:finite_mean(r['variants'][v][m] for r in rows) for m in MODELS} for v in VARIANTS}
    choices={p:winner(scores[p]) for p in PACKAGES}
    for package in PACKAGES:
        a,b=scores[package][MODELS[0]],scores[package][MODELS[1]]
        scores[package+'_model_gap']=exact_result(Fraction(b['lower_fraction'])-Fraction(a['upper_fraction']),Fraction(b['upper_fraction'])-Fraction(a['lower_fraction']))
    output.mkdir()
    with (output/'per_source_family.jsonl').open('x',encoding='utf-8') as stream:
        for row in rows:stream.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    summary={'status':'complete_prospective_gap_analysis_with_unknown_bounds',
      'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'protocol_sha256':sha(directory/'protocol.json'),
      'prediction_rows_sha256':sha(directory/'prediction_rows.jsonl'),'capture_integrity_sha256':sha(directory/'capture_integrity.json'),
      'source_sha256':protocol['source_sha256'],'models':list(MODELS),'allocation':ALLOCATION,
      'capture':{'strict_complete_requests':integrity['strict_complete_requests'],'valid_json_requests':integrity['valid_json_requests'],
        'global_issues':integrity.get('global_issues',[]),
        'known_scores':sum(r['score_lower']==r['score_upper'] for r in prediction.values()),
        'unknown_scores':sum(r['score_lower']!=r['score_upper'] for r in prediction.values()),'labels':dict(Counter(r['label'] for r in prediction.values()))},
      'primary':primary,'scores':scores,'secondary_choices':{'scope':'Descriptive secondary only; no selection/confirmation causal consequence',
        'robust_unique_winners':choices,'different_identified_winners':choices['comparison']!=choices['target'] if all(choices.values()) else None},
      'bootstrap':{'family':bootstrap(rows,'source_family',10000,20261113118),'batch_block':bootstrap(rows,'batch_block',10000,20261113119)},
      'limitations':['Selected30 sourcefamilies, not a random sample of publicmath tasks','P1instances0and1, not the previous P1/P2 mixture',
        'Two fixedaliases, publicpretrainingexposure and immutableweight snapshots unproved','No isolatedaddedclause causality or populationgeneralization',
        'Agent source reviews, externalhumanvalidation pending','All unknownformat/capture scoresretain[0,1]; no repair/imputation']}
    write(output/'summary.json',summary)
    print(json.dumps({'primary':primary,'capture':summary['capture'],'output':str(output)},indent=2))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True)
    analyze(p.parse_args().directory)
