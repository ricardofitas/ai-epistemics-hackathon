#!/usr/bin/env python3
"""Offline, frozen-input scoring consequences for the Q48 WSC recast.

No network or inference. Official coreference gold is not official NLI gold.
Use --self-test for fabricated fixtures only. Actual analysis requires explicit
externally checked Git/time/manifest/protocol provenance and a new output folder.
"""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys

import numpy as np

MODELS = ['gemma-4-31b-it', 'glm-5.2', 'qwen3.8-27b', 'deepseek-v4-flash']
LABELS = {'entailment', 'neutral', 'contradiction'}
ROLES = ['selection', 'confirmation']
RULES = ['literal_bad', 'repaired_binary']
METRICS = ['paired', 'items']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode()


def index(values, field):
    result = {v[field]: v for v in values}
    require(len(values) == len(result), 'Duplicate ' + field)
    return result


def instant(value):
    x = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(x.tzinfo is not None, 'Explicit time zone required')
    return x


def parse_predictions(text, expected):
    """Whole JSON, or exactly one outer code fence; never salvage a fragment."""
    text = text.strip()
    if text.startswith('```'):
        m = re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```', text, flags=re.S | re.I)
        require(m is not None, 'Invalid outer JSON fence')
        text = m.group(1).strip()
    def no_duplicates(pairs):
        out = {}
        for k, v in pairs:
            require(k not in out, 'Duplicate JSON object key')
            out[k] = v
        return out
    value = json.loads(text, object_pairs_hook=no_duplicates,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    require(isinstance(value, dict) and set(value) == {'predictions'}, 'Expected only predictions object')
    entries = value['predictions']
    require(isinstance(entries, list), 'Predictions must be a list')
    result = {}
    for r in entries:
        require(isinstance(r, dict) and set(r) == {'id', 'label'}, 'Prediction must have only id/label')
        require(isinstance(r['id'], str) and r['id'] not in result, 'Missing/duplicate prediction ID')
        require(isinstance(r['label'], str), 'Label must be a string')
        label = r['label'].casefold()
        require(label in LABELS, 'Invalid NLI label')
        result[r['id']] = label
    require(set(result) == set(expected) and len(entries) == len(expected), 'Unexpected or missing task IDs')
    return result


def correctness(pred, variant, rule):
    if pred is None:
        return None
    if variant == 'gold':
        return int(pred == 'entailment')
    return int(pred == 'contradiction' if rule == 'literal_bad' else pred != 'entailment')


def pair_bounds(positive, negative, rule):
    a = correctness(positive, 'gold', rule)
    b = correctness(negative, 'non_gold', rule)
    if a == 0 or b == 0:
        return (0.0, 0.0)
    if a == b == 1:
        return (1.0, 1.0)
    return (0.0, 1.0)


def distortion_bounds(positive, negative):
    # Difference of the two pair scores using the SAME unknown predictions.
    if (positive is not None and positive != 'entailment') or negative in {'contradiction', 'entailment'}:
        return (0.0, 0.0)
    if positive == 'entailment' and negative == 'neutral':
        return (1.0, 1.0)
    return (0.0, 1.0)


def f1_pair(targets, predictions, classes):
    values = []
    for c in classes:
        tp = sum(t == c and p == c for t, p in zip(targets, predictions))
        fp = sum(t != c and p == c for t, p in zip(targets, predictions))
        fn = sum(t == c and p != c for t, p in zip(targets, predictions))
        d = 2 * tp + fp + fn
        values.append(2 * tp / d if d else 0.0)
    return sum(values) / len(values)


def bounds_summary(lower, upper, fully_captured):
    lo, hi = float(np.mean(lower)), float(np.mean(upper))
    return {'lower': lo, 'upper': hi,
            'identified_value': lo if np.array_equal(lower, upper) else None,
            'complete_value': lo if fully_captured else None,
            'unit_count': len(lower), 'fully_captured': bool(fully_captured)}


def cluster_draws(passages, seed, draws):
    families = sorted({p['family_id'] for p in passages})
    require(families, 'Empty cohort')
    membership = np.array([[int(p['family_id'] == f) for p in passages] for f in families], dtype=np.int64)
    rng = np.random.default_rng(seed)
    # Multinomial family multiplicities equal drawing F source clusters with replacement.
    counts = rng.multinomial(len(families), np.full(len(families), 1 / len(families)), size=draws)
    weights = counts @ membership
    return families, weights


def ci(values, weights):
    require(len(values) == weights.shape[1], 'Bootstrap unit mismatch')
    averages = (weights @ np.asarray(values, dtype=float)) / weights.sum(axis=1)
    return [float(x) for x in np.quantile(averages, [.025, .975], method='linear')]


def order_from_bounds(values):
    max_lower = max(v['lower'] for v in values.values())
    possible = sorted(m for m, v in values.items() if v['upper'] >= max_lower)
    robust = [m for m, v in values.items() if all(m == o or v['lower'] > w['upper'] for o, w in values.items())]
    return {'possible_winners': possible, 'robust_unique_winner': robust[0] if len(robust) == 1 else None,
            'tie_or_unresolved': len(robust) != 1,
            'meaning': 'Winner sets include ties and all candidates compatible with missing-label bounds.'}


def difference_bounds(a, b):
    return [a['lower'] - b['upper'], a['upper'] - b['lower']]


def strict_sign(interval):
    return 1 if interval[0] > 0 else (-1 if interval[1] < 0 else 0)


def compute_scores(protocol, key, predictions):
    models = protocol['models']
    grouped = defaultdict(dict)
    for t in key:
        grouped[t['passage_id']][t['variant']] = t
    passages = []
    for pid, pair in sorted(grouped.items()):
        g, n = pair['gold'], pair['non_gold']
        passages.append({'passage_id': pid, 'family_id': g['family_id'],
                         'analysis_role': g['analysis_role'], 'gold_id': g['task_id'], 'non_gold_id': n['task_id']})
    missing = {m: sum(predictions[m].get(t['task_id']) is None for t in key) for m in models}
    complete_matrix = not any(missing.values())
    by_cohort, arrays = {}, {}
    draws = protocol['uncertainty']['draws']
    seed = protocol['uncertainty']['seed']
    for cnum, role in enumerate(['selection', 'confirmation', 'all']):
        cohort = [p for p in passages if role == 'all' or p['analysis_role'] == role]
        families, weights = cluster_draws(cohort, seed + cnum, draws)
        # Secondary item accuracy has two tasks per passage; its cluster contribution
        # is the within-passage mean, yielding exactly the same item-weighted average.
        cohort_output = {'passages': len(cohort), 'families': len(families), 'candidates': {},
                         'bootstrap': {'draws': draws, 'seed': seed + cnum, 'unit': 'source family',
                                       'interval': 'two-sided 95% percentile, NumPy linear quantiles'}}
        for m in models:
            candidate = {'missing_items': sum(predictions[m].get(tid) is None for p in cohort for tid in [p['gold_id'], p['non_gold_id']]),
                         'rules': {}}
            complete = candidate['missing_items'] == 0
            for rule in RULES:
                lo, hi, ilo, ihi = [], [], [], []
                targets, preds, corrected_preds = [], [], []
                for p in cohort:
                    a, b = predictions[m].get(p['gold_id']), predictions[m].get(p['non_gold_id'])
                    l, u = pair_bounds(a, b, rule)
                    lo.append(l); hi.append(u)
                    item_values = [correctness(a, 'gold', rule), correctness(b, 'non_gold', rule)]
                    ilo.append(sum(x if x is not None else 0 for x in item_values) / 2)
                    ihi.append(sum(x if x is not None else 1 for x in item_values) / 2)
                    targets.extend(['entailment', 'contradiction'])
                    preds.extend([a, b])
                    corrected_preds.extend(['entailment' if v == 'entailment' else ('contradiction' if v is not None else None) for v in [a, b]])
                akey = (role, m, rule)
                arrays[akey] = {'paired_lower': np.array(lo), 'paired_upper': np.array(hi),
                                'items_lower': np.array(ilo), 'items_upper': np.array(ihi),
                                'complete': complete, 'weights': weights}
                result = {metric: bounds_summary(arrays[akey][metric + '_lower'], arrays[akey][metric + '_upper'], complete) for metric in METRICS}
                for metric in METRICS:
                    result[metric]['conditional_cluster_ci95'] = ci(arrays[akey][metric + '_lower'], weights) if complete else None
                result['paired']['unit_kind'] = 'source passage pair'
                result['items']['unit_kind'] = 'ordered NLI task'
                result['items']['unit_count'] = 2 * len(cohort)
                result['macro_f1_complete'] = f1_pair(targets, preds if rule == 'literal_bad' else corrected_preds, ['entailment', 'contradiction']) if complete else None
                result['macro_f1_classes'] = ['entailment', 'contradiction'] if rule == 'literal_bad' else ['entailment', 'non_entailment']
                candidate['rules'][rule] = result
            lower, upper = zip(*(distortion_bounds(predictions[m].get(p['gold_id']), predictions[m].get(p['non_gold_id'])) for p in cohort))
            dist = bounds_summary(np.array(lower), np.array(upper), complete)
            dist['conditional_cluster_ci95'] = ci(lower, weights) if complete else None
            dist['interpretation'] = 'Paired-score repair-minus-literal difference on identical predictions. Nonnegativity is expected by construction.'
            candidate['paired_score_distortion'] = dist
            cohort_output['candidates'][m] = candidate
        cohort_output['rankings'] = {metric: {rule: order_from_bounds({m: cohort_output['candidates'][m]['rules'][rule][metric] for m in models}) for rule in RULES} for metric in METRICS}
        comparisons = []
        for a, b in itertools.combinations(models, 2):
            result = {'candidate_a': a, 'candidate_b': b, 'metrics': {}}
            for metric in METRICS:
                comparison = {}
                for rule in RULES:
                    va = cohort_output['candidates'][a]['rules'][rule][metric]
                    vb = cohort_output['candidates'][b]['rules'][rule][metric]
                    da = arrays[(role, a, rule)][metric + '_lower']
                    db = arrays[(role, b, rule)][metric + '_lower']
                    comparison[rule] = {'a_minus_b_bounds': difference_bounds(va, vb),
                                        'complete_difference': va['complete_value'] - vb['complete_value'] if va['complete_value'] is not None and vb['complete_value'] is not None else None,
                                        'conditional_cluster_ci95': ci(da - db, weights) if va['fully_captured'] and vb['fully_captured'] else None}
                badsign = strict_sign(comparison['literal_bad']['a_minus_b_bounds'])
                goodsign = strict_sign(comparison['repaired_binary']['a_minus_b_bounds'])
                comparison['strict_reversal_robust_to_missing_bounds'] = bool(badsign * goodsign == -1)
                comparison['complete_strict_reversal'] = bool(badsign * goodsign == -1) if arrays[(role, a, 'literal_bad')]['complete'] and arrays[(role, b, 'literal_bad')]['complete'] else None
                comparison['rule'] = 'Strict opposite nonzero orderings; ties/overlapping bounds are not reversals.'
                result['metrics'][metric] = comparison
            comparisons.append(result)
        cohort_output['all_six_pairwise_comparisons'] = comparisons
        by_cohort[role] = cohort_output
    select = by_cohort['selection']['rankings']['paired']
    badwinner = select['literal_bad']['robust_unique_winner']
    goodwinner = select['repaired_binary']['robust_unique_winner']
    choice = {'literal_selected': badwinner, 'repaired_selected': goodwinner,
              'selection_metric': 'paired source-passage correctness',
              'selection_policy_fidelity': 'Registered unique raw paired-score abstraction, not the complete Q48 significantly-higher-or-macroF1 decision policy. No significance gate is asserted met.',
              'evaluation_metric': 'repaired binary paired correctness on confirmation only',
              'status': 'indeterminate_tie_or_missing_bounds', 'bounds': None,
              'complete_signed_effect': None, 'conditional_cluster_ci95': None,
              'fixed_winners_no_bootstrap_reselection': True,
              'eligible_primary_consequence': bool(complete_matrix and badwinner is not None and goodwinner is not None)}
    if badwinner is not None and goodwinner is not None:
        if badwinner == goodwinner:
            choice.update({'status': 'same_selected_candidate_zero_effect', 'bounds': [0.0, 0.0],
                           'complete_signed_effect': 0.0 if complete_matrix else None,
                           'conditional_cluster_ci95': [0.0, 0.0] if complete_matrix else None})
        else:
            conf = by_cohort['confirmation']['candidates']
            a, b = conf[goodwinner]['rules']['repaired_binary']['paired'], conf[badwinner]['rules']['repaired_binary']['paired']
            complete = a['fully_captured'] and b['fully_captured']
            choice.update({'status': 'unique_winners_complete_confirmation' if complete else 'unique_winners_missing_confirmation_bounds',
                           'bounds': difference_bounds(a, b),
                           'complete_signed_effect': a['complete_value'] - b['complete_value'] if complete else None,
                           'conditional_cluster_ci95': ci(arrays[('confirmation', goodwinner, 'repaired_binary')]['paired_lower'] - arrays[('confirmation', badwinner, 'repaired_binary')]['paired_lower'], arrays[('confirmation', goodwinner, 'repaired_binary')]['weights']) if complete else None})
    threeway = {}
    confident = [t for t in key if t['analyst_three_way_target'] in LABELS]
    for m in models:
        known = [(t, predictions[m].get(t['task_id'])) for t in confident]
        correct = sum(p == t['analyst_three_way_target'] for t, p in known if p is not None)
        miss = sum(p is None for _, p in known)
        threeway[m] = {'eligible_analyst_items': len(confident), 'missing_items': miss,
                       'correct_observed': correct, 'score_bounds': [correct / len(confident), (correct + miss) / len(confident)] if confident else None,
                       'complete_accuracy': correct / len(confident) if confident and not miss else None,
                       'official_three_way_gold': False}
    return {'primary_full_candidate_matrix_complete': complete_matrix,
            'primary_status': 'complete' if complete_matrix else 'incomplete_all_four_candidates_not_fully_captured',
            'missing_items_by_candidate': missing, 'cohorts': by_cohort,
            'fixed_selection_confirmation_consequence': choice,
            'secondary_analyst_three_way_sensitivity': threeway,
            'interpretation': 'Fixed source slice and requested aliases only. Missing bounds are partial identification, not imputed semantic errors. Cluster intervals are conditional on this curated sample and observed fixed winners; shared-request context dependence across source families is not separately estimated. No representative prevalence, significance, immutable weights or real-user harm claim.'}


def audit_inputs(directory, freeze_commit, freeze_time, manifest_sha256, protocol_sha256):
    root = directory
    require(re.fullmatch('[0-9a-f]{40}', freeze_commit) is not None, 'Invalid externally checked Git freeze SHA')
    frozen_at = instant(freeze_time)
    require(sha(root / 'manifest.jsonl') == manifest_sha256, 'Frozen manifest hash mismatch')
    require(sha(root / 'protocol.json') == protocol_sha256, 'Frozen protocol hash mismatch')
    protocol = load(root / 'protocol.json')
    require(protocol['models'] == MODELS, 'Changed four predeclared candidate configurations')
    require(sha(Path(__file__)) == protocol['analysis_sha256'], 'Executing analyzer is not protocol-pinned')
    common_path = root.parent / 'methods/capture_audit_source.py'
    require(sha(common_path) == protocol['capture_audit_source_sha256'], 'Capture-audit source changed')
    runner = root.parent / 'methods/run_adaption_stream_pilot.py'
    require(sha(runner) == protocol['runner_sha256'], 'Frozen runner changed')
    for name, expected in protocol['hashes'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe protocol artifact path')
        require(sha(root / name) == expected, 'Frozen artifact hash mismatch: ' + name)
    sem_name = protocol['final_semantic_eligibility_filename']
    require(not Path(sem_name).is_absolute() and '..' not in Path(sem_name).parts, 'Unsafe semantic artifact path')
    require(sha(root / sem_name) == protocol['final_semantic_eligibility_sha256'], 'Final pre-output semantic decisions changed')
    selected = load(root / 'selected_data.json')
    source_passages = index(selected['items'], 'passage_id')
    semantic = load(root / sem_name)
    semantic_decisions = index(semantic['rows'], 'review_id')
    split_record = load(root / 'source_split.json')
    require(split_record['all_semantic_decisions'] == semantic['rows'], 'Split/source semantic decisions differ')
    require(set(split_record['selected_review_ids']) == {p['source_review_id'] for p in source_passages.values()}, 'Selected semantic source IDs differ')
    for source in source_passages.values():
        decision = semantic_decisions[source['source_review_id']]
        require(decision['eligible'] is True and decision['positive_entailment'] == 'yes' and decision['negative_not_entailed'] == 'yes', 'Unvalidated semantic source inclusion')
        require(decision['negative_three_way'] == source['analyst_negative_three_way'], 'Analyst-only sensitivity label changed')
        require(split_record['clustering']['family_mapping'][source['source_review_id']] == source['family_id'], 'Source family differs from frozen cluster record')
        require(split_record['family_roles'][source['family_id']] == source['analysis_role'], 'Source family role differs from split')
        for field, label in [('source_positive_record', True), ('source_negative_record', False)]:
            entry = source[field]
            require(hashlib.sha256(entry['raw_line_utf8'].encode()).hexdigest() == entry['raw_line_sha256'], 'Raw WSC source line hash mismatch')
            require(json.loads(entry['raw_line_utf8']) == entry['record'], 'Raw WSC source line differs from decoded record')
            require(entry['record']['label'] is label and entry['record']['text'] == source['premise'], 'Original coreference labels/text changed')
    task_key = load(root / 'task_key.json')['rows']
    tasks = index(task_key, 'task_id')
    require(len(tasks) == 2 * len(source_passages), 'Each passage requires two unique tasks')
    family_roles = {}
    by_passage = defaultdict(list)
    for task in task_key:
        pid = task['passage_id']
        require(pid in source_passages, 'Unknown source passage in key')
        source = source_passages[pid]
        require(task['analysis_role'] in ROLES and task['analysis_role'] == source['analysis_role'], 'Task/split mismatch')
        require(task['family_id'] == source['family_id'], 'Task/source family mismatch')
        require(task['source_review_id'] == source['source_review_id'], 'Source semantic identity mismatch')
        require(task['variant'] in {'gold', 'non_gold'}, 'Invalid source variant')
        require(task['binary_target'] == ('entailment' if task['variant'] == 'gold' else 'non_entailment'), 'Invalid binary key')
        require(task['literal_advice_target'] == ('entailment' if task['variant'] == 'gold' else 'contradiction'), 'Literal advice key changed')
        require(task['analyst_three_way_target'] in LABELS | {'uncertain'}, 'Invalid analyst-only target')
        require(task['analyst_three_way_target'] == ('entailment' if task['variant'] == 'gold' else source['analyst_negative_three_way']), 'Sensitivity label differs from source-only decision')
        require(source.get('official_nli_gold') is False, 'Analyst recast cannot become official NLI gold')
        require(source['analyst_positive_entailment'] == 'yes' and source['analyst_negative_not_entailed'] == 'yes', 'Unvalidated binary source item')
        family = task['family_id']
        require(family not in family_roles or family_roles[family] == task['analysis_role'], 'Source family crosses selection/confirmation')
        family_roles[family] = task['analysis_role']
        by_passage[pid].append(task)
    require(set(by_passage) == set(source_passages), 'Source passage coverage differs')
    require(all({t['variant'] for t in v} == {'gold', 'non_gold'} and len(v) == 2 for v in by_passage.values()), 'Malformed passage pair')
    require(protocol['source_passages'] == len(source_passages) and protocol['source_families'] == len(family_roles), 'Protocol/source counts changed')
    require(protocol['split']['passages'] == dict(Counter(p['analysis_role'] for p in source_passages.values())), 'Protocol split counts changed')
    require(protocol['uncertainty']['draws'] == 10000 and protocol['uncertainty']['seed'] == 2026111323, 'Bootstrap specification changed')
    jobs = rows(root / 'manifest.jsonl')
    jobs_by_id = index(jobs, 'trial_id')
    require(len(jobs) == protocol['request_plan']['requests'], 'Planned call count mismatch')
    seen = set()
    all_instructions = set()
    for job in jobs:
        m = job['requested_model']
        require(m in MODELS and job['request_payload']['model'] == m, 'Unplanned candidate/model payload')
        payload = job['request_payload']
        require(payload['temperature'] == 0 and payload['max_output_tokens'] == 8192 and payload['stream'] is True, 'Changed classifier controls')
        require(payload['tools'] == [] and payload['tool_choice'] == 'none' and payload['agentic_memory'] is False and payload['store'] is False and 'previous_response_id' not in payload, 'Tools/history controls changed')
        require(hashlib.sha256(canonical(payload)).hexdigest() == job['request_sha256'], 'Manifest canonical wire mismatch')
        require(isinstance(payload.get('instructions'), str) and payload['instructions'], 'Missing common classifier instruction')
        all_instructions.add(payload['instructions'])
        inputs = json.loads(payload['input'])
        require(isinstance(inputs, list) and [v['id'] for v in inputs] == job['task_ids'], 'Input IDs differ from manifest')
        require(len(set(job['task_ids'])) == len(job['task_ids']), 'Duplicate task within a batch')
        require(job['batch_role'] in ROLES, 'Unknown batch role')
        require(set(job['passage_ids']) == {tasks[t]['passage_id'] for t in job['task_ids']}, 'Batch source passage IDs differ')
        for item in inputs:
            require(set(item) == {'id', 'premise', 'hypothesis'}, 'Source/target metadata in classifier input')
            t = tasks[item['id']]
            require(t['analysis_role'] == job['batch_role'], 'Selection and confirmation share one request')
            source = source_passages[t['passage_id']]
            require(item['premise'] == source['premise'] and item['hypothesis'] == source[t['variant'] + '_replacement_hypothesis'], 'Model-facing source text changed')
            require((m, item['id']) not in seen, 'Duplicate candidate/task request')
            seen.add((m, item['id']))
        require(all({t['task_id'] for t in by_passage[pid]} <= set(job['task_ids']) for pid in job['passage_ids']), 'Split one paired source across batches')
    require(len(all_instructions) == 1, 'Classifier instruction varies across candidates')
    require(seen == set(itertools.product(MODELS, tasks)), 'Missing planned candidate/task classifications')
    require(protocol['request_plan']['ordered_classifications_per_model'] == len(tasks) and protocol['request_plan']['ordered_classifications_total'] == len(seen), 'Protocol classification allocation mismatch')
    spec = importlib.util.spec_from_file_location('frozen_wsc_capture_audit', common_path)
    common = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(common)
    captures_list = rows(root / 'responses.jsonl')
    captures = index(captures_list, 'trial_id')
    require(set(captures) == set(jobs_by_id), 'Missing or unplanned raw captures')
    receipt = load(root / 'run_metadata.json')
    require(receipt['requested'] == len(jobs) and receipt['recorded'] == len(jobs) and receipt['retries'] == 0, 'Run receipt differs from frozen allocation')
    predictions = {m: {tid: None for tid in tasks} for m in MODELS}
    trials, item_rows = [], []
    for job in jobs:
        raw = captures[job['trial_id']]
        start_verified = False
        if not raw.get('local_capture_error'):
            require(instant(raw['started_utc']) > frozen_at and instant(raw['ended_utc']) >= instant(raw['started_utc']), 'Capture started before freeze or invalid times')
            start_verified = True
        checks = common.audit_capture(root, job, raw, frozen_at)
        content_ok = str(raw.get('response_content_type', '')).split(';')[0].strip().casefold() == 'text/event-stream'
        scorable = bool(checks['completion_verified'] and content_ok and raw.get('stream_json_error_count') == 0)
        parsed, error = {}, None
        if scorable:
            try:
                parsed = parse_predictions(raw['output_text'], job['task_ids'])
            except (ValueError, TypeError, KeyError) as exc:
                error = str(exc)
        else:
            error = 'operational_incomplete_or_protocol_quality_failure'
        valid = scorable and error is None
        if valid:
            predictions[job['requested_model']].update(parsed)
        trials.append({'trial_id': job['trial_id'], 'requested_model': job['requested_model'],
                       'returned_model': raw.get('returned_model'), 'batch_role': job['batch_role'],
                       'expected_tasks': len(job['task_ids']), 'capture_complete': bool(checks['completion_verified']),
                       'strict_capture_quality': scorable, 'prediction_batch_valid': valid, 'parse_or_capture_issue': error,
                       'capture_integrity': checks['capture_integrity'], 'http_status': raw.get('http_status'),
                       'start_verified_after_freeze': start_verified, 'started_utc': raw.get('started_utc'),
                       'ended_utc': raw.get('ended_utc'), 'local_capture_error': raw.get('local_capture_error'),
                       'provider_status': raw.get('response_status'), 'terminal_event': raw.get('terminal_event'),
                       'incomplete_details': raw.get('incomplete_details'), 'api_error': raw.get('api_error'),
                       'transport_error': raw.get('transport_error'), 'usage': raw.get('usage'),
                       'event_status_mismatch': checks.get('event_status_mismatch', False),
                       'malformed_sse_json_frames': raw.get('stream_json_error_count'),
                       'final_text_sha256': raw.get('output_text_sha256'), 'journal_sha256': raw.get('stream_journal_sha256')})
        for tid in job['task_ids']:
            item_rows.append({'requested_model': job['requested_model'], 'task_id': tid,
                              'trial_id': job['trial_id'], 'prediction': parsed.get(tid) if valid else None,
                              'prediction_batch_valid': valid, **{k: tasks[tid][k] for k in ['passage_id', 'family_id', 'analysis_role', 'variant', 'binary_target', 'literal_advice_target', 'analyst_three_way_target']}})
    integrity = {'freeze_commit': freeze_commit, 'freeze_utc': freeze_time,
                 'external_git_provenance_limit': 'Git/time/hash arguments are externally verified inputs; this analyzer performs no network lookup.',
                 'manifest_sha256': manifest_sha256, 'protocol_sha256': protocol_sha256,
                 'executing_analyzer_sha256': sha(Path(__file__)),
                 'candidate_configurations': MODELS, 'source_passages': len(source_passages),
                 'source_families': len(family_roles), 'requested_calls': len(jobs), 'recorded_calls': len(captures),
                 'valid_prediction_batches': sum(t['prediction_batch_valid'] for t in trials),
                 'complete_capture_batches': sum(t['capture_complete'] for t in trials),
                 'requested_classifications': len(seen), 'valid_classifications': sum(x['prediction'] is not None for x in item_rows),
                 'all_capture_hash_checks_pass': all(t['capture_integrity'] == 'verified' for t in trials),
                 'all_observed_starts_after_freeze': True,
                 'all_attempt_starts_verified_after_freeze': all(t['start_verified_after_freeze'] for t in trials),
                 'untimed_local_capture_failures': sum(not t['start_verified_after_freeze'] for t in trials),
                 'all_requests_attempted_once': True,
                 'no_model_replacement_or_retry': True,
                 'reported_usage_cost_sum': sum((t.get('usage') or {}).get('cost') or 0 for t in trials),
                 'billing_limit': 'Provider usage is not verified account debit, complete billing or USD.',
                 'human_review': 'pending; semantic first agent agreement is not external expert validation',
                 'input_hashes': {'selected_data': sha(root / 'selected_data.json'), 'task_key': sha(root / 'task_key.json'),
                                  'source_split': sha(root / 'source_split.json'), 'responses': sha(root / 'responses.jsonl'),
                                  'run_metadata': sha(root / 'run_metadata.json')}}
    return protocol, task_key, predictions, trials, item_rows, integrity


def analyze(directory, freeze_commit, freeze_time, manifest_sha256, protocol_sha256):
    protocol, key, predictions, trials, item_rows, integrity = audit_inputs(directory, freeze_commit, freeze_time, manifest_sha256, protocol_sha256)
    scores = compute_scores(protocol, key, predictions)
    scores['integrity'] = integrity
    scores['claim_limits'] = {'new_study': 'Exploratory consequence test of Q48; does not activate or alter the failed historical PAWS protocol.',
                            'labels': 'Analyst-validated binary recast under source intended-reading convention, not official WSC three-way NLI gold.',
                            'sample': 'Curated source-train slice, not held out from model pretraining or representative of all WSC.',
                            'causal_scope': 'Scoring-rule comparison on identical immutable predictions; no measured real-user adoption or harm.',
                            'statistical_scope': 'Conditional source-family bootstrap; no population/significance claim. Fixed selected winners, no bootstrap reselection.',
                            'model_identity': 'Requested/returned aliases do not establish immutable model weights.'}
    return scores, trials, item_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--freeze-commit')
    ap.add_argument('--freeze-time')
    ap.add_argument('--manifest-sha256')
    ap.add_argument('--protocol-sha256')
    ap.add_argument('--output-directory', type=Path)
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        from test_analyze_wsc import self_test
        print(json.dumps(self_test()))
        return
    require(all([args.freeze_commit, args.freeze_time, args.manifest_sha256, args.protocol_sha256]), 'Actual analysis requires all four externally checked freeze arguments')
    out = args.output_directory or args.directory / 'analysis'
    require(not out.exists(), 'Refusing to overwrite an analysis output directory')
    result, trials, predictions = analyze(args.directory, args.freeze_commit, args.freeze_time, args.manifest_sha256, args.protocol_sha256)
    out.mkdir(parents=True)
    (out / 'summary.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    (out / 'trial_integrity.json').write_text(json.dumps(trials, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    (out / 'item_predictions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in predictions))
    print(json.dumps({'status': result['primary_status'], 'calls': result['integrity']['recorded_calls'],
                      'valid_classifications': result['integrity']['valid_classifications'],
                      'missing': result['missing_items_by_candidate'],
                      'selection_confirmation': result['fixed_selection_confirmation_consequence']}))


if __name__ == '__main__':
    main()
