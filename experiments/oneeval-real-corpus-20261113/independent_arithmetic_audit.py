"""Recompute every reducer and ranking using exact rational arithmetic."""
from collections import defaultdict
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results'

def lines(name):
    return [json.loads(x) for x in gzip.decompress((RESULTS / name).read_bytes()).decode().splitlines()]

def dumps(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'))

def main():
    grouped = defaultdict(list)
    for row in lines('ROW_PARSE_AUDIT.jsonl.gz'):
        grouped[(row['cohort'], row['dataset'], row['system'])].append(row)
    expected = {}
    exact_pair_audit = []
    for key, rows in grouped.items():
        for denominator in ('valid_only', 'total'):
            for seed in (None, *range(10)):
                order = 'source' if seed is None else 'sha256_seed_' + str(seed)
                data = rows if seed is None else sorted(rows, key=lambda row: hashlib.sha256(
                    ('oneeval-real-corpus-20261113|' + str(seed) + '|' + row['dataset'] + '|' + dumps(row['id'])).encode()).digest())
                def counts(part):
                    correct = sum(row['prediction_parse']['ok'] and row['reference_parse']['ok']
                                  and row['prediction_parse']['normalized'] == row['reference_parse']['normalized'] for row in part)
                    valid = sum(row['reference_parse']['ok'] and
                                (denominator == 'total' or row['prediction_parse']['ok']) for row in part)
                    return correct, valid
                correct, valid = counts(data)
                canonical = Fraction(correct, valid) if valid else Fraction(0)
                excluded = valid != len(data)
                for workers in (1, 2, 4, 8):
                    chunk_size = math.ceil(len(data) / workers)
                    chunk_sizes = list(range(0, len(data), chunk_size))
                    if excluded:
                        weighted = Fraction(0)
                        for start in chunk_sizes:
                            chunk = data[start:start+chunk_size]
                            c, v = counts(chunk)
                            weighted += len(chunk) * (Fraction(c, v) if v else Fraction(0))
                        parallel = weighted / len(data)
                    else:
                        parallel = canonical
                    for name in ('choice_accuracy', 'accuracy', 'acc'):
                        result = canonical if name == 'choice_accuracy' or len(data) <= 100 else parallel
                        expected[(*key, denominator, order, workers, name)] = (result, canonical)
    score_rows = lines('ALL_SCORE_REPLAYS.jsonl.gz')
    for row in score_rows:
        key = (row['cohort'], row['dataset'], row['system'], row['denominator'], row['order'], row['workers'], row['name'])
        result, canonical = expected[key]
        assert abs(float(result) - row['score']) < 1e-12
        assert abs(float(canonical) - row['canonical_score']) < 1e-12
    comparisons = lines('ALL_PAIR_COMPARISONS.jsonl.gz')
    for row in comparisons:
        tail = (row['denominator'], row['order'], row['workers'], 'accuracy')
        a, ca = expected[(row['cohort'], row['dataset'], row['system_a'], *tail)]
        b, cb = expected[(row['cohort'], row['dataset'], row['system_b'], *tail)]
        reversal = (a - b) * (ca - cb) < 0
        assert reversal == row['strict_reversal']
        if reversal:
            exact_pair_audit.append({**row, 'canonical_exact_a': str(ca), 'canonical_exact_b': str(cb),
                                     'alias_exact_a': str(a), 'alias_exact_b': str(b)})
    report = {'method': 'Separate exact Fraction arithmetic from saved parser statuses; no upstream metric runner or analyzer formula imported.',
              'scope': 'Checks denominator, chunk weighting, permutations, pair signs. Does not independently validate natural-language choice parsing.',
              'score_combinations_checked': len(score_rows), 'pair_comparisons_checked': len(comparisons),
              'strict_reversal_configurations': len(exact_pair_audit),
              'distinct_reversed_pairs': sorted({(r['cohort'], r['dataset'], r['system_a'], r['system_b']) for r in exact_pair_audit}),
              'reversal_details': exact_pair_audit}
    (RESULTS / 'INDEPENDENT_ARITHMETIC_AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'reversal_details'}, indent=2))

if __name__ == '__main__':
    main()
