#!/usr/bin/env python3
"""Fabricated offline fixtures only; never opens actual model captures."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import analyze_wsc as a


def dump(path, value, jsonl=False):
    path.write_text((''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in value)
                     if jsonl else json.dumps(value, indent=2, ensure_ascii=False) + '\n'))


def entry(text, label, n):
    r = {'idx': n, 'text': text, 'label': label, 'target': {'span1_text': 'Alpha' if label else 'Beta', 'span2_text': 'He'}}
    raw = json.dumps(r) + '\n'
    return {'record': r, 'raw_line_utf8': raw, 'raw_line_sha256': hashlib.sha256(raw.encode()).hexdigest()}


def fixture(root, negative=False, tie=False):
    """Three wholly synthetic source passages, four candidates and eight calls."""
    wsc = root / 'wsc'; wsc.mkdir()
    methods = root / 'methods'; methods.mkdir()
    actual_methods = Path(__file__).resolve().parents[1] / 'methods'
    for name in ['capture_audit_source.py', 'run_adaption_stream_pilot.py']:
        shutil.copyfile(actual_methods / name, methods / name)
    data, tasks, decisions, mapping, family_roles = [], [], [], {}, {}
    for n in range(1, 4):
        pid, rid, family = f'P{n:03d}', f'W{n:03d}', f'F{n:03d}'
        role = 'selection' if n <= 2 else 'confirmation'
        text = f'Synthetic passage {n} with no external source claim.'
        data.append({'passage_id': pid, 'source_review_id': rid, 'family_id': family,
                     'analysis_role': role, 'premise': text,
                     'gold_replacement_hypothesis': f'Synthetic gold {n}',
                     'non_gold_replacement_hypothesis': f'Synthetic non-gold {n}',
                     'source_positive_record': entry(text, True, n * 2),
                     'source_negative_record': entry(text, False, n * 2 + 1),
                     'official_nli_gold': False, 'analyst_positive_entailment': 'yes',
                     'analyst_negative_not_entailed': 'yes', 'analyst_negative_three_way': 'neutral'})
        decisions.append({'review_id': rid, 'eligible': True, 'positive_entailment': 'yes',
                          'negative_not_entailed': 'yes', 'negative_three_way': 'neutral'})
        mapping[rid] = family; family_roles[family] = role
        for variant in ['gold', 'non_gold']:
            tasks.append({'task_id': f'X{len(tasks)+1:03d}', 'passage_id': pid, 'source_review_id': rid,
                          'family_id': family, 'analysis_role': role, 'variant': variant,
                          'binary_target': 'entailment' if variant == 'gold' else 'non_entailment',
                          'literal_advice_target': 'entailment' if variant == 'gold' else 'contradiction',
                          'analyst_three_way_target': 'entailment' if variant == 'gold' else 'neutral'})
    dump(wsc / 'selected_data.json', {'source_passages': 3, 'source_families': 3, 'items': data})
    dump(wsc / 'task_key.json', {'rows': tasks})
    dump(wsc / 'semantic_final.json', {'rows': decisions})
    dump(wsc / 'source_split.json', {'all_semantic_decisions': decisions,
                                   'selected_review_ids': list(mapping),
                                   'clustering': {'family_mapping': mapping}, 'family_roles': family_roles})
    lookup = {p['passage_id']: p for p in data}
    manifest, captures = [], []
    (wsc / 'api_artifacts').mkdir(); (wsc / 'stream_journals').mkdir()
    for mnum, model in enumerate(a.MODELS):
        for role in a.ROLES:
            batch = [t for t in tasks if t['analysis_role'] == role]
            inputs = [{'id': t['task_id'], 'premise': lookup[t['passage_id']]['premise'],
                       'hypothesis': lookup[t['passage_id']][t['variant'] + '_replacement_hypothesis']} for t in batch]
            payload = {'model': model, 'instructions': 'Synthetic fixture instruction; no inference.',
                       'input': json.dumps(inputs), 'temperature': 0.0, 'max_output_tokens': 8192,
                       'stream': True, 'tools': [], 'tool_choice': 'none', 'agentic_memory': False, 'store': False}
            tid = f'IW-{len(manifest)+1:03d}'
            job = {'trial_id': tid, 'requested_model': model, 'batch_role': role,
                   'task_ids': [t['task_id'] for t in batch],
                   'passage_ids': list(dict.fromkeys(t['passage_id'] for t in batch)),
                   'request_payload': payload, 'request_sha256': hashlib.sha256(a.canonical(payload)).hexdigest()}
            manifest.append(job)
            predictions = []
            for t in batch:
                n = int(t['passage_id'][1:])
                if t['variant'] == 'gold':
                    label = 'entailment'
                elif tie:
                    label = 'neutral'
                elif mnum == 0:
                    label = 'entailment' if negative and n == 3 else 'neutral'
                elif mnum == 1:
                    label = 'contradiction' if n == 1 else ('neutral' if negative and n == 3 else 'entailment')
                elif mnum == 2:
                    label = 'neutral' if n == 1 else 'entailment'
                else:
                    label = 'entailment'
                predictions.append({'id': t['task_id'], 'label': label})
            text = json.dumps({'predictions': predictions})
            provider = {'status': 'completed', 'output': [{'type': 'message', 'role': 'assistant',
                         'content': [{'type': 'output_text', 'text': text}]}]}
            frame = {'event': 'response.completed', 'data': {'type': 'response.completed', 'response': provider},
                     'partial_frame': False, 'json_error': None}
            ending = {'event': 'capture_end', 'http_status': 200, 'terminal_event': 'response.completed', 'transport_error': None}
            journal = wsc / 'stream_journals' / f'{tid}.jsonl'
            dump(journal, [frame, ending], jsonl=True)
            raw = {'trial_id': tid, 'attempt_count': 1,
                   'started_utc': '2026-11-13T01:00:01+00:00', 'ended_utc': '2026-11-13T01:00:02+00:00',
                   'request_payload': payload, 'request_sha256': job['request_sha256'],
                   'output_text': text, 'output_text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                   'http_status': 200, 'response_status': 'completed', 'raw_response': provider,
                   'terminal_event_seen': True, 'terminal_event': 'response.completed',
                   'used_delta_fallback': False, 'stream_incomplete': False, 'stream_format_deviation': False,
                   'completed_nonempty': True, 'stream_journal_sha256': a.sha(journal),
                   'stream_frame_count': 1, 'stream_json_error_count': 0,
                   'transport_error': None, 'response_content_type': 'text/event-stream',
                   'requested_model': model, 'returned_model': model, 'usage': {'cost': 0.0}}
            dump(wsc / 'api_artifacts' / f'{tid}.json', raw)
            captures.append(raw)
    dump(wsc / 'manifest.jsonl', manifest, jsonl=True)
    dump(wsc / 'responses.jsonl', captures, jsonl=True)
    dump(wsc / 'run_metadata.json', {'requested': len(manifest), 'recorded': len(manifest), 'retries': 0})
    protocol = {'models': a.MODELS, 'source_passages': 3, 'source_families': 3,
                'split': {'passages': {'selection': 2, 'confirmation': 1}},
                'uncertainty': {'draws': 10000, 'seed': 2026111323},
                'request_plan': {'requests': len(manifest), 'ordered_classifications_per_model': len(tasks),
                                 'ordered_classifications_total': len(tasks) * 4},
                'hashes': {name: a.sha(wsc / name) for name in ['selected_data.json', 'task_key.json', 'manifest.jsonl', 'source_split.json']},
                'final_semantic_eligibility_filename': 'semantic_final.json',
                'final_semantic_eligibility_sha256': a.sha(wsc / 'semantic_final.json'),
                'analysis_sha256': a.sha(Path(a.__file__)),
                'capture_audit_source_sha256': a.sha(methods / 'capture_audit_source.py'),
                'runner_sha256': a.sha(methods / 'run_adaption_stream_pilot.py')}
    dump(wsc / 'protocol.json', protocol)
    return wsc, ('a' * 40, '2026-11-13T01:00:00Z', a.sha(wsc / 'manifest.jsonl'), a.sha(wsc / 'protocol.json'))


def alter_capture(wsc, number, callback):
    path = wsc / 'api_artifacts' / f'IW-{number:03d}.json'
    r = json.loads(path.read_text()); callback(r)
    dump(path, r)
    aggregate = a.rows(wsc / 'responses.jsonl')
    for n, value in enumerate(aggregate):
        if value['trial_id'] == r['trial_id']: aggregate[n] = r
    dump(wsc / 'responses.jsonl', aggregate, jsonl=True)


def self_test():
    checked = 0
    def yes(value, message):
        nonlocal checked
        assert value, message
        checked += 1
    def rejects(function, message):
        nonlocal checked
        try: function()
        except (ValueError, KeyError, TypeError): checked += 1; return
        raise AssertionError(message)
    yes(a.parse_predictions('{"predictions":[{"id":"X1","label":"Neutral"}]}', ['X1']) == {'X1': 'neutral'}, 'casefold parser')
    yes(a.parse_predictions('```json\n{"predictions":[{"id":"X1","label":"entailment"}]}\n```', ['X1'])['X1'] == 'entailment', 'one fence')
    for text in ['prefix {"predictions":[]}', '{"predictions":[{"id":"X1","label":"E"}]}',
                 '{"predictions":[]}', '{"predictions":[{"id":"X1","label":"neutral"},{"id":"X1","label":"neutral"}]}',
                 '{"predictions":[{"id":"X1","label":"neutral","why":"x"}]}',
                 '{"predictions":[],"predictions":[]}']:
        rejects(lambda text=text: a.parse_predictions(text, ['X1']), 'invalid full JSON must fail')
    for p, n, rule, expected in [(None, 'entailment', 'repaired_binary', (0., 0.)),
                                ('contradiction', None, 'literal_bad', (0., 0.)),
                                ('entailment', None, 'literal_bad', (0., 1.)),
                                ('entailment', 'neutral', 'repaired_binary', (1., 1.)),
                                ('entailment', 'neutral', 'literal_bad', (0., 0.))]:
        yes(a.pair_bounds(p, n, rule) == expected, 'pair partial-identification boundary')
    yes(a.distortion_bounds(None, 'contradiction') == (0., 0.), 'coupled C yields no score distortion')
    yes(a.distortion_bounds('entailment', 'neutral') == (1., 1.), 'coupled neutral penalty')
    yes(a.distortion_bounds('entailment', None) == (0., 1.), 'unknown penalty bounded')
    _, weights = a.cluster_draws([{'family_id': 'A'}, {'family_id': 'A'}, {'family_id': 'B'}], 123, 1000)
    yes(bool(a.np.all(weights[:, 0] == weights[:, 1])), 'source variants move jointly in family bootstrap')
    yes(set(a.np.unique(weights[:, 0])) <= {0, 1, 2}, 'draw exactly number of families rather than individual tasks')
    with tempfile.TemporaryDirectory() as d:
        wsc, args = fixture(Path(d))
        result, trials, predictions = a.analyze(wsc, *args)
        yes(result['primary_full_candidate_matrix_complete'], 'all-four complete matrix')
        yes(len(trials) == 8 and len(predictions) == 24, 'all calls and ordered labels retained')
        selection = result['cohorts']['selection']['candidates']
        yes(selection[a.MODELS[0]]['rules']['literal_bad']['paired']['complete_value'] == 0, 'literal bad penalty')
        yes(selection[a.MODELS[0]]['rules']['repaired_binary']['paired']['complete_value'] == 1, 'repaired paired accuracy')
        yes(selection[a.MODELS[0]]['rules']['repaired_binary']['items']['unit_count'] == 4, 'item denominator')
        yes(selection[a.MODELS[0]]['rules']['literal_bad']['macro_f1_complete'] == .5, 'literal neutral FNs in E/C macroF1')
        yes(selection[a.MODELS[0]]['rules']['repaired_binary']['macro_f1_complete'] == 1, 'repaired binary macroF1')
        choice = result['fixed_selection_confirmation_consequence']
        yes(choice['literal_selected'] == a.MODELS[1] and choice['repaired_selected'] == a.MODELS[0], 'strict selected winner change')
        yes(choice['complete_signed_effect'] == 1 and choice['conditional_cluster_ci95'] == [1, 1], 'positive independent confirmation effect')
        yes(choice['eligible_primary_consequence'], 'complete matrix makes unique consequence primary eligible')
        six = result['cohorts']['selection']['all_six_pairwise_comparisons']
        yes(len(six) == 6 and six[0]['metrics']['paired']['complete_strict_reversal'], 'all pairs and strict reversal')
        yes(result['secondary_analyst_three_way_sensitivity'][a.MODELS[0]]['official_three_way_gold'] is False, 'no invented official NLI gold')
        # Repeated runs are bit-for-bit stable in the result structure.
        yes(a.analyze(wsc, *args)[0] == result, 'deterministic recomputation')
        protocol, key, matrix, *_ = a.audit_inputs(wsc, *args)
        for task in key:
            if task['variant'] == 'non_gold': matrix[a.MODELS[0]][task['task_id']] = 'contradiction'
        same = a.compute_scores(protocol, key, matrix)['fixed_selection_confirmation_consequence']
        yes(same['literal_selected'] == same['repaired_selected'] == a.MODELS[0], 'same unique winner retained')
        yes(same['complete_signed_effect'] == 0 and same['conditional_cluster_ci95'] == [0, 0], 'same selected model has exact zero consequence')
        original = (wsc / 'api_artifacts/IW-001.json').read_bytes()
        alter_capture(wsc, 1, lambda r: r.update(output_text=r['output_text'] + ' '))
        rejects(lambda: a.analyze(wsc, *args), 'text hash tampering rejected')
        (wsc / 'api_artifacts/IW-001.json').write_bytes(original)
        aggregate = a.rows(wsc / 'responses.jsonl'); aggregate[0] = json.loads(original); dump(wsc / 'responses.jsonl', aggregate, jsonl=True)
        alter_capture(wsc, 1, lambda r: r.update(started_utc='2026-11-12T00:00:00Z'))
        rejects(lambda: a.analyze(wsc, *args), 'pre-freeze start rejected')
    with tempfile.TemporaryDirectory() as d:
        wsc, args = fixture(Path(d), negative=True)
        result = a.analyze(wsc, *args)[0]
        yes(result['fixed_selection_confirmation_consequence']['complete_signed_effect'] == -1, 'negative heldout effect preserved')
    with tempfile.TemporaryDirectory() as d:
        wsc, args = fixture(Path(d), tie=True)
        result = a.analyze(wsc, *args)[0]
        yes(result['fixed_selection_confirmation_consequence']['status'] == 'indeterminate_tie_or_missing_bounds', 'ties not arbitrary winners')
        yes(len(result['cohorts']['selection']['rankings']['paired']['repaired_binary']['possible_winners']) == 4, 'all tied candidates retained')
        yes(not any(c['metrics']['paired']['complete_strict_reversal'] for c in result['cohorts']['selection']['all_six_pairwise_comparisons']), 'ties not reversals')
    with tempfile.TemporaryDirectory() as d:
        wsc, args = fixture(Path(d))
        # Preserve valid artifacts but make a complete batch fail strict SSE quality.
        alter_capture(wsc, 1, lambda r: r.update(response_content_type='application/json'))
        result = a.analyze(wsc, *args)[0]
        yes(not result['primary_full_candidate_matrix_complete'], 'strict capture-quality failure prevents full primary')
        yes(result['missing_items_by_candidate'][a.MODELS[0]] == 4, 'all invalid-batch tasks missing')
        s = result['cohorts']['selection']['candidates'][a.MODELS[0]]['rules']['repaired_binary']['paired']
        yes(s['lower'] == 0 and s['upper'] == 1 and s['complete_value'] is None, 'missing bounds not error imputation')
        yes(not result['fixed_selection_confirmation_consequence']['eligible_primary_consequence'], 'incomplete primary cannot be promoted')
    with tempfile.TemporaryDirectory() as d:
        wsc, args = fixture(Path(d))
        alter_capture(wsc, 1, lambda r: r.update(local_capture_error='SyntheticFailure'))
        # A local capture placeholder has no timestamps; it remains accounted for.
        alter_capture(wsc, 1, lambda r: [r.pop(k, None) for k in ['started_utc', 'ended_utc']])
        result = a.analyze(wsc, *args)[0]
        yes(result['integrity']['untimed_local_capture_failures'] == 1, 'untimed local capture retained')
        yes(not result['integrity']['all_capture_hash_checks_pass'], 'local unverifiable capture not called verified')
        yes(result['integrity']['recorded_calls'] == 8 and result['integrity']['valid_classifications'] == 20, 'operational missingness visible')
    with tempfile.TemporaryDirectory() as d:
        wsc, args = fixture(Path(d))
        (wsc / 'task_key.json').write_text((wsc / 'task_key.json').read_text() + '\n')
        rejects(lambda: a.analyze(wsc, *args), 'key byte tampering rejected')
    return {'synthetic_only': True, 'checks_passed': checked, 'actual_model_predictions_opened': False,
            'inference_calls': 0, 'fixture_classifications': 24,
            'coverage': ['whole-JSON parser', 'coupled missing bounds', 'all-six ordering', 'strict reversal',
                         'tied winner sets', 'positive and negative heldout consequences',
                         'primary completeness', 'source and wire capture audit', 'tamper rejection',
                         'local operational failure accounting', 'deterministic cluster analysis']}


if __name__ == '__main__':
    print(json.dumps(self_test()))
