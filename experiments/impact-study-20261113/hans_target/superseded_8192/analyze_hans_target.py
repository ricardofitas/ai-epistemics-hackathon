#!/usr/bin/env python3
"""Offline HANS80 target analysis with fixed WSC choices and conservative missing bounds."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import numpy as np

LABELS = {'entailment', 'neutral', 'contradiction'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_predictions(text, expected):
    text = text.strip()
    if text.startswith('```'):
        match = re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```', text, re.S | re.I)
        require(match is not None, 'Invalid outer JSON fence')
        text = match.group(1)
    value = json.loads(text)
    require(isinstance(value, dict) and set(value) == {'predictions'}, 'Expected only predictions object')
    result = value['predictions']
    require(isinstance(result, list), 'Predictions must be an array')
    require(len(result) == len(expected), 'Missing or extra prediction row')
    parsed = {}
    for r in result:
        require(isinstance(r, dict) and set(r) == {'id', 'label'}, 'Expected only id and label')
        require(isinstance(r['id'], str) and r['id'] in expected and r['id'] not in parsed,
                'Unknown or duplicate task ID')
        require(isinstance(r['label'], str) and r['label'].casefold() in LABELS,
                'Unsupported NLI label')
        parsed[r['id']] = r['label'].casefold()
    require(set(parsed) == set(expected), 'Task coverage differs')
    return parsed


def binary_correct(prediction, gold):
    if prediction is None:
        return None
    require(prediction in LABELS and gold in {'entailment', 'non-entailment'}, 'Invalid label')
    target = 'entailment' if prediction == 'entailment' else 'non-entailment'
    return int(target == gold)


def bounds(values):
    require(len(values) > 0 and all(x in {None, 0, 1} for x in values), 'Invalid accuracy values')
    observed = [x for x in values if x is not None]
    n, missing = len(values), len(values) - len(observed)
    correct = sum(observed)
    return {'planned': n, 'valid': n - missing, 'missing': missing, 'observed_correct': correct,
            'accuracy_if_complete': correct / n if missing == 0 else None,
            'observed_accuracy_available_items_only': correct / len(observed) if observed else None,
            'full_cohort_accuracy_bounds': [correct / n, (correct + missing) / n]}


def difference_bounds(a, b, same_candidate=False):
    require(len(a) == len(b) and len(a) > 0, 'Different paired dimensions')
    if same_candidate:
        return [0.0, 0.0]
    lows, highs = [], []
    for x, y in zip(a, b):
        xa, xb = (0, 1) if x is None else (x, x)
        ya, yb = (0, 1) if y is None else (y, y)
        lows.append(xa - yb)
        highs.append(xb - ya)
    return [sum(lows) / len(a), sum(highs) / len(a)]


def quantile_interval(draws):
    return [float(v) for v in np.quantile(draws, [.025, .975], method='linear')]


def resampling_indices(task_rows, draws, seed):
    rng = np.random.default_rng(seed)
    blocks = []
    for subcase in sorted({r['subcase'] for r in task_rows}):
        positions = np.array([n for n, r in enumerate(task_rows) if r['subcase'] == subcase])
        blocks.append(rng.choice(positions, size=(draws, len(positions)), replace=True))
    return np.concatenate(blocks, axis=1)


def fixed_choice_result(wsc, models, correct, draws):
    choice = wsc.get('fixed_selection_confirmation_consequence', {})
    result = {'selection_source': 'Registered WSC selection paired score only; never HANS scores',
              'literal_selected': choice.get('literal_selected'),
              'repaired_selected': choice.get('repaired_selected'),
              'WSC_full_candidate_matrix_complete': wsc.get('primary_full_candidate_matrix_complete') is True,
              'status': 'indeterminate_WSC_selection_or_completeness', 'signed_target_effect': None,
              'conservative_effect_bounds': None, 'conditional_item_ci95': None,
              'policy_limit': 'This follows the registered raw paired-score winner rule, not every significance/macro-F1 option in the original advice.'}
    literal, repaired = result['literal_selected'], result['repaired_selected']
    if not (result['WSC_full_candidate_matrix_complete'] and
            choice.get('eligible_primary_consequence') is True and
            literal in models and repaired in models):
        return result
    a, b = correct[repaired], correct[literal]
    result['conservative_effect_bounds'] = difference_bounds(a, b, repaired == literal)
    if literal == repaired:
        result['status'] = 'same_fixed_candidate_zero_choice_effect'
        result['signed_target_effect'] = 0.0
        result['conditional_item_ci95'] = [0.0, 0.0]
    elif any(v is None for v in a + b):
        result['status'] = 'fixed_unique_WSC_choices_target_incomplete_bounds_only'
    else:
        delta = np.array(a, dtype=float) - np.array(b, dtype=float)
        result['status'] = 'fixed_unique_WSC_choices_selected_target_pair_complete'
        result['signed_target_effect'] = float(delta.mean())
        result['conditional_item_ci95'] = quantile_interval(delta[draws].mean(axis=1))
    result['target_complete_for_all_four_candidates'] = all(all(v is not None for v in correct[m]) for m in models)
    return result


def self_test():
    checks = []
    def check(name, condition):
        require(condition, 'Synthetic failure: ' + name)
        checks.append(name)
    def rejects(name, text, expected):
        try:
            parse_predictions(text, expected)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            checks.append(name)
            return
        raise AssertionError(name)
    check('binary neutral mapping', binary_correct('neutral', 'non-entailment') == 1)
    check('binary contradiction mapping', binary_correct('contradiction', 'non-entailment') == 1)
    check('entailment error', binary_correct('entailment', 'non-entailment') == 0)
    check('operational missing not semantic error', binary_correct(None, 'entailment') is None)
    check('missing bounds', bounds([1, 0, None, None])['full_cohort_accuracy_bounds'] == [.25, .75])
    check('all missing bounds', bounds([None, None])['full_cohort_accuracy_bounds'] == [0, 1])
    check('negative paired difference', difference_bounds([0, 0], [1, 1]) == [-1, -1])
    check('coupled same candidate', difference_bounds([None], [None], True) == [0, 0])
    check('incomplete paired bounds', difference_bounds([1, None], [None, 0]) == [0, 1])
    text = '{"predictions":[{"id":"a","label":"NEUTRAL"}]}'
    check('valid JSON casefold', parse_predictions(text, ['a']) == {'a': 'neutral'})
    check('single fence', parse_predictions('```json\n' + text + '\n```', ['a']) == {'a': 'neutral'})
    rejects('reject refusal', 'Sorry, cannot classify', ['a'])
    rejects('reject extra prose', text + '\nExplanation', ['a'])
    rejects('reject duplicate ID', '{"predictions":[{"id":"a","label":"neutral"},{"id":"a","label":"neutral"}]}', ['a','b'])
    rejects('reject extra ID', '{"predictions":[{"id":"x","label":"neutral"}]}', ['a'])
    rejects('reject unsupported label', '{"predictions":[{"id":"a","label":"non-entailment"}]}', ['a'])
    rejects('reject unregistered field', '{"predictions":[{"id":"a","label":"neutral","confidence":1}]}', ['a'])
    tasks = [{'subcase': 'a'}, {'subcase': 'a'}, {'subcase': 'b'}, {'subcase': 'b'}]
    draws = resampling_indices(tasks, 100, 9)
    check('stratified paired draws', np.all(draws[:, :2] < 2) and np.all(draws[:, 2:] >= 2))
    wsc = {'primary_full_candidate_matrix_complete': True,
           'fixed_selection_confirmation_consequence': {'eligible_primary_consequence': True,
             'literal_selected': 'bad', 'repaired_selected': 'repair'}}
    r = fixed_choice_result(wsc, ['bad','repair'], {'bad':[1,1,1,1], 'repair':[0,0,0,0]}, draws)
    check('signed negative effect retained', r['signed_target_effect'] == -1)
    r = fixed_choice_result(wsc, ['bad','repair'], {'bad':[1,0,1,0], 'repair':[1,0,1,0]}, draws)
    check('null effect retained', r['signed_target_effect'] == 0)
    wsc['fixed_selection_confirmation_consequence']['eligible_primary_consequence'] = False
    check('tied WSC choice not selected via target', fixed_choice_result(wsc, ['bad','repair'], {'bad':[0]*4,'repair':[1]*4}, draws)['signed_target_effect'] is None)
    return {'synthetic_checks': len(checks), 'status': 'PASS', 'checks': checks}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory', type=Path, nargs='?', default=Path(__file__).resolve().parent)
    ap.add_argument('--freeze-commit')
    ap.add_argument('--freeze-time')
    ap.add_argument('--manifest-sha256')
    ap.add_argument('--protocol-sha256')
    ap.add_argument('--output-directory', type=Path)
    ap.add_argument('--wsc-summary', type=Path)
    ap.add_argument('--wsc-summary-sha256')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test()))
        return
    require(bool(args.freeze_commit and re.fullmatch('[0-9a-f]{40}', args.freeze_commit)), 'Require externally verified Git freeze commit')
    require(args.freeze_time and args.manifest_sha256 and args.protocol_sha256, 'Require freeze time and exact frozen hashes')
    root = args.directory
    require(sha(root / 'protocol.json') == args.protocol_sha256, 'Frozen protocol mismatch')
    require(sha(root / 'manifest.jsonl') == args.manifest_sha256, 'Frozen manifest mismatch')
    protocol = load(root / 'protocol.json')
    for name, expected in protocol['hashes'].items():
        require(sha(root / name) == expected, 'Pinned artifact mismatch: ' + name)
    if 'analysis_sha256' in protocol:
        require(sha(Path(__file__).resolve()) == protocol['analysis_sha256'], 'Executing analyzer differs from frozen pin')
    source = load(root / 'selected_data.json')['items']
    key = load(root / 'task_key.json')['rows']
    source_by_id = {r['task_id']: r for r in source}
    key_by_id = {r['task_id']: r for r in key}
    require(len(source) == len(source_by_id) == len(key) == len(key_by_id) == 80, 'Target item/key coverage invalid')
    require(set(source_by_id) == set(key_by_id), 'Source/key IDs differ')
    for task_id, r in source_by_id.items():
        require({k:v for k,v in r.items() if k not in ['premise','hypothesis']} == key_by_id[task_id], 'Target key differs from pinned source')
    models = protocol['models']
    require(len(models) == len(set(models)) == 4, 'Wrong candidate set')
    manifest = rows(root / 'manifest.jsonl')
    aggregate = rows(root / 'responses.jsonl')
    captures = {r['trial_id']: r for r in aggregate}
    require(len(manifest) == len({r['trial_id'] for r in manifest}) == len(aggregate) == len(captures) == 40,
            'Missing/duplicate/unplanned attempt records')
    require(set(captures) == {r['trial_id'] for r in manifest}, 'Capture and manifest IDs differ')
    audit_path = root.parent / 'methods/capture_audit_source.py'
    if 'capture_audit_source_sha256' in protocol:
        require(sha(audit_path) == protocol['capture_audit_source_sha256'], 'Capture auditor differs from frozen pin')
    spec = importlib.util.spec_from_file_location('capture_audit_common', audit_path)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    freeze = audit.instant(args.freeze_time)
    receipt = load(root / 'run_metadata.json')
    require(receipt.get('requested') == receipt.get('recorded') == 40 and receipt.get('retries') == 0,
            'Run receipt differs from the one-attempt40-request allocation')
    predictions = {m:{} for m in models}
    quality = []
    for job in manifest:
        model = job['requested_model']
        require(model in models and job['request_payload']['model'] == model, 'Candidate changed')
        model_inputs = json.loads(job['request_payload']['input'])
        require({r['id'] for r in model_inputs} == set(job['task_ids']), 'Opaque input/task mismatch')
        for row in model_inputs:
            require(set(row) == {'id','premise','hypothesis'}, 'Unexpected model-facing metadata')
            s = source_by_id[row['id']]
            require(row['premise'] == s['premise'] and row['hypothesis'] == s['hypothesis'], 'Model input differs from frozen source')
        raw = captures[job['trial_id']]
        checks = audit.audit_capture(root, job, raw, freeze)
        capture_valid = (checks['completion_verified'] and
                         str(raw.get('response_content_type','')).lower().startswith('text/event-stream') and
                         raw.get('stream_json_error_count') == 0)
        item_predictions = None
        error = None
        if capture_valid:
            try:
                item_predictions = parse_predictions(raw['output_text'], job['task_ids'])
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                error = str(exc)
        else:
            error = 'incomplete_or_invalid_capture'
        for task_id in job['task_ids']:
            require(task_id not in predictions[model], 'Repeated candidate target item')
            predictions[model][task_id] = item_predictions[task_id] if item_predictions is not None else None
        quality.append({'trial_id': job['trial_id'], 'requested_model': model,
                        'http_status': raw.get('http_status'), 'response_status': raw.get('response_status'),
                        'terminal_event': raw.get('terminal_event'),
                        'capture_integrity': checks['capture_integrity'], 'capture_valid': bool(capture_valid),
                        'parser_valid': item_predictions is not None, 'unscorable_reason': error,
                        'task_ids': job['task_ids'], 'usage': raw.get('usage')})
    require(all(set(predictions[m]) == set(source_by_id) for m in models), 'Candidate target coverage differs')
    ordered = sorted(source_by_id)
    tasks = [source_by_id[k] for k in ordered]
    correct = {m:[binary_correct(predictions[m][k], source_by_id[k]['gold_binary']) for k in ordered] for m in models}
    draws = resampling_indices(tasks, protocol['uncertainty']['draws'], protocol['uncertainty']['seed'])
    results = {}
    for m in models:
        all_scores = bounds(correct[m])
        by_stratum = {s: bounds([correct[m][n] for n,r in enumerate(tasks) if r['subcase'] == s])
                      for s in sorted({r['subcase'] for r in tasks})}
        ci = None if any(v is None for v in correct[m]) else quantile_interval(np.array(correct[m])[draws].mean(axis=1))
        results[m] = {**all_scores, 'conditional_item_ci95': ci, 'by_stratum': by_stratum,
                      'three_way_prediction_counts': dict(Counter(v or 'missing' for v in predictions[m].values()))}
    pairwise = []
    for i,a in enumerate(models):
        for b in models[i+1:]:
            limits = difference_bounds(correct[a], correct[b])
            complete = not any(v is None for v in correct[a] + correct[b])
            delta = np.array(correct[a],dtype=float) - np.array(correct[b],dtype=float) if complete else None
            pairwise.append({'a':a,'b':b,'complete_fixed_pair':complete,
                             'signed_accuracy_difference':float(delta.mean()) if complete else None,
                             'conservative_difference_bounds':limits,
                             'robust_order':'a_above_b' if limits[0]>0 else 'b_above_a' if limits[1]<0 else 'tied_or_indeterminate',
                             'conditional_item_ci95':quantile_interval(delta[draws].mean(axis=1)) if complete else None})
    combined = {'status':'not_combined_no_WSC_summary_supplied','signed_target_effect':None}
    wsc_sha = None
    if args.wsc_summary:
        require(args.wsc_summary_sha256 and sha(args.wsc_summary) == args.wsc_summary_sha256, 'WSC summary binding missing or changed')
        wsc_sha = args.wsc_summary_sha256
        combined = fixed_choice_result(load(args.wsc_summary), models, correct, draws)
    output = args.output_directory or root / 'analysis'
    require(not output.exists(), 'Refusing to overwrite analysis directory')
    output.mkdir(parents=True)
    prediction_rows = [{'model':m,'task_id':k,'source_pair_id':source_by_id[k]['source_pair_id'],
                        'subcase':source_by_id[k]['subcase'],'official_gold_binary':source_by_id[k]['gold_binary'],
                        'predicted_three_way':predictions[m][k],
                        'binary_correct':binary_correct(predictions[m][k],source_by_id[k]['gold_binary'])}
                       for m in models for k in ordered]
    summary = {'scope':'New separately frozen exploratory HANS80 external target, not old PAWS pilot activation',
               'freeze_commit':args.freeze_commit,'freeze_utc':args.freeze_time,
               'protocol_sha256':args.protocol_sha256,'manifest_sha256':args.manifest_sha256,
               'attempted_requests':40,'target_items':80,'classification_labels':320,
               'all_four_candidates_complete':all(r['missing']==0 for r in results.values()),
               'valid_parsed_requests':sum(r['parser_valid'] for r in quality),
               'unscorable_requests':sum(not r['parser_valid'] for r in quality),
               'by_model':results,'all_six_fixed_pairwise_comparisons':pairwise,
               'fixed_WSC_choice_external_consequence':combined,'WSC_summary_sha256':wsc_sha,
               'input_hashes': {n:sha(root/n) for n in ['protocol.json','manifest.jsonl','selected_data.json',
                                                       'task_key.json','responses.jsonl','run_metadata.json']},
               'analyzer_sha256':sha(Path(__file__).resolve()),
               'capture_auditor_sha256':sha(audit_path),
               'uncertainty':protocol['uncertainty'],'human_review':'pending',
               'limits':['Two fixed public HANS subcases; no whole-domain NLI, pretraining exclusion, real-user harm or population-ranking claim.',
                         'All candidate outputs are retained; operational missingness is bounded, never imputed as semantic failure.',
                         'WSC choice aliases are fixed before target inspection; no HANS-based tie breaking or candidate selection.'],
               'reported_usage_cost_sum':sum((r.get('usage') or {}).get('cost') or 0 for r in quality),
               'billing_limit':'Provider usage.cost is not verified account debit, complete billing or USD conversion.'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    (output/'predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in prediction_rows))
    (output/'capture_quality.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in quality))
    print(json.dumps({k:summary[k] for k in ['attempted_requests','target_items','all_four_candidates_complete','valid_parsed_requests','unscorable_requests']}))


if __name__ == '__main__':
    main()
