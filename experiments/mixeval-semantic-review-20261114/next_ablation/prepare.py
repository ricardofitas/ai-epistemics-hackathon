"""Offline source selection and factorial request compilation. Does not call any API."""
import collections, gzip, hashlib, json, pathlib, unicodedata
ROOT=pathlib.Path(__file__).resolve().parent
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
def normalized(x):return ' '.join(unicodedata.normalize('NFKC',str(x)).casefold().split())
def semantic_hash(r):return sha(canonical([normalized(r['prompt']),normalized(r['context'])]))
def write(n,x): (ROOT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def compile_all():
 protocol=json.loads((ROOT/'PROTOCOL.json').read_text())
 pool_bytes=(ROOT/'SOURCE_POOL.jsonl.gz').read_bytes()
 assert sha(pool_bytes)=='c00abfba2d087d451bec17ef6b2367cb0582831aa1f128e61288f597841cd568'
 pool=[json.loads(l) for l in gzip.decompress(pool_bytes).decode().splitlines()]
 exclusions=json.loads((ROOT/'PRIOR20_EXCLUSIONS.json').read_text())
 old_hashes=set(exclusions['source_hashes']);old_sem=set(exclusions['normalized_question_context_hashes'])
 eligible=[];seen=set();removed=collections.Counter()
 for row in sorted((r for r in pool if r['split']=='free_form'),key=lambda r:r['source_sha256']):
  assert sha(canonical(row['record']))==row['source_sha256']
  sm=semantic_hash(row['record'])
  if row['source_sha256'] in old_hashes or sm in old_sem:removed['prior_generation_overlap']+=1;continue
  if sm in seen:removed['duplicate_normalized_text']+=1;continue
  seen.add(sm);eligible.append(row)
 assert len(eligible)>=20
 selected=eligible[:20];models=protocol['models'];conds=protocol['conditions'];manifest=[]
 for j,source in enumerate(selected):
  r=source['record'];orders={m:[conds[(pos+j+2*mi)%4] for pos in range(4)] for mi,m in enumerate(models)}
  for pos in range(4):
   for mi in [j%2,1-j%2]:
    model=models[mi];cond=orders[model][pos];instruction,carrier=cond.split('__')
    inst=protocol['template'][instruction+'_instruction']
    chunks=[protocol['template']['shared_prefix'],inst,'Question:\n'+r['prompt'],'Context:\n'+r['context']]
    if carrier=='A.None':chunks.append(protocol['template']['carrier_present'])
    chunks.append(protocol['template']['shared_suffix']);prompt='\n\n'.join(chunks)
    assert len(prompt.encode())<=protocol['maximum_prompt_utf8_bytes_per_request']
    payload={'model':model,'input':prompt,'temperature':0,'max_output_tokens':4096}
    manifest.append({'trial_id':f'MXA-{j:02}-{conds.index(cond)}-{mi}','source_rank':j,'source_index':source['source_index'],'source_sha256':source['source_sha256'],'normalized_question_context_sha256':semantic_hash(r),'condition':cond,'instruction':instruction,'options_carrier':carrier,'condition_position':pos,'model_position':int(mi!=j%2),'prompt_sha256':sha(prompt.encode()),'request_sha256':sha(canonical(payload)),'request_payload':payload})
 assert len(manifest)==160 and len({r['trial_id'] for r in manifest})==160
 expected={(s['source_sha256'],m,c) for s in selected for m in models for c in conds}
 assert {(r['source_sha256'],r['request_payload']['model'],r['condition']) for r in manifest}==expected
 counter=collections.Counter((r['request_payload']['model'],r['condition'],r['condition_position']) for r in manifest)
 assert set(counter.values())=={5}
 assert not (old_hashes & {r['source_sha256'] for r in selected})
 assert not (old_sem & {semantic_hash(r['record']) for r in selected})
 for source in selected:
  rs=[r for r in manifest if r['source_sha256']==source['source_sha256'] and r['request_payload']['model']==models[0]]
  prompts={r['condition']:r['request_payload']['input'] for r in rs}
  for carrier in ['absent','A.None']:
   ff=prompts['free_form__'+carrier];ch=prompts['choice__'+carrier]
   assert ff.replace(protocol['template']['free_form_instruction'],'<INSTRUCTION>')==ch.replace(protocol['template']['choice_instruction'],'<INSTRUCTION>')
  for instruction in ['free_form','choice']:
   present=prompts[instruction+'__A.None'];absent=prompts[instruction+'__absent']
   assert present.replace('\n\n'+protocol['template']['carrier_present'],'')==absent
 write('selected20.json',selected)
 (ROOT/'manifest.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in manifest))
 receipt={'status':'OFFLINE_PASS_PREPARED_ONLY','pool_records':len(pool),'freeform_pool_records':sum(r['split']=='free_form' for r in pool),'eligible_after_exclusion':len(eligible),'removed':dict(removed),'selected':20,'prior_generation_exact_and_normalized_overlap':0,'models':models,'conditions':conds,'planned_calls':160,'maximum_total_output_tokens':655360,'actual_model_calls':0,'source_composition':dict(collections.Counter(s['record']['benchmark_name'] for s in selected)),'counterbalance_each_model_condition_position':5,'factor_only_byte_differences_pass':True,'max_prompt_bytes':max(len(r['request_payload']['input'].encode()) for r in manifest),'protocol_sha256':sha((ROOT/'PROTOCOL.json').read_bytes()),'source_pool_sha256':sha(pool_bytes),'selected_sha256':sha((ROOT/'selected20.json').read_bytes()),'manifest_sha256':sha((ROOT/'manifest.jsonl').read_bytes()),'exclusion_sha256':sha((ROOT/'PRIOR20_EXCLUSIONS.json').read_bytes())}
 write('PREPARATION.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':compile_all()
