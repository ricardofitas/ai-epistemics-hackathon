"""Check source hashes and quantitative manuscript claims without rerunning inference."""
import json,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parent
def read(n):return json.loads((P/'evidence'/n).read_text())
for n,m in json.loads((P/'EVIDENCE_SOURCES.json').read_text()).items():
 assert hashlib.sha256((P/'evidence'/n).read_bytes()).hexdigest()==m['sha256']
cal=read('calibration.json');assert (cal['panels'],cal['checked_records'],cal['outcomes'])==(21,64119,{'FAIL':7,'PASS':14})
w=read('wino.json');assert w['counts']['records']==1267
assert w['failures']['question_not_bound']==1267 and w['failures']['reference_changed_answer']==628 and w['failures']['conflicting_gold_for_same_prompt_groups']==300
assert w['input_collisions']['minimum_deterministic_errors']==309
s=read('sciq.json');assert s['failures']['context_not_bound']==884 and s['failures']['reference_changed_answer']==s['failures']['native_reference_invalid']==3
assert read('labbench.json')['failures']['correct_choice_missing']==33
pr=read('prospective.json');assert pr['sampled_rows']==400 and pr['initial_adapter_false_alerts']==2
sp=read('splits.json');assert sp['new_rows']+pr['sampled_rows']==sp['total_rows_in_four_captured_splits']==27746
assert [x['full_split_rows'] for x in sp['benchmarks']]==[1172,500,14042,12032]
assert sum(x['false_literal_alerts_corrected'] for x in sp['benchmarks'])+pr['initial_adapter_false_alerts']==171
assert read('split_checks.json')['status']=='PASS'
cap=read('capture.json');assert cap['checked_trials']==200 and cap['complete']==194 and cap['response_statuses']['incomplete']==6
fa=read('factorization.json');models={'gemma-4-31b-it':([-0.1,0.82],0.42),'qwen3.8-27b':([0.36,0.48],0.40)}
for model,(bounds,delta) in models.items():
 g=next(x for x in fa['strict_source_gains'] if x['model']==model and x['stratum']=='all_frozen_panel')
 assert g['pairs']==50 and g['unknown_sensitivity']==bounds
 r=next(x for x in fa['factorizations'] if x['model']==model and x['stratum']=='all_frozen_panel')
 assert math.isclose(r['reference_effect_on_corrected_outputs'],delta)
orig=read('paired_constant_controls.json')
assert orig['unique_source_questions']==50 and orig['independent_prompt_groups']==35
constant=[r for r in orig['raw_output_reference_replays'] if r['stratum']=='all_frozen_panel' and r['condition']=='corrected_prompt' and r['predictor']=='always_B']
assert len(constant)==2 and all(r['shipped']['score']==1 and r['source_reference']['score']==.5 for r in constant)
res=read('resources.json');assert res['input_tokens']==14547 and res['output_tokens']==97047 and res['total_tokens']==111594
m=read('mutations.json');assert (m['source_units'],m['synthetic_variants'],m['v1_accepted_altered'])==(200,2200,800)
h=read('harness.json');assert (h['source_units'],h['native_condition_rows'],h['native_per_option_request_objects'])==(200,200,801)
assert h['counts']['controlled_stale_metadata_rejected_at_wire']==600
assert read('external.json')['affected_external_run_verified'] is False
ni=read('native_integration.json');assert ni['status']=='completed' and ni['source_units_completed']==200 and ni['native_option_requests']==801 and ni['constructed_fixture_evaluations']==400 and ni['projection_carrier_differences']==0 and ni['errors']==[]
social=read('social_summary.json');sv=read('social_verification.json');protocol=read('social_protocol.json')
assert social['official_split_rows']==1954 and social['selected_source_rows']==100 and social['condition_variants']==600 and social['new_model_calls']==0
assert sv['status']=='PASS' and sv['verified_condition_variants']==600 and sv['distinct_contexts']==100 and sv['predeclared_expectation_mismatches']==[]
conditions={r['condition']:r for r in social['conditions']}
for c in protocol['conditions']:
 r=conditions[c];assert r['rows']==100
 for v in ['v1','v2']:assert r['statuses'][v]=={protocol['expected_'+v][c]:100}
assert sum(r['counting_function_invocations']['v1'] for r in social['conditions'])==400
assert sum(r['counting_function_invocations']['v2'] for r in social['conditions'])==200
assert protocol['frozen_checker_sha256']=='d833080f11b7bb3376056ca3a9720796a1181aa34749e6763a36d5fe1309d70e'
assert protocol['frozen_wrapper_sha256']=='ced1e14f65213bc64f124a82f52f8c3a6d98b6b068026e8a0b486e8ad15228cf'
assert len(read('primary_literature.json')['sources'])==3
pages=json.loads((P/'manuscript.json').read_text());assert len(pages)==7
assert len(json.loads((P/'claims.json').read_text()))==9
result=dict(status='PASS',claims_checked=9,additional_mechanism_checks=8,new_model_requests=0,scope='Synthesis consistency check against source snapshots; not new experimental evidence')
(P/'CLAIM_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))

