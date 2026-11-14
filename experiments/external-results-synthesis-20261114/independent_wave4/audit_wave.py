#!/usr/bin/env python3
"""Offline parameterized wave audit. Standard library only; no production module imports.
Scope: one 400-slot wave, not the full 3,200-slot study.
"""
import argparse, collections, datetime, decimal, gzip, hashlib, json, pathlib, re, string
from fractions import Fraction
parser=argparse.ArgumentParser(description='Independent offline main-campaign wave audit; no production imports')
parser.add_argument('--run-root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1])
parser.add_argument('--wave',type=int,required=True,choices=range(1,9))
parser.add_argument('--input',type=pathlib.Path,help='Extracted wave directory')
parser.add_argument('--output',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent)
parser.add_argument('--zip-sha256',required=True)
args=parser.parse_args()
ROOT=args.run_root.resolve(); OUT=args.output.resolve(); OUT.mkdir(parents=True,exist_ok=True)
WAVE=args.wave; START=(WAVE-1)*25; STOP=START+25
BASE=args.input.resolve() if args.input else ROOT/f'artifacts/wave{WAVE}'
ZIP=BASE.with_suffix('.zip')
D=decimal.Decimal
MODELS=['gemma-4-31b-it','qwen3.8-27b','deepseek-v4-flash','glm-5.2']
ARMS=['free_clear','free_none','choice_clear','choice_none']
RATES=[(D('.09'),D('.34')),(D('.039'),D('1.25')),(D('.045'),D('.14')),(D('1.40'),D('4.40'))]
errors=[]; checks=collections.Counter(); observations=[]
def check(ok, label, detail=''):
    checks[label]+=1
    if not ok: errors.append({'check':label,'detail':str(detail)})
def sha(b): return hashlib.sha256(b).hexdigest()
def canon(x): return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def lines(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def time(s): return datetime.datetime.fromisoformat(s)
def payload(c,m,a,i):
    parts=['Answer the source question using its context when relevant.',
      'Give the factual answer to the question in free form.' if a.startswith('free') else 'Select the best answer from the provided options.',
      'Question:\n'+c['question'],'Context:\n'+c['context']]
    if a.endswith('none'): parts.append('Options:\nA. None')
    parts.append('Put your final answer in <answer>...</answer> tags.')
    return dict(model=m,input='\n\n'.join(parts),temperature=0,max_output_tokens=4096 if i%4 in (0,1) else 6144,
                stream=True,tools=[],agentic_memory=False,store=False,tool_choice='none')
def final_answer(t):
    tags=re.findall(r'<answer\b[^>]*>(.*?)</answer\s*>',t,re.I|re.S)
    if tags: return tags[-1].strip(),'tag'
    ss=[x.strip() for x in t.splitlines() if x.strip()]
    return (re.sub(r'^(?:final answer|answer)\s*:\s*','',ss[-1],flags=re.I).strip(),'last_line') if ss else ('','empty')
def norm(s): return ' '.join(re.sub(r'\b(a|an|the)\b',' ',s.lower().translate(str.maketrans('','',string.punctuation))).split())
def num(s,u):
    s=s.strip().strip('*').strip().removesuffix('.').strip().replace('−','-')
    if u.startswith('$'):s=s.removeprefix('$').strip()
    suffix=u.strip().lstrip('$, ').strip()
    if suffix and s.casefold().endswith(' '+suffix.casefold()):s=s[:-len(suffix)].strip()
    if not re.fullmatch(r'[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:/\d+)?',s):return None
    try:return Fraction(s.replace(',',''))
    except (ValueError,ZeroDivisionError):return None
cases=json.loads((ROOT/'code/cases.json').read_bytes())
check(len(cases)==200,'frozen_case_count')
plan=[]
for i in range(START,STOP):
    c=cases[i]
    for position in range(4):
        for slot in range(4):
            offset=i//2+i%2; mi=(slot+offset)%4; ai=(position+mi+offset//4)%4
            m=MODELS[mi]; a=ARMS[ai]; p=payload(c,m,a,i)
            plan.append(dict(key=f"{c['dataset']}-{c['id']}-m{mi}-a{ai}",case=i,model=m,arm=a,request_sha=sha(canon(p)),payload=p))
manifest={r['key']:r for r in plan}
check(len(manifest)==400,'planned_unique_slots')
all_attempts=[]; all_finals={}; section_out={}; all_ids=set(); terminal_total=0
scores=collections.defaultdict(lambda:dict(n=0,correct=0,unknown=0,dummy=0,fallback=0))
for section, first,last in [(f's{WAVE-1}-front',START,START+4),(f's{WAVE-1}-back',START+4,STOP)]:
    section_scores=collections.defaultdict(lambda:dict(n=0,correct=0,unknown=0,dummy=0,fallback=0))
    folder=BASE/section; expected=[r for r in plan if first<=r['case']<last]
    intents=lines(folder/'intent.jsonl'); attempts=lines(folder/'attempts.jsonl')
    im={(r['key'],r['attempt']):r for r in intents}; am={(r['key'],r['attempt']):r for r in attempts}
    check(len(im)==len(intents),'unique_intent_identity',section)
    check(len(am)==len(attempts),'unique_attempt_identity',section)
    check(im.keys()==am.keys(),'intent_attempt_bijection',section)
    firsts=[x['key'] for x in intents if x['attempt']==1]
    check(firsts==[x['key'] for x in expected],'first_dispatch_schedule_order',section)
    finals={}; terminals=set(); used=collections.Counter(); reported=D(0); rated=D(0); conservative=D(0)
    bykey=collections.defaultdict(list)
    for a in attempts: bykey[a['key']].append(a)
    for key,aa in bykey.items():
        aa.sort(key=lambda a:a['attempt'])
        check([x['attempt'] for x in aa]==list(range(1,len(aa)+1)),'contiguous_attempt_numbers',key)
        check(len(aa)<=3,'maximum_three_attempts',key)
        for prior,nxt in zip(aa,aa[1:]):
            check(prior['http']==429 and prior['status']=='http_429','retry_only_explicit_429',key)
            check(time(nxt['start'])>=time(prior['end']),'retry_after_prior_end',key)
        finals[key]=aa[-1]
    for a in attempts:
        ident=(a['key'],a['attempt']); key=a['key']; r=manifest.get(key); it=im.get(ident)
        check(r is not None and first<=a['case']<last,'attempt_within_section',ident)
        if not r or not it:continue
        for k in ('case','model','arm','request_sha'):check(a[k]==r[k],'attempt_'+k,ident)
        check(it['request_sha']==r['request_sha'],'intent_request_sha',ident)
        p=r['payload']; ip,op=RATES[MODELS.index(r['model'])]
        reservation=(D(len(p['input'].encode())+1024)*ip+D(p['max_output_tokens'])*op)/D(1000000)
        check(abs(D(str(it['reserved']))-reservation)<D('1e-12'),'reservation_reconstruction',ident)
        check(time(it['at'])<=time(a['start'])<=time(a['end']),'attempt_time_order',ident)
        tpath=folder/'terminal'/f"{key}-{a['attempt']}.json.gz"
        if tpath.exists():
            terminals.add(tpath.name); terminal_total+=1
            raw=gzip.decompress(tpath.read_bytes()); t=json.loads(raw)
            check(raw==canon(t),'terminal_canonical_bytes',ident)
            check(sha(raw)==a.get('terminal_sha'),'terminal_byte_sha',ident)
            text=''.join(item.get('text','') for block in t.get('output',[]) if block.get('type')=='message' for item in block.get('content',[]) if item.get('type')=='output_text')
            text=text or t.get('output_text') or ''
            check(text==a.get('text'),'terminal_text_reconstruction',ident)
            check(sha(text.encode())==a.get('output_sha'),'output_text_sha',ident)
            for ak,tk in [('returned_model','model'),('response_id','id'),('status','status'),('incomplete_details','incomplete_details')]:
                check(a.get(ak)==t.get(tk),'terminal_'+tk,ident)
            check(t.get('model')==r['model'],'returned_requested_model',ident)
            check(bool(t.get('id')) and t['id'] not in all_ids,'unique_response_id',ident);all_ids.add(t.get('id'))
            for k in ['max_output_tokens','temperature','store','tool_choice','tools']:check(t.get(k)==p[k],'terminal_parameter_'+k,ident)
            u=t.get('usage') or {}; kept={k:u[k] for k in ['input_tokens','output_tokens','total_tokens','cost'] if k in u and isinstance(u[k],(int,float)) and not isinstance(u[k],bool) and u[k]>=0}
            check(a.get('usage')==kept,'terminal_usage_match',ident)
            check(u.get('input_tokens',-1)+u.get('output_tokens',-1)==u.get('total_tokens'),'usage_total_sum',ident)
            check(0<=u.get('output_tokens',-1)<=p['max_output_tokens'],'output_within_assigned_cap',ident)
            check(a['http']==200,'terminal_http200',ident)
            expected_event={'completed':'response.completed','incomplete':'response.incomplete'}.get(t.get('status'))
            check(a.get('terminal_event') in ['response.completed','response.incomplete','json_object'],'recognized_terminal_event',ident)
            if a.get('terminal_event')!=expected_event: observations.append(dict(kind='event_status_mismatch',key=key,attempt=a['attempt'],event=a.get('terminal_event'),status=t.get('status'),eligible=a.get('eligible')))
            elig=a['http']==200 and a.get('terminal_event') in ['response.completed','json_object'] and t.get('status')=='completed' and t.get('model')==r['model'] and bool(t.get('id')) and bool(text.strip())
            check(a.get('eligible')==elig,'eligibility_reconstruction',ident)
            if t.get('status')=='incomplete':check(t.get('incomplete_details',{}).get('reason')=='max_output_tokens','incomplete_reason',ident)
        else:
            check(a.get('http')==429 and a.get('status')=='http_429' and not a.get('eligible') and not a.get('usage'),'missing_terminal_only_http429',ident)
        u=a.get('usage') or {}
        reported+=D(str(u.get('cost',0))); used['input']+=u.get('input_tokens',0);used['output']+=u.get('output_tokens',0)
        if 'input_tokens' in u and 'output_tokens' in u:
            fee=(D(u['input_tokens'])*ip+D(u['output_tokens'])*op)/D(1000000)
            rated+=fee; conservative+=max(fee,D(str(u.get('cost',0))))
        else:conservative+=reservation
    disk={p.name for p in (folder/'terminal').glob('*.json.gz')}
    check(disk==terminals,'terminal_file_attempt_bijection',section)
    # Every dispatch after an explicit 429 must respect the recorded global cooldown.
    for a in attempts:
        if a.get('http')!=429:continue
        endpoint=time(a['end']); delay=max(4,float(a.get('retry_after_seconds',0)))
        nexts=[time(i['at']) for i in intents if time(i['at'])>=endpoint]
        if nexts:check((min(nexts)-endpoint).total_seconds()>=delay-.02,'recorded_429_cooldown',a['key'])
    schedule=json.loads((folder/'schedule.json').read_bytes()); cap=2; gap=1.; nh=0
    for j,s in enumerate(schedule):
        if j==0: check(s=={'elapsed_s':0.0,'reason':'initial','start_gap':1.0,'window':2},'initial_schedule',section);continue
        check(s['elapsed_s']>=schedule[j-1]['elapsed_s'],'schedule_monotone',section)
        if s['reason']=='HTTP_429':cap=max(2,cap//2);gap=min(5.5,max(1.25,1.55*gap));nh+=1
        elif s['reason']=='24_accepted':cap=min(8,cap*2);gap=max(.35,gap*.8)
        else:check(False,'known_schedule_transition',s)
        # Saved gaps are rounded; propagate a small tolerance for successive operations.
        check(s['window']==cap and abs(s['start_gap']-gap)<.003,'schedule_transition_rule',s)
    check(nh==sum(a.get('http')==429 for a in attempts),'schedule_429_transition_count',section)
    independent=dict(planned=len(expected),started_unique=len(finals),attempts=len(attempts),eligible=sum(a.get('eligible') is True for a in finals.values()),status=dict(collections.Counter(a['status'] for a in finals.values())),explicit_429=sum(a.get('http')==429 for a in attempts),unstarted=len(expected)-len(finals),input_tokens=used['input'],output_tokens=used['output'],reported_cost=float(reported))
    summary=json.loads((folder/'summary.json').read_bytes())
    for k,v in independent.items():
        check(abs(summary[k]-v)<1e-10 if isinstance(v,float) else summary[k]==v,'summary_'+k,section)
    progress=json.loads((folder/'progress.json').read_bytes())
    for k in ['planned','attempts']:check(progress[k]==independent[k],'progress_'+k,section)
    check(progress['completed']==independent['eligible'],'progress_completed',section)
    check(progress['unique_started']==independent['started_unique'],'progress_unique_started',section)
    check(progress['tokens']==dict(used),'progress_tokens',section)
    check(progress['stop'] is None,'no_stop',section)
    check(abs(D(str(progress['reserved_or_spent_credits']))-conservative)<=D('.00000051'),'progress_conservative_cost',section)
    check(conservative<=D(str(progress['ceiling_credits'])),'within_credit_ceiling',section)
    independent.update(reported_cost_decimal=str(reported),rate_calculated_cost_decimal=str(rated),conservative_charge_decimal=str(conservative),elapsed_s=progress['elapsed_s'],schedule_transitions=len(schedule))
    section_out[section]=independent;all_attempts+=attempts;all_finals.update(finals)
    # Independent endpoint extraction and normalization, for descriptive partial-panel counts.
    for r in expected:
        c=cases[r['case']]; a=finals.get(r['key'],{}); d=section_scores[(r['model'],c['dataset'],r['arm'])];d['n']+=1
        if not a.get('eligible'):d['unknown']+=1;continue
        ans,how=final_answer(a['text'])
        if c['dataset']=='squad':correct=bool(ans) and norm(ans) in {norm(g) for g in c['gold']}
        else:
            g={num(x,c['unit']) for x in c['gold']};check(None not in g,'numeric_gold_parse',r['key']);v=num(ans,c['unit']);correct=v is not None and v in g
        d['correct']+=int(correct);d['fallback']+=int(how=='last_line')
        d['dummy']+=int(bool(re.fullmatch(r'(?:[\(\[]?a[\)\].:]?(?:\s*[-:.)]?\s*none(?: of the above)?)?|none(?: of the above)?)\s*[.!]?',ans,re.I)))
    for m in MODELS:
        for ds in ['squad','tabmwp']:
            if not any(cases[i]['dataset']==ds for i in range(first,last)):continue
            for arm in ARMS:
                check(summary['models'][m][ds]['scores'][arm]==section_scores[(m,ds,arm)],'section_score_crosscheck',(section,m,ds,arm))
    for k,v in section_scores.items():
        for metric,value in v.items():scores[k][metric]+=value
check(set(all_finals)==set(manifest),'complete_400_slot_coverage')
result=dict(scope='Wave3 only: 400 of 3200 planned slots; case indexes 50..74 (25 sources), partial panel. No whole-study inference.',execution_commit='e853332434abc73d162ccf38eda2534b72c21cf0',zip_sha256=sha(ZIP.read_bytes()),cases_sha256=sha((ROOT/'code/cases.json').read_bytes()),source_datasets=dict(collections.Counter(cases[i]['dataset'] for i in range(START,STOP))),slots_by_model=dict(collections.Counter(r['model'] for r in plan)),slots_by_arm=dict(collections.Counter(r['arm'] for r in plan)),sections=section_out,total=dict(planned=400,attempts=len(all_attempts),unique_started=len(all_finals),terminal_files=terminal_total,completed=sum(a.get('eligible') is True for a in all_finals.values()),incomplete=sum(a['status']=='incomplete' for a in all_finals.values()),final_errors=sum(a['status'] not in ['completed','incomplete'] for a in all_finals.values()),http429_attempts=sum(a['http']==429 for a in all_attempts),input_tokens=sum(a.get('usage',{}).get('input_tokens',0) for a in all_attempts),output_tokens=sum(a.get('usage',{}).get('output_tokens',0) for a in all_attempts),reported_cost_decimal=str(sum((D(str(a.get('usage',{}).get('cost',0))) for a in all_attempts),D(0))),conservative_charge_decimal=str(sum((D(s['conservative_charge_decimal']) for s in section_out.values()),D(0)))),incomplete_by_model=dict(collections.Counter(a['model'] for a in all_finals.values() if a['status']=='incomplete')),incomplete_by_arm=dict(collections.Counter(a['arm'] for a in all_finals.values() if a['status']=='incomplete')),scores=[dict(model=k[0],dataset=k[1],arm=k[2],**v) for k,v in sorted(scores.items())],checks=dict(checks),failures=errors,observations=observations,limitations=['Source corpus selection/pinned upstream blobs not rederived; audit uses freshly fetched frozen cases.json.','Terminal bytes retained, but raw SSE stream bytes not present, so stream_sha is syntactically recorded rather than independently rehashed.','No provider recontact, human semantic validation, or full-study claims.'])
check(result['zip_sha256']==args.zip_sha256,'zip_identity')
result['checks']=dict(checks);result['failures']=errors
(OUT/'audit_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'failures':errors,'total':result['total'],'sections':section_out},indent=2))
raise SystemExit(bool(errors))
