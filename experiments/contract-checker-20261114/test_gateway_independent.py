"""Independent offline engineering regression over four exposed captures.

No network, model, installed-native imports, or frozen input writes. Synthetic
mutations and controls have separate denominators from archived natural cases.
"""
from __future__ import annotations
import copy
import dataclasses
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('independent_gateway', WORK / 'source_contract_gateway.py')
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)
SELECTED = json.loads((ROOT / 'real/selected2.json').read_text())
SOURCES = {str(x['source_index']): x for x in SELECTED}
CASES = {}
for identity in ('40', '200'):
    for condition in ('source_typed', 'native_gallery'):
        directory = ROOT / 'real/results/real' / f'{identity}_{condition}'
        trace = json.loads((directory / 'HTTP_TRACE.json').read_text())
        assert len(trace) == 1
        t = trace[0]
        req = json.dumps(t['request_payload'], allow_nan=False).encode()
        raw = t['response_body'].encode()
        assert hashlib.sha256(req).hexdigest() == t['request_sha256']
        assert hashlib.sha256(raw).hexdigest() == t['body_sha256']
        CASES[(identity, condition)] = (t, req, raw, json.loads((directory / 'RESULT.json').read_text()))


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def capture(req, raw, **kwargs):
    return g.TransportCapture(http_status=kwargs.pop('http_status', 200), actual_request_bytes=req,
                              response_bytes=raw, capture_label=kwargs.pop('capture_label', 'historical archived HTTP_TRACE replay'), **kwargs)


def run(identity='40', condition='source_typed', *, registry=None, source=None,
        reference=None, raw=None, request=None, transport=None, **kwargs):
    entry = SOURCES[identity]
    t, req, archived_raw, original = CASES[(identity, condition)]
    source = copy.deepcopy(entry['record'] if source is None else source)
    key = kwargs.pop('source_key', (identity, entry['source_sha256']))
    reg = g.SourceRegistry.from_selected(SELECTED) if registry is None else registry
    reference = copy.deepcopy(source['target']) if reference is None else reference
    req = req if request is None else request
    raw = archived_raw if raw is None else raw
    fn = (lambda prepared: capture(req, raw)) if transport is None else transport
    return g.run_entrypoint(reg, key, source, reference, fn, native_request_bytes=req, **kwargs)


def raw_mutate(edit):
    raw = json.loads(CASES[('40', 'source_typed')][2])
    edit(raw)
    return json.dumps(raw, allow_nan=False).encode()


def row_source_mutate(key, value):
    s = copy.deepcopy(SOURCES['40']['record'])
    if value is DELETE:
        s.pop(key, None)
    else:
        s[key] = value
    return s


def anchored(source):
    key = (str(source.get('id')), digest(source))
    return g.SourceRegistry({key: source}), key


def with_source(source, **kwargs):
    reg, key = anchored(source)
    # Omit captured request bytes: malformed-source cases must fail before
    # transport, not simply because an unrelated archive request differs.
    calls = []
    def transport(prepared):
        calls.append(prepared)
        return capture(prepared.body, CASES[('40','source_typed')][2])
    r = g.run_entrypoint(reg, key, source, copy.deepcopy(source.get('target')), transport, **kwargs)
    r['_observed_transport_calls'] = len(calls)
    return r


def metric(primary=None, details=None):
    return {'primary_metric_result': {'score': 0.0, **(primary or {})}, 'primary_metric_details': [0.0] if details is None else details}


def score_run(value, **kwargs):
    return run(metric_adapter=lambda row: copy.deepcopy(value), scorer_sha256='a'*64, **kwargs)


def safe(v):
    if isinstance(v, bytes):
        return {'bytes_length': len(v), 'sha256': hashlib.sha256(v).hexdigest(), 'utf8': v.decode('utf8', errors='replace')}
    if isinstance(v, dict):
        return {str(k): safe(x) for k, x in v.items()}
    if isinstance(v, (tuple,list)):
        return [safe(x) for x in v]
    return v


DELETE = object()
SUCCESS = {'VERIFIED_WITHOUT_METRIC', 'SCORED'}
results = []

def check(name, group, action, predicate, expected):
    try:
        report = action()
        ok = bool(predicate(report))
        item = {'name': name, 'group': group, 'passed': ok, 'expected': expected,
                'actual_status': report.get('status'), 'failures': report.get('failures'),
                'transport_calls': report.get('transport_calls'), 'metric_calls': report.get('metric_calls')}
        if not ok:
            item['counterexample_report'] = safe(report)
    except Exception as e:
        item = {'name': name, 'group': group, 'passed': False, 'expected': expected,
                'exception': type(e).__name__, 'message': str(e)}
    results.append(item)


