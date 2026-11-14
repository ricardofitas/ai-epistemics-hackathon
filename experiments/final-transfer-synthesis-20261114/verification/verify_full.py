#!/usr/bin/env python3
"""Offline independent full closeout and SAME24ID replay. No producer imports.

Reuses only the archived independent numeric validator's transport primitives,
parameterized over the full parent design. Scoring and selection are independent.
Run: python run2055/verification/verify_full.py
"""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal as D
import hashlib, importlib.util, json, re, string, zipfile

ROOT=Path(__file__).resolve().parents[1]; OUT=Path(__file__).resolve().parent
CAP=ROOT/'capture'; ART=CAP/'work/artifacts'; CODE=CAP/'work/code'
read=lambda p:json.loads(p.read_bytes())
lines=lambda p:[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
sha=lambda b:hashlib.sha256(b).hexdigest()
sp=importlib.util.spec_from_file_location('archived_independent',CAP/'work/independent_numeric/verify.py')
ind=importlib.util.module_from_spec(sp);sp.loader.exec_module(ind)
M=ind.MODELS; A=ind.MAIN_ARMS; canon=ind.canonical
audit=ind.Audit(); check=audit.check; cases=read(CODE/'cases.json'); summary=read(ROOT/'final_reports/results/summary.json')
check(sha(canon(cases))==ind.CASES_SHA,'frozen_case_identity')
check(len(cases)==200 and Counter(c['dataset'] for c in cases)=={'squad':100,'tabmwp':100},'source_coverage')
plan=[]
for i,c in enumerate(cases):
    for position in range(4):
        for slot in range(4):
            offset=i//2+i%2;mi=(slot+offset)%4;ai=(position+mi+offset//4)%4;m,a=M[mi],A[ai]
            p=ind.payload(c,m,i,a)
            plan.append(dict(key=f"{c['dataset']}-{c['id']}-m{mi}-a{ai}",case=i,model=m,arm=a,request_sha=sha(canon(p)),payload=p))
manifest={r['key']:r for r in plan}
check(len(manifest)==3200,'unique_3200_slots')
frozen=[{k:v for k,v in r.items() if k!='payload'} for r in plan]
check(sha(canon(frozen))==read(CODE/'design_receipt.json')['manifest_sha'],'frozen_manifest_identity')
final,totals=audit.capture(ART,plan,numeric=False)
check(len(final)==3200 and totals['unique_started']==3200 and totals['pending_intents']==0,'all_slots_started_and_recorded')
archives=[]; sections=[]; attempts=[]; disk=set(); declared=set()
provenance=read(ROOT/'final_reports/results/provenance.json')
for wave in range(1,9):
    base=ART/f'wave{wave}'; zp=base.with_suffix('.zip');digest=sha(zp.read_bytes())
    check(digest==provenance['waves'][wave-1][2].removeprefix('sha256:'),'original_wave_zip_digest',wave)
    with zipfile.ZipFile(zp) as z:
        for info in z.infolist():
            if not info.is_dir():
                p=base/info.filename
                check(p.exists() and p.read_bytes()==z.read(info),'original_zip_extracted_bytes',(wave,info.filename))
    archives.append(dict(wave=wave,sha256=digest))
    for ap in sorted(base.glob('*/attempts.jsonl')):
        folder=ap.parent;aa=lines(ap);ii=lines(folder/'intent.jsonl');im={(x['key'],x['attempt']):x for x in ii}; attempts.extend(aa)
        check(len(ii)==len(im)==len(aa),'intent_attempt_bijection',folder.name)
        start=(wave-1)*25;stop=wave*25
        expected=[r['key'] for r in plan if start<=r['case']<stop and ((r['case']<start+4)==folder.name.endswith('front'))]
        check([x['key'] for x in ii if x['attempt']==1]==expected,'initial_dispatch_order',folder.name)
        spent=D(0); rated=D(0);transport=[]
        for a in aa:
            identity=(a['key'],a['attempt']);p=manifest[a['key']]['payload'];u=a.get('usage') or {};ip,op=ind.RATES[a['model']]
            reserve=(D(len(p['input'].encode())+1024)*ip+D(p['max_output_tokens'])*op)/1000000
            check(abs(D(str(im[identity]['reserved']))-reserve)<D('1e-12'),'full_reservation_reconstruction',identity)
            if 'input_tokens' in u and 'output_tokens' in u:
                rate=(D(u['input_tokens'])*ip+D(u['output_tokens'])*op)/1000000;rated+=rate;spent+=max(rate,D(str(u.get('cost',0))))
            else:spent+=D(str(im[identity]['reserved']))
            tp=folder/'terminal'/f"{a['key']}-{a['attempt']}.json.gz"
            if tp.exists():declared.add(tp.resolve())
            else:
                check((a['http'],a['status']) in [(429,'http_429'),(200,'missing_terminal'),(504,'http_504')],'allowed_recorded_nonterminal_transport',identity)
                check(not a['eligible'] and not u and not a.get('terminal_event'),'no_fabricated_nonterminal_outcome',identity)
                if a['http']!=429:
                    check(sum(x['key']==a['key'] for x in aa)==1,'unknown_transport_never_retried',identity)
                    transport.append(dict(key=a['key'],attempt=a['attempt'],http=a['http'],status=a['status']))
        disk.update(p.resolve() for p in folder.glob('terminal/*.json.gz'))
        progress=read(folder/'progress.json')
        check(abs(spent-D(str(progress['reserved_or_spent_credits'])))<=D('0.00000051'),'conservative_progress_charge',folder.name)
        check(spent<=D(str(progress['ceiling_credits'])),'section_credit_ceiling',folder.name)
        sections.append(dict(section=folder.name,conservative_charge=str(spent),rate_card=str(rated),transport_unknowns=transport))
check(disk==declared,'global_terminal_attempt_bijection')

norm=lambda s:' '.join(re.sub(r'\b(a|an|the)\b',' ',s.lower().translate(str.maketrans('','',string.punctuation))).split())
def grade(c,text):
    ans,extraction=ind.final_answer(text)
    if c['dataset']=='squad':correct=bool(ans) and norm(ans) in {norm(g) for g in c['gold']}
    else:
        v=ind.number(ans,c['unit']);correct=v is not None and v in {ind.number(g,c['unit']) for g in c['gold']}
    dummy=bool(re.fullmatch(r'(?:[\(\[]?a[\)\].:]?(?:\s*[-:.)]?\s*none(?: of the above)?)?|none(?: of the above)?)\s*[.!]?',ans,re.I))
    return int(correct),int(dummy),extraction,ans
groups=defaultdict(dict);observations=[]
for r in plan:
    a=final.get(r['key'],{});c=cases[r['case']]
    v=grade(c,a['_independent_text']) if a.get('_independent_eligible') else (None,None,None,None)
    groups[(r['model'],c['dataset'],r['case'])][r['arm']]=v
    observations.append(dict(key=r['key'],source_index=r['case'],source_id=c['id'],model=r['model'],arm=r['arm'],request_sha=r['request_sha'],response_id=a.get('response_id'),status=a.get('status'),correct=v[0],dummy=v[1],final_answer=v[3]))
contrasts={'choice_carrier':[('choice_clear',1),('choice_none',-1)],'free_carrier':[('free_clear',1),('free_none',-1)],'interaction':[('choice_clear',1),('choice_none',-1),('free_none',1),('free_clear',-1)]}
results={}
for m in M:
    results[m]={}
    for ds in ('squad','tabmwp'):
        rows=[v for (mm,dd,i),v in groups.items() if (mm,dd)==(m,ds)];scores={};effects={}
        for arm in A:
            vs=[r[arm] for r in rows]
            scores[arm]=dict(n=len(vs),correct=sum(v[0]==1 for v in vs),dummy=sum(v[1]==1 for v in vs),unknown=sum(v[0] is None for v in vs),fallback=sum(v[2]=='last_line' for v in vs))
        for name,terms in contrasts.items():
            lo=hi=0;cc=[]
            for row in rows:
                l=h=0;complete=True
                for arm,sgn in terms:
                    x=row[arm][0]
                    if x is None:l+=min(0,sgn);h+=max(0,sgn);complete=False
                    else:l+=sgn*x;h+=sgn*x
                lo+=l;hi+=h
                if complete:cc.append(l)
            effects[name]=dict(n=len(rows),lower_pp=round(100*lo/len(rows),3),upper_pp=round(100*hi/len(rows),3),complete_pairs_or_sets=len(cc),complete_only_pp=round(100*sum(cc)/len(cc),3) if cc else None)
        results[m][ds]=dict(scores=scores,contrasts=effects)
check(results==summary['models'],'all_primary_scores_dummy_counts_and_source_paired_bounds')
aggregate=dict(planned=3200,started_unique=len(final),attempts=len(attempts),eligible=sum(a['_independent_eligible'] for a in final.values()),status=dict(Counter(a['status'] for a in final.values())),explicit_429=sum(a['http']==429 for a in attempts),unstarted=3200-len(final),terminal_objects_verified=len(disk),input_tokens=sum((a.get('usage') or {}).get('input_tokens',0) for a in attempts),output_tokens=sum((a.get('usage') or {}).get('output_tokens',0) for a in attempts))
for k,v in aggregate.items():check(v==summary[k],'original_summary_'+k)
cost=sum((D(str((a.get('usage') or {}).get('cost',0))) for a in attempts),D(0));rated=sum((D(s['rate_card']) for s in sections),D(0))
check(abs(cost-D(str(summary['reported_cost'])))<D('1e-10'),'reported_cost')
check(round(rated,7)==D(str(summary['rate_card_credits_without_cached_discount'])),'rate_card_rounded_seven_decimals')
caps={}
for a in attempts:
    if a['http']!=200:continue
    key=f"{a['model']}:{manifest[a['key']]['payload']['max_output_tokens']}";v=caps.setdefault(key,dict(received=0,complete=0,max_output_tokens=0))
    v['received']+=1;v['complete']+=int(a['eligible']);v['max_output_tokens']+=int((a.get('incomplete_details') or {}).get('reason')=='max_output_tokens')
check(caps==summary['cap_comparison'],'cap_table_HTTP200_received_definition')
pooled={}
for ds in ('squad','tabmwp'):
    pooled[ds]=dict(cases=100,scores={})
    for name in ('choice_carrier','interaction'):pooled[ds][name]=[sum(results[m][ds]['contrasts'][name][k] for m in M)/4 for k in ('lower_pp','upper_pp')]
    for arm in ('choice_clear','choice_none'):pooled[ds]['scores'][arm]={k:sum(results[m][ds]['scores'][arm][k] for m in M) for k in ('n','correct','unknown','dummy')}
check(pooled==read(ROOT/'final_reports/results/verified-8-waves.json')['datasets'],'verified8_pooled_scores_and_bounds')
decision={}
for arm in ('choice_none','free_clear'):
    src={m:results[m]['squad']['scores'][arm] for m in M};best=max(v['correct'] for v in src.values());winners=[m for m in M if src[m]['correct']+src[m]['unknown']>=best]
    target={m:results[m]['tabmwp']['scores']['free_clear'] for m in M};regret={}
    for m in winners:
        others=[v for mm,v in target.items() if mm!=m];t=target[m]
        regret[m]=[max(0,max(v['correct'] for v in others)-t['correct']-t['unknown']),max(0,max(v['correct']+v['unknown'] for v in others)-t['correct'])]
    decision[arm]=dict(admissible_winners=winners,target_clean_regret_pp=regret)
check(decision==summary['decision_transfer'],'admissible_winners_and_conditional_regret')
selected=sorted([(i,c) for i,c in enumerate(cases) if 150<=i<200 and c['dataset']=='tabmwp'],key=lambda x:sha(('20261114-numeric-option-v1|'+x[1]['id']).encode()))[:24]
indices={i for i,c in selected};linkage=[o for o in observations if o['source_index'] in indices]; numeric=lines(ART/'wavenumeric/capture/attempts.jsonl')
check(len(indices)==24 and len(linkage)==384,'same24_all_parent_slots')
check({a['case'] for a in numeric}==indices,'same24_numeric_source_indices')
check({a['key'] for a in numeric}=={f"tab-{c['id']}-{mi}-{arm}" for i,c in selected for mi in range(4) for arm in ('correct','wrong')},'same24_all_numeric_source_model_arm_keys')
counts={m:{arm:dict(planned=24,correct=sum(o['correct']==1 for o in linkage if o['model']==m and o['arm']==arm),dummy=sum(o['dummy']==1 for o in linkage if o['model']==m and o['arm']==arm),unknown=sum(o['correct'] is None for o in linkage if o['model']==m and o['arm']==arm)) for arm in A} for m in M}
original=read(CAP/'verified6/audit_result.json')
check(len(original['failures'])==14 and {v['check'] for v in original['failures']}=={'missing_terminal_only_http429'},'original_14_overstrict_failures_preserved')
result=dict(passed=not audit.errors,aggregate=aggregate,provider_cost_decimal=str(cost),rate_card_decimal=str(rated),archives=archives,sections=sections,models=results,pooled=pooled,cap_comparison=caps,decision_transfer=decision,same24=dict(source_count=24,planned=384,recorded=len(linkage),eligible=sum(o['correct'] is not None for o in linkage),unknown=sum(o['correct'] is None for o in linkage),source_indices=sorted(indices),by_model_condition=counts),checks=dict(audit.checks),failures=audit.errors,transport_observations=audit.observations,independent_validator_sha256=sha((CAP/'work/independent_numeric/verify.py').read_bytes()),original_sixwave_failure_report_sha256=sha((CAP/'verified6/audit_result.json').read_bytes()),limitations=['No new API calls or network operations; no production scoring/design imports.','Raw SSE bytes absent; recorded stream_sha cannot be independently rehashed.','Frozen source identity and all request identities checked; upstream corpus sampling not rerun.','Original 14 overstrict checker failures preserved. All 94 incomplete, 11 missing-terminal, and 9 HTTP504 outcomes remain unknown; no fabricated terminals.','Cap comparison received means HTTP200 attempts, including 11 missing-terminal streams.','Numeric secondary adjudication not repeated. SAME24ID retains fixed factual endpoint; label-only A remains nonnumeric.'])
(OUT/'full_closeout_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
(OUT/'same24_parent_observations.json').write_text(json.dumps(linkage,indent=2,sort_keys=True)+'\n')
print(json.dumps(dict(passed=result['passed'],aggregate=aggregate,same24=result['same24'],checks=sum(audit.checks.values()),failures=audit.errors),indent=2))
raise SystemExit(0 if result['passed'] else 1)
