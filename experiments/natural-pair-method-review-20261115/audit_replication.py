from pathlib import Path
import json,hashlib,re,collections,itertools
R=Path(__file__).parent;P=R/'originality/content';spec=json.load(open(P/'replicacao_64_pares.json'));meta=json.load(open(P/'resultados.json'));sha=lambda x:hashlib.sha256(x).hexdigest();canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
w=R/'payload/wino_track';cases=json.load(open(w/'cases.json'));manifest=[json.loads(x) for x in (w/'manifest.jsonl').read_bytes().splitlines()];oldint=[json.loads(x) for x in (R/'old_intents.jsonl').read_bytes().splitlines()]
assert sha((w/'cases.json').read_bytes())==meta['sources_sha256']['wino_track/cases.json'];assert sha((w/'manifest.jsonl').read_bytes())==meta['sources_sha256']['wino_track/manifest.jsonl'];assert sha((R/'old_intents.jsonl').read_bytes())==meta['sources_sha256']['compact_execution/14138164416/execution_track/capture/intent.jsonl']
mi={m['trial_id']:m for m in manifest};idx={(c['source_row_index'],c['prompt_arm']):c for c in cases};q={(m['source_row_index'],m['request_payload']['model'],m['prompt_arm']):m for m in manifest};oldindices={mi[r['trial_id']]['source_row_index'] for r in oldint}|{c['source_row_index'] for c in cases if c['prior_model_panel']};assert len(oldindices)==117
seen=set();edits=collections.Counter();details=[];distinct_request_hashes=set()
for pair in spec['selected']:
 a,b=pair['members'];assert a['index'] not in seen and b['index'] not in seen;seen.update([a['index'],b['index']]);assert not {a['index'],b['index']}&oldindices;assert abs(a['index']-b['index'])==1;assert {a['gold'],b['gold']}=={'A','B'}
 cs=[idx[x['index'],'native_gallery'] for x in [a,b]];assert cs[0]['source_row']['option1']==cs[1]['source_row']['option1'];assert cs[0]['source_row']['option2']==cs[1]['source_row']['option2'];assert cs[0]['prompt']==cs[1]['prompt']
 s1,s2=[c['source_row']['sentence'] for c in cs];t1=re.findall(r'\w+|[^\w\s]',s1);t2=re.findall(r'\w+|[^\w\s]',s2)
 # Full token Levenshtein; review only, no panel replacement/subselection.
 prev=list(range(len(t2)+1))
 for i,x in enumerate(t1,1):
  row=[i]
  for j,y in enumerate(t2,1):row.append(min(prev[j]+1,row[j-1]+1,prev[j-1]+(x!=y)))
  prev=row
 dist=prev[-1];edits[dist]+=1
 for member in [a,b]:
  c=idx[member['index'],'native_gallery'];assert c['source_row_sha256']==member['source_sha256'];assert sha(canonical(c['source_row']))==member['source_sha256'];assert chr(64+int(c['source_row']['answer']))==member['gold']
  for model in spec['models']:
   actual=[q[member['index'],model,arm] for arm in spec['prompt_arms']];assert [x['request_sha256'] for x in actual]==member['requests_by_model'][model]
   for r in actual:assert sha(canonical(r['request_payload']))==r['request_sha256'];distinct_request_hashes.add(r['request_sha256'])
 details.append({'selection_sha256':pair['selection_sha256'],'indices':[a['index'],b['index']],'gold':[a['gold'],b['gold']],'token_edit_distance':dist,'original_prompt_hash':cs[0]['prompt_sha256']})
assert len(seen)==128;assert len(spec['selected'])==64
# Pointwise source/native group scores on two opposite-gold items are disjoint indicators.
def score(preds,gold):return int(preds==gold),int(preds==('B','B'))
support=collections.Counter()
for original in itertools.product(['A','B',None],repeat=2):
 for repaired in itertools.product(['A','B',None],repeat=2):
  s0,n0=score(original,('A','B'));s1,n1=score(repaired,('A','B'));assert s0+n0<=1 and s1+n1<=1;support[(s1-s0)-(n1-n0)]+=1
assert set(support)=={-2,-1,0,1,2};assert sum(support.values())==81
out={'status':'PASS_SOURCE_SELECTION_AND_REQUEST_IDENTITY_REVIEW_NO_INFERENCE','selected_pairs':64,'source_questions':128,'planned_trial_cells':1024,'unique_payload_hashes':len(distinct_request_hashes),'previous_model_intent_or_prior_panel_indices_excluded':117,'selected_previous_intent_overlap':0,'pair_token_edit_distances':dict(edits),'all_original_pairs_identical_visible_requests':True,'all_gold_pairs_opposite':True,'models':spec['models'],'new_model_calls':0,'enumerated_four_output_states':81,'primary_contrast_support_counts':{str(k):v for k,v in sorted(support.items())},'readiness':'Panel and estimand reviewed, not a launched or executed provider trial. New catalog/budget/transport and analyzer freeze still required before dispatch.','limits':['Same One-Eval revision and known mechanism, source pairs selected using question fields and previous intent coverage. Not new semantic source pool or independent framework replication.','Token minimality reviewed after selection; no replacements made.','Identical payloads on two different source items must receive distinct trial IDs and genuinely separate provider requests. Hash-only response caching would change the stated experiment.','Group consistency metric and conditional probability bounds are known methods, not original theoretical contributions.'],'pair_details':details}
(R/'DESIGN_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='pair_details'})
