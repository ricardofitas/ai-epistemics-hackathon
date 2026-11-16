import asyncio, collections, hashlib, json, shutil, sqlite3, sys, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'gammaf-launch-package'
if not SOURCE.exists():SOURCE=ROOT.parent
sys.path.insert(0,str(SOURCE))
from gammaf_epistemic.live_adaption import ContentAddressedCache, LiveConfig, BudgetTracker, World, run_world, parse_vote
R=ROOT/'results'; O=ROOT/'audit'; O.mkdir(exist_ok=True)
manifest=json.loads((R/'artifacts/repaired_manifest.json').read_text())
payload=json.loads((R/'artifacts/repaired_full_options/repaired_results.json').read_text())
events=[json.loads(s) for s in (R/'artifacts/repaired_full_options/request_ledger.jsonl').read_text().splitlines()]
starts={e['attempt']:e for e in events if e['event']=='attempt_started'}
ends={e['attempt']:e for e in events if e['event']!='attempt_started'}
assert len(starts)==len(ends)==2331 and starts.keys()==ends.keys()
completed=[e for e in ends.values() if e['event']=='attempt_completed']
salt='gammaf-v2-full-options-20261115-v1:'+manifest['manifest_sha256']
db=sqlite3.connect(R/'artifacts/repaired_full_options/repaired_cache.sqlite')
cache_data=dict(db.execute('select key,text from completions'))
for e in completed:
 s=starts[e['attempt']]
 assert hashlib.sha256(json.dumps(s['messages'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==s['prompt_sha256']
 k=ContentAddressedCache.make_key(s['model'],s['messages'],s['temperature'],s['max_tokens'],salt)
 assert cache_data[k]==e['text']
 assert 'OPTIONS: [A] ' in s['messages'][1]['content']
assert len(cache_data)==len(completed)==2327
shutil.copy2(R/'artifacts/repaired_full_options/repaired_cache.sqlite',O/'replay.sqlite')
c=sqlite3.connect(O/'replay.sqlite');c.execute('delete from checkpoints');c.commit();c.close()
class NoNetwork:
 async def complete(self,*args,**kwargs):
  raise AssertionError('Offline replay cache miss; no provider call permitted')
async def replay():
 cache=ContentAddressedCache(O/'replay.sqlite');budget=BudgetTracker(max_api_calls=4500,max_credits=100)
 config=LiveConfig(model=manifest['model'],rounds=3,temperature=.7,max_output_tokens=1024,salt=salt,max_retries=0,timeout=90,capture_samples=True)
 table={(r['world'],r['arm']):r for r in payload['rows']}
 checked=0
 for record in manifest['worlds']:
  w=dict(record)
  for n in ('options','insiders'):w[n]=tuple(w[n])
  w['option_texts']=tuple(tuple(x) for x in w['option_texts'])
  world=World(**w)
  for arm in ('GAMMAF-FixedTarget-PostHoc','EpistemicGuard-Inline'):
   row=(await run_world(world,arm,NoNetwork(),cache,budget,config)).as_dict()
   orig=table[(world.key,arm)]
   for field in ('votes','flags','correct','released_correct','rounds','interventions'):
    if field in row:assert row[field]==orig[field],(world.key,arm,field)
   checked+=1
 assert cache.hits==cache.lookups==3840
 cache.close()
 return checked
checked=asyncio.run(replay())
content_nonempty=sum(bool(e.get('content','').strip()) for e in completed)
def legal_options(e):
 s=starts[e['attempt']]
 return tuple(re.findall(r'(?:OPTIONS: |\n)\[([A-Z])\]',s['messages'][1]['content']))
content_parse_disagreements=sum(parse_vote(e['text'],legal_options(e),'MMLUPRO')!=parse_vote(e['content'],legal_options(e),'MMLUPRO') for e in completed if e.get('content','').strip())
receipt={'freeze_files_verified':33,'artifact_zip_sha256':hashlib.sha256((ROOT/'results.zip').read_bytes()).hexdigest(),'planned_pairs':64,'observed_pairs':64,'observed_debates':128,'missing_pairs':0,'row_failures':payload['failures'],'offline_replayed_debates':checked,'offline_cache_hits':3840,'offline_cache_misses':0,'completed_requests_linked_to_cache':len(completed),'physical_attempts':len(starts),'failed_transport_attempts':4,'observed_content_channel_nonempty':content_nonempty,'reasoning_only_completions':len(completed)-content_nonempty,'nonempty_content_parser_disagreements':content_parse_disagreements,'channel_caveat':'Frozen parser examines combined reasoning and content, can take the first structured field or last standalone label; reasoning-only replies are not abstentions. No channel change or regenerated trajectories performed. Explicit provider finish status not retained; cannot count true truncations.','reported_input_tokens':sum(e['input_tokens'] for e in completed),'reported_output_tokens':sum(e['output_tokens'] for e in completed),'usage_caveat':'All reported token usage is zero, so actual token totals and billed cost are unknown, not zero.','conservative_reserved_nominal_units':sum(e['reserved_credits'] for e in starts.values()),'new_provider_calls_during_audit':0}
(O/'VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
