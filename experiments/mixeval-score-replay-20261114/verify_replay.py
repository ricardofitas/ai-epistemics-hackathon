"""Independent delegated-agent reconciliation of frozen parser replay.

Does not import or execute the parent runner. Re-parses native outputs with
the pinned original parser package and re-executes official helper bodies.
No provider, model, tokenizer, whole-engine or benchmark inference is used.
"""
import ast
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import random
import re
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P / 'reviewer/upstream'))
from one_eval.metrics.parsers import parse_value
from one_eval.metrics.parsers.choice import normalize_choice_labels

canonical = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
read_gz = lambda n: [json.loads(line) for line in gzip.decompress((P / n).read_bytes()).splitlines()]
dump = lambda n, v: (P / n).write_text(json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


class CountRandom:
    def __init__(self):
        self.generator = random.Random(42)
        self.history = []

    def choice(self, labels):
        result = self.generator.choice(labels)
        self.history.append({'labels': list(labels), 'result': result})
        return result


def official_helpers():
    # Independent extraction; parent runner and its load_official are unused.
    src = P / 'official/mix_eval/utils/metric_utils.py'
    names = {'find_all_sub', 'parse_multi_choice_response_rule', 'check_is_number',
             'normalize_str', 'extract_numbers', 'parse_freeform_response_rule',
             'eval_multi_choice', 'eval_freeform_rule'}
    nodes = [node for node in ast.parse(src.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == names
    rng = CountRandom()
    namespace = {'re': re, 'np': np, 'random': rng}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(src), 'exec'), namespace)
    return namespace, rng


def main():
    frozen = json.loads((P / 'FROZEN_IMPLEMENTATION.json').read_text())
    for name, expected in frozen.items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == expected, name
    protocol = json.loads((P / 'PROTOCOL.json').read_text())
    for name, expected in protocol['inputs'].items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == expected
    selected = read_gz('SELECTED.jsonl.gz')
    captures = read_gz('SCORING_CAPTURES.jsonl.gz')
    source = {(row['split'], row['source_index']): row for row in selected}
    assert len(selected) == len(source) == 200
    assert len(captures) == 2400
    old = P.parent / 'synthesis-v13-20261114/mixeval/SELECTED.jsonl.gz'
    original_selection_available = old.is_file()
    if original_selection_available:
        assert old.read_bytes() == (P / 'SELECTED.jsonl.gz').read_bytes()
    expected_order = [
        (split, family, condition, item['source_index'])
        for split in ['free_form', 'multiple_choice']
        for family in protocol['constructed_output_families']
        for condition in protocol['conditions']
        for item in selected if item['split'] == split
    ]
    actual_order = [(c['split'], c['output_family'], c['condition'], c['source_index']) for c in captures]
    assert actual_order == expected_order
    assert len(set(actual_order)) == 2400
    summary = json.loads((P / 'SUMMARY.json').read_text())
    assert summary['errors'] == [] and summary['new_model_calls'] == 0
    panels = {(r['split'], r['output_family'], r['condition']): r for r in summary['panels']}
    assert len(panels) == 24
    gallery = json.loads((P / 'GALLERY_ENTRY.json').read_text())
    parser = gallery['meta']['evaluation']['parser']
    official, rng = official_helpers()
    args = SimpleNamespace(model_type='ChatModel')
    counts = defaultdict(Counter)
    response_invariance = defaultdict(set)
    counterexamples = {'official_first_alias_misses': [], 'native_scalarized_MC_reference_or_prediction_losses': []}
    physical = Counter()
    for item in selected:
        record = item['record']
        assert item['source_sha256'] == hashlib.sha256(canonical(record)).hexdigest()
        assert isinstance(record['target'], list) and record['target']
        physical[item['split'] + ':target_container:' + type(record['target']).__name__] += 1
        if item['split'] == 'free_form':
            assert all(isinstance(x, str) for x in record['target'])
            assert record['options'] == ['None']
            physical['free_form:all_target_elements:str'] += 1
            physical['free_form:options:list_containing_string_None'] += 1
        else:
            assert len(record['target']) == 1
            assert type(record['target'][0]) is int
            assert all(isinstance(x, str) for x in record['options'])
            assert 0 <= record['target'][0] < len(record['options'])
            physical['multiple_choice:singleton_target_element:int'] += 1
            physical['multiple_choice:option_count:' + str(len(record['options']))] += 1
    for capture in captures:
        split, family, condition = capture['split'], capture['output_family'], capture['condition']
        record = source[(split, capture['source_index'])]['record']
        assert capture['source_sha256'] == hashlib.sha256(canonical(record)).hexdigest()
        if split == 'free_form':
            fixture = {'source_first_reference': record['target'][0], 'explicit_wrong': 'ZXQ_UNRELATED_SENTINEL', 'empty': '', 'always_A': 'A'}[family]
        else:
            idx = record['target'][0]
            fixture = {'source_first_reference': chr(65 + idx), 'explicit_wrong': chr(65 + (idx + 1) % len(record['options'])), 'empty': '', 'always_A': 'A'}[family]
        assert capture['constructed_response'] == fixture
        response_invariance[(split, capture['source_index'], family)].add(fixture)
        row = capture['result']
        assert row['generated_ans'] == fixture
        key = (split, family, condition)
        tallies = counts[key]
        tallies['rows'] += 1
        if condition == 'official_rule_type_dispatch':
            assert row['target'] == record['target']
            before = len(rng.history)
            if split == 'free_form':
                parsed = official['parse_freeform_response_rule'](args, fixture)
                score = official['eval_freeform_rule'](record['target'], parsed)
                assert sorted(map(repr, row['parsed'])) == sorted(map(repr, parsed))
            else:
                labels = [chr(65 + i) for i in range(len(record['options']))]
                parsed = official['parse_multi_choice_response_rule'](args, fixture, labels, dict(zip(labels, record['options'])))
                score = official['eval_multi_choice'](labels[record['target'][0]], parsed)
                assert row['parsed'] == parsed
            fallback = len(rng.history) > before
            assert row['random_fallback'] is fallback
            assert row['eval_valid'] is True and row['eval_error'] == ''
            assert row['eval_score'] == int(score)
            tallies.update(valid_samples=1, score=int(score), random_fallback_calls=int(fallback))
            if split == 'free_form' and family == 'source_first_reference' and not score:
                counterexamples['official_first_alias_misses'].append({
                    'source_index': capture['source_index'], 'source_sha256': capture['source_sha256'],
                    'response': fixture, 'parsed': parsed, 'target': record['target'],
                    'reason': 'Response strips final periods but target normalization does not.' if capture['source_index'] == 1425 else 'Key-response extraction splits literal alias on the internal indicator is .',
                })
        else:
            expected_target = record['target'][0] if condition == 'singleton_reference_only' and len(record['target']) == 1 else record['target']
            assert row['target'] == expected_target
            expected_options = ['None'] if split == 'free_form' else [value.strip() for value in record['options']]
            assert row['options'] == record['options']
            assert row['normalized_choices'] == expected_options
            assert row['prompt'] == record['prompt']
            # IDs are pandas-inferred numeric values after saved JSON reload.
            assert str(row['id']) == str(int(record['id']))
            independent_record = dict(record, target=expected_target,
                                      normalized_choices=expected_options,
                                      choices_text='\n'.join(chr(65+i)+'. '+v for i,v in enumerate(expected_options)))
            pred = parse_value(fixture, parser, independent_record)
            ref = parse_value(expected_target, parser, independent_record)
            assert row['eval_pred_choice'] == (pred.normalized if pred.ok else None)
            assert row['eval_ref_choice'] == (ref.normalized if ref.ok else None)
            assert row['eval_parse_strategy'] == pred.strategy
            labels = normalize_choice_labels(parser.get('choices', 'A-D'), independent_record)
            assert row['eval_pred'] == (float(labels.index(pred.normalized)) if pred.ok and pred.normalized in labels else None)
            if not ref.ok:
                assert row['eval_valid'] is False and row['eval_score'] is None and row['eval_error'] == 'invalid_reference'
                tallies['invalid_references'] += 1
            else:
                expected_score = int(pred.ok and pred.normalized == ref.normalized)
                error = '' if pred.ok else ('empty_output' if pred.error == 'empty_output' else 'parse_failed')
                assert row['eval_valid'] is True and row['eval_score'] == expected_score and row['eval_error'] == error
                tallies.update(valid_samples=1, score=expected_score, valid_predictions=int(pred.ok), parse_failed=int(error == 'parse_failed'), empty_output=int(error == 'empty_output'))
            if split == 'multiple_choice' and family == 'source_first_reference' and condition == 'singleton_reference_only' and row['eval_score'] != 1:
                counterexamples['native_scalarized_MC_reference_or_prediction_losses'].append({
                    'source_index': capture['source_index'], 'source_sha256': capture['source_sha256'],
                    'source_target': record['target'], 'source_correct_letter': fixture,
                    'option_count': len(record['options']), 'options': record['options'],
                    'native_reference_choice': row['eval_ref_choice'],
                    'native_prediction_choice': row['eval_pred_choice'], 'error': row['eval_error'],
                    'reason': 'Static A-D excludes source-correct E. Index4 then falls through to one-based fallback and is incorrectly normalized to D.',
                })
    assert all(len(responses) == 1 for responses in response_invariance.values())
    assert len(response_invariance) == 800
    native_capture_files = 0
    for key in panels:
        if key[-1] == 'official_rule_type_dispatch':
            continue
        stem = '__'.join(key)
        stored_rows = pd.read_json(P / 'captures' / (stem + '.jsonl'), lines=True).to_dict('records')
        stored_rows = [{k: None if isinstance(v, float) and not np.isfinite(v) else v
                        for k, v in row.items()} for row in stored_rows]
        captured_rows = [c['result'] for c in captures
                         if (c['split'], c['output_family'], c['condition']) == key]
        assert stored_rows == captured_rows
        stored_stats = json.loads((P / 'captures' / (stem + '.stats.json')).read_text())[0]
        assert all(panels[key][name] == value for name, value in stored_stats.items())
        native_capture_files += 1
    for key, tallies in counts.items():
        report = panels[key]
        assert tallies['rows'] == report['total_samples'] == 100
        assert tallies['valid_samples'] == report['valid_samples']
        assert tallies['invalid_references'] == report['invalid_references']
        expected_accuracy = tallies['score'] / tallies['valid_samples'] if tallies['valid_samples'] else 0.0
        assert expected_accuracy == report['accuracy']
        assert tallies['random_fallback_calls'] == report['random_fallback_calls']
        if key[-1] != 'official_rule_type_dispatch':
            for name in ['valid_predictions', 'parse_failed', 'empty_output']:
                assert tallies[name] == report[name]
            assert report['interpretation'] == ('UNSCORABLE' if tallies['valid_samples'] == 0 else 'SCORABLE_DIAGNOSTIC')
    assert len(rng.history) == 100
    assert {r['source_index'] for r in counterexamples['official_first_alias_misses']} == {1425, 1248}
    assert {r['source_index'] for r in counterexamples['native_scalarized_MC_reference_or_prediction_losses']} == {1624, 196}
    # Confirm every frozen byte still matches after separate reconciliation.
    for name, expected in frozen.items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == expected
    counterexamples['official_empty_MC_probe'] = {
        'seed': 42, 'dedicated_rng': True, 'source_order': [x['source_index'] for x in selected if x['split'] == 'multiple_choice'],
        'fallback_count': 100, 'correct_guesses': counts[('multiple_choice', 'empty', 'official_rule_type_dispatch')]['score'],
        'guesses': rng.history,
        'qualification': 'Deterministic illustration of original optional rule fallback. Not a model score, prevalence estimate, or official model-judge result.',
    }
    dump('COUNTEREXAMPLES.json', counterexamples)
    verification = {
        'status': 'PASS', 'reviewer': 'separate delegated scoring_review agent',
        'frozen_protocol_commit': 'fe6c1952e913391cd424825d8e703cc85d1375c7',
        'frozen_files_checked': len(frozen), 'source_rows_verified': 200,
        'condition_records_verified': len(captures), 'complete_unique_condition_coverage': True,
        'preserved_original_selection_bytes': True if original_selection_available else None,
        'original_selection_byte_comparison': 'PASS' if original_selection_available else 'NOT_AVAILABLE: prior sibling archive absent; frozen selected SHA256 and per-record source hashes verified',
        'frozen_selected_SHA256_verified': True,
        'output_invariance_groups': len(response_invariance),
        'independent_official_helper_calls': 800, 'independent_native_parser_pairs': 1600,
        'summary_panels_reconciled': 24, 'random_fallback_draws_reproduced': len(rng.history),
        'native_capture_frame_and_stats_pairs_verified': native_capture_files,
        'source_physical_types': dict(physical), 'native_zero_denominators': sum(r['valid_samples'] == 0 for r in panels.values()),
        'official_exact_first_alias_misses': 2, 'native_scalarized_MC_losses': 2,
        'new_provider_model_calls': 0,
        'retained_verifier_development_alerts': ['Initial independent-review assertion expected free-form options JSON-null. Actual source options are already the list ["None"] in all100cases. Assertion corrected after inspecting physical source types; frozen runner/protocol/captures unchanged. Placeholder is displayed by wrong task-kind route, not inserted by preprocessing.', 'Initial comparison expected the original options field itself to be trimmed. Source options remain raw; normalized_choices carries stripped values. Assertions now distinguish both columns, preserving the previously documented one-row whitespace difference.'],
        'scope': 'Independent agent/code reconciliation, exact original parser/helper re-execution, source hashes/physical types/order and captured outputs. Not independent human review or complete installed-engine/model execution.',
    }
    dump('VERIFICATION.json', verification)
    print(json.dumps(verification))


if __name__ == '__main__':
    main()
