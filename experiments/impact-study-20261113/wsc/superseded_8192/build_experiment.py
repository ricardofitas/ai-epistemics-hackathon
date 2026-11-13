#!/usr/bin/env python3
"""Build a NEW output-blind Q48 scoring-consequence experiment after semantic review."""
import argparse,collections,datetime as dt,difflib,hashlib,json,math,random,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODELS=['gemma-4-31b-it','glm-5.2','qwen3.8-27b','deepseek-v4-flash']
SEEDS={'source_cap':2026111316,'family_split':2026111317,'opaque_task_ids':2026111318,'within_roles':2026111319,'request_order':2026111322,'bootstrap':2026111323}
INSTRUCTION=('Classify each ordered premise/hypothesis pair using ordinary English interpretation and commonsense. '
'Use entailment when the hypothesis must be true under the ordinary intended reading of the premise; '
'contradiction when it must be false under that reading; neutral when neither follows. '
'Do not assume unmentioned events or restrictions. Treat each pair independently. '
'Return exactly one JSON object with a predictions array and one entry per supplied id, '
'each containing only id and label. Valid labels are entailment, contradiction, neutral. '
'Do not include explanations, probabilities or additional text.')

def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value,jsonl=False):
 text=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in value) if jsonl else json.dumps(value,indent=2,ensure_ascii=False)+'\n'
 if path.exists() and path.read_text()!=text:raise ValueError('Refusing changed existing prospective artifact '+str(path))
 path.write_text(text)
