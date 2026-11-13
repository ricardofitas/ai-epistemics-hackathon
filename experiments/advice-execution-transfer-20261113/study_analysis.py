"""Exact source admission, advice translation and score projections for this study."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import re


def load(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def number(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    # This exact, pre-frozen codec accepts decimal/scientific numbers or one fraction.
    atom = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
    if not re.fullmatch(atom + '(?:/' + atom + ')?', value):
        return None
    try:
        if '/' in value:
            numerator, denominator = value.split('/')
            return Fraction(numerator) / Fraction(denominator)
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def strict_complete(record):
    return (record.get('completed_nonempty') is True and record.get('response_status') == 'completed'
            and record.get('http_status') == 200 and record.get('terminal_event_seen') is True
            and record.get('stream_incomplete') is False and record.get('used_delta_fallback') is False
            and record.get('transport_error') is None)


def response_json(record):
    if not strict_complete(record):
        return None
    try:
        value = json.loads(record['output_text'])
    except (ValueError, KeyError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def source_admission(directory):
    directory = Path(directory)
    records = {r['trial_id']: r for r in lines(directory / 'reviews/responses.jsonl')}
    candidates = load(directory / 'transfer/candidate_families.json')
    dispositions, admitted = [], []
    for family in candidates:
        decisions = []
        for reviewer in (1, 2):
            trial = f"{family['review_id']}-R{reviewer}"
            review = response_json(records.get(trial, {}))
            reasons = []
            if review is None:
                reasons.append('review_incomplete_or_invalid_json')
            else:
                if review.get('seed_clarity') != 'pass':
                    reasons.append('seed_not_strict_pass')
                if number(review.get('seed_answer')) is None or number(review.get('seed_answer')) != number(family['seed_answer']):
                    reasons.append('seed_answer_mismatch_or_unresolved')
                variants = review.get('variants')
                if not isinstance(variants, list) or len(variants) != 3 or {
                        v.get('id') for v in variants if isinstance(v, dict)} != {'numeric', 'paraphrase', 'added_operation'}:
                    reasons.append('variant_schema_invalid')
                else:
                    by_id = {v['id']: v for v in variants}
                    for original in family['variants']:
                        judged = by_id[original['id']]
                        if judged.get('clarity') != 'pass' or judged.get('transform_fit') != 'pass':
                            reasons.append(original['id'] + '_not_strict_pass')
                        derived, gold = number(judged.get('answer')), number(original['answer'])
                        if gold is None or derived is None or derived != gold:
                            reasons.append(original['id'] + '_answer_mismatch_or_unresolved')
            decisions.append({'reviewer': reviewer, 'trial_id': trial, 'passed': not reasons,
                              'reasons': reasons, 'first_review': review})
        passed = all(d['passed'] for d in decisions)
        dispositions.append({'family_id': family['family_id'], 'review_id': family['review_id'],
                             'admitted': passed, 'first_reviews': decisions})
        if passed:
            admitted.append(family)
    return {'candidate_count': len(candidates), 'admitted_count': len(admitted),
            'exclusions_are_not_counts_of_proven_gold_errors': True,
            'families': dispositions}, admitted


def bounds_json(lower, upper):
    return {'lower': str(lower), 'upper': str(upper),
            'lower_pp': float(100 * lower), 'upper_pp': float(100 * upper)}


def mean_bounds(values):
    if not values:
        return None
    return tuple(sum((value[j] for value in values), Fraction(0)) / len(values) for j in (0, 1))


def gap_from_families(rows, key, pair):
    a = mean_bounds([tuple(Fraction(str(v)) for v in r[key][pair[0]]) for r in rows])
    b = mean_bounds([tuple(Fraction(str(v)) for v in r[key][pair[1]]) for r in rows])
    return a[0] - b[1], a[1] - b[0]


def archived_bank(directory):
    families = lines(Path(directory) / 'replay_math.jsonl')
    pair = ['deepseek-v4-flash', 'gemma-4-31b-it']
    transformed = []
    for row in families:
        transformed.append({'family_id': row['family_id'], **row['variants'], 'target': {
            model: [sum(Fraction(str(row['variants'][key][model][j])) for key in ('numeric', 'paraphrase')) / 2
                    for j in (0, 1)] for model in pair}})
    target = gap_from_families(transformed, 'target', pair)
    bank = {'target': bounds_json(*target)}
    for variant in ('p1', 'p2'):
        gap = gap_from_families(transformed, variant, pair)
        bank[variant] = {'gap': bounds_json(*gap),
                         'distortion': bounds_json(gap[0] - target[1], gap[1] - target[0])}
    return bank


def quote_valid(value, text):
    return isinstance(value, str) and bool(value.strip()) and ' '.join(value.split()) in ' '.join(text.split())


def translation_analysis(directory):
    directory = Path(directory)
    records = {r['trial_id']: r for r in lines(directory / 'reviews/responses.jsonl')}
    packet = {r['item_id']: r for r in lines(directory / 'translation/packet.jsonl')}
    keys = lines(directory / 'translation/key.jsonl')
    allowed_variants = {'p1', 'p2', 'p1_p2', 'base', 'svamp', 'constructed', 'unresolved'}
    allowed_metrics = {'accuracy', 'drop_from_seed', 'retention', 'all_variants_correct', 'answer_equality', 'unresolved'}
    bank = archived_bank(directory)
    output = []
    for key in keys:
        item = packet[key['item_id']]
        reviews = []
        for reviewer in (1, 2):
            trial = f"{key['item_id']}-R{reviewer}"
            extraction = response_json(records.get(trial, {}))
            valid = (extraction is not None and extraction.get('variant') in allowed_variants
                     and extraction.get('metric') in allowed_metrics
                     and type(extraction.get('requires_seed')) is bool
                     and type(extraction.get('requires_new_items')) is bool
                     and isinstance(extraction.get('required_filters'), list)
                     and all(quote_valid(q, item['answer']) for q in extraction.get('required_filters', []))
                     and quote_valid(extraction.get('variant_quote'), item['answer'])
                     and quote_valid(extraction.get('metric_quote'), item['answer']))
            reviews.append({'reviewer': reviewer, 'trial_id': trial, 'valid': bool(valid), 'extraction': extraction})
        both = all(r['valid'] for r in reviews)
        fields = ('variant', 'metric', 'requires_seed', 'requires_new_items')
        agreement = both and all(reviews[0]['extraction'][k] == reviews[1]['extraction'][k] for k in fields)
        row = {**key, 'both_reviews_valid': both, 'strict_execution_agreement': agreement,
               'first_reviews': reviews, 'original_answer_sha256': item['answer_sha256']}
        if agreement:
            plan = {k: reviews[0]['extraction'][k] for k in fields}
            plan['required_filters'] = sorted(set(q for r in reviews for q in r['extraction']['required_filters']))
            row['plan'] = plan
            variant = plan['variant']
            if plan['requires_new_items']:
                row['execution_status'] = 'requires_authored_and_validated_questions'
            elif plan['required_filters']:
                row['execution_status'] = 'requires_filter_definition_or_annotation'
            elif plan['requires_seed'] or plan['metric'] in ('drop_from_seed', 'retention'):
                row['execution_status'] = 'requires_seed_predictions_and_paired_rule'
            elif variant in ('p1', 'p2', 'p1_p2') and plan['metric'] == 'accuracy':
                row['execution_status'] = 'restricted_archived_resource_score_replay'
            elif variant == 'base':
                row['execution_status'] = 'base_resource_predictions_not_in_replay_bank'
            elif variant == 'svamp':
                row['execution_status'] = 'svamp_resource_predictions_not_in_replay_bank'
            else:
                row['execution_status'] = 'requires_metric_or_resource_resolution'
            # A resource-only projection is labeled separately from full plan execution.
            if variant in ('p1', 'p2', 'p1_p2'):
                options = [variant] if variant != 'p1_p2' else ['p1', 'p2']
                lows = [Fraction(bank[v]['distortion']['lower']) for v in options]
                highs = [Fraction(bank[v]['distortion']['upper']) for v in options]
                row['resource_projection'] = {
                    'scope': '30 archived families, same two solvers; original seed/drop/filters not executed',
                    'distortion': bounds_json(min(lows), max(highs))}
        else:
            row['execution_status'] = 'translation_disagreement_or_unresolved_review'
        output.append(row)
    missing = load(directory / 'translation/original_missing.json')
    for item in missing:
        output.append({'original_trial_id': item['trial_id'], 'model': item['model'],
                       'condition': item['condition'], 'repetition': item['repetition'],
                       'execution_status': 'original_advice_incomplete'})
    output.sort(key=lambda r: r['original_trial_id'])
    assert len(output) == 36
    (directory / 'advice_execution.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in output))
    return {'planned_original_advice': 36, 'complete_original_advice': 26,
            'valid_double_extractions': sum(r.get('both_reviews_valid', False) for r in output),
            'strict_agreement': sum(r.get('strict_execution_agreement', False) for r in output),
            'status_counts': dict(Counter(r['execution_status'] for r in output)),
            'resource_bank': bank,
            'condition_counts': {condition: dict(Counter(r['execution_status'] for r in output if r['condition'] == condition))
                                 for condition in sorted({r['condition'] for r in output})}}, output


def score_solver(record, gold):
    if not strict_complete(record):
        return (0, 1), 'capture_incomplete'
    text = record.get('output_text', '').strip()
    matches = re.findall(r'<answer>([^<>]+)</answer>', text)
    if len(matches) != 1 or not text.endswith('</answer>'):
        return (0, 1), 'answer_format_unresolved'
    parsed = number(matches[0])
    answer = number(gold)
    if parsed is None or answer is None:
        return (0, 1), 'answer_numeric_unresolved'
    correct = int(parsed == answer)
    return (correct, correct), 'correct' if correct else 'wrong'


def transfer_analysis(directory):
    directory = Path(directory)
    families = load(directory / 'solvers/admitted_families.json')
    if not families:
        return {'status': 'no_strictly_admitted_source_families', 'families': 0}
    protocol = load(directory / 'transfer/protocol.json')
    manifest = lines(directory / 'solvers/manifest.jsonl')
    records = {r['trial_id']: r for r in lines(directory / 'solvers/responses.jsonl')}
    scores, labels, rows = {}, Counter(), []
    for request in manifest:
        key = (request['family_id'], request['variant'], request['request_payload']['model'])
        value, label = score_solver(records.get(request['trial_id'], {}), request['gold'])
        scores[key] = tuple(Fraction(v) for v in value)
        labels[label] += 1
        rows.append({'trial_id': request['trial_id'], 'family_id': key[0], 'variant': key[1],
                     'model': key[2], 'score': list(value), 'label': label})
    (directory / 'solver_scores.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    pair_results = []
    for label, pair in [('primary', protocol['primary_pair']), ('secondary', protocol['secondary_pair'])]:
        per_family = []
        for family in families:
            fid = family['family_id']
            def model_gap(variant):
                a, b = scores[fid, variant, pair[0]], scores[fid, variant, pair[1]]
                return a[0] - b[1], a[1] - b[0]
            extra = model_gap('added_operation')
            targets = [model_gap(k) for k in ('numeric', 'paraphrase')]
            target = tuple((targets[0][j] + targets[1][j]) / 2 for j in (0, 1))
            per_family.append((extra[0] - target[1], extra[1] - target[0]))
        distortion = mean_bounds(per_family)
        randomizer = random.Random(protocol['bootstrap']['seed'])
        bootstrap_low, bootstrap_high = [], []
        for _ in range(protocol['bootstrap']['replicates']):
            sample = [per_family[randomizer.randrange(len(per_family))] for _ in per_family]
            lower, upper = mean_bounds(sample)
            bootstrap_low.append(float(lower)); bootstrap_high.append(float(upper))
        bootstrap_low.sort(); bootstrap_high.sort()
        def quantile(values, p):
            position = (len(values) - 1) * p
            low = int(position); high = min(low + 1, len(values) - 1)
            return values[low] + (values[high] - values[low]) * (position - low)
        pair_results.append({'role': label, 'pair': pair, 'distortion': bounds_json(*distortion),
                             'finite_cohort_lower_at_least_10pp': distortion[0] >= Fraction(1, 10),
                             'descriptive_family_bootstrap_envelope_pp': [100 * quantile(bootstrap_low, .025),
                                                                         100 * quantile(bootstrap_high, .975)],
                             'per_family': [{'family_id': family['family_id'], **bounds_json(*value)}
                                            for family, value in zip(families, per_family)]})
    accuracy = {}
    for model in protocol['solvers']:
        accuracy[model] = {}
        for variant in ('numeric', 'paraphrase', 'added_operation'):
            accuracy[model][variant] = bounds_json(*mean_bounds([scores[f['family_id'], variant, model] for f in families]))
    return {'status': 'complete_fixed_cohort_analysis', 'families': len(families), 'planned_solver_calls': len(manifest),
            'recorded_solver_calls': len(records), 'labels': dict(labels), 'accuracy': accuracy, 'pairs': pair_results,
            'scope': protocol['scope']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    translation, advice_rows = translation_analysis(args.directory)
    transfer = transfer_analysis(args.directory)
    dump(args.directory / 'analysis_summary.json', {'translation': translation, 'transfer': transfer})
    report = ['# Advice execution and transformation transfer', '',
              'Two independent model readers translated the archived advice without author, condition or solver scores.',
              'The coordinator knew prior results. External human validation remains pending.', '',
              f"All 36 archived attempts are retained. Strict double-reader agreement on {translation['strict_agreement']}/26 completed answers.", '',
              '| Execution status | Advice attempts |', '|---|---:|']
    report.extend(f'| {status} | {count} |' for status, count in translation['status_counts'].items())
    report.extend(['', 'Resource-only projections are distinct from executing seed-based drops, filters or full 50-instance plans.',
                   'P1/P2 mixing is unspecified in these answers, so its bounds range over all common convex mixtures.', '',
                   '## New source-family transfer', '', f"Admitted source families: {transfer['families']}."])
    for pair in transfer.get('pairs', []):
        result = pair['distortion']
        report.append(f"{pair['role']} pair {pair['pair']}: gap distortion {result['lower_pp']:.2f} to {result['upper_pp']:.2f} pp; "
                      f"descriptive family resampling {pair['descriptive_family_bootstrap_envelope_pp']} pp.")
    report.extend(['', 'The transfer uses released GSM-Plus adding-operation items. It does not substitute these for prior Apple recommendations.',
                   'Every source exclusion, invalid annotation, incomplete call and unknown correctness is retained.',
                   'The sample shares the GSM8K parent corpus with earlier studies. No broad domain generalization is established.'])
    (args.directory / 'RESULTS.md').write_text('\n'.join(report) + '\n')
    print(json.dumps({'translation_agreement': translation['strict_agreement'],
                      'admitted_families': transfer['families'], 'solver_labels': transfer.get('labels', {})}))


if __name__ == '__main__':
    main()
