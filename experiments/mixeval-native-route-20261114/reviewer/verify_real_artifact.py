"""Independent paired-pilot artifact, call-ledger and unknown-bound audit.

This verifier makes no provider/judge calls and never regenerates responses.
Invoke with the extracted Action artifact directory after capture has ended.
"""
import argparse
import ast
from collections import Counter
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

import numpy as np

P = Path(__file__).resolve().parent
canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
sha = lambda data: hashlib.sha256(data).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def load_freeform_rules(root):
    path = root / 'official/mix_eval/utils/metric_utils.py'
    assert sha(path.read_bytes()) == '85077e61ca01f4c240158ff3b18a0451130fa879a2a46a11f3b382dbbf1fd73a'
    names = {'check_is_number', 'normalize_str', 'extract_numbers', 'parse_freeform_response_rule', 'eval_freeform_rule'}
    nodes = [node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == len(names)
    env = {'re': re, 'np': np}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), 'exec'), env)
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artifact_directory')
    parser.add_argument('--output', default=str(P / 'REAL_ARTIFACT_VERIFICATION.json'))
    args = parser.parse_args()
    root = Path(args.artifact_directory).resolve()
    protocol = json.loads((root / 'PROTOCOL.json').read_text())
    analysis_protocol = json.loads((root / 'ANALYSIS_PROTOCOL.json').read_text())
    launch = json.loads((root / 'LAUNCH.json').read_text())
    assert sha((root / 'PROTOCOL.json').read_bytes()) == launch['protocol_sha256']
    assert sha((root / 'manifest.jsonl').read_bytes()) == launch['manifest_sha256']
    for name, digest in protocol['frozen_files'].items():
        assert sha((root / name).read_bytes()) == digest, name
    manifest = read_jsonl(root / 'manifest.jsonl')
    cases = json.loads((root / 'selected20.json').read_text())
    assert len(manifest) == 80 and len(cases) == 20
    by_trial = {row['trial_id']: row for row in manifest}
    assert len(by_trial) == 80
    source = {case['source_index']: case for case in cases}
    assert len(source) == 20
    models = protocol['models']
    assert len(models) == 2 and protocol['maximum_requests'] == 80
    expected_order = [(case['source_index'], condition, model) for case in cases
                      for condition in protocol['conditions'] for model in models]
    assert [(row['source_index'], row['condition'], row['request_payload']['model']) for row in manifest] == expected_order
    for row in manifest:
        payload = row['request_payload']
        case = source[row['source_index']]
        assert sha(canonical(case['record'])) == case['source_sha256'] == row['source_sha256']
        assert sha(canonical(payload)) == row['request_sha256']
        assert sha(payload['input'].encode()) == row['prompt_sha256']
        assert payload['model'] in models and payload['max_output_tokens'] == 4096
        assert payload['temperature'] == 0 and len(payload['input'].encode()) <= 8192
        expected_prompt = case['binding_only_prompt'] if row['condition'] == 'binding_only' else case['official_typed_prompt']
        assert payload['input'] == expected_prompt
    artifact_index = json.loads((root / 'ARTIFACT_INDEX.json').read_text())
    assert artifact_index['credential_scan_passed'] is True
    for entry in artifact_index['files']:
        target = (root / entry['path']).resolve()
        assert target.is_relative_to(root)
        assert sha(target.read_bytes()) == entry['sha256'], entry['path']
    ledger = read_jsonl(root / 'CALL_LEDGER.jsonl')
    starts = [event for event in ledger if event['event'] == 'attempt_started']
    recorded = [event for event in ledger if event['event'] == 'attempt_recorded']
    assert len(starts) <= 80 and len({event['trial_id'] for event in starts}) == len(starts)
    assert [event['trial_id'] for event in starts] == [row['trial_id'] for row in manifest[:len(starts)]]
    assert len({event['trial_id'] for event in recorded}) == len(recorded)
    assert {event['trial_id'] for event in recorded} <= {event['trial_id'] for event in starts}
    for event in starts:
        assert event['request_sha256'] == by_trial[event['trial_id']]['request_sha256']
        assert event['attempt_count'] == 1
    times = [datetime.fromisoformat(event['utc'].replace('Z', '+00:00')) for event in starts]
    intervals = [(second-first).total_seconds() for first, second in zip(times, times[1:])]
    start_ids = {event['trial_id'] for event in starts}
    aggregate = {row['trial_id']: row for row in read_jsonl(root / 'responses.jsonl')}
    assert len(aggregate) == len(read_jsonl(root / 'responses.jsonl'))
    functions = load_freeform_rules(root)
    scored = []
    score_lookup = {}
    warnings = []
    errors = []
    usage_input = usage_output = usage_records = 0
    cost = Decimal(0)
    returned_models = Counter()
    for row in manifest:
        tid = row['trial_id']
        path = root / 'api_artifacts' / (tid + '.json')
        artifact = json.loads(path.read_text()) if path.exists() else None
        score = None
        state = 'unattempted' if tid not in start_ids else 'attempted_without_final_artifact'
        parsed = None
        if artifact is not None:
            assert tid in start_ids and artifact['trial_id'] == tid
            assert artifact.get('attempt_count') == 1
            if tid in aggregate:
                assert artifact == aggregate[tid]
            # Minimal transport/capture-error receipts intentionally omit the
            # request payload and hash. They are unknown, not scorable errors.
            request_associated = artifact.get('request_sha256') == row['request_sha256']
            if artifact.get('request_sha256') is not None and not request_associated:
                errors.append({'trial_id': tid, 'error': 'request_hash_mismatch'})
            if artifact.get('request_payload') is not None:
                assert sha(canonical(artifact['request_payload'])) == row['request_sha256']
                assert artifact['request_payload'] == row['request_payload']
            text = artifact.get('output_text')
            text_valid = isinstance(text, str) and sha(text.encode()) == artifact.get('output_text_sha256')
            if isinstance(text, str) and not text_valid:
                errors.append({'trial_id': tid, 'error': 'output_text_hash_mismatch'})
            complete = (request_associated and text_valid and artifact.get('completed_nonempty') is True
                        and artifact.get('http_status') == 200 and artifact.get('response_status') == 'completed'
                        and not artifact.get('stream_incomplete') and not artifact.get('transport_error')
                        and not artifact.get('api_error') and bool(text.strip()))
            if complete:
                parsed = functions['parse_freeform_response_rule'](SimpleNamespace(model_type='ChatModel'), text)
                score = float(functions['eval_freeform_rule'](source[row['source_index']]['record']['target'], parsed))
                state = 'completed_scored'
            else:
                state = 'capture_incomplete_or_empty'
                if artifact.get('local_capture_error'):
                    warnings.append({'trial_id': tid, 'warning': 'minimal_local_capture_error_retained_unknown'})
            usage = artifact.get('usage')
            if isinstance(usage, dict):
                if all(type(usage.get(k)) in (int, float) and usage[k] >= 0 for k in ['input_tokens', 'output_tokens']):
                    usage_records += 1
                    usage_input += usage['input_tokens']
                    usage_output += usage['output_tokens']
                    if usage['output_tokens'] > 4096:
                        errors.append({'trial_id': tid, 'error': 'provider_output_cap_violation'})
                if usage.get('cost') is not None:
                    units = Decimal(str(usage['cost']))
                    assert units.is_finite() and units >= 0
                    cost += units
            returned = artifact.get('returned_model')
            if returned:
                returned_models[(row['request_payload']['model'], str(returned))] += 1
                if returned != row['request_payload']['model']:
                    warnings.append({'trial_id': tid, 'warning': 'returned_model_identifier_differs_from_requested',
                                     'requested': row['request_payload']['model'], 'returned': returned})
        key = (row['request_payload']['model'], row['source_index'], row['condition'])
        assert key not in score_lookup
        score_lookup[key] = score
        scored.append({'trial_id': tid, 'model': key[0], 'source_index': key[1], 'condition': key[2],
                       'score': score, 'state': state, 'parsed': parsed})
    assert set(aggregate) <= start_ids
    on_disk_ids = {path.stem for path in (root / 'api_artifacts').glob('*.json')} if (root / 'api_artifacts').exists() else set()
    assert on_disk_ids <= start_ids
    effects = []
    for model in sorted(models):
        low = high = wins = losses = ties = complete = 0
        pairs = []
        for source_index in source:
            binding = score_lookup[(model, source_index, 'binding_only')]
            typed = score_lookup[(model, source_index, 'official_typed')]
            low += (typed if typed is not None else 0) - (binding if binding is not None else 1)
            high += (typed if typed is not None else 1) - (binding if binding is not None else 0)
            if binding is not None and typed is not None:
                complete += 1
                wins += typed > binding
                losses += binding > typed
                ties += binding == typed
            pairs.append({'source_index': source_index, 'binding_only': binding, 'official_typed': typed})
        effects.append({'model': model, 'pairs': 20, 'complete_pairs': complete, 'typed_wins': wins,
                        'binding_wins': losses, 'ties': ties, 'gain_bounds': [low/20, high/20], 'pairs_detail': pairs})
    comparison = 'NOT_AVAILABLE'
    if (root / 'ANALYSIS_SUMMARY.json').exists():
        existing = json.loads((root / 'ANALYSIS_SUMMARY.json').read_text())
        assert existing['effects'] == effects
        assert existing['completed_scored'] == sum(item['score'] is not None for item in scored)
        assert existing['input_tokens'] == usage_input and existing['output_tokens'] == usage_output
        assert Decimal(existing['cost_units']) == cost
        comparison = 'PASS'
    report = {'status': 'PASS' if not errors else 'FAIL', 'planned_trials': 80,
              'source_questions': 20, 'distinct_requested_models': 2,
              'attempt_started_events': len(starts), 'attempt_recorded_events': len(recorded),
              'per_trial_artifacts': len(on_disk_ids), 'completed_scored': sum(item['score'] is not None for item in scored),
              'minimum_observed_UTC_start_interval_seconds': min(intervals) if intervals else None,
              'usage_records': usage_records, 'input_tokens': usage_input, 'output_tokens': usage_output,
              'cost_units': str(cost), 'cost_currency': None, 'analysis_summary_comparison': comparison,
              'effects': effects, 'returned_model_pairs': [{'requested': k[0], 'returned': k[1], 'count': v} for k,v in returned_models.items()],
              'warnings': warnings, 'errors': errors, 'new_provider_or_judge_calls_by_verifier': 0,
              'scope': 'Independent source/manifest/artifact-index/call-ledger/usage/official-rule/pair-bound reconciliation. Empty/incomplete/missing/local-error captures remain unknown. Native model execution and provider authenticity are not independently reproduced.'}
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n')
    Path(args.output).with_name('REAL_INDEPENDENT_SCORES.json').write_text(json.dumps(scored, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
