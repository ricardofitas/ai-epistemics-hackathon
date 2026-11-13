#!/usr/bin/env python3
"""Source-only linkage; no model outputs or performance used."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parent

def norm(s):
    return ' '.join(unicodedata.normalize('NFKC', s).replace('’', "'").split())

def load(name):
    return [(i, line, json.loads(line)) for i, line in enumerate((ROOT / name).read_text().splitlines())]

def final_answer(row):
    if 'solution' in row:
        result = str(row['answer']).strip()
        assert str(row['solution']).rsplit('####', 1)[-1].strip() == result
    else:
        result = row['answer'].rsplit('####', 1)[-1].strip()
    assert re.fullmatch(r'[-+]?\d[\d,]*(?:\.\d+)?', result), result
    return result.replace(',', '')

def variant(name, triple, role):
    index, line, row = triple
    return {'variant': name, 'selection_role': role, 'source_row_index_zero_based': index,
            'source_row_sha256': hashlib.sha256(line.encode()).hexdigest(),
            'question': row['question'], 'gold_answer': final_answer(row),
            'source_solution': row.get('solution', row.get('answer'))}

def main():
    symbolic = load('GSM_symbolic.jsonl')
    p1 = load('GSM_p1.jsonl')
    p2 = load('GSM_p2.jsonl')
    plus = load('gsm_plus_v1.jsonl')
    maps = [{t[2]['original_id']: t for t in xs if t[2]['instance'] == 0}
            for xs in (symbolic, p1, p2)]
    grouped = {}
    for t in plus:
        grouped.setdefault(norm(t[2]['seed_question']), {})[t[2]['perturbation_type']] = t
    families = []
    for oid in sorted(set(maps[0]) & set(maps[1]) & set(maps[2])):
        seed = maps[0][oid][2]
        linked = grouped[norm(seed['original_question'])]
        pu = linked['problem understanding']
        num = linked['numerical substitution']
        assert pu[2]['answer'] == pu[2]['seed_answer']
        assert pu[2]['seed_answer'] == num[2]['seed_answer']
        assert final_answer({'answer': seed['original_answer']}) == pu[2]['seed_answer']
        variants = [variant('numeric', num, 'matched_target'),
                    variant('paraphrase', pu, 'matched_target'),
                    variant('p1', maps[1][oid], 'mismatched_added_clause'),
                    variant('p2', maps[2][oid], 'mismatched_added_clause')]
        for v in variants:
            v['source_file'] = {'numeric':'gsm_plus_v1.jsonl', 'paraphrase':'gsm_plus_v1.jsonl',
                                'p1':'GSM_p1.jsonl', 'p2':'GSM_p2.jsonl'}[v['variant']]
        families.append({'source_family_id': 'GSM8K-' + str(oid),
                         'original_gsm8k_test_row_zero_based': oid,
                         'apple_template_id': seed['id'],
                         'seed_question': seed['original_question'],
                         'seed_gold_answer': pu[2]['seed_answer'],
                         'seed_solution': seed['original_answer'],
                         'source_validation_status': 'pending',
                         'variants': variants})
    assert len(families) == 50
    result = {'status': 'source_only_no_model_performance',
              'family_count': 50, 'variants_per_family': 4,
              'normalization': 'Unicode NFKC, curly apostrophe to ASCII, collapse whitespace',
              'linkage': 'Same normalized original GSM8K question; Apple original_id links symbolic/P1/P2',
              'scope': 'Numerical substitution and harmless wording are distinct target examples, not their composition. '
                       'Problem-understanding source label is not itself proof of semantic validity. '
                       'All selected question/gold pairs need independent source-only review before inference.',
              'families': families}
    target = ROOT / 'candidate_families.json'
    with target.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'families': len(families), 'questions': 4 * len(families),
                      'candidate_pool_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}))

if __name__ == '__main__':
    main()
