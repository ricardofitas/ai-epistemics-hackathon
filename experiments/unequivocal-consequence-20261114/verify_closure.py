"""Root cross-check of independent native replay and raw response verification."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
a=json.loads((ROOT/'review/proof/RESULT.json').read_bytes())
b=json.loads((ROOT/'ROOT_FIXED_OUTPUT_VERIFICATION.json').read_bytes())
assert a['status']=='PASS_REFERENCE_ONLY_CONSEQUENCE' and b['status']=='PASS'
assert a['all_metric_contracts_unchanged'] and a['reference_key_only_rows_and_outputs_unchanged']
checks=2
for row in a['models']:
    m=row['model_result'];c=row['constant_B_result'];raw=b['models'][row['model']]
    assert m['original']['score']==.5 and c['original']['score']==1
    for mode in ['reference_key_only','reference_value_only']:
        assert m[mode]['score']==raw['known_correct']/12 and c[mode]['score']==.5
        assert m[mode]['parser']==c[mode]['parser']==a['native_original_parser']
        assert m[mode]['scored_samples']==m['original']['scored_samples']==12
        checks+=3
    assert m['original_reference_parse_counts']=={'B':12}
    assert m['corrected_reference_parse_counts']=={'A':6,'B':6}
    assert row['robust_model_vs_constant_reversal'] and raw['model_strictly_better_for_every_unknown_assignment']
    checks+=3
for control in a['full_source_constructed_controls']:
    r=control['result'];kind=control['predictor']
    if kind=='oracle':old=639/1267;new=1
    else:
        assert kind=='constant_B';old=1;new=639/1267
    assert r['original']['score']==old
    assert r['reference_key_only']['score']==r['reference_value_only']['score']==new
    assert r['original_reference_parse_counts']=={'B':1267}
    checks+=3
for control in a['healthy_hellaswag_controls']:
    assert control['original']['score']==control['reference_only']['score']==11/12
    assert control['metric_contract_unchanged'];checks+=2
arc=json.loads((ROOT/'arc_openbook/results/SUMMARY.json').read_bytes())
arcv=json.loads((ROOT/'arc_openbook/results/VERIFICATION.json').read_bytes())
assert arc['status']==arcv['status']=='PASS'
assert arcv['credited_unoffered_labels_arc_openbook']==88
squad=json.loads((ROOT/'squad/RESULT.json').read_bytes())
assert squad['source_questions']==100 and squad['complete']==1539 and squad['unknown']==61
assert squad['closure']['official_squad_metric_execution']=='PASS'
assert squad['closure']['natural_supported_native_fault_attribution']=='UNESTABLISHED'
checks+=5
natural=json.loads((ROOT/'natural_review/INDEPENDENT_REPAIR_RECOUNT.json').read_bytes())
assert natural['original_source_fields_unchanged'] and natural['source_rows']==3562
assert natural['baselines']['A']['native_source_semantic_mismatch_rows']==[]
assert natural['baselines']['A']['native_correct']==905
assert len(natural['baselines']['B']['native_source_semantic_mismatch_rows'])==6
checks+=4
out=dict(status='PASS',root_cross_checks=checks,primary_consequence='WinoGrande reference-only correction reverses fixed-model-output vs constant-B comparison',
         original_model_outputs_reused=24,source_questions_for_models=12,full_source_constructed_control_questions=1267,
         human_labels=0,new_model_calls=0,new_judge_calls=0,manuscript_files_changed=0,
         scope='Root arithmetic/identity cross-check plus separately executed native metric replay. Does not assert third-party historical leaderboard impact or population model accuracy.')
(ROOT/'ROOT_CLOSURE_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
