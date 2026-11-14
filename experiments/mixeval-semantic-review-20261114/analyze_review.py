import collections,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent
def jl(n):return [json.loads(x) for x in (P/n).read_text().splitlines()]
packet=jl('packet.jsonl');key=jl('key.jsonl');a=jl('reviewer_a.jsonl');b=jl('reviewer_b.jsonl')
def index(rows):
 assert len({x['opaque_id'] for x in rows})==len(rows)
 return {x['opaque_id']:x for x in rows}
pack=index(packet);aa=index(a);bb=index(b)
assert set(pack)==set(aa)==set(bb) and len(key)==80
for reviews in [a,b]:
 for r in reviews:
  text=pack[r['opaque_id']]['response_text']
  for dimension in ['final','content']:
   assert r[dimension+'_label'] in ['correct','incorrect','uncertain']
   if r[dimension+'_label']=='correct':assert r[dimension+'_excerpt'] and r[dimension+'_excerpt'] in text
allrows=[];disagreements=[]
for k in key:
 r=dict(k)
 for dim in ['final','content']:
  if not k['judged']:r[dim+'_label']='unknown';continue
  al=aa[k['opaque_id']][dim+'_label'];bl=bb[k['opaque_id']][dim+'_label']
  r[dim+'_label']=al if al==bl and al!='uncertain' else 'unknown'
  if al!=bl:disagreements.append({'opaque_id':k['opaque_id'],'dimension':dim,'reviewer_a':al,'reviewer_b':bl})
 allrows.append(r)
def bounds(label):return (1,1) if label=='correct' else (0,0) if label=='incorrect' else (0,1)
models={}
for model in sorted({r['model'] for r in allrows}):
 rs=[r for r in allrows if r['model']==model];assert len(rs)==40
 stats={}
 for dim in ['final','content']:
  cs={c:collections.Counter(r[dim+'_label'] for r in rs if r['condition']==c) for c in ['binding_only','official_typed']}
  assert all(sum(n.values())==20 for n in cs.values())
  bysource=collections.defaultdict(dict)
  for r in rs:bysource[r['source_index']][r['condition']]=r
  assert len(bysource)==20
  lo=hi=0
  for pair in bysource.values():
   assert len(pair)==2
   bm,bx=bounds(pair['binding_only'][dim+'_label']);tm,tx=bounds(pair['official_typed'][dim+'_label'])
   lo+=tm-bx;hi+=tx-bm
  stats[dim]={'counts':cs,'paired_gain_bounds_pp':[5*lo,5*hi]}
 stats['original_rule_counts']={c:collections.Counter('unknown' if not r['judged'] else 'correct' if r['common_rule_score']==1 else 'incorrect' for r in rs if r['condition']==c) for c in ['binding_only','official_typed']}
 stats['correct_content_in_incorrect_final']=[r['trial_id'] for r in rs if r['content_label']=='correct' and r['final_label']=='incorrect']
 stats['rule_credit_without_correct_final']=[r['trial_id'] for r in rs if r['judged'] and r['common_rule_score']==1 and r['final_label']=='incorrect']
 stats['correct_final_without_rule_credit']=[r['trial_id'] for r in rs if r['judged'] and r['common_rule_score']==0 and r['final_label']=='correct']
 models[model]=stats
summary={'status':'PASS','stage':'retrospective masked assistant adjudication','protocol_commit':'de205ec97d15cb290815063d4f190279e7410632','reviewed':69,'capture_unknown':11,'fixed_questions_per_model':20,'agreement':{d:sum(aa[k][d+'_label']==bb[k][d+'_label'] for k in pack) for d in ['final','content']},'disagreements':disagreements,'models':models,'new_model_api_calls':0,'new_judge_api_calls':0,'limits':['Two assistant reviewers, not human or official default judge','Previously exposed20case panel; fixedprotocol before individual adjudication does not make retrospective review a prospective trial','Original rule score retained; final-answer/content axes are distinct declared constructs','Bounds are worstcase unknown-answer sensitivity on fixedpanel, notconfidenceintervals']}
(P/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
(P/'CONSENSUS.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in allrows))
(P/'INTEGRITY.json').write_text(json.dumps({'status':'PASS','files':{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['PROTOCOL.json','packet.jsonl','key.jsonl','reviewer_a.jsonl','reviewer_b.jsonl','SUMMARY.json','CONSENSUS.jsonl']},'packet_key_bijection':True,'grounded_correct_excerpts':True,'preserved_primary_unknown':11},indent=2)+'\n')
print(json.dumps(summary,indent=2))
