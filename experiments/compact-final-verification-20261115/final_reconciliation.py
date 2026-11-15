import pathlib,json,hashlib,gzip
from collections import Counter
R=pathlib.Path(__file__).parent;W=R/'final_capture/compact_execution/capture'
rd=lambda p:[json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
old=[]
for aid in ['14138164416','14138939635']:old+=rd(R/aid/'execution_track/capture/intent.jsonl')
oldkeys={(x['trial_id'],x['attempt'],x['request_sha256']) for x in old};attempts=rd(W/'attempts.jsonl');new=[a for a in attempts if (a['trial_id'],a['attempt'],a['request_sha256']) not in oldkeys];seed=[a for a in attempts if a not in new];normal=rd(W/'analysis/NORMALIZED.jsonl');n={r['trial_id']:r for r in normal};lookup={a['trial_id']:a for a in seed};reused=[r for r in normal if r['complete'] and r['trial_id'] in lookup and lookup[r['trial_id']].get('eligible')]
assert len(new)==574;assert len(seed)==68;assert len(reused)==65;assert Counter(x['http_status'] for x in new)=={200:518,504:52,429:4}
summary={'new_POST_attempts_excluding_seed':len(new),'seed_attempts_preserved':len(seed),'new_POST_http_statuses':dict(Counter(x['http_status'] for x in new)),'completed_reused':len(reused),'completed_new':518,'complete_total':583,'unknown_total':53,'new_504_unknown':52,'old_504_unknown_preserved':1,'last_terminal_429_unresolved':0,'new_unique_request_IDs':len({x['trial_id'] for x in new}),'all_intent_ids':len({x['trial_id'] for x in rd(W/'intent.jsonl')}),'final_executor_spent_or_committed_credits':json.load(open(W/'FINAL.json'))['spent_or_committed_credits'],'cost_scope':'Executor reservation/usage accounting includes seeded prior replies and unknown reservations; not independently confirmed provider billing or a confirmed currency amount.'}
(R/'FINAL_RESOURCE_RECONCILIATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
# Secondary balanced common-complete descriptive panel; keep primary all-planned missingness bounds.
pairs=json.load(open(W/'analysis/COMPACT_OUTCOMES-PAIR_DETAILS.json'));o=[]
for tier in ['core16','nested32']:
 for task in ['evalscope-siqa','oneeval-scienceqa']:
  for hint in ([True,False] if task=='oneeval-scienceqa' else [True]):
   xs=[x for x in pairs if x['config_id']==task and (tier=='nested32' or x['tier']=='core16') and x['source_has_context']==hint];good={x['row_id'] for x in xs if all(y['original_source_correct'] is not None and y['repaired_source_correct'] is not None for y in xs if y['row_id']==x['row_id'])}
   for model in sorted({x['model'] for x in xs}):
    z=[x for x in xs if x['row_id'] in good and x['model']==model];o.append({'tier':tier,'task':task,'hint':hint,'model':model,'complete_common_questions':len(good),'original_correct':sum(x['original_source_correct'] for x in z),'repaired_correct':sum(x['repaired_source_correct'] for x in z)})
(R/'COMMON_COMPLETE_FINAL.json').write_text(json.dumps({'scope':'Secondary availability-conditioned complete-case panel; unchanged primary planned-panel unknown bounds.','results':o},indent=2)+'\n')
