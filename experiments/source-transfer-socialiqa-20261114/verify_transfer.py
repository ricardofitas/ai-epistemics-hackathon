"""Independent raw-source selection, semantics, gates and denominator reconciliation."""
import json,gzip,hashlib
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent
raw=[json.loads(x) for x in (P/'dev.jsonl').read_text().splitlines()];gold=(P/'dev-labels.lst').read_text().splitlines();assert len(raw)==len(gold)==1954
canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
hashv=lambda x:hashlib.sha256(x).hexdigest()
proto=json.loads((P/'PROTOCOL.json').read_text())
assert hashv((P/'official_archive.zip').read_bytes())==proto['source']['expected_archive_sha256']
for file,key in [('check_contract.py','frozen_checker_sha256'),('source_bound.py','frozen_wrapper_sha256')]:assert hashv((P/file).read_bytes())==proto[key]
order=sorted(range(len(raw)),key=lambda i:(hashv(canonical({'record':raw[i],'label':int(gold[i])})),i))[:100]
selected=[json.loads(x) for x in gzip.decompress((P/'SELECTED.jsonl.gz').read_bytes()).splitlines()];assert [s['source_index'] for s in selected]==order
out=[json.loads(x) for x in gzip.decompress((P/'RESULTS.jsonl.gz').read_bytes()).splitlines()];assert len(out)==600
seen=set();mismatches=[]
for item in out:
 i=item['source_index'];c=item['condition'];assert i in order and (i,c) not in seen;seen.add((i,c));assert item['disposition']=='completed'
 source=raw[i];answer={'1':'answerA','2':'answerB','3':'answerC'}[gold[i].strip()];rec=item['record'];correct=source[answer]
 assert rec['correct_text']==correct
 assert rec['choices'][ord(rec['expected_reference'])-65]==correct
 assert rec['reference']==rec['expected_reference']
 if c in ['healthy','coherent_permutation']:
  assert Counter(rec['choices'])==Counter(source[k] for k in ['answerA','answerB','answerC']);assert source['context']+'\n'+source['question'] in rec['prompt']
 if c=='distractor_drop':assert len(rec['choices'])==2 and correct in rec['choices']
 if c=='question_omission':assert rec['question_probe_changed'] is False
 if c=='context_omission':assert rec['context_probe_changed'] is False
 if c=='missing_source':assert not any(k in rec for k in ['source_question','source_choices','source_correct_index'])
 for v in ['v1','v2']:
  expected=proto['expected_'+v][c];observed=item[v]['status']
  if observed!=expected:mismatches.append(dict(source_index=i,condition=c,version=v,expected=expected,observed=observed))
  assert item['counting_function_invocations'][v]==int(observed=='PASS')
assert len(seen)==len(order)*len(proto['conditions'])
summary=json.loads((P/'SUMMARY.json').read_text())
for s in summary['conditions']:
 for v in ['v1','v2']:
  assert s['statuses'][v]==dict(Counter(x[v]['status'] for x in out if x['condition']==s['condition']))
assert not json.loads((P/'ERRORS.json').read_text())
report=dict(status='PASS',selected_rows=100,verified_condition_variants=600,unique_context_question_pairs=len({(raw[i]['context'],raw[i]['question']) for i in order}),distinct_contexts=len({raw[i]['context'] for i in order}),predeclared_expectation_mismatches=mismatches,provider_calls=0,reporting_note='SUMMARY.independent_context_groups counts distinct exact contexts only; this does not prove statistical independence.',scope='Independent source/order/reference/condition/gate reconciliation; not rerun model inference or global project exposure census.')
(P/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
