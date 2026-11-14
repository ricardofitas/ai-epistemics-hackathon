"""Independent retained-record arithmetic audit. Does not rerun native pipeline."""
from pathlib import Path
from collections import Counter
import json,hashlib

HERE=Path(__file__).resolve().parent
ROOT=HERE/'archive'
expected_zip='0fff22307ea63ae0bbe15a9e03088344ce9479cf5d64d4d196e03efa2ed9871b'
assert hashlib.sha256((HERE/'native-entrypoint.zip').read_bytes()).hexdigest()==expected_zip
summary=json.loads((ROOT/'entrypoint-summary.json').read_bytes())
keys={'cupcase':('clean_case_presentation','correct_diagnosis',['correct_diagnosis','distractor1','distractor2','distractor3']),
      'sciq':('question','correct_answer',['correct_answer','distractor1','distractor2','distractor3']),
      'gpqa':('Question','Correct Answer',['Correct Answer','Incorrect Answer 1','Incorrect Answer 2','Incorrect Answer 3']),
      'mmlu':('question','answer','choices')}
def rows(path):return [json.loads(x) for x in path.read_text().split('\n') if x]
results={}
for name,dataset in summary['datasets'].items():
    folder=ROOT/'entrypoint_records'/name
    source=rows(folder/'source.jsonl');question_key,answer_key,choice_keys=keys[name]
    assert len(source)==dataset['source_rows']
    assert hashlib.sha256((folder/'source.jsonl').read_bytes()).hexdigest()==dataset['source_jsonl_sha256']
    positions=Counter()
    for row in source:
        choices=[str(row[k]) for k in choice_keys] if isinstance(choice_keys,list) else row[choice_keys]
        pos=int(row[answer_key]) if name=='mmlu' else choices.index(str(row[answer_key]))
        positions[pos]+=1
    assert {str(k):v for k,v in positions.items()}==dataset['gold_position_counts']
    out={}
    for letter,expected in dataset['baselines'].items():
        label=folder/('constant-'+letter)
        native_return=json.loads((label/'native-return.json').read_bytes())
        record_path=ROOT/('entrypoint_records/'+native_return['detail_path'].split('/entrypoint_records/',1)[1])
        records=rows(record_path);prompts=rows(label/'captured-prompts.jsonl');indices=rows(label/'prompt-index.jsonl')
        assert len(records)==len(prompts)==len(indices)==len(source)
        assert hashlib.sha256(record_path.read_bytes()).hexdigest()==expected['result_sha256']
        correct=sum(row['eval_score']==1 for row in records)
        valid=sum(bool(row['eval_valid']) for row in records)
        present=0;unresolved=0
        for original,row,prompt,index in zip(source,records,prompts,indices):
            # Task fields, rather than ancillary binary-float metadata.
            for k in [question_key,answer_key]+(choice_keys if isinstance(choice_keys,list) else [choice_keys]):
                assert row[k]==original[k],(name,k)
            assert row['generated_ans']=='<answer>'+letter+'</answer>'
            text=prompt['prompt'];has_question=str(original[question_key]) in text
            assert has_question==index['question_present']
            assert hashlib.sha256(text.encode()).hexdigest()==index['prompt_sha256']
            present+=has_question
            unresolved+=('{clean_case_presentation}' in text if name=='cupcase' else '{Question}' in text if name=='gpqa' else False)
        assert correct==expected['correct_rows'] and valid==expected['valid_rows'] and present==expected['own_question_present']
        assert abs(correct/valid-expected['report_score'])<1e-12
        assert expected['native_stats']['role']=='diagnostic' and expected['native_stats']['display_as_primary'] is False
        assert expected['report_source']=='dataflow_eval:accuracy'
        assert expected['ordinary_metric_score']==0.0
        assert expected['diagnostic_removed_report_source']=='dataflow_eval:missing'
        out[letter]=dict(rows=len(records),valid=valid,correct=correct,report_score=correct/valid,
                        question_present=present,unresolved_question_placeholder=unresolved,
                        original_source_task_fields_identical=True,
                        primary_metric_display=expected['ordinary_metric_score'],
                        selected_diagnostic_marked_nonprimary=True)
    results[name]=dict(source_rows=len(source),gold_positions=dict(positions),baselines=out)
report=dict(status='PASS',artifact_sha256=expected_zip,source_revision=summary['one_eval_revision'],
            datasets=results,new_native_runs=0,new_model_calls=0,
            scope='Independent retained-artifact identity/task-field/prompt/score recount, not installed CLI or third-party historical result attribution.')
(HERE/'INDEPENDENT_ENTRYPOINT_RECOUNT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