def group_sources(pool):
 ids=sorted(pool);parent={x:x for x in ids}
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def join(a,b):
  a,b=find(a),find(b)
  if a!=b:parent[max(a,b)]=min(a,b)
 normalize=lambda t:re.sub(r'\s+',' ',t.casefold()).strip()
 texts={k:normalize(pool[k]['source_text']) for k in ids}
 edges=[]
 for i,a in enumerate(ids):
  for b in ids[i+1:]:
   ratio=max(difflib.SequenceMatcher(None,texts[a],texts[b],autojunk=False).ratio(),difflib.SequenceMatcher(None,texts[b],texts[a],autojunk=False).ratio())
   if ratio>=.80:join(a,b);edges.append({'a':a,'b':b,'max_symmetric_sequence_ratio':ratio})
 groups=collections.defaultdict(list)
 for k in ids:groups[find(k)].append(k)
 mapping={k:f'F{n:03d}' for n,(_,vals) in enumerate(sorted(groups.items()),1) for k in vals}
 return mapping,edges

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--eligibility',type=Path,required=True,help='Separate final semantic eligibility JSON with rows containing review_id and eligible boolean')
 args=ap.parse_args()
 if (ROOT/'api_artifacts').exists() or (ROOT/'stream_journals').exists():raise ValueError('Never rebuild after candidate inference started')
 pool={r['review_id']:r for r in map(json.loads,(ROOT/'semantic_review_packet.jsonl').read_text().splitlines())}
 final=json.loads(args.eligibility.read_text()); judgments=final['rows']; decisions={r['review_id']:r for r in judgments}
 approval=json.loads((ROOT/'ROOT_SEMANTIC_APPROVAL.json').read_text());freeze=json.loads((ROOT/'semantic_ab_freeze.json').read_text())
 assert approval['status']=='approved_for_prospective_execution_after_separate_git_freeze'
 assert approval['input_semantic_final_sha256']==sha(args.eligibility)
 assert approval['first_a_sha256']==sha(ROOT/'semantic_first_a.jsonl')
 assert approval['first_b_sha256']==sha(ROOT/'semantic_first_b.jsonl')
 assert freeze['semantic_packet_sha256']==sha(ROOT/'semantic_review_packet.jsonl')
 assert freeze['first_sha256']=={'a':sha(ROOT/'semantic_first_a.jsonl'),'b':sha(ROOT/'semantic_first_b.jsonl')}
 assert final['semantic_first_freeze_sha256']==sha(ROOT/'semantic_ab_freeze.json')
 assert set(decisions)==set(pool) and len(judgments)==len(pool)==81
 for r in decisions.values():
  assert type(r['eligible']) is bool
  if r['eligible']:
   assert r['positive_entailment']=='yes' and r['negative_not_entailed']=='yes'
   assert r.get('negative_three_way') in ['neutral','contradiction','uncertain']
 families,edges=group_sources(pool)
 discovery_families={families[k] for k in ['W001','W074']}
 prior_excluded=sorted(k for k in pool if families[k] in discovery_families)
 eligible=sorted(k for k in pool if decisions[k]['eligible'] and k not in prior_excluded)
 rng=random.Random(SEEDS['source_cap']);rng.shuffle(eligible)
 selected=sorted(eligible[:80]);assert len(selected)>=40,'Too few validated passages for this pilot; redesign/freeze separately'
 family_members=collections.defaultdict(list)
 for k in selected:family_members[families[k]].append(k)
 if len(family_members)<10:raise ValueError('Too few independent source families')
 shuffled=sorted(family_members);rng=random.Random(SEEDS['family_split']);rng.shuffle(shuffled)
 roles={};sizes={'selection':0,'confirmation':0}
 for f in shuffled:
  minsize=min(sizes.values());candidates=[r for r in sizes if sizes[r]==minsize]
  role=rng.choice(candidates);roles[f]=role;sizes[role]+=len(family_members[f])
 data=[]
 for i,k in enumerate(selected,1):
  r=pool[k];d=decisions[k];f=families[k]
  data.append({'passage_id':f'P{i:03d}','source_review_id':k,'family_id':f,'analysis_role':roles[f],'premise':r['source_text'],'gold_replacement_hypothesis':r['hypothesis_gold_replacement'],'non_gold_replacement_hypothesis':r['hypothesis_non_gold_replacement'],'source_positive_record':r['source_gold_record'],'source_negative_record':r['source_non_gold_record'],'analyst_positive_entailment':'yes','analyst_negative_not_entailed':'yes','analyst_negative_three_way':d['negative_three_way'],'semantic_rationale':d.get('rationale','See final semantic review.'),'official_nli_gold':False})
 tasks=[]
 for r in data:
  for variant in ['gold','non_gold']:
   tasks.append({'passage_id':r['passage_id'],'family_id':r['family_id'],'analysis_role':r['analysis_role'],'source_review_id':r['source_review_id'],'variant':variant,'premise':r['premise'],'hypothesis':r[variant+'_replacement_hypothesis'],'binary_target':'entailment' if variant=='gold' else 'non_entailment','literal_advice_target':'entailment' if variant=='gold' else 'contradiction','analyst_three_way_target':'entailment' if variant=='gold' else r['analyst_negative_three_way']})
 random.Random(SEEDS['opaque_task_ids']).shuffle(tasks)
 for i,t in enumerate(tasks,1):t['task_id']=f'X{i:03d}'
 bypassage=collections.defaultdict(list)
 for t in tasks:bypassage[t['passage_id']].append(t)
 batches=[];rng=random.Random(SEEDS['within_roles'])
 for role in ['selection','confirmation']:
  passages=[r['passage_id'] for r in data if r['analysis_role']==role];rng.shuffle(passages)
  for start in range(0,len(passages),4):
   group=passages[start:start+4];batch=[]
   for pid in group:
    pair=bypassage[pid].copy();rng.shuffle(pair);batch.extend(pair)
   rng.shuffle(batch)
   batches.append({'batch_index':len(batches)+1,'batch_role':role,'passage_ids':group,'tasks':batch})
 manifest=[]
 for model in MODELS:
  for batch in batches:
   modelinput=[{'id':t['task_id'],'premise':t['premise'],'hypothesis':t['hypothesis']} for t in batch['tasks']]
   payload={'model':model,'instructions':INSTRUCTION,'input':json.dumps(modelinput,ensure_ascii=False),'max_output_tokens':8192,'temperature':0.0,'stream':True,'tools':[],'tool_choice':'none','agentic_memory':False,'store':False}
   manifest.append({'trial_id':f'IW-{len(manifest)+1:03d}','requested_model':model,'batch_index':batch['batch_index'],'batch_role':batch['batch_role'],'passage_ids':batch['passage_ids'],'task_ids':[t['task_id'] for t in batch['tasks']],'request_payload':payload,'request_sha256':hashlib.sha256(canonical(payload)).hexdigest()})
 random.Random(SEEDS['request_order']).shuffle(manifest)
 for i,r in enumerate(manifest,1):r['execution_order']=i
 write(ROOT/'selected_data.json',{'source_passages':len(data),'source_families':len(family_members),'items':data})
 write(ROOT/'task_key.json',{'rows':[{k:v for k,v in t.items() if k not in ['premise','hypothesis']} for t in tasks]})
 write(ROOT/'manifest.jsonl',manifest,True)
 write(ROOT/'source_split.json',{'clustering':{'normalization':'casefold and collapse whitespace only','similarity':'max of SequenceMatcher(a,b,autojunk=False).ratio and reverse >=0.80; connected components on all81 mechanical cases','family_mapping':families,'edges':edges},'prior_discovery_family_exclusions':prior_excluded,'source_only_eligible_before_cap':len(eligible),'selected_review_ids':selected,'family_roles':roles,'role_passage_counts':sizes,'all_semantic_decisions':judgments})
 protocol={'id':'q48-wsc-scoring-consequence-v1','stage':'NEW_exploratory_consequence_test_no_candidate_outputs_seen','activation':'Root source/semantic review and separate Git payload/protocol freeze required. Not governed by or an activation of the old failed PAWS protocol.','observation_link':'Q48/PR-11 in prior60-call advice wave; original candidate answer recommended E for gold WSC replacement and C for every non-gold replacement.','models':MODELS,'model_selection':'Four prior declared hosted aliases, fixed before all candidate performance; immutable weights unavailable. No candidates added or removed based on observed scores.','source':json.loads((ROOT/'source/receipt.json').read_text()),'source_scope':'Official WSC source-train public data, curated subject-pronoun/titlecase-name slice; not held out from pretraining, not representative WSC. Analyst NLI labels are separate from source coreference annotations.','source_passages':len(data),'source_families':len(family_members),'split':{'method':'Random source-family ordering then greedy passage-count balancing; whole connected family assigned one role, ties randomized with fixed seed.','passages':sizes,'independence_limit':'Distinct source-family clusters operationally reduce variant overlap; threshold clustering cannot prove semantic independence.'},'seeds':SEEDS,'request_plan':{'requests':len(manifest),'ordered_classifications_per_model':len(tasks),'ordered_classifications_total':len(tasks)*len(MODELS),'max_passages_per_batch':4,'max_ordered_pairs_per_batch':8,'role_separated_contexts':True,'model_blinding':'Only opaque IDs, original premise and one replacement hypothesis plus common label definitions. No coreference labels, source/benchmark/role/variant/family IDs, evidence or judge facts transmitted.','controls':{'temperature':0.0,'max_output_tokens':8192,'stream':True,'tools':[],'tool_choice':'none','agentic_memory':False,'store':False,'history':'none','client_retries':0,'concurrency':2,'socket_timeout_seconds':120},'max_requested_output_tokens':8192*len(manifest),'cost_limit':'No account/USD/billing equivalence claim. Preserve provider usage and missing charges. Root assesses live pricing before freeze.'},'semantic_convention':'Original unresolved passage transmitted. Official coreference gold supplies intended interpretation for source-only semantic review. Positive entailment and negative nonentailment separately validated, not inherited blindly. No official NLI gold claimed.','scoring':{'primary_unit':'Passage pair: both gold and non-gold hypotheses classified correctly under the stated rule. Original answer called this role-swap accuracy, but these are paired WSC recasts, not literal swapped-argument minimal pairs.','literal_bad_pair':'1 iff gold prediction=entailment AND non-gold prediction=contradiction; otherwise0.','repaired_binary_pair':'1 iff gold prediction=entailment AND non-gold prediction in{neutral,contradiction}; otherwise0.','primary_score_distortion':'Within candidate/cohort, repaired_binary_pair accuracy minus literal_bad_pair accuracy on the SAME predictions. The nonnegative arithmetic relation is expected by construction, not itself a novel causal discovery.','secondary_items':'Individual classification accuracy under the same two rules; E/C macroF1 under literal labels with neutral treated as a wrong prediction; repaired E/nonE macroF1.','secondary_three_way':'Only independently confident analyst negatives labeledN/C; positivesE. Report coverage and complete subset before scoring. Never exclude items after seeing candidate outputs or call this official NLI gold.'},'ranking_and_selection':{'fixed_comparisons':'All6pairwise candidate comparisons, for both primary pair metric and secondary item metric, selection/confirmation/full descriptive cohorts. Full cohort ranking is descriptive, not independent decision consequence.','primary_candidate_choice':'Prospective raw-score selection abstraction: unique maximum primary paired score on selection cohort under each scoring rule. Winner sets for ties remain set-valued; do not choose an arbitrary tied candidate. This does not execute the complete Q48 significance-gated or alternative-macroF1 choice policy, so a changed raw winner is not proof that literal full advice would select it.','primary_consequence':'If both winner sets are unique, report repaired-selected minus literal-selected repaired_binary_pair accuracy on disjoint confirmation cohort. It may be positive, zero or negative; same selected model yields zero. No stopping/resampling to get reversal.','ranking_reversal':'Only strict opposite signs of the two non-tied candidate score differences, same fixed cohort. Null or tie is not a reversal.','claim_limit':'Scoring-rule comparison and declared raw-score selection abstraction conditional on fixed predictions/candidates and this validated source slice. No claim Q48 statistical gate was met or its full advice adopted. Repaired binary WSC recast measures directional entailment on this coreference-derived slice, not the full original argument-role target. Any external HANS target is a separately frozen supplement, not merged silently into this endpoint. Not real-user adoption, causal downstream harm, intrinsic WSC defect or general model ranking.'},'missing_data':{'full_candidate_primary':'Requires valid complete predictions for ALL planned inputs for ALL four fixed candidates. If any missing/invalid capture, mark primary complete-candidate analysis incomplete. No dropping candidates, replacing responses, retries, or imputing semantic error.','coupled_distortion_bounds':'Primary pair repaired-minus-bad equals indicator(gold prediction=E AND non-gold prediction=N). It is fixed0 if observed gold is notE or observed non-gold is notN, fixed1 if both observed requirements hold, otherwise[0,1]. Individual-score distortion equals negativeN indicators divided by all ordered inputs. Do not subtract independently extremized score bounds as if predictions varied separately.','additional_bounds':'For each fixed cohort and score, missing/invalid predictions give conservative [0,1] contribution bounds at task or passage unit; if one pair member is known wrong the paired correctness upper bound is0, otherwise missing pair component yields[0,1]. Report score bounds for all four candidates. Declare robust ordering only if lower_A>upper_B or vice versa; overlap/ties remain indeterminate. Use bounded selection/winner sets rather than silently complete-case filtering.','transport':'A scorable capture requiresHTTP200, text/event-stream, terminal response.completed AND provider statuscompleted, nonempty finalassistanttext, no transport error/delta fallback/format deviation/malformed SSE JSON. Preserve event/status mismatches as operational incomplete.','parser':'Parse whole final assistant JSONobject, optionally one outer fencedJSONblock; all and only expected taskIDs once; labels casefolded entailment/contradiction/neutral. No fixing model outputs with a second call.'},'uncertainty':{'draws':10000,'seed':SEEDS['bootstrap'],'unit':'Resample source-family clusters jointly across candidates within each cohort; carry all passages and both replacements in each chosen cluster.','interval':'Two-sided95percentile, NumPy linear quantiles. Tiny/source-curated sample and cluster count limit interpretation; no population prevalence or significance claim.','implementation':'NumPy default_rng(seed+offset), offsets selection=0/confirmation=1/all=2; multinomial counts forF source-family draws, passage-weighted means carrying all variants, item denominator2timespassages.','selection':'Fix observed unique winners when bootstrapping confirmation effect; no bootstrap reselection. Report conditional selection uncertainty limitation.','dependence_limits':'Family clustering is an operational approximation, not proof of independent schemas. Multiple families can share one request context; this bootstrap does not separately estimate cross-family batch or provider-level dependence. Intervals are descriptive conditional resampling, not calibrated population guarantees.'},'stopping':'Attempt every frozen manifest row exactly once. Keep nulls, ties, invalid output and incomplete captures; no result-dependent new candidates, item changes or stopping.','human_review':'pending; independent first agent semantic ratings are not external expert validation','hashes':{n:sha(ROOT/n) for n in ['semantic_review_packet.jsonl','selection_intent.json','selected_data.json','task_key.json','manifest.jsonl','source_split.json','prepare_review_pool.py','build_experiment.py','ROOT_SEMANTIC_APPROVAL.json','semantic_ab_freeze.json','semantic_first_a.jsonl','semantic_first_b.jsonl','semantic_first_b_receipt.json','mechanical_pool_manifest.json','design.md','verify_preflight.py','test_analyze_wsc.py','SEMANTIC_DESIGN_REVIEW.json','DESIGN_CODE_PREREVIEW.json','ANALYZER_VERIFICATION.json']},'final_semantic_eligibility_filename':args.eligibility.name,'final_semantic_eligibility_sha256':sha(args.eligibility),'analysis_sha256':sha(ROOT/'analyze_wsc.py'),'capture_audit_source_sha256':sha(ROOT.parent/'methods/capture_audit_source.py'),'runner_sha256':sha(ROOT.parent/'methods/run_adaption_stream_pilot.py')}
 write(ROOT/'protocol.json',protocol)
 print(json.dumps({'passages':len(data),'families':len(family_members),'split':sizes,'requests':len(manifest),'classifications':len(tasks)*len(MODELS),'manifest_sha256':sha(ROOT/'manifest.jsonl')}))
if __name__=='__main__':main()
