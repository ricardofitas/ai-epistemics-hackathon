"""Check source hashes and quantitative manuscript claims without rerunning inference."""
import json,hashlib,math,csv
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
gate = read('native_gate.json')
gate_verification = read('native_gate_verification.json')
assert gate['source_units'] == 200 and gate['condition_records'] == 1600
assert gate['statuses'] == {'PASS': 400, 'FAIL': 1000, 'INCOMPLETE': 200}
assert gate['counting_sink_invocations'] == 400 and gate['provider_model_calls'] == 0
assert gate_verification['accepted_request_snapshots_identical_at_sink'] == 400
assert gate_verification['failed_or_incomplete_sink_calls'] == 0
root = read('causal_root.json')
root_verification = read('causal_verification.json')
assert root['source_rows_reused'] == 633 and root['condition_records'] == 3798
assert root['provider_model_requests'] == 0 and root['errors'] == []
panels = root['panels']
assert panels['winogrande']['native']['question_bound'] == 0
assert panels['winogrande']['bind_source_symbols']['question_bound'] == 100
assert panels['sciq']['native']['declared_nonempty_context'] == 90
assert panels['sciq']['native']['declared_context_bound'] == 0
assert panels['sciq']['bind_source_symbols']['declared_context_bound'] == 90
for benchmark in ('arc-challenge', 'openbookqa'):
    assert panels[benchmark]['native']['choices_preserved'] == 0
    assert panels[benchmark]['decode_parallel_choices']['choices_preserved'] == 100
assert panels['openbookqa']['decode_parallel_choices']['question_bound'] == 0
assert panels['openbookqa']['both_shared_repairs']['question_bound'] == 100
lab = panels['lab-bench-language-agent-biology-benchmark']
assert lab['both_shared_repairs']['gold_present'] == 0
assert lab['lab_complete_options']['gold_present'] == 33
for benchmark in ('medmcqa', 'mmlu'):
    for condition in panels[benchmark].values():
        assert condition['question_bound'] == condition['choices_preserved'] == 100
assert root_verification['status'] == 'PASS'
transfer = read('mmmlu_transfer.json')
assert transfer['source_rows'] == 14042 and transfer['selected_rows'] == 100
assert transfer['panels']['native']['question_bound'] == 0
assert transfer['panels']['bind_source_symbols']['question_bound'] == 100
assert all(panel['choices_preserved'] == panel['gold_present'] == 100 for panel in transfer['panels'].values())
assert transfer['provider_model_requests'] == 0 and transfer['errors'] == []
mix = read('mixeval_summary.json')
review = read('mixeval_review.json')
mix_verification = read('mixeval_verification.json')
assert mix['source_rows_selected'] == 200 and mix['condition_records'] == 600
assert mix['provider_model_calls'] == 0 and mix['errors'] == []
for condition in ('native', 'bind_only'):
    row = mix['panels']['free_form:' + condition]
    assert row['field_presence_check'] == row['metadata_route_parser_consistent'] == 100
    assert row['source_type_preserved'] == 0 and row['MC_instruction'] == 100
repair = mix['panels']['free_form:bind_and_type']
assert repair['source_type_preserved'] == repair['question_bound'] == 100
assert repair['MC_instruction'] == repair['metadata_route_parser_consistent'] == 0
assert mix_verification['freeform_native_artificial_None_options'] == 100
assert mix_verification['MC_initial_exact_option_matches'] == 99
assert mix_verification['MC_reviewed_option_matches'] == 100
assert review['original_results_retained'] is True
assert review['type_dialect']['source_rows'] == 100
assert review['type_dialect']['condition_appearances'] == 300
assert review['option_whitespace']['source_rows'] == 1
assert review['freeform_result_unchanged'] is True
assert read('external_update.json')['independently_affected_run_verified'] is False
assert len(read('fork_inventory.json')['forks']) == 29
copies = read('external_update.json')['fork_followup']['inspected']
assert len(copies) == 3 and sum(item['matching_current_native_tool'] for item in copies) == 2
score = read('scoring_replay_summary.json')
assert score['source_rows']==200 and score['condition_records']==2400 and score['errors']==[]
raw=[r for r in score['panels'] if r['condition']=='native_list_reference']
assert len(raw)==8 and all(r['valid_samples']==0 and r['invalid_references']==100 for r in raw)
assert read('scoring_replay_verification.json')['status']=='PASS'
assert read('scoring_adapter_verification.json')['status']=='PASS'
public=read('public_score_summary.json');pv=read('public_score_verification.json')
assert public['captured_real_outputs']==49 and pv['reference_exclusions_native']==49
assert pv['typed_correct']=={'free_form':13,'multiple_choice':20}
assert read('public_exact_alias_summary.json')['real_score_changes']==0
assert read('public_exact_alias_summary.json')['synthetic_oracle_repairs']==2
den=read('denominator_review.json')
assert den['panels']['free_form']['scored_samples']==den['panels']['multiple_choice']['scored_samples']==0

