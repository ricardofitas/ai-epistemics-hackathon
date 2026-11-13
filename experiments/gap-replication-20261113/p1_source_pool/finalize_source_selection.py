#!/usr/bin/env python3
"""Apply frozen exact30 pass/pass source gate to two complete first-review streams.

Never revises source questions, golds or first review decisions. Insufficient
admission exits before creating the output directory or any selected cohort.
"""
import argparse
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
PLAN_SHA = '48ed92bb748408acfdcf3ca06f634c2b7491d5863a86f7e5cafad671757711d5'
VARIANTS = ('numeric', 'paraphrase', 'p1_i0', 'p1_i1')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def scalar(value):
    require(isinstance(value, (str, int, float)) and not isinstance(value, bool), 'Non-numeric computed answer')
    text = str(value).strip()
    if ',' in text:
        require(re.fullmatch(r'[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?', text), 'Invalid thousands separator')
        text = text.replace(',', '')
    return Fraction(text)


def read_reviews(path, expected):
    records = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        require(isinstance(row, dict), 'First review row must be an object')
        rid = row.get('response_id')
        require(rid in expected and rid not in records, 'Missing, unknown or duplicate first-review response_id')
        require(row.get('source_family_id') == expected[rid], 'First review family-ID mismatch: ' + rid)
        require(row.get('family_disposition') in ('pass', 'reject', 'uncertain'), 'Invalid family disposition: ' + rid)
        require('review_id' not in row or row['review_id'] == rid, 'Conflicting review identifiers: ' + rid)
        records[rid] = row
    require(set(records) == set(expected), 'Each first review must cover all50 source families exactly once')
    return records


def assess(row, family):
    reasons = []
    if row['family_disposition'] != 'pass':
        reasons.append('family_disposition_' + row['family_disposition'])
    checks = row.get('variant_checks')
    if not isinstance(checks, dict) or set(checks) != set(VARIANTS):
        reasons.append('missing_or_unexpected_four_variant_checks')
        checks = {}
    golds = {v['variant']: v['gold_answer'] for v in family['variants']}
    for name in VARIANTS:
        check = checks.get(name)
        if not isinstance(check, dict):
            reasons.append(name + ':missing_variant_check'); continue
        if check.get('gold_status') != 'pass':
            reasons.append(name + ':gold_status_not_pass')
        try:
            if scalar(check.get('computed_answer')) != scalar(golds[name]):
                reasons.append(name + ':computed_answer_differs_from_source_gold')
        except (ValueError, TypeError, ZeroDivisionError, OverflowError):
            reasons.append(name + ':missing_or_invalid_computed_answer')
        if name in ('numeric', 'paraphrase') and check.get('target_structure_status') != 'same':
            reasons.append(name + ':target_structure_status_not_same')
        if not isinstance(check.get('arithmetic_evidence'), str) or not check['arithmetic_evidence'].strip():
            reasons.append(name + ':missing_independent_arithmetic_evidence')
    return {'accepted': not reasons, 'reasons': reasons}


