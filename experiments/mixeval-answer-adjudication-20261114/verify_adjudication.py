#!/usr/bin/env python3
"""Independent, offline integrity and arithmetic verifier for the frozen audit.

Does not adjudicate semantic correctness or mutate review/aggregate inputs.
Run only after both independent reviews and SUMMARY.json have been saved.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
FROZEN = {
    'ADJUDICATION_PROTOCOL.json': 'f88703926f4424e15733aa6114f05afeab42cfffad5a94aeed1ea414d430e271',
    'BLINDED_CASES.json': '1a17ad5600325358f261977d9591d5f7ad5fc5315aec49c0f1cdd5f2b3e32cda',
    'PRIVATE_MAPPING.json': 'bde48577a36edd9d13a26406a9a4799ecb9215d3d051a9b076ad5aac91883873',
    'INPUT_PROVENANCE.json': 'bb6cfd86e2a5cde3027fcab181e4828fa692a8702963272b606adfadb7bbad12',
}
FINAL = {'SUPPORTED', 'SYMBOLIC', 'ABSENT', 'INCOMPATIBLE', 'UNCERTAIN'}
NONFINAL = {'SUPPORTED', 'NOT_OBSERVED', 'UNCERTAIN'}
DEFINITE_ZERO = {'SYMBOLIC', 'ABSENT', 'INCOMPATIBLE'}
CONDITIONS = ('binding_only', 'official_typed')


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def read(path):
    return json.loads(path.read_text())


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def occurrences(text, snippet):
    """Include overlapping occurrences, without interpreting the text."""
    if not snippet:
        return []
    found = []
    pos = text.find(snippet)
    while pos >= 0:
        found.append((pos, pos + len(snippet)))
        pos = text.find(snippet, pos + 1)
    return found


def check_evidence(text, row, where):
    final_label, nonfinal_label = row['final_label'], row['nonfinal_label']
    check(final_label in FINAL, where + ': invalid final label')
    check(nonfinal_label in NONFINAL, where + ': invalid nonfinal label')
    final_span = row['final_span']
    check(isinstance(final_span, str), where + ': final_span must be a string')
    spans = occurrences(text, final_span)
    check(not final_span or bool(spans), where + ': final span is not an exact substring')
    if final_label not in {'ABSENT', 'UNCERTAIN'}:
        check(bool(final_span), where + ': asserted final label lacks final span')
    for key in ('final_evidence', 'nonfinal_evidence', 'reason'):
        check(isinstance(row[key], str), where + ': ' + key + ' must be a string')
    if final_label == 'SUPPORTED':
        quote = row['final_evidence']
        check(bool(quote) and quote in text, where + ': final support needs exact output quote')
        check(quote in final_span, where + ': final support quote is outside final span')
    if nonfinal_label == 'SUPPORTED':
        quote = row['nonfinal_evidence']
        evidence_spans = occurrences(text, quote)
        check(bool(quote) and bool(evidence_spans), where + ': nonfinal support needs exact quote')
        # A repeated final-span string may denote different occurrences. Accept
        # only if at least one final occurrence and evidence occurrence are disjoint.
        if final_span:
            check(any(e1 <= f0 or f1 <= e0 for e0, e1 in evidence_spans for f0, f1 in spans),
                  where + ': no nonfinal evidence occurrence outside any final span occurrence')


def authoritative(work):
    inp = work.parent / 'package' / 'real-generation'
    protocol = read(work / 'ADJUDICATION_PROTOCOL.json')
    for name, expected in FROZEN.items():
        check(sha((work / name).read_bytes()) == expected, 'frozen input changed: ' + name)
    provenance = read(work / 'INPUT_PROVENANCE.json')
    archive = work.parent / 'inputs' / 'Epistemics_MixEval_integracao_e_geracao_emparelhada_20261114.zip'
    archive_hash = sha(archive.read_bytes())
    check(archive_hash == provenance['archive_sha256'] == protocol['input_archive_sha256'], 'archive SHA mismatch')
    for name, expected in provenance['input_files'].items():
        check(sha((inp / name).read_bytes()) == expected, 'authoritative input hash mismatch: ' + name)
    check(sha((work / 'BLINDED_CASES.json').read_bytes()) == provenance['blinded_sha256'], 'blind provenance mismatch')
    selected = read(inp / 'selected20.json')
    sources = {r['source_index']: r for r in selected}
    check(len(sources) == len(selected) == 20, 'source panel must have 20 unique questions')
    for index, row in sources.items():
        check(sha(canonical(row['record'])) == row['source_sha256'], 'source canonical SHA mismatch: ' + str(index))
    manifest_rows = [json.loads(line) for line in (inp / 'manifest.jsonl').read_text().splitlines() if line.strip()]
    manifest = {r['trial_id']: r for r in manifest_rows}
    analysis_rows = read(inp / 'ANALYSIS_CAPTURES.json')
    analysis = {r['trial_id']: r for r in analysis_rows}
    mapping_rows = read(work / 'PRIVATE_MAPPING.json')
    mapping = {r['trial_id']: r for r in mapping_rows}
    blind_rows = read(work / 'BLINDED_CASES.json')
    blind = {r['opaque_id']: r for r in blind_rows}
    check(len(manifest) == len(manifest_rows) == len(analysis) == len(analysis_rows) == len(mapping) == len(mapping_rows) == 80, 'trial IDs must be 80 unique')
    check(manifest.keys() == analysis.keys() == mapping.keys(), 'trial ID universes differ')
    check(len(blind) == len(blind_rows) == 69, 'blinded IDs must be 69 unique')
    check(len({r['opaque_id'] for r in mapping_rows}) == 80, 'opaque mapping IDs not unique')
    spec = importlib.util.spec_from_file_location('audit_original_scoring_adapter', inp / 'scoring_adapter.py')
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    completed = 0
    parser_order_only_differences = 0
    groupkeys = set()
    for tid, row in mapping.items():
        orig, request = analysis[tid], manifest[tid]
        src = sources[request['source_index']]
        record = src['record']
        capture = read(inp / 'api_artifacts' / (tid + '.json'))
        text = capture.get('output_text', '')
        check(isinstance(text, str), tid + ': output is not string')
        check(capture['trial_id'] == tid, tid + ': capture association mismatch')
        check(sha(canonical(request['request_payload'])) == request['request_sha256'] == capture['request_sha256'], tid + ': request SHA mismatch')
        check(capture['request_payload'] == request['request_payload'], tid + ': capture request differs')
        check(sha(request['request_payload']['input'].encode()) == request['prompt_sha256'], tid + ': prompt SHA mismatch')
        check(sha(text.encode()) == capture['output_text_sha256'] == row['output_sha256'], tid + ': output SHA mismatch')
        check(row['source_sha256'] == request['source_sha256'] == src['source_sha256'], tid + ': source SHA mismatch')
        check(row['opaque_id'] == sha(('fixed-final-audit-v1:' + tid).encode())[:20], tid + ': opaque SHA mismatch')
        for key, value in orig.items():
            check(row[key] == value, tid + ': original capture field changed: ' + key)
        check(row['source_index'] == request['source_index'] and row['condition'] == request['condition'] and row['model'] == request['request_payload']['model'], tid + ': source/model/condition association mismatch')
        key = (row['model'], row['source_index'], row['condition'])
        check(key not in groupkeys, tid + ': duplicated source/model/condition')
        groupkeys.add(key)
        complete_capture = (capture.get('completed_nonempty') is True and capture.get('http_status') == 200 and capture.get('response_status') == 'completed' and not capture.get('stream_incomplete') and not capture.get('transport_error') and not capture.get('api_error') and bool(text.strip()))
        if complete_capture:
            recomputed = adapter.score_case(record, text, random.Random(42))
            original_judge = dict(orig['judged'])
            replay_judge = dict(recomputed)
            if isinstance(original_judge.get('parsed'), list) and isinstance(replay_judge.get('parsed'), list):
                if original_judge['parsed'] != replay_judge['parsed']:
                    parser_order_only_differences += 1
                original_judge['parsed'] = sorted(original_judge['parsed'], key=canonical)
                replay_judge['parsed'] = sorted(replay_judge['parsed'], key=canonical)
            check(replay_judge == original_judge, tid + ': independent original rule replay differs')
            included = recomputed['status'] == 'PASS' and recomputed['score'] is not None
        else:
            included = False
            check(orig['score'] is None and orig['judged'] is None, tid + ': incomplete capture has score')
        check(row['included'] is included, tid + ': inclusion differs from original capture completeness')
        if included:
            completed += 1
            check(orig['status'] == 'completed_scored' and orig['score'] in (0, 1), tid + ': bad completed score')
            expected = dict(opaque_id=row['opaque_id'], question=record['prompt'], context=record['context'], accepted_references=record['target'], output_text=text)
            check(blind.get(row['opaque_id']) == expected, tid + ': blind text/source mismatch')
        else:
            check(row['opaque_id'] not in blind and row['score'] is None, tid + ': unknown included in review')
    check(completed == 69 and len(mapping) - completed == 11, 'must preserve 69 completed and 11 capture unknowns')
    expected_order = sorted(blind, key=lambda oid: sha(('order-v1:' + oid).encode()))
    check([r['opaque_id'] for r in blind_rows] == expected_order, 'blinded ordering hash mismatch')
    models = sorted({r['model'] for r in mapping_rows})
    check(len(models) == 2, 'expected two models')
    check(groupkeys == {(m, s, c) for m in models for s in sources for c in CONDITIONS}, 'must have four trials per source, 20 pairs per model')
    return mapping_rows, blind, sorted(sources), models, parser_order_only_differences


def combined(a, b, metric):
    x, y = a[metric + '_label'], b[metric + '_label']
    if x == y == 'SUPPORTED':
        return 1
    if metric == 'final' and x in DEFINITE_ZERO and y in DEFINITE_ZERO:
        return 0
    if metric == 'nonfinal' and x == y == 'NOT_OBSERVED':
        return 0
    return None


def recompute(mapping, reviews, sources, models):
    out = {'planned_trials': 80, 'completed_reviewed': 69, 'capture_unknowns': 11, 'source_questions': 20,
           'reviewers': {}, 'combined': {}, 'paired': {}, 'disagreements': {}}
    for name, rows in reviews.items():
        groups = {}
        for model in models:
            for condition in CONDITIONS:
                counts = Counter()
                for trial in mapping:
                    if trial['model'] != model or trial['condition'] != condition or not trial['included']:
                        continue
                    r = rows[trial['opaque_id']]
                    counts[(r['final_label'], r['nonfinal_label'], int(trial['score']))] += 1
                groups[model + '|' + condition] = [dict(final_label=f, nonfinal_label=n, rule_credit=c, count=num)
                    for (f, n, c), num in sorted(counts.items())]
        out['reviewers'][name] = groups
    a, b = reviews['A'], reviews['B']
    trial_values = {}
    for trial in mapping:
        oid = trial['opaque_id']
        trial_values[oid] = {'rule': trial['score'], **{metric: combined(a[oid], b[oid], metric) if trial['included'] else None for metric in ('final', 'nonfinal')}}
    for metric in ('final', 'nonfinal'):
        count = sum(a[t['opaque_id']][metric + '_label'] != b[t['opaque_id']][metric + '_label'] for t in mapping if t['included'])
        out['disagreements'][metric] = {'count': count, 'denominator': 69}
    for model in models:
        for condition in CONDITIONS:
            rows = [t for t in mapping if t['model'] == model and t['condition'] == condition]
            group = {'planned': 20, 'captured': sum(t['included'] for t in rows), 'capture_unknowns': sum(not t['included'] for t in rows)}
            for metric in ('rule', 'final', 'nonfinal'):
                values = [trial_values[t['opaque_id']][metric] for t in rows]
                known1, known0, unknown = values.count(1), values.count(0), values.count(None)
                group[metric] = {'supported_or_credit': known1, 'zero': known0, 'unknown': unknown, 'rate_bounds': [known1 / 20, (known1 + unknown) / 20]}
            out['combined'][model + '|' + condition] = group
        pairs = {}
        lookup = {(t['source_index'], t['condition']): t for t in mapping if t['model'] == model}
        for metric in ('rule', 'final', 'nonfinal'):
            details = []
            lower = upper = complete = typed_wins = binding_wins = ties = 0
            for source in sources:
                binding = trial_values[lookup[(source, 'binding_only')]['opaque_id']][metric]
                typed = trial_values[lookup[(source, 'official_typed')]['opaque_id']][metric]
                lo = (0 if typed is None else typed) - (1 if binding is None else binding)
                hi = (1 if typed is None else typed) - (0 if binding is None else binding)
                lower += lo
                upper += hi
                if typed is not None and binding is not None:
                    complete += 1
                    typed_wins += typed > binding
                    binding_wins += binding > typed
                    ties += binding == typed
                details.append(dict(source_index=source, binding_only=binding, official_typed=typed, gain_bounds=[lo, hi]))
            pairs[metric] = {'pairs': 20, 'complete_pairs': complete, 'typed_wins': typed_wins, 'binding_wins': binding_wins, 'ties': ties, 'gain_bounds': [lower / 20, upper / 20], 'pairs_detail': details}
        out['paired'][model] = pairs
    out['trial_values'] = trial_values
    return out


def load_review(path, blind):
    payload = read(path)
    # Schema will be fixed against the frozen reviewer instructions before use.
    rows = payload['cases'] if isinstance(payload, dict) else payload
    check(isinstance(rows, list), path.name + ': expected review rows')
    by_id = {r['opaque_id']: r for r in rows}
    check(len(by_id) == len(rows) == 69 and by_id.keys() == blind.keys(), path.name + ': must label all 69 unique blinded IDs')
    for oid, row in by_id.items():
        check_evidence(blind[oid]['output_text'], row, path.name + ':' + oid)
    return by_id


def compare_summary(summary, independent, mapping, reviews, work):
    """Independently reconstruct every numeric result in the frozen public schema."""
    expected_top = {'status', 'reviewed', 'capture_unknowns', 'provider_calls', 'assistant_reviewers', 'groups', 'effects', 'interpretation', 'protocol_commit'}
    check(set(summary) == expected_top, 'SUMMARY top-level schema mismatch')
    check(summary['status'] == 'complete_dual_review' and summary['reviewed'] == 69 and summary['capture_unknowns'] == 11, 'SUMMARY completion counts differ')
    check(summary['provider_calls'] == 0 and summary['assistant_reviewers'] == 2, 'SUMMARY review/call counts differ')
    check(summary['protocol_commit'] == read(work / 'INPUT_PROVENANCE.json')['protocol_commit'], 'SUMMARY frozen protocol commit mismatch')
    check(isinstance(summary['interpretation'], str) and bool(summary['interpretation'].strip()), 'SUMMARY interpretation must be nonempty prose')
    expected_groups = []
    vals = independent['trial_values']
    for key, counts in independent['combined'].items():
        model, condition = key.split('|')
        rows = [t for t in mapping if t['model'] == model and t['condition'] == condition]
        captured = [t for t in rows if t['included']]
        rater_labels = {}
        for number, name in enumerate(('A', 'B')):
            rater_labels[str(number)] = {metric: dict(Counter(reviews[name][t['opaque_id']][metric + '_label'] for t in captured)) for metric in ('final', 'nonfinal')}
        g = dict(model=model, condition=condition, total=20,
                 completed=counts['captured'], capture_unknowns=counts['capture_unknowns'],
                 original_rule_correct=counts['rule']['supported_or_credit'],
                 final_supported_bounds=[counts['final']['supported_or_credit'], counts['final']['supported_or_credit'] + counts['final']['unknown']],
                 nonfinal_supported_bounds=[counts['nonfinal']['supported_or_credit'], counts['nonfinal']['supported_or_credit'] + counts['nonfinal']['unknown']],
                 final_label_disagreements=sum(reviews['A'][t['opaque_id']]['final_label'] != reviews['B'][t['opaque_id']]['final_label'] for t in captured),
                 nonfinal_label_disagreements=sum(reviews['A'][t['opaque_id']]['nonfinal_label'] != reviews['B'][t['opaque_id']]['nonfinal_label'] for t in captured),
                 rule_credit_final_zero=sum(t['score'] == 1 and vals[t['opaque_id']]['final'] == 0 for t in captured),
                 rule_credit_final_unknown=sum(t['score'] == 1 and vals[t['opaque_id']]['final'] is None for t in captured),
                 supported_nonfinal_with_final_zero=sum(vals[t['opaque_id']]['nonfinal'] == 1 and vals[t['opaque_id']]['final'] == 0 for t in captured),
                 consensus_symbolic_final=sum(reviews['A'][t['opaque_id']]['final_label'] == reviews['B'][t['opaque_id']]['final_label'] == 'SYMBOLIC' for t in captured),
                 rater_labels=rater_labels)
        expected_groups.append(g)
    check(len(summary['groups']) == 4, 'SUMMARY must have four model-condition groups')
    actual_groups = {(g['model'], g['condition']): g for g in summary['groups']}
    check(len(actual_groups) == 4, 'SUMMARY has duplicated group')
    for g in expected_groups:
        key = (g['model'], g['condition'])
        actual = actual_groups.get(key)
        check(actual is not None, 'SUMMARY missing group ' + str(key))
        check(set(actual) == set(g), 'SUMMARY group schema differs ' + str(key))
        for field, expected in g.items():
            check(actual[field] == expected, 'SUMMARY group value differs ' + str(key) + ':' + field)
    check(len(summary['effects']) == 2, 'SUMMARY must have two per-model paired effects')
    actual_effects = {e['model']: e for e in summary['effects']}
    check(len(actual_effects) == 2, 'SUMMARY duplicates paired model effect')
    for model, metrics in independent['paired'].items():
        expected = dict(model=model, source_questions=20,
                        final_score_gain_bounds=metrics['final']['gain_bounds'],
                        nonfinal_score_gain_bounds=metrics['nonfinal']['gain_bounds'])
        check(actual_effects.get(model) == expected, 'SUMMARY source-level N20 bounds differ: ' + model)
    records = read(work / 'ADJUDICATED_RECORDS.json')
    check(isinstance(records, list) and len(records) == 80, 'ADJUDICATED_RECORDS must retain all80')
    by_id = {r['opaque_id']: r for r in records}
    check(len(by_id) == 80 and set(by_id) == {r['opaque_id'] for r in mapping}, 'ADJUDICATED_RECORDS IDs differ')
    for t in mapping:
        oid = t['opaque_id']
        labels = [{'final': reviews[name][oid]['final_label'], 'nonfinal': reviews[name][oid]['nonfinal_label']} for name in ('A', 'B')] if t['included'] else None
        expected = dict(t, final_score=vals[oid]['final'], nonfinal_score=vals[oid]['nonfinal'], labels=labels)
        check(by_id[oid] == expected, 'ADJUDICATED_RECORDS differs from independent labels/combination: ' + oid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT)
    parser.add_argument('--prepare-only', action='store_true', help='verify frozen inputs without loading review files')
    args = parser.parse_args()
    report = {'status': 'FAIL', 'verifier': 'independent_offline_v1', 'semantic_adjudication': False, 'new_network_model_api_calls': 0,
              'verification_scope': 'Frozen inputs, authoritative source/capture/request hashes, inclusion, replay of all69 optional-rule scores,69 labels per reviewer, label domains, exact output quotes, final evidence inside final span, nonfinal evidence outside a possible selected final-span occurrence, every numeric SUMMARY field and all80 ADJUDICATED_RECORDS.',
              'limitations': ['Structural and arithmetic verification does not independently validate semantic labels or official-reference truth.', 'Agreement of assistant reviewers does not establish human validation or statistically independent errors; same-model-family and prior-exposure limitations remain.', 'Pairing uses the fixed20source questions for each model; the40trials per model are not40independent questions.']}
    try:
        mapping, blind, sources, models, parser_order_differences = authoritative(args.work)
        report['input_integrity'] = {'trials': 80, 'blinded_cases': 69, 'capture_unknowns_excluded': 11, 'source_questions': 20, 'rule_scores_replayed': 69, 'parser_order_only_differences': parser_order_differences, 'parser_comparison': 'Free-form parser returns a set converted to list; compare parsed tokens as multisets only. Scores and every other judged field remain exact.'}
        if args.prepare_only:
            report['status'] = 'READY_INPUTS_VERIFIED'
        else:
            reviews = {name: load_review(args.work / ('REVIEW_' + name + '.json'), blind) for name in ('A', 'B')}
            independent = recompute(mapping, reviews, sources, models)
            summary = read(args.work / 'SUMMARY.json')
            compare_summary(summary, independent, mapping, reviews, args.work)
            report['independent_recomputation'] = independent
            report['status'] = 'PASS'
        report['verifier_sha256'] = sha(Path(__file__).read_bytes())
        report['checked_input_sha256'] = {p.name: sha(p.read_bytes()) for p in args.work.glob('*.json') if p.name in {*FROZEN, 'REVIEW_A.json', 'REVIEW_B.json', 'SUMMARY.json', 'ADJUDICATED_RECORDS.json'}}
    except Exception as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
    destination = args.work / ('VERIFIER_READINESS.json' if args.prepare_only else 'VERIFICATION.json')
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('independent_recomputation', 'checked_input_sha256')}))
    return 0 if report['status'] in ('PASS', 'READY_INPUTS_VERIFIED') else 1


if __name__ == '__main__':
    sys.exit(main())
