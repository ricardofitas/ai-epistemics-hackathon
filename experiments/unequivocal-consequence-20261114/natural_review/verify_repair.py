"""Independent source/score recount for retained source-preserving repair."""
from pathlib import Path
from collections import Counter
import json,hashlib,random
HERE=Path(__file__).resolve().parent
OLD=HERE/'archive';NEW=HERE/'repair_archive'
assert hashlib.sha256((HERE/'native-repair.zip').read_bytes()).hexdigest()=='66de2030edca15d53c8318b59821d2e8ef06c31f3e94f8e7cba6d2bd4b5378fe'
def rows(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
s=json.loads((NEW/'repair-summary.json').read_bytes())
original=rows(OLD/'entrypoint_records/cupcase/source-before-native.jsonl')
repaired=rows(NEW/'entrypoint_records/cupcase-repaired/source-before-native.jsonl')
assert len(original)==len(repaired)==3562
rng=random.Random(20261114);positions=[];source_differences=[]
for i,(old,new) in enumerate(zip(original,repaired)):
    for key,value in old.items():
        if new[key]!=value:source_differences.append((i,key))
    choices=[old[k] for k in ['correct_diagnosis','distractor1','distractor2','distractor3']]
    rng.shuffle(choices)
    assert new['neutral_choices']==choices
    positions.append(choices.index(old['correct_diagnosis']))
assert not source_differences
summary={}
for letter,metadata in s['repaired_cupcase']['baselines'].items():
    folder=NEW/'entrypoint_records/cupcase-repaired'/('constant-'+letter)
    native=json.loads((folder/'native-return.json').read_bytes())
    actual_path=NEW/('entrypoint_records/'+native['detail_path'].split('/entrypoint_records/',1)[1])
    actual=rows(actual_path);prompts=rows(folder/'captured-prompts.jsonl')
    assert hashlib.sha256(actual_path.read_bytes()).hexdigest()==metadata['result_sha256']
    assert len(actual)==len(prompts)==len(original)
    confusion=Counter();mismatch_ids=[];own_present=0
    for i,(old,new,out,prompt) in enumerate(zip(original,repaired,actual,prompts)):
        for key,value in old.items():assert out[key]==value
        assert out['neutral_choices']==new['neutral_choices']
        assert out['generated_ans']=='<answer>'+letter+'</answer>'
        expected=(new['neutral_choices'][ord(letter)-ord('A')]==old['correct_diagnosis'])
        got=out['eval_score']==1
        confusion[(expected,got)]+=1
        if expected!=got:mismatch_ids.append(i)
        own_present+=old['clean_case_presentation'] in prompt['prompt']
    native_correct=sum(x['eval_score']==1 for x in actual)
    assert native_correct==metadata['correct_rows'] and own_present==3562
    assert metadata['report_score']==native_correct/3562
    assert metadata['report_source']=='dataflow_eval:accuracy'
    assert metadata['native_stats']['role']=='diagnostic' and metadata['native_stats']['display_as_primary'] is False
    summary[letter]=dict(native_correct=native_correct,source_semantic_correct=sum(k[0]*v for k,v in confusion.items()),
                         first_occurrence_position_correct=positions.count(ord(letter)-ord('A')),
                         native_source_semantic_confusion={str(k):v for k,v in confusion.items()},
                         native_source_semantic_mismatch_rows=mismatch_ids,
                         own_question_present=own_present,report_score=native_correct/3562,
                         same_constant_prediction_bytes=True,source_fields_unchanged=True,
                         selected_report_source=metadata['report_source'],primary_metric_display=metadata['ordinary_metric_score'])
report=dict(status='PASS_WITH_RETAINED_PARSER_DISAGREEMENTS',source_rows=3562,
            original_source_fields_unchanged=True,
            seeded_choice_multisets_and_order_preserved=True,
            full_source_question_restored=True,baselines=summary,
            source_revision=s['one_eval_revision'],artifact_sha256='66de2030edca15d53c8318b59821d2e8ef06c31f3e94f8e7cba6d2bd4b5378fe',
            new_native_runs=0,new_model_calls=0)
(HERE/'INDEPENDENT_REPAIR_RECOUNT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