def finalize(pool, a_path, b_path, out):
    require(not out.exists(), 'Refusing existing output directory: ' + str(out))
    require(a_path.resolve() != b_path.resolve(), 'Two independent first-review file paths are required')
    require(sha(pool / 'selection_plan.json') == PLAN_SHA, 'Frozen source selection plan changed')
    plan = load(pool / 'selection_plan.json')
    for filename, digest in plan['input_sha256'].items():
        require(sha(pool / filename) == digest, 'Frozen source input changed: ' + filename)
    require(plan['required_selected_families'] == 30 and plan['candidate_families'] == 50, 'Frozen quota changed')
    ranked = load(pool / 'candidate_families.json')['families']
    require(len(ranked) == 50 and [f['candidate_rank'] for f in ranked] == list(range(1, 51)), 'Invalid frozen priority order')
    expected_order = sorted(ranked, key=lambda f: (hashlib.sha256(f"20261113117|{f['source_family_id']}".encode()).hexdigest(), f['source_family_id']))
    require(ranked == expected_order, 'Frozen SHA256 priority changed')
    expected = {f'P{i:03d}': f['source_family_id'] for i, f in enumerate(ranked, 1)}
    require(all(f['response_id'] == f['review_id'] == f'P{i:03d}' for i, f in enumerate(ranked, 1)), 'Frozen review ID mismatch')
    excluded = set(load(pool / 'excluded_previous_families.json')['source_family_ids'])
    require(not (excluded & {f['source_family_id'] for f in ranked}), 'Previous source family entered new pool')
    a, b = read_reviews(a_path, expected), read_reviews(b_path, expected)
    reviews = {'a': {'path': 'source_reviews/source_review_a.jsonl', 'sha256': sha(a_path)},
               'b': {'path': 'source_reviews/source_review_b.jsonl', 'sha256': sha(b_path)}}
    disposition, eligible = [], []
    for family in ranked:
        rid = family['response_id']
        aa, bb = assess(a[rid], family), assess(b[rid], family)
        accepted = aa['accepted'] and bb['accepted']
        disposition.append({'response_id': rid, 'source_family_id': family['source_family_id'],
                            'candidate_rank': family['candidate_rank'], 'source_eligible': accepted,
                            'raw_first_review_a': a[rid], 'raw_first_review_b': b[rid],
                            'review_a_assessment': aa, 'review_b_assessment': bb})
        if accepted:
            eligible.append(family)
    if len(eligible) < 30:
        print(json.dumps({'status': 'STOP_insufficient_source_valid_families', 'required_families': 30,
                          'strict_both_first_pass_families': len(eligible),
                          'candidate_families_reviewed': 50, 'solver_inference_permitted': False,
                          'first_review_sha256': {k: v['sha256'] for k, v in reviews.items()},
                          'output_created': False}, indent=2))
        return 2
    selected = []
    for slot, family in enumerate(eligible[:30], 1):
        row = copy.deepcopy(family)
        row.update({'status': 'accepted', 'source_validation_status': 'accepted',
                    'selection_slot': slot, 'analysis_role': 'replication',
                    'batch_block': (slot - 1) // 3 + 1, 'source_review_id': family['response_id'],
                    'source_review_references': copy.deepcopy(reviews)})
        selected.append(row)
    slots = {f['source_family_id']: f['selection_slot'] for f in selected}
    for row in disposition:
        row['selected'] = row['source_family_id'] in slots
        row['selection_slot'] = slots.get(row['source_family_id'])
        row['not_selected_reason'] = (None if row['selected'] else
            'strict_source_review_gate_failed' if not row['source_eligible'] else 'after_first30_in_frozen_priority')
    disposition_value = {'status': 'strict_first_review_disposition_no_overrides',
                         'selection_plan_sha256': PLAN_SHA, 'candidate_family_count': 50,
                         'strict_both_first_pass_family_count': len(eligible), 'selected_family_count': 30,
                         'review_streams': reviews, 'families': disposition}
    disposition_bytes = encode(disposition_value)
    selected_value = {'status': 'accepted_source_reviewed', 'cohort_id': 'p1-gap-replication-20261113',
                      'family_count': 30, 'variants_per_family': 4,
                      'selection_plan_sha256': PLAN_SHA,
                      'source_disposition_sha256': hashlib.sha256(disposition_bytes).hexdigest(),
                      'source_review_gate': 'strict_both_first_pass_no_overrides',
                      'no_solver_outputs_generated_or_inspected': True,
                      'scope': 'Single prospective replication cohort; two released P1 realizations vs separate numerical substitution and paraphrase target examples. No P2 or split.',
                      'human_source_validation': 'pending; two independent agent first reviews',
                      'families': selected}
    payloads = {'source_disposition.json': disposition_bytes, 'selected_data.json': encode(selected_value),
                'source_manifest.json': (pool / 'source_manifest.json').read_bytes(),
                'selection_plan.json': (pool / 'selection_plan.json').read_bytes(),
                'source_reviews/source_review_a.jsonl': a_path.read_bytes(),
                'source_reviews/source_review_b.jsonl': b_path.read_bytes()}
    for filename in ('candidate_families.json', 'source_review_packet.jsonl', 'excluded_previous_families.json',
                     'source_inventory.json', 'previous_candidate_families.json', 'POOL_PREPARATION_RECEIPT.json'):
        payloads['source_inputs/' + filename] = (pool / filename).read_bytes()
    out.mkdir(parents=True)
    for name, data in payloads.items():
        target = out / name; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(data)
    receipt = {'status': 'exact30_source_gate_passed_before_solver_inference',
               'eligible_count': len(eligible), 'selected_count': 30,
               'selected_review_ids': [f['response_id'] for f in selected],
               'selected_source_family_ids': [f['source_family_id'] for f in selected],
               'review_streams': reviews, 'source_selection_plan_sha256': PLAN_SHA,
               'finalizer_sha256': sha(Path(__file__).resolve()),
               'source_inputs_and_review_bytes_preserved': True,
               'source_questions_and_gold_values_unchanged': True,
               'no_coordinator_override': True, 'no_solver_outputs_used': True,
               'sha256': {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}}
    with (out / 'SOURCE_GATE_RECEIPT.json').open('x') as f:
        json.dump(receipt, f, indent=2); f.write('\n')
    print(json.dumps(receipt, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pool-dir', type=Path, default=HERE)
    ap.add_argument('--review-a', type=Path, required=True)
    ap.add_argument('--review-b', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()
    raise SystemExit(finalize(args.pool_dir, args.review_a, args.review_b, args.output_dir))


if __name__ == '__main__':
    main()
