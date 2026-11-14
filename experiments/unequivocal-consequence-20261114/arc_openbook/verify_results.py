"""Independent data-only reconciliation of the component consequence ledger."""
from pathlib import Path
from collections import Counter
import gzip,hashlib,json,re
ROOT=Path(__file__).resolve().parent
summary=json.loads((ROOT/'results/SUMMARY.json').read_bytes())
rows=json.loads((ROOT/'results/CAPTURES.json').read_bytes())
checks=0
for row in rows:
    assert hashlib.sha256(row['prompt'].encode()).hexdigest()==row['prompt_sha256']
    labels=re.findall(r'(?:^|\n)\{?([A-Z])\.\s',row['prompt'])
    expected=[chr(65+i) for i in range(len(row['displayed_choices']))]
    assert labels==expected,(row['benchmark'],row['condition'],labels,expected)
    assert (row['source_label'] in labels)==row['source_label_is_offered']
    checks+=3
for report in summary['results']:
    name=report['benchmark']
    for condition,result in report['conditions'].items():
        part=[r for r in rows if r['benchmark']==name and r['condition']==condition]
        assert len(part)==100
        assert sum(not r['source_label_is_offered'] for r in part)==result['label_not_offered']
        assert sum(r['question_present'] for r in part)==result['question_present']
        assert sum(r['displayed_choices']==r['source_choices'] for r in part)==result['choices_preserved']
        checks+=4
    before=report['conditions']['original'];after=report['conditions']['choices_and_binding']
    assert after['choices_preserved']==after['question_present']==100
    assert after['credited_unoffered_labels']==0
    assert before['source_letter_fixture_score']['score']==after['source_letter_fixture_score']['score']
    checks+=3
assert [r['conditions']['original']['credited_unoffered_labels'] for r in summary['results']]==[45,43,0]
out=dict(status='PASS',data_only_checks=checks,source_questions=300,condition_records=1200,
         credited_unoffered_labels_arc_openbook=88,ordinary_generator_import=True,
         ordinary_metric_import=True,full_dataflow_eval_tool_import=False,
         model_calls=0,scope='Independent reconciliation implementation by the same executor; not human or provider verification.')
(ROOT/'results/VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
compressed=gzip.compress((ROOT/'results/CAPTURES.json').read_bytes(),mtime=0)
(ROOT/'results/CAPTURES.json.gz').write_bytes(compressed)
print(json.dumps(out,indent=2))
