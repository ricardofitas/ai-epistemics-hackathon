from pathlib import Path
from collections import Counter,defaultdict
import json,gzip,hashlib,re,sys
R=Path(__file__).parent;W=R/(sys.argv[1] if len(sys.argv)>1 else 'wave0018');P=R/'payload/compact_science'
rd=lambda p:[json.loads(l) for l in p.read_bytes().splitlines() if l.strip()]
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
manifest=rd(P/'compact-all-manifest.jsonl');assert sha((P/'compact-all-manifest.jsonl').read_bytes())=='d4f063c6f16f47a804d68fa4e505abde62d90a74d9729ad98570768d277cd315';requests={r['trial_id']:r for r in manifest};assert len(requests)==636
normal=rd(W/'analysis/NORMALIZED.jsonl');norm={r['trial_id']:r for r in normal};assert len(norm)==len(normal)
old_intent=[];old_attempt=[]
for a in ['14138164416','14138939635']:
 old_intent+=rd(R/a/'execution_track/capture/intent.jsonl');old_attempt+=rd(R/a/'execution_track/capture/attempts.jsonl')
old_keys={(x['trial_id'],x['attempt'],x['request_sha256']) for x in old_intent}
old_last={};old_started={x['trial_id'] for x in old_intent}
for a in old_attempt:old_last[a['trial_id']]=a
raw_index={}
for f in (W/'responses').glob('*.json.gz'):raw_index[sha(f.read_bytes())]=json.loads(gzip.decompress(f.read_bytes()))
checks=Counter();unresolved=[];strict_scores={}
cases={(x['config_id'],x['row_id']):x for x in rd(P/'compact-selected-cases.jsonl')}
for n in normal:
 req=requests[n['trial_id']];assert n['request_sha256']==req['request_sha256']==sha(canon(req['request_payload']))
 raw=raw_index[n['raw_capture_sha256']];assert raw['trial_id']==n['trial_id'];assert raw['request_sha256']==n['request_sha256'];assert raw['request_payload']==req['request_payload'];assert raw['text']==n['output_text'];checks['normalized_raw_hash_identity']+=1
 if n['complete']:
  assert raw['http_status']==200 and raw['response_id'] and raw['returned_model']==req['request_payload']['model'];assert raw['eligible'] is True;assert raw['status']=='stop';assert not raw['stream_incomplete'];u=raw['usage'];assert type(u['prompt_tokens'])==int and type(u['completion_tokens'])==int and 0<=u['completion_tokens']<=req['request_payload']['max_tokens'];checks['strict_complete']+=1
  vals=[(m.start(),m.group(1).upper()) for p in [r'<answer>\s*([A-Za-z])\s*</answer>',r'(?:^|\n)\s*(?:ANSWER|Answer|Final answer|答案)\s*[:：]\s*\(?([A-Za-z])\)?\s*[.。]?\s*$'] for m in re.finditer(p,n['output_text'],re.M)]
  if vals:
   label=max(vals)[1];task=cases[(req['metadata']['config_id'],req['metadata']['row_id'])];sem=task['source']['source_semantics'];strict_scores[n['trial_id']]=int(label==chr(65+sem['gold_index']));checks['explicit_final_independently_read']+=1
  else:unresolved.append(n['trial_id'])
# No resend of old ambiguous starts: old orphan IDs must not have a new intent. Retries only follow explicit429.
intents=rd(W/'intent.jsonl');attempts=rd(W/'attempts.jsonl');seen={};new_ids=set();retrychecks=0
for x in intents:
 key=(x['trial_id'],x['attempt'],x['request_sha256']);assert key not in seen;seen[key]=x
 if key in old_keys:continue
 new_ids.add(x['trial_id'])
 if x['trial_id'] in old_started:assert old_last.get(x['trial_id'],{}).get('http_status')==429
 if x['attempt']>1:
  prev=next((a for a in attempts+old_attempt if a['trial_id']==x['trial_id'] and a['attempt']==x['attempt']-1),None);assert prev and prev['http_status']==429;retrychecks+=1
 assert x['request_sha256']==requests[x['trial_id']]['request_sha256']
 assert '2026-11-15T00:46'<=x['at']<'2026-11-15T10:31:35'
