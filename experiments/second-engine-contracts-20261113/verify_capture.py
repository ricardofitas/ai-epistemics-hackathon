"""Independent corpus/target checks on captured native EvalScope artifacts."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / 'capture'

def rows(path):
    with gzip.open(path, 'rt') as source:
        return [json.loads(line) for line in source]

summary = []
for panel in sorted((CAPTURE / 'evidence').iterdir()):
    raw = rows(panel / 'RAW_RECORDS.jsonl.gz')
    before = rows(panel / 'NATIVE_PRE_FORMAT_SAMPLES.jsonl.gz')
    after = rows(panel / 'NATIVE_READY_SAMPLES.jsonl.gz')
    checks = rows(panel / 'SOURCE_CHECKS.jsonl.gz')
    scores = json.loads((panel / 'NATIVE_SCORES.json').read_text())
    setup = json.loads((panel / 'SETUP.json').read_text())
    name = setup['name']
    assert len(raw) == len(before) == len(after) == len(checks) == setup['samples']
    counts = Counter()
    for index, (record, sample) in enumerate(zip(raw, before)):
        if name == 'winogrande':
            target = {'1': 'A', '2': 'B'}[str(record['answer'])]
            assert sample['choices'] == [record['option1'], record['option2']]
        elif name == 'hellaswag':
            target = 'ABCD'[int(record['label'])]
        elif name == 'boolq':
            assert type(record['answer']) is bool
            target = {True: 'A', False: 'B'}[record['answer']]
            assert sample['choices'] == ['Yes', 'No']
        elif name == 'pubmedqa':
            target = str(record['answer']).upper()
        else:
            target = record['answer']
            assert sample['choices'] == record['choices']
            if 'answer_index' in record:
                assert target == 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[record['answer_index']]
        assert sample['target'] == target == after[index]['target']
        counts[target] += 1
    for score in scores:
        assert score['rows'] == len(raw)
        assert abs(sum(score['target_counts'].values()) - len(raw)) == 0
        if not score['shuffle_choices']:
            assert score['target_counts'] == dict(counts)
        target_counts = score['target_counts']
        expected = 1.0 if score['predictor'] == 'oracle' else target_counts.get(score['predictor'], 0) / len(raw)
        assert abs(score['score'] - expected) < 1e-12
    assert all(c['reference_matches_source'] and c['question_mutation_changes_prompt'] for c in checks)
    assert all(c['context_mutation_changes_prompt'] is not False for c in checks)
    summary.append({'benchmark': name, 'rows': len(raw), 'target_counts': dict(counts),
                    'max_constant_score': max(s['score'] for s in scores if not s['shuffle_choices'] and s['predictor'] != 'oracle'),
                    'oracle_score': next(s['score'] for s in scores if not s['shuffle_choices'] and s['predictor'] == 'oracle'),
                    'score_conditions': len(scores)})

# Join the newly captured native SciQ rows to all prior immutable AllenAI test
# records. Exact question only; retain ambiguity/unmatched counts explicitly.
reference_source = ROOT / 'reference_source/sciq__test.jsonl.gz'
if not reference_source.exists():
    reference_source = ROOT.parent / 'default_contract_source_capture_20261113/capture/sciq__test.jsonl.gz'
original = rows(reference_source)
lookup = defaultdict(list)
for record in original:
    lookup[record['question']].append(record)
native = rows(CAPTURE / 'evidence/sciq__modelscope/RAW_RECORDS.jsonl.gz')
join = Counter()
for record in native:
    matches = lookup[record['question']]
    if len(matches) != 1:
        join['unmatched' if not matches else 'ambiguous'] += 1
        continue
    source = matches[0]
    assert Counter(record['choices']) == Counter([source['correct_answer'], source['distractor1'], source['distractor2'], source['distractor3']])
    assert record['choices']['ABCD'.index(record['answer'])] == source['correct_answer']
    assert record['support'] == source['support']
    join['exact_question_options_gold_context_match'] += 1
assert join['exact_question_options_gold_context_match'] == len(native) == 1000, dict(join)
assert len({r['question'] for r in native}) == len(native)
report = {'status': 'verified', 'source_rows': sum(p['rows'] for p in summary),
          'native_score_conditions': sum(p['score_conditions'] for p in summary),
          'panels': summary, 'sciq_original_source_join': dict(join),
          'scope': 'Checks captured native row-score outputs and source semantics; not a model-inference or publication-impact study.',
          'artifact_sha256': hashlib.sha256((ROOT / 'second-engine-contracts-43525347543.zip').read_bytes()).hexdigest()}
(ROOT / 'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
