import csv,hashlib,json,pathlib,shutil
P=pathlib.Path(__file__).resolve().parent
S=P.parent/'semantic_review'
def load(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
pages=load(P/'manuscript.json')
assert len(pages)==13
for page in pages:
 for block in page['blocks']:
  if 'text' in block:block['text']=block['text'].replace('v1.4','v1.5').replace('Version 1.4','Version 1.5')
# Replace existing interpretation rather than adding enough text to overflow the eight-page main body.
for b in pages[7]['blocks']:
 if b.get('text','').startswith('These are sensitivity bounds over the fixed panel'):
  b['text']='These are fixed-panel sensitivity bounds, not population confidence intervals. The instruction/format intervention, exposed sources, fixed order and heuristic scoring constrain interpretation. Retrospective masked assistant review separates final factual answers from endorsed rationale content (Appendix E): Gemma can retain correct content before a final A tag. This additional construct-specific analysis preserves the original common-rule result above.'
for b in pages[11]['blocks']:
 if b.get('text','').startswith('A separately labelled post-outcome output review'):
  b['text']='The exploratory lexical review finds 14 of 18 completed Qwen binding-only texts contain only the A answer tag. A later masked assistant adjudication under fixed criteria separates final factual answers, endorsed content and common-rule credit (Appendix E). It reuses these outputs, leaves the original rule analysis unchanged and is not human or default-judge validation.'
claims=load(P/'claims.json')
claims.append({'id':'C16','section':'10 and Appendix E','claim':'69maskedresponses;68/69agreement peraxis;17content/finaldiscordances;9Gemmarulecreditswithoutcorrectfinal;Gemmafinal40..75pp/content-35..0pp;Qwenfinal55..80pp/content45..70pp','evidence':'semantic_review_summary.json;semantic_review_verification.json;semantic_review_protocol.json','qualification':'Retrospective two-assistant adjudication of exposed outputs; construct-specific labels,11captureunknowns plus1adjudicationuncertainty; no human/defaultjudge or population claim'})
save(P/'claims.json',claims)
claimpage=pages[12]
claimpage['blocks'][0]['text']=claimpage['blocks'][0]['text'].replace('fifteen','sixteen')
claimpage['blocks'][1]['rows'].append(['C16','Masked review: 69 outputs, 68/69 agreement per axis; 17 correct-content/final-tag discordances.','Retrospective assistant review; separate final/content constructs; Appendix E.'])
for b in claimpage['blocks']:
 if b.get('text','').startswith('Run verify_claims.py'):b['text']=b['text'].replace('fifteen','sixteen')
 if b.get('text','').startswith('Version 1.5 integrates'):b['text']='Version 1.5 adds masked assistant review of existing paired responses. Original scoring and raw captures remain unchanged; final-answer and factual-content results are separate constructs.'
pages.append({'title':'Appendix E. Final answers and factual content','blocks':[
 {'kind':'heading','text':'E.1. Fixed retrospective review criteria'},
 {'kind':'p','text':'Protocol de205ec97d15cb290815063d4f190279e7410632 fixes the rubric before individual adjudication. Two assistant reviewers independently inspect all 69 complete outputs in opaque-ID order with model, condition and original score hidden. They receive the source question/context and accepted aliases. Prior aggregate exposure and possible format leakage remain; this is retrospective assistant annotation, not human annotation or the official default model judge. All 11 incomplete captures remain unknown.'},
 {'kind':'p','text':'The final-answer axis requires an endorsed factual answer; a bare A/None tag does not answer a source free-form task. The content axis separately credits an explicitly endorsed correct fact anywhere in the output. Incidental or negated alias mentions do not qualify. Each axis has correct, incorrect or uncertain labels. Consensus requires agreement; one disagreement about using perique as blending tobacco, without explicitly stating smoking, stays unknown.'},
 {'kind':'table','headers':['Model','Original common-rule gain','Final-answer gain','Factual-content gain'],'rows':[['Gemma','-5 to +25 pp','+40 to +75 pp','-35 to 0 pp'],['Qwen','+50 to +75 pp','+55 to +80 pp','+45 to +70 pp']],'widths':[60,140,140,139]},
 {'kind':'heading','text':'E.2. What the disagreement between constructs shows'},
 {'kind':'p','text':'Reviewers agree on 68/69 labels on each axis. Seventeen completed outputs endorse the source-correct fact but end with an uninformative choice tag: 15 Gemma and two Qwen binding-only outputs. Nine of these Gemma outputs receive common-rule credit from the preceding rationale. Those are differences between whole-text credit and the declared final-answer criterion, not nine demonstrated factual false positives. One Qwen final answer, Prepare for the worst., is semantically correct despite failing the longer accepted alias But prepare for the worst.'},
 {'kind':'p','text':'For Gemma, binding-only has two consensus-correct final answers but 17 correct-content outputs; typed generation has 12 on both axes. Typed Gemma has five unknown labels: four incomplete captures plus the adjudication uncertainty. Qwen has two binding-only final answers and four correct-content outputs; typed generation has 15 on both axes. Original rule outcomes remain unchanged.'},
 {'kind':'heading','text':'E.3. Bounds, verification and the next test'},
 {'kind':'p','text':'All bounds pair the same 20 questions per model, assigning each unknown correctness in [0,1]. They are finite-panel sensitivity bounds, not confidence intervals. Source/request identities, packet/key bijection, grounded excerpts and independent aggregate reconstruction pass. No new model or judge API calls are made. The review does not establish hidden capability loss or population superiority; a prospective instruction-by-carrier ablation on new questions is the next causal test.'}
]})
save(P/'manuscript.json',pages)
with (P/'claim_evidence.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['claim_id','section','numerical_or_status_claim','evidence_files','qualification']);w.writeheader()
 for c in claims:w.writerow(dict(claim_id=c['id'],section=c['section'],numerical_or_status_claim=c['claim'],evidence_files=c['evidence'],qualification=c['qualification']))
evidence=load(P/'EVIDENCE_SOURCES.json')
for src,dest in [('SUMMARY.json','semantic_review_summary.json'),('INDEPENDENT_VERIFICATION.json','semantic_review_verification.json'),('PROTOCOL.json','semantic_review_protocol.json')]:
 shutil.copy2(S/src,P/'evidence'/dest)
 evidence[dest]={'source_archive':'Epistemics_revisao_semantica_equipa_e_ablacao_20261114.zip','member':'semantic_review/'+src,'sha256':hashlib.sha256((P/'evidence'/dest).read_bytes()).hexdigest(),'qualification':'Retrospective masked assistant adjudication, separately labelled from frozen rule scores'}
save(P/'EVIDENCE_SOURCES.json',evidence)
renderer=(P/'render_manuscript.py').read_text().replace('v1.4','v1.5');(P/'render_manuscript.py').write_text(renderer)
verifier=(P/'verify_claims.py').read_text().replace('len(pages) == 13 and len(claims) == 15','len(pages) == 14 and len(claims) == 16').replace("pages[-1]['blocks'][1]['rows']","pages[-2]['blocks'][1]['rows']").replace("claims_checked=15, working_draft_version='1.4'","claims_checked=16, working_draft_version='1.5'")
insert='''semantic=read('semantic_review_summary.json')
assert semantic['status']=='PASS' and semantic['reviewed']==69 and semantic['capture_unknown']==11
assert semantic['agreement']=={'final':68,'content':68}
sm=semantic['models'];sg=sm['gemma-4-31b-it'];sq=sm['qwen3.8-27b']
assert sg['final']['paired_gain_bounds_pp']==[40,75] and sg['content']['paired_gain_bounds_pp']==[-35,0]
assert sq['final']['paired_gain_bounds_pp']==[55,80] and sq['content']['paired_gain_bounds_pp']==[45,70]
assert len(sg['correct_content_in_incorrect_final'])==15 and len(sq['correct_content_in_incorrect_final'])==2
assert len(sg['rule_credit_without_correct_final'])==9 and len(sq['correct_final_without_rule_credit'])==1
assert read('semantic_review_verification.json')['status']=='PASS'
assert read('semantic_review_protocol.json')['version']==1

'''
verifier=verifier.replace("pages = json.loads((P / 'manuscript.json').read_text())",insert+"pages = json.loads((P / 'manuscript.json').read_text())")
(P/'verify_claims.py').write_text(verifier)
readiness=load(P/'READINESS.json');readiness.update(working_draft_version='1.5',pages=14,claims=16)
readiness['not_ready_for_external_submission'][-1]='Small source-exposed fixed-order pilot; retrospective assistant adjudication is not human/default-judge validation; final-answer/content constructs remain separate.'
readiness['next_actions'][0]='Run fixed prospective instruction/carrier ablation on new informative questions; preserve all unknown captures and semantic ambiguities.'
readiness['integrated_updates'].append('Masked assistant adjudication of final answers and endorsed factual content on69existingcompleteoutputs')
readiness['semantic_review']='PASS68/69agreementperaxis;17content/finaldiscordances;newAPIcalls0'
save(P/'READINESS.json',readiness)
save(P/'REVISION_1_5.json',{'revision':'1.5','main_text_pages':8,'structured_pages':14,'claim_count':16,'synthesis_model_calls':0,'adjudicators':'two assistants, masked to model/condition/score','adjudication_outputs':69,'source_capture_unknowns':11,'additional_adjudication_unknowns':1,'original_rule_results_retained':True})
with (P/'REPRODUCTION.txt').open('a') as f:f.write('\nVersion1.5: verify_claims.py also checks maskedreview summary/protocol/independentverification. Full protocol, maskedpacket/key,69-rowreviews and80-rowconsensus are in the separate semantic-review study package. This is retrospective assistant review; no new model or judge API calls.\n')
print({'structured_pages':len(pages),'claims':len(claims)})