# Recount every production pair, including all planned unknowns; do not import production analyzer.
pairs=json.load(open(W/'analysis/COMPACT_OUTCOMES-PAIR_DETAILS.json'));assert len(pairs)==256
for p in pairs:
 for arm in ['original','repaired']:
  tid=p[arm+'_trial_id'];val=p[arm+'_source_correct'];n=norm.get(tid)
  if n is None or not n['complete']:assert val is None
  elif tid in strict_scores:assert strict_scores[tid]==val
 lo=(p['repaired_source_correct'] if p['repaired_source_correct'] is not None else 0)-(p['original_source_correct'] if p['original_source_correct'] is not None else 1)
 hi=(p['repaired_source_correct'] if p['repaired_source_correct'] is not None else 1)-(p['original_source_correct'] if p['original_source_correct'] is not None else 0)
 assert p['gain_bounds']==[lo,hi]
outcomes=json.load(open(W/'analysis/COMPACT_OUTCOMES.json'));summary=[]
for a in outcomes['paired_analysis']:
 selected=[p for p in pairs if p['config_id']==a['config_id'] and p['model']==a['model'] and(a['tier']=='nested32' or p['tier']=='core16') and(a['stratum']=='all_source_questions' or p['source_has_context']==(a['stratum']=='hint_present'))]
 cc=[p for p in selected if p['original_source_correct'] is not None and p['repaired_source_correct'] is not None];diffs=[p['repaired_source_correct']-p['original_source_correct'] for p in cc]
 assert len(cc)==a.get('complete_pairs',0);assert sum(x>0 for x in diffs)==a.get('repaired_wins',0);assert sum(x<0 for x in diffs)==a.get('original_wins',0)
 lo=sum(p['gain_bounds'][0] for p in selected)/len(selected);hi=sum(p['gain_bounds'][1] for p in selected)/len(selected);assert a['paired_gain_missingness_bounds']==[lo,hi]
 summary.append({k:a.get(k) for k in ['tier','config_id','model','stratum','source_questions','complete_pairs','repaired_wins','original_wins','ties','paired_gain_missingness_bounds','complete_pairs_cluster_bootstrap_95CI']})
refs=json.load(open(W/'analysis/COMPACT_OUTCOMES-REFERENCE_DETAILS.json'));excluded_correct=[];reduxchanges=[]
for x in refs:
 if x['trial_id'] in strict_scores:assert bool(strict_scores[x['trial_id']])==x['source_canonical_correct']
 if x['config_id']=='oneeval-supergpqa' and x['source_canonical_correct'] and not x['original_eligible']:excluded_correct.append(x['trial_id'])
 if x['config_id']=='oneeval-mmlu-redux' and x['original_correct']!=x['reference_only_correct_same_parser']:reduxchanges.append(x['trial_id'])
report={'status':'PASS_SNAPSHOT_IDENTITIES_AND_INDEPENDENT_EXPLICIT_FINAL_PAIR_RECOUNT','wave':W.name,'counts':dict(checks),'normalized_records':len(normal),'normalized_complete':sum(x['complete'] for x in normal),'new_unique_intent_ids_in_this_capture':len(new_ids),'old_seed_intents':sum((x['trial_id'],x['attempt'],x['request_sha256']) in old_keys for x in intents),'explicit429_retry_checks':retrychecks,'unresolved_explicit_final_ids':unresolved,'native_scoring_not_independently_read_where_unresolved':True,'complete_pairs':sum(p['original_source_correct'] is not None and p['repaired_source_correct'] is not None for p in pairs),'core_complete_pairs':sum(p['tier']=='core16' and p['original_source_correct'] is not None and p['repaired_source_correct'] is not None for p in pairs),'supergpqa_explicit_source_correct_native_excluded':excluded_correct,'redux_reference_only_changed':reduxchanges,'paired_summary':summary,'artifact_is_cumulative_not_atomic':'Analysis, raw replies and ledgers may differ by a few in-flight writes. Scientific counts refer to the exact NORMALIZED.jsonl snapshot, not later raw files.','new_calls_by_reviewer':0}
(R/(W.name+'_VERIFICATION.json')).write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['paired_summary','supergpqa_explicit_source_correct_native_excluded','redux_reference_only_changed','unresolved_explicit_final_ids']});print('Unresolved explicit finals',len(unresolved),'SuperGPQA excluded correct',len(excluded_correct),'Redux flag changes',len(reduxchanges))
