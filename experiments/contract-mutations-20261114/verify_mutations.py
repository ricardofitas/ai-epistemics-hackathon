"""Recompute mutation denominators, source lineage and gate accounting."""
import json,gzip,hashlib
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=Path(__import__('sys').argv[1]).resolve()
def rows(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
inputs=rows(ROOT/'INPUTS.jsonl.gz');results=rows(ROOT/'RESULTS.jsonl.gz')
protocol=json.loads((ROOT/'PROTOCOL.json').read_text())
assert len(inputs)==200 and len(results)==2200
assert hashlib.sha256((ROOT/'check_contract.py').read_bytes()).hexdigest()==protocol['frozen_v1_sha256']
by_source={(r['benchmark'],r['source_index']):r for r in inputs};assert len(by_source)==200
for name in ['mmlu','mmlu-pro']:
 expected=rows(BASE/'work/holdout/capture'/name/'SELECTED.jsonl.gz')[:100]
 assert [r['source_index'] for r in inputs if r['benchmark']==name]==[s['source_index'] for s in expected]
 assert all(by_source[(name,s['source_index'])]['record']==s['record'] for s in expected)
groups=defaultdict(list);evidence=Counter()
for r in results:
 assert r['disposition']=='completed'
 rec=r['record'];groups[r['condition']].append(r)
 for version in ['v1','v2']:
  assert r['backend_calls'][version]==int(r[version]['status']=='PASS')
 source=by_source[(r['benchmark'],r['source_index'])]['record'];q=source['question'];opts=source['choices'] if r['benchmark']=='mmlu' else source['options']
 if r['condition']=='question_truncation':
  assert rec['question_probe_changed'] is True and q not in rec['prompt']
  evidence['partial_question_positive_probe']+=1
 if r['condition'] in ['distractor_replace','distractor_drop','duplicate_gold']:
  assert Counter(x.strip() for x in rec['choices'])!=Counter(x.strip() for x in opts)
  assert rec['correct_text'] in rec['choices'];evidence['gold_preserved_but_option_set_changed']+=1
summary=json.loads((ROOT/'SUMMARY.json').read_text())
for group in summary['conditions']:
 rs=groups[group['condition']];assert len(rs)==group['rows']==200
 for version in ['v1','v2']:
  assert {s:sum(r[version]['status']==s for r in rs) for s in ['PASS','FAIL','INCOMPLETE']}==group[version]
benign=['identity','trim_only','coherent_permutation'];altered=['distractor_replace','distractor_drop','duplicate_gold','question_truncation','question_omission','gold_removed','wrong_reference']
result=dict(status='PASS',source_units=200,synthetic_variants=2200,
 benign_controls=sum(len(groups[k]) for k in benign),
 altered_task_variants=sum(len(groups[k]) for k in altered),
 v1_accepted_altered=sum(r['v1']['status']=='PASS' for k in altered for r in groups[k]),
 v2_accepted_altered=sum(r['v2']['status']=='PASS' for k in altered for r in groups[k]),
 missing_source_incomplete=sum(r['v2']['status']=='INCOMPLETE' for r in groups['missing_source']),
 verified_mechanisms=dict(evidence),provider_requests=0,
 interpretation='Counts describe intentionally constructed development cases, not natural frequency, independent generalization, or statistical precision.')
(ROOT/'VERIFIED_ACCOUNTING.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

