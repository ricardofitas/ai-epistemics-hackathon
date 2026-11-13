"""Run with the standard library after unzipping the follow-up bundle."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
report = json.loads((ROOT / 'prompt_collision_results.json').read_text())
stream = gzip.decompress((ROOT / 'validated_rows.jsonl.gz').read_bytes())
assert hashlib.sha256(stream).hexdigest() == report['evidence_rows_uncompressed_sha256']
records = [json.loads(line) for line in stream.splitlines()]
assert len(records) == 1267 and [r['row'] for r in records] == list(range(1267))
engines = {'oneeval_native': 'One-Eval native', 'oneeval_source_bound': 'One-Eval source-bound renderer', 'evalscope_native': 'EvalScope native'}
for key, title in engines.items():
    by_text = defaultdict(Counter)
    for row in records:
        by_text[row[key]][row['source_one_based_gold']] += 1
    observed = report['systems'][title]
    assert len(by_text) == observed['distinct_prompts']
    assert sum(min(c['1'], c['2']) for c in by_text.values()) == observed['unavoidable_errors']
    assert sum(max(c['1'], c['2']) for c in by_text.values()) == observed['maximum_correct']
    assert sum(bool(c['1'] and c['2']) for c in by_text.values()) == observed['mixed_gold_groups']
    assert sum(sum(c.values()) for c in by_text.values() if c['1'] and c['2']) == observed['rows_in_mixed_groups']
plan = json.loads((ROOT / 'NEXT_EXPERIMENT.json').read_text())
request_bytes = gzip.decompress((ROOT / 'planned_requests.jsonl.gz').read_bytes())
assert hashlib.sha256(request_bytes).hexdigest() == plan['manifest_uncompressed_sha256']
cases_file = (ROOT / 'fresh_panel.jsonl.gz').read_bytes()
assert hashlib.sha256(cases_file).hexdigest() == plan['cases_compressed_sha256']
cases = {row['source_row']: row for row in map(json.loads, gzip.decompress(cases_file).splitlines())}
requests = list(map(json.loads, request_bytes.splitlines()))
assert len(cases) == 50 and len(requests) == 200
for item in requests:
    case = cases[item['source_row']]
    assert item['request_payload']['input'] == case[item['condition']]
    assert case['native_prompt'] == records[item['source_row']]['oneeval_native']
    assert case['corrected_prompt'] == records[item['source_row']]['oneeval_source_bound']
strata = Counter(c['stratum'] for c in cases.values())
assert strata == {'contradictory_pair': 30, 'singleton_control': 20}
assert len({(r['source_row'], r['condition'], r['request_payload']['model']) for r in requests}) == 200
print('Verified all 1,267 rows, all three ceilings, and the frozen 50-question panel. No inference is invoked.')
