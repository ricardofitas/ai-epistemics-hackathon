#!/usr/bin/env python3
"""Prepare source-only, source-disjoint released-P1 candidate pool.

No model output or source-review decisions are consumed. Every released question,
answer, source solution and row hash is retained without semantic edits.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import unicodedata

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OLD = REPO / 'experiments/impact-study-20261113/consequence_math_sources_20261113'
PINS = {
    'GSM_p1.jsonl': '5478fe81b9cdc5d9447514ca68b0dfbb6cb01b7227fefadf143469b103b592ac',
    'gsm_plus_v1.jsonl': '885c279bfa9cde767ea23f79fd462d566fa0dbf6af9f2dcf30c75aa94f3d4041',
}
PRIOR_SHA = '75f8d43160aa9f7a24539060d6bb6e0272fe98802a6ca66e5f523b4b5ce45540'
INVENTORY_SHA = '7e0fa512efde603db98826a7e8014d6385c807d31a71743fe3498cce68354edc'
SEED = 20261113117
VARIANTS = ('numeric', 'paraphrase', 'p1_i0', 'p1_i1')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', text).replace('’', "'").split())


def load_rows(path):
    data = path.read_bytes()
    return [(i, line, json.loads(line)) for i, line in enumerate(data.decode('utf-8').splitlines())]


def number(text):
    text = str(text).strip()
    require(bool(re.fullmatch(r'[-+]?\d[\d,]*(?:\.\d+)?', text)), 'Unsupported source numeric answer: ' + repr(text))
    value = text.replace(',', '')
    Fraction(value)
    return value


def final_answer(row):
    if 'solution' in row:
        answer = str(row['answer']).strip()
        require(str(row['solution']).rsplit('####', 1)[-1].strip() == answer,
                'GSM-Plus solution/final answer differs')
        return number(answer)
    return number(row['answer'].rsplit('####', 1)[-1].strip())


def variant(name, source_file, triple):
    index, line, row = triple
    result = {
        'variant': name,
        'source_file': source_file,
        'source_row_index_zero_based': index,
        'source_row_sha256': digest(line.encode('utf-8')),
        'question': row['question'],
        'gold_answer': final_answer(row),
        'source_final_answer': str(row['answer']).strip() if 'solution' in row else row['answer'].rsplit('####', 1)[-1].strip(),
        'source_solution': row.get('solution', row.get('answer')),
    }
    if source_file == 'GSM_p1.jsonl':
        result['source_metadata'] = {k: row[k] for k in ('id', 'instance', 'original_id')}
    else:
        result['source_metadata'] = {'perturbation_type': row['perturbation_type']}
    return result


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def prepare(source_dir, prior_path, inventory_path, out):
    for path in [prior_path, inventory_path, source_dir / 'source_manifest.json',
                 *(source_dir / name for name in PINS)]:
        require(path.is_file(), 'Missing source input: ' + str(path))
    require(digest(prior_path.read_bytes()) == PRIOR_SHA, 'Previous reviewed pool changed')
    require(digest(inventory_path.read_bytes()) == INVENTORY_SHA, 'Source inventory changed')
    for filename, sha in PINS.items():
        require(digest((source_dir / filename).read_bytes()) == sha,
                'Pinned raw source changed: ' + filename)
    previous = json.loads(prior_path.read_text())
    require(len(previous['families']) == 50, 'Previous source pool is not all50 reviewed families')
    previous_ids = {f['source_family_id'] for f in previous['families']}
    previous_questions = {norm(f['seed_question']) for f in previous['families']}
    require(len(previous_ids) == len(previous_questions) == 50, 'Previous IDs/questions are not unique')
    inventory = json.loads(inventory_path.read_text())
    inventory_ids = {f['source_family_id'] for f in inventory['new_p1_linked_families']}
    require(len(inventory_ids) == 50, 'Inventory source-disjoint P1 count changed')
    apple_rows = load_rows(source_dir / 'GSM_p1.jsonl')
    plus_rows = load_rows(source_dir / 'gsm_plus_v1.jsonl')
    apple = {}
    for triple in apple_rows:
        row = triple[2]
        if row['instance'] in (0, 1):
            key = (row['original_id'], row['instance'])
            require(key not in apple, 'Duplicate P1 family/instance')
            apple[key] = triple
    plus = {}
    for triple in plus_rows:
        row = triple[2]
        key = (norm(row['seed_question']), row['perturbation_type'])
        require(key not in plus, 'Duplicate GSM-Plus family/type')
        plus[key] = triple
    families = []
    for oid in sorted({oid for oid, _ in apple}):
        family_id = 'GSM8K-' + str(oid)
        if family_id in previous_ids:
            continue
        p0, p1 = apple[oid, 0], apple[oid, 1]
        row = p0[2]
        seed_question = row['original_question']
        seed_norm = norm(seed_question)
        require(seed_norm not in previous_questions, 'New family repeats previous normalized source question')
        require(p1[2]['original_question'] == seed_question and p1[2]['original_answer'] == row['original_answer'],
                'P1 instances disagree on exact source seed')
        numerical = plus[seed_norm, 'numerical substitution']
        paraphrase = plus[seed_norm, 'problem understanding']
        require(numerical[2]['seed_question'] == paraphrase[2]['seed_question'], 'GSM-Plus seed mismatch')
        require(numerical[2]['seed_answer'] == paraphrase[2]['seed_answer'], 'GSM-Plus seed gold mismatch')
        seed_gold = final_answer({'answer': row['original_answer']})
        require(seed_gold == number(numerical[2]['seed_answer']), 'Apple/GSM-Plus source final answer mismatch')
        require(number(paraphrase[2]['answer']) == seed_gold, 'Paraphrase released gold differs from seed final answer')
        families.append({
            'source_family_id': family_id,
            'original_gsm8k_test_row_zero_based': oid,
            'apple_template_id': row['id'],
            'seed_question': seed_question,
            'seed_gold_answer': seed_gold,
            'seed_solution': row['original_answer'],
            'gsm_plus_seed_question': numerical[2]['seed_question'],
            'gsm_plus_seed_solution': numerical[2]['seed_solution'],
            'linkage_normalization': 'Unicode NFKC; curly apostrophe to ASCII; collapse whitespace',
            'source_validation_status': 'pending_two_independent_first_reviews',
            'variants': [variant('numeric', 'gsm_plus_v1.jsonl', numerical),
                         variant('paraphrase', 'gsm_plus_v1.jsonl', paraphrase),
                         variant('p1_i0', 'GSM_p1.jsonl', p0),
                         variant('p1_i1', 'GSM_p1.jsonl', p1)],
        })
    require(len(families) == 50 and {f['source_family_id'] for f in families} == inventory_ids,
            'Computed source-disjoint P1 family pool differs from inventory')
    families.sort(key=lambda f: (digest(f"{SEED}|{f['source_family_id']}".encode()), f['source_family_id']))
    for rank, family in enumerate(families, 1):
        family['candidate_rank'] = rank
        family['review_id'] = f'P{rank:03d}'
        family['response_id'] = family['review_id']
        family['priority_sha256'] = digest(f"{SEED}|{family['source_family_id']}".encode())
        require(tuple(v['variant'] for v in family['variants']) == VARIANTS, 'Variant order changed')
    manifest = []
    for item in json.loads((source_dir / 'source_manifest.json').read_text()):
        filename = item['name'] + ('.md' if item['name'].endswith('readme') else '.jsonl')
        if filename in PINS:
            require(item['sha256'] == PINS[filename], 'Source manifest pin mismatch')
            manifest.append({**item, 'filename': filename})
    require({x['filename'] for x in manifest} == set(PINS), 'Missing raw source provenance')
    excluded = {'status': 'exclude_every_previous_reviewed_family_regardless_of_prior_admission',
                'source_file': 'previous_candidate_families.json', 'source_sha256': PRIOR_SHA,
                'family_count': 50, 'source_family_ids': sorted(previous_ids),
                'normalized_seed_question_sha256': sorted(digest(q.encode()) for q in previous_questions)}
    pool = {'status': 'source_only_pending_independent_review_no_solver_outputs',
            'family_count': 50, 'variants_per_family': 4, 'variant_ids': list(VARIANTS),
            'source_family_priority_seed': SEED, 'families': families,
            'scope': 'P1 instance0/instance1 are two released realizations of P1, not P1/P2. Numerical substitution and paraphrase are separate target examples, not composed transformations.'}
    packet = ''.join(json.dumps(f, ensure_ascii=False, separators=(',', ':')) + '\n' for f in families).encode('utf-8')
    payloads = {'candidate_families.json': encoded(pool),
                'source_review_packet.jsonl': packet,
                'source_manifest.json': encoded(manifest),
                'excluded_previous_families.json': encoded(excluded),
                'source_inventory.json': inventory_path.read_bytes(),
                'previous_candidate_families.json': prior_path.read_bytes()}
    plan = {
        'study_id': 'p1-gap-replication-20261113',
        'stage': 'source_only_preplan_before_first_reviews_and_solver_inference',
        'objective': 'Prepare source-disjoint released-P1 prospective gap-distortion replication; final scientific protocol must be frozen before solver inference.',
        'candidate_families': 50, 'required_selected_families': 30,
        'source_family_priority_seed': SEED,
        'priority_formula': "SHA256(UTF-8('20261113117|' + source_family_id)); ascending hex digest, then family ID",
        'source_gate': {
            'review_streams': 2, 'first_reviews_only': True,
            'all50_candidates_reviewed_by_each_stream': True,
            'family_disposition_required': 'pass',
            'all_four_source_gold_status_required': 'pass',
            'independently_computed_numeric_answers_must_equal_unchanged_source_gold': True,
            'independent_arithmetic_evidence_each_variant': True,
            'numeric_and_paraphrase_target_structure_status_required': 'same',
            'p1_instances_must_be_solvable_and_source_family_linkage_valid': True,
            'uncertain_or_reject_excluded': True,
            'coordinator_overrides': False, 'question_edits': False, 'gold_edits': False,
        },
        'selection_rule': 'Select the first30 candidates in frozen SHA256 priority order that pass both complete independent first source reviews. Never use solver outputs or revised review decisions for admission.',
        'insufficient_source_rule': 'If fewer than30 candidates pass both first reviews, STOP before all solver inference; no smaller cohort, threshold relaxation or amendment within this study.',
        'later_invalidity_rule': 'Any discovered invalidity after source admission stops this cohort for a separate amendment; no post-output replacements.',
        'cohort': {'families': 30, 'variants_per_family': 4,
                   'analysis_role': 'single_prospective_replication_cohort_all30',
                   'selection_confirmation_split': False},
        'batching': {'families_per_batch': 3, 'blocks': 10,
                     'rule': 'Selected rank positions1-3,4-6,...,28-30 form fixed blocks; same family blocks across both models and all four variants; each batch has one variant only.'},
        'target_resource': ['numeric', 'paraphrase'],
        'comparison_resource': ['p1_i0', 'p1_i1'],
        'scope': 'Two independent P1 realizations are averaged; this is a P1-only partial resource replication, not a releasedP1/P2 replication. All50 prior reviewed families are excluded, including prior rejected/uncertain families.',
        'no_model_outputs_used': True, 'human_source_certification': 'pending; first source review is by independent agents',
        'input_sha256': {name: digest(data) for name, data in payloads.items()},
        'raw_source_pins': PINS,
    }
    payloads['selection_plan.json'] = encoded(plan)
    out.mkdir(parents=True, exist_ok=True)
    for name in payloads:
        require(not (out / name).exists(), 'Refusing to overwrite source-only output: ' + str(out / name))
    for name, data in payloads.items():
        with (out / name).open('xb') as f:
            f.write(data)
    report = {'status': 'source_only_pool_prepared_no_reviews_or_solver_calls',
              'family_count': 50, 'question_count': 200,
              'source_disjoint_from_all_previous50_reviewed': True,
              'source_variants': list(VARIANTS),
              'sha256': {name: digest(data) for name, data in payloads.items()}}
    with (out / 'POOL_PREPARATION_RECEIPT.json').open('x') as f:
        json.dump(report, f, indent=2); f.write('\n')
    print(json.dumps(report, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-dir', type=Path, default=OLD)
    ap.add_argument('--prior-candidates', type=Path, default=OLD / 'candidate_families.json')
    ap.add_argument('--inventory', type=Path, default=REPO / 'new_gap_source_inventory_20261113.json')
    ap.add_argument('--output-dir', type=Path, default=HERE)
    args = ap.parse_args()
    prepare(args.source_dir, args.prior_candidates, args.inventory, args.output_dir)


if __name__ == '__main__':
    main()