def blocked(r):
    return r['status'] not in SUCCESS


def preblocked(r):
    return blocked(r) and r['transport_calls'] == 0


def main():
    for identity in ('40','200'):
        t, req, raw, old = CASES[(identity,'source_typed')]
        final = json.loads(raw)['choices'][0]['message']['content']
        check(f'archive_{identity}_typed', 'natural_controls', lambda i=identity: run(i, delivered_row=CASES[(i,'source_typed')][3]['delivered_row'], original_native_result=CASES[(i,'source_typed')][3]['native_metric_runner']),
              lambda r,f=final, o=old: r['status']=='VERIFIED_WITHOUT_METRIC' and r['provider_final_content']==f and r['delivered_row']['generated_ans']==o['delivered_row']['generated_ans'] and r['original_native_result']==o['native_metric_runner'],
              'VERIFIED_WITHOUT_METRIC; provider structured final string preserved verbatim; native delivered generated_ans untouched')
        check(f'archive_{identity}_stock_typed_gate', 'natural_controls', lambda i=identity: run(i,'native_gallery'), preblocked, 'INVALID before transport: stock request cannot pass typed profile')
        check(f'archive_{identity}_stock_zero_replay', 'historical_native_metric_replay', lambda i=identity: score_run(CASES[(i,'native_gallery')][3]['native_metric_runner'],identity=i),
              lambda r: r['status']=='UNSCORABLE' and 'eligible_metric_score' not in r, 'UNSCORABLE; historical zero with scored_samples=0 and [null] must not become measured wrong answer')
        check(f'archive_{identity}_typed_original_zero_replay', 'historical_native_metric_replay', lambda i=identity: score_run(CASES[(i,'source_typed')][3]['native_metric_runner'],identity=i),
              lambda r: r['status']=='SCORED' and r['eligible_metric_score']==0, 'SCORED historical native diagnostic zero (numeric per-row detail); no fresh installed-native execution')
    for field, values in {'prompt':[DELETE,'', '   ', 42, []], 'context':[DELETE,None,42,{}], 'target':[DELETE,[],None,'Dance',[''],['Dance',42]], 'problem_type':[DELETE,'choice','free_form'], 'id':[True,False,None,40.0,[],{}, {'a':1},-1,'']}.items():
        for i,value in enumerate(values):
            check(f'malformed_source_{field}_{i}','artificial_source_faults',lambda f=field,v=value: with_source(row_source_mutate(f,v)),preblocked,'non-eligible before transport under explicit supported source schema')
    def registered_id_differs_from_index():
        source=copy.deepcopy(SOURCES['40']['record']);source['id']='case40'
        entry={'source_index':40,'source_sha256':digest(source),'record':source}
        reg=g.SourceRegistry.from_selected([entry])
        return run(registry=reg,source=source,source_key=('40',entry['source_sha256']))
    check('registered_row_id_distinct_from_source_index','positive_preservation',registered_id_differs_from_index,lambda r:r['status']=='VERIFIED_WITHOUT_METRIC' and r['delivered_row']['id']=='case40','registry source lookup identity and actual row ID are separate; exact registered record and hash suffice')
    def integer_source_id_roundtrip():
        source=copy.deepcopy(SOURCES['40']['record']);source['id']=40
        row=copy.deepcopy(source);row['id']='40'
        return with_source(source,delivered_row=row)
    check('integer_source_id_exact_string_roundtrip','positive_preservation',integer_source_id_roundtrip,lambda r:r['status']=='VERIFIED_WITHOUT_METRIC' and type(r['delivered_row']['id']) is str,'canonical nonnegative integer source ID can roundtrip to identical decimal string')
    check('unknown_task','artificial_source_faults',lambda:run(task_type='other'),preblocked,'unsupported task fails before transport')
    check('unsupported_provider','artificial_source_faults',lambda:run(provider_type='responses'),preblocked,'unsupported provider fails before transport')
    check('unknown_source','artificial_source_faults',lambda:run(source_key=('999','a'*64)),preblocked,'unknown trusted source fails before transport')
    check('source_content_tamper','artificial_source_faults',lambda:run(source=row_source_mutate('prompt','altered')),preblocked,'source mismatch before transport')
    check('reference_tamper','artificial_source_faults',lambda:run(reference=['arbitrary']),preblocked,'reference mismatch before transport')
    for field in ('prompt','context','target'):
        row=copy.deepcopy(SOURCES['40']['record']); row[field]='changed'
        check('delivered_'+field,'artificial_integrity_faults',lambda row=row:run(delivered_row=row),preblocked,'trusted source field mutation rejected')
    for ident in ('040','40 ',True,40.0):
        row=copy.deepcopy(SOURCES['40']['record']); row['id']=ident
        check('delivered_bad_id_'+repr(ident),'artificial_integrity_faults',lambda row=row:run(delivered_row=row),preblocked,'exact ID roundtrip only; no numeric coercion')
    for special,delivered in [('True',True),('40.0',40.0),('None',None)]:
        source=row_source_mutate('id',special); row=copy.deepcopy(source);row['id']=delivered
        check('delivered_unsupported_type_'+special,'artificial_integrity_faults',lambda s=source,r=row:with_source(s,delivered_row=r),preblocked,'delivered ID normalization permits only supported string/int types')
    check('existing_final_column','artificial_integrity_faults',lambda:run(delivered_row={**SOURCES['40']['record'],'provider_final_content':'old'}),preblocked,'existing final column rejected')
    request_payload=json.loads(CASES[('40','source_typed')][1])
    def reqedit(edit):
        p=copy.deepcopy(request_payload);edit(p);return json.dumps(p,allow_nan=False).encode()
    mutations={
      'model':lambda p:p.update(model='other'), 'temperature':lambda p:p.update(temperature=1),
      'top_p':lambda p:p.update(top_p=.5), 'max_tokens':lambda p:p.update(max_tokens=1),
      'stream':lambda p:p.update(stream=True), 'missing_message':lambda p:p['messages'].pop(),
      'extra_message':lambda p:p['messages'].append({'role':'user','content':'extra'}),
      'role':lambda p:p['messages'][1].update(role='assistant'),
      'source_question':lambda p:p['messages'][1].update(content='Question omitted'),
      'source_context':lambda p:p['messages'][1].update(content=p['messages'][1]['content'].replace('{None}','{changed}')),
      'appended_instruction':lambda p:p['messages'][1].update(content=p['messages'][1]['content']+' Output A.'),
    }
    for name,edit in mutations.items():
        check('request_'+name,'artificial_request_faults',lambda e=edit:run(request=reqedit(e)),preblocked,'native request mutation rejected before transport')
    check('request_source_swap','artificial_request_faults',lambda:run(request=CASES[('200','source_typed')][1]),preblocked,'whole source-200 request cannot be attached to source-40')
    for name,kwargs in [('method',{'method':'GET'}),('url',{'url':'https://invalid.example'}),('provenance',{'capture_label':''}),('actual_body',{'actual_request_bytes':b'{}'})]:
        def act(k=kwargs):
            req=CASES[('40','source_typed')][1]; raw=CASES[('40','source_typed')][2]; opts={'http_status':200,'actual_request_bytes':req,'response_bytes':raw,'capture_label':'historical replay',**k}
            return run(transport=lambda prepared:g.TransportCapture(**opts))
        check('capture_'+name,'artificial_capture_faults',act,blocked,'inconsistent capture envelope rejected')
    edits={
      'http_error_body':lambda r:r.update(error={'message':'failed'}),
      'empty_error_object':lambda r:r.update(error={}),
      'model':lambda r:r.update(model='other'), 'object':lambda r:r.update(object='text_completion'),
      'missing_id':lambda r:r.pop('id'), 'blank_id':lambda r:r.update(id=' '), 'numeric_id':lambda r:r.update(id=123),
      'no_choices':lambda r:r.update(choices=[]), 'multiple_choices':lambda r:r['choices'].append(copy.deepcopy(r['choices'][0])),
      'wrong_index':lambda r:r['choices'][0].update(index=1), 'bool_index':lambda r:r['choices'][0].update(index=False),
      'unfinished':lambda r:r['choices'][0].update(finish_reason='length'),
      'missing_message':lambda r:r['choices'][0].pop('message'),
      'wrong_role':lambda r:r['choices'][0]['message'].update(role='user'),
      'missing_content':lambda r:r['choices'][0]['message'].pop('content'),
      'null_content':lambda r:r['choices'][0]['message'].update(content=None),
      'blank_content':lambda r:r['choices'][0]['message'].update(content='\n '),
      'array_content':lambda r:r['choices'][0]['message'].update(content=[{'type':'text','text':'Dance'}]),
      'numeric_content':lambda r:r['choices'][0]['message'].update(content=42),
      'tool_calls':lambda r:r['choices'][0]['message'].update(tool_calls=[{'id':'tool','type':'function','function':{'name':'f','arguments':'{}'}}]),
    }
    for name,edit in edits.items():
        check('response_'+name,'artificial_capture_faults',lambda e=edit:run(raw=raw_mutate(e)),blocked,'response with error/unsupported or incomplete final is non-eligible')
    for name,raw in [('invalid_json',b'{'),('not_object',b'[]'),('duplicate_keys',b'{"id":"x","id":"y"}'),('nonfinite',b'{"x":NaN}'),('invalid_utf8',b'\xff')]:
        check('response_'+name,'artificial_capture_faults',lambda b=raw:run(raw=b),blocked,'malformed/unsupported response non-eligible')
    for status in (500,401,True,'200'):
        check('http_'+repr(status),'artificial_capture_faults',lambda s=status:run(transport=lambda p:capture(p.body,CASES[('40','source_typed')][2],http_status=s)),blocked,'HTTP status must be integer 200')
    def duplicate():
        registry=g.SourceRegistry.from_selected(SELECTED)
        first=run(registry=registry); second=run(registry=registry)
        return {**second,'_first_status':first['status']}
    check('duplicate_response','artificial_integrity_faults',duplicate,lambda r:r['_first_status']=='VERIFIED_WITHOUT_METRIC' and blocked(r) and 'duplicate_response_id' in r['failures'],'second capture with identical response id blocked')
    def registry_mutation():
        source=copy.deepcopy(SOURCES['40']['record']);key=('40',digest(source));reg=g.SourceRegistry({key:source});source['prompt']='changed'
        return run(registry=reg)
    check('registry_isolated_from_input_mutation','positive_preservation',registry_mutation,lambda r:r['status']=='VERIFIED_WITHOUT_METRIC','registry copied anchor independently')
    def transport_mutation():
        source=copy.deepcopy(SOURCES['40']['record']);ref=copy.deepcopy(source['target']);row=copy.deepcopy(source)
        def fn(p):
            source['prompt']='changed';ref.clear();row['target'].clear()
            return capture(p.body,CASES[('40','source_typed')][2])
        return run(source=source,reference=ref,delivered_row=row,transport=fn)
    check('inplace_mutation_during_transport','positive_preservation',transport_mutation,lambda r:r['status']=='VERIFIED_WITHOUT_METRIC' and r['delivered_row']['target']==SOURCES['40']['record']['target'] and r['delivered_row']['prompt']==SOURCES['40']['record']['prompt'],'approved source, reference and row stay snapshotted')
    def reentrant():
        reg=g.SourceRegistry.from_selected(SELECTED); inner=[]
        def fn(p):
            inner.append(run(registry=reg)); return capture(p.body,CASES[('40','source_typed')][2])
        r=run(registry=reg,transport=fn);r['_inner_status']=inner[0]['status'];return r
    check('reentrant_duplicate','artificial_integrity_faults',reentrant,lambda r:blocked(r) and r['_inner_status']=='VERIFIED_WITHOUT_METRIC','only one same-ID transaction eligible under reentrant callback')
    for name,value in [('null_details',metric(details=[None])),('bool_details',metric(details=[True])),('zero_eligible',metric(primary={'scored_samples':0})),('invalid_reference',metric(primary={'invalid_references':1})),('no_details',{'primary_metric_result':{'score':0}}),('bool_score',metric(primary={'score':True})),('nan_score',metric(primary={'score':float('nan')})),('error_result',{'error':'failed'})]:
        check('metric_'+name,'artificial_metric_faults',lambda m=value:score_run(m),lambda r:r['status'] in {'UNSCORABLE','INCOMPLETE'} and 'eligible_metric_score' not in r,'no numeric eligible score for invalid/zero-eligible metric')
    for name,value in [('negative_count',metric(primary={'scored_samples':-1})),('bool_count',metric(primary={'scored_samples':True})),('string_count',metric(primary={'scored_samples':'1'})),('multiple_count',metric(primary={'scored_samples':2})),('inconsistent_score',metric(primary={'score':1},details=[0])),('out_of_range_high',metric(primary={'score':2},details=[2])),('out_of_range_low',metric(primary={'score':-1},details=[-1]))]:
        check('metric_'+name,'artificial_metric_faults',lambda m=value:score_run(m),blocked,'malformed per-row metric evidence must not become SCORED')
    check('missing_scorer_identity','artificial_metric_faults',lambda:run(metric_adapter=lambda row:metric()),preblocked,'metric adapter requires explicit scorer identity before transport')
    final='\n\n<think>literal final</think> <answer>Dance</answer>  '
    check('literal_final_preserved','positive_preservation',lambda:run(raw=raw_mutate(lambda r:r['choices'][0]['message'].update(content=final,reasoning_content='unrelated'))),lambda r:r['status']=='VERIFIED_WITHOUT_METRIC' and r['provider_final_content']==final and r['provider_final_content_sha256']==hashlib.sha256(final.encode()).hexdigest(),'API final content is copied verbatim; tags/whitespace/reasoning never parsed')
    def hash_separation():
        r1=run(metric_adapter=lambda row:metric(),scorer_sha256='a'*64)
        r2=run(metric_adapter=lambda row:metric(),scorer_sha256='b'*64)
        fields=('source_sha256','request_sha256','response_sha256','provider_final_content_sha256','metric_result_sha256')
        return {**r1,'_unchanged':all(r1[x]==r2[x] for x in fields),'_scorer_changed':r1['scorer_sha256']!=r2['scorer_sha256']}
    check('scorer_metadata_hash_separation','positive_preservation',hash_separation,lambda r:r['status']=='SCORED' and r['_unchanged'] and r['_scorer_changed'],'scorer manifest identity stays separate from source/request/response/final/result hashes')
    def metric_mutation():
        def adapter(row):
            row['target'].clear();row['prompt']='mutated';row['provider_final_content']='mutated'
            return metric()
        return run(metric_adapter=adapter,scorer_sha256='a'*64)
    check('metric_callback_mutation_isolated','positive_preservation',metric_mutation,lambda r:r['status']=='SCORED' and r['delivered_row']['target']==SOURCES['40']['record']['target'] and r['delivered_row']['provider_final_content']=='\n\nDance','metric callback receives isolated copy, never mutates approved row')
    def cross_source_callback():
        other_raw=CASES[('40','source_typed')][2]
        return run(identity='200',transport=lambda p:capture(p.body,other_raw,capture_label='ARTIFICIAL trusted callback misassociation control'))
    check('transport_trust_cannot_prove_response_source_association','trust_boundary_controls',cross_source_callback,lambda r:r['status']=='VERIFIED_WITHOUT_METRIC' and 'no independent provider authentication' in r['trust_scope'],'declared transport trust boundary accepts internally consistent capture; hashes cannot prove model answered this source')
    def changed_content_callback():
        altered=raw_mutate(lambda r:r['choices'][0]['message'].update(content='artificial final'))
        return run(raw=altered)
    check('response_hash_observes_callback_bytes_not_external_anchor','trust_boundary_controls',changed_content_callback,lambda r:r['status']=='VERIFIED_WITHOUT_METRIC' and r['provider_final_content']=='artificial final' and r['response_sha256']!=hashlib.sha256(CASES[('40','source_typed')][2]).hexdigest(),'transport is the trust anchor: self-consistent substituted response body changes observed hash but is not independently authenticated')
    report={'scope':'Engineering regression on four previously exposed archived requests; no prospective evaluation, new model/provider calls, or installed-native execution.',
            'module_sha256':hashlib.sha256((WORK/'source_contract_gateway.py').read_bytes()).hexdigest(),
            'new_provider_calls':0,'fresh_installed_metric_runner_calls':0,'trust_limitations':['Caller transport is trusted for actual bytes and source-response association; captured response SHA is observed, not compared to an independently trusted provider receipt.','All native metric evidence in this test is explicitly historical replay or synthetic fault input; no installed MetricRunner was imported or executed.'],'results':results,
            'groups':{group:{'tested':sum(x['group']==group for x in results),'passed':sum(x['group']==group and x['passed'] for x in results)} for group in sorted({x['group'] for x in results})}}
    report['status']='PASS' if all(x['passed'] for x in results) else 'FAIL'
    dest=WORK/'INDEPENDENT_GATEWAY_REVIEW.json'
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    initial=WORK/'INDEPENDENT_GATEWAY_REVIEW_INITIAL.json'
    if not initial.exists():initial.write_bytes(dest.read_bytes())
    print(json.dumps({'status':report['status'],'groups':report['groups'],'failed':[x['name'] for x in results if not x['passed']]},indent=2))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