for name,n,correct in [('native_route_free_form.json',17,13),('native_route_multiple_choice.json',32,20)]:
 r=read(name);assert r['status']=='PASS' and r['source_rows']==r['scored_rows']==n
 assert r['shim_events']==[] and r['generation_calls']==1 and r['new_model_calls']==0
 assert r['native_primary_metric_stage_executed'] is False
 assert round(r['typed_rule_mean']*n)==correct
controls=read('native_route_controls.json');assert controls['status']=='PASS' and len(controls['controls'])==10
assert all(c['status']=='INCOMPLETE' and c['typed_rule_mean'] is None and c['local_generation_batches']==0 for c in controls['controls'])

assert read('native_route_verification.json')['status']=='PASS_WITH_PROVENANCE_ERRATUM'
generation=read('paired_generation_analysis.json')
assert generation['planned_requests']==generation['recorded_artifacts']==80
assert generation['completed_scored']==69
assert generation['input_tokens']==8062 and generation['output_tokens']==66304
ge={x['model']:x for x in generation['effects']}
assert ge['gemma-4-31b-it']['gain_bounds']==[-.05,.25]
assert ge['qwen3.8-27b']['gain_bounds']==[.5,.75]
assert generation['new_judge_calls']==0
assert read('paired_generation_verification.json')['status']=='PASS'

adjud = read('adjudication_summary.json')
assert adjud['reviewed']==69 and adjud['capture_unknowns']==11
assert read('adjudication_verification.json')['status']=='PASS'
assert {x['model']:x['final_score_gain_bounds'] for x in adjud['effects']}=={'gemma-4-31b-it':[.4,.7],'qwen3.8-27b':[.55,.8]}
assert next(g for g in adjud['groups'] if g['model']=='gemma-4-31b-it' and g['condition']=='binding_only')['rule_credit_final_zero']==9
assert all(g['final_label_disagreements']==g['nonfinal_label_disagreements']==0 for g in adjud['groups'])
pages = json.loads((P / 'manuscript.json').read_text())
claims = json.loads((P / 'claims.json').read_text())
assert len(pages) == 14 and len(claims) == 16
assert 150 <= len(pages[0]['blocks'][2]['text'].split()) <= 250
assert [row[0] for row in pages[12]['blocks'][1]['rows']] == [claim['id'] for claim in claims[:15]]
for claim in claims:
    assert all((P / 'evidence' / name).is_file() for name in claim['evidence'].split(';'))
with (P / 'claim_evidence.csv').open(newline='') as stream:
    ledger = list(csv.DictReader(stream))
assert len(ledger) == len(claims)
for row, claim in zip(ledger, claims):
    assert row == dict(claim_id=claim['id'], section=claim['section'],
                       numerical_or_status_claim=claim['claim'],
                       evidence_files=claim['evidence'], qualification=claim['qualification'])
result = dict(status='PASS', claims_checked=16, working_draft_version='1.5',
              integrated_mechanisms=['native source gate', 'shared input causes', 'MMMLU prediction', 'MixEval task kind'],
              verifier_model_requests=0, new_experiments_during_synthesis=0,
              scope='Synthesis consistency check against source snapshots')
(P/'CLAIM_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))

