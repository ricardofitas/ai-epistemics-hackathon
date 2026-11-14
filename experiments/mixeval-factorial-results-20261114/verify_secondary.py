#!/usr/bin/env python3
"""Offline independent audit. Does not import the study's scorers/aggregators.

Run --packet-only before reviews exist. The default validates both independent
reviews and recomputes consensus. --summary PATH also compares an existing
SECONDARY_SUMMARY.json to the independently calculated final/content effects.
Only --output is written; all study inputs remain unchanged.
"""
import argparse
import collections
import hashlib
import itertools
import json
from pathlib import Path

CONDITIONS = ('free_form__absent', 'free_form__A.None', 'choice__absent', 'choice__A.None')
COEFFICIENTS = {
    'instruction_freeform_minus_choice_at_absent': (1, 0, -1, 0),
    'instruction_freeform_minus_choice_at_present': (0, 1, 0, -1),
    'carrier_absent_minus_present_at_freeform': (1, -1, 0, 0),
    'carrier_absent_minus_present_at_choice': (0, 0, 1, -1),
    'interaction_instruction_gain_absent_minus_present': (1, -1, -1, 1),
}

def read(p):
    return json.loads(p.read_text())

def sha(b):
    return hashlib.sha256(b).hexdigest()

def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def index(rows, field):
    require(isinstance(rows, list), f'{field}: expected list')
    require(all(isinstance(r, dict) and field in r for r in rows), f'{field}: invalid record')
    out = {r[field]: r for r in rows}
    require(len(out) == len(rows), f'{field}: duplicate identities')
    return out

def aggregate(key, scores):
    """Paired fixed-panel bounds calculated directly from 80 slots/model.

    Each slot has an independent unknown value in [0,1]. Extremizing the signed
    coefficients is exact because each contrast is linear. No imputation or
    complete-case denominator is used.
    """
    result = {}
    for model in sorted({r['model'] for r in key}):
        rows = [r for r in key if r['model'] == model]
        sources = sorted({r['source_index'] for r in rows})
        require(len(sources) == 20 and len(rows) == 80, f'{model}: panel not 20x4')
        matrix = {(r['source_index'], r['condition']): scores[r['opaque_id']] for r in rows}
        require(set(matrix) == set(itertools.product(sources, CONDITIONS)), f'{model}: crossing differs')
        counts = {}
        for c in CONDITIONS:
            vals = [matrix[s, c] for s in sources]
            require(all(v is None or (type(v) in (int, float) and v in (0, 1)) for v in vals), 'score domain')
            counts[c] = dict(planned=20, known_correct=vals.count(1), known_incorrect=vals.count(0), unknown=vals.count(None))
        effects = {}
        for name, coeffs in COEFFICIENTS.items():
            lo = hi = 0
            for s in sources:
                for c, a in zip(CONDITIONS, coeffs):
                    v = matrix[s, c]
                    if v is None:
                        lo += min(0, a)
                        hi += max(0, a)
                    else:
                        lo += a * v
                        hi += a * v
            effects[name] = dict(lower=lo / 20, upper=hi / 20)
        result[model] = dict(source_cases=20, counts=counts, contrasts=effects)
    return result

def compare_models(expected, observed, context):
    require(set(expected) == set(observed), f'{context}: model identities')
    for model, data in expected.items():
        other = observed[model]
        require(other['source_cases'] == 20, f'{context}: denominator')
        require(other['counts'] == data['counts'], f'{context}: {model} counts')
        require(set(other['contrasts']) == set(COEFFICIENTS), f'{context}: contrast names')
        for name, bounds in data['contrasts'].items():
            for endpoint, value in bounds.items():
                require(abs(other['contrasts'][name][endpoint] - value) < 1e-12, f'{context}: {model}/{name}/{endpoint}')

def review_rows(value):
    if isinstance(value, list):
        return value
    for name in ('reviews', 'annotations', 'items', 'judgments', 'records'):
        if isinstance(value.get(name), list):
            return value[name]
    raise ValueError('review JSON must be list or object with reviews/annotations/items/judgments/records list')

def validate_review(path, packet):
    rows = index(review_rows(read(path)), 'opaque_id')
    require(set(rows) == set(packet), f'{path.name}: must contain exactly 152 packet IDs')
    for oid, r in rows.items():
        require(r.get('final_label') in {'correct', 'incorrect', 'uncertain'}, f'{path.name}/{oid}: final domain')
        require(r.get('content_label') in {'correct', 'incorrect', 'uncertain'}, f'{path.name}/{oid}: content domain')
        require(r.get('tag_format') in {'compliant', 'noncompliant'}, f'{path.name}/{oid}: format domain')
        require(isinstance(r.get('reason'), str) and bool(r['reason'].strip()), f'{path.name}/{oid}: missing reason')
        require(isinstance(r.get('source_ambiguity_note'), str), f'{path.name}/{oid}: ambiguity field')
        for axis in ('final', 'content'):
            excerpt = r.get(axis + '_excerpt')
            require(isinstance(excerpt, str), f'{path.name}/{oid}: excerpt not string')
            require(not excerpt or excerpt in packet[oid]['response_text'], f'{path.name}/{oid}: excerpt not verbatim')
            require(r[axis + '_label'] != 'correct' or bool(excerpt.strip()), f'{path.name}/{oid}: correct without quote')
    return rows

def audit(args):
    root = args.root.resolve()
    actual, work = root / 'actual', root / 'work'
    key_rows, packet_rows = read(work / 'key.json'), read(work / 'packet.json')
    key, packet = index(key_rows, 'opaque_id'), index(packet_rows, 'opaque_id')
    require(len(key) == 160 and len(packet) == 152, '160 slots, 152 eligible required')
    require([r['opaque_id'] for r in packet_rows] == sorted(packet), 'packet not opaque-ID sorted')
    require(len({r['trial_id'] for r in key_rows}) == 160, 'duplicate trial IDs')
    selected = index(read(actual / 'selected20.json'), 'source_index')
    require(len(selected) == 20, 'source panel size')
    for s in selected.values():
        require(sha(canonical(s['record'])) == s['source_sha256'], 'frozen source hash mismatch')
    manifest = index([json.loads(l) for l in (actual / 'manifest.jsonl').read_text().splitlines()], 'trial_id')
    require(set(manifest) == {r['trial_id'] for r in key_rows}, 'manifest/key trial IDs')
    statuses = collections.Counter()
    missing = []
    for oid, r in key.items():
        tid = r['trial_id']
        require(oid == sha(('factorial-secondary-v1:' + tid).encode()), 'mask ID mismatch')
        m, s = manifest[tid], selected[r['source_index']]
        require(r['model'] == m['request_payload']['model'] and r['condition'] == m['condition'] and r['source_index'] == m['source_index'], 'key/manifest mismatch')
        require(r['source_sha256'] == s['source_sha256'] == m['source_sha256'], 'key/source mismatch')
        raw = read(actual / 'api_artifacts' / (tid + '.json'))
        require(raw['trial_id'] == tid, 'raw trial mismatch')
        require(raw['request_payload'] == m['request_payload'] and raw['request_sha256'] == m['request_sha256'] == sha(canonical(m['request_payload'])), 'request identity')
        require(raw['requested_model'] == raw['returned_model'] == r['model'], 'returned model mismatch')
        text = raw['output_text']
        require(isinstance(text, str), 'raw output not text')
        require(sha(text.encode()) == raw['output_text_sha256'] == r['output_sha256'], 'raw output bytes hash mismatch')
        raw_text = raw['raw_response'].get('output_text')
        require(raw_text == text, 'terminal output_text differs')
        statuses[raw['response_status']] += 1
        eligible = (raw['http_status'] == 200 and raw['response_status'] == 'completed' and bool(text.strip()) and not any(raw.get(f) for f in ('api_error', 'transport_error', 'local_capture_error', 'stream_incomplete', 'used_delta_fallback', 'stream_json_error_count')))
        require(r['eligible'] is eligible and (oid in packet) is eligible, 'eligibility mismatch')
        if eligible:
            require(r['status'] == 'completed_scored' and r['score'] in (0, 1) and r['integrity'] == 'PASS', 'eligible key state')
            p = packet[oid]
            require(set(p) == {'opaque_id', 'source_question', 'source_context', 'accepted_answers', 'response_text'}, 'unmasked packet field')
            require((p['source_question'], p['source_context'], p['accepted_answers'], p['response_text']) == (s['record']['prompt'], s['record']['context'], s['record']['target'], text), 'packet source/output bytes differ')
        else:
            require(r['score'] is None, 'ineligible output assigned score')
            missing.append(tid)
    require(len(missing) == 8 and statuses == {'completed': 152, 'incomplete': 8}, 'unknown/status counts')
    provenance = read(work / 'PACKET_PROVENANCE.json')
    for field, path in [('packet_sha256', work/'packet.json'), ('key_sha256', work/'key.json'), ('protocol_sha256', actual/'SECONDARY_ADJUDICATION_PROTOCOL.json')]:
        require(provenance[field] == sha(path.read_bytes()), f'{field}: provenance mismatch')
    primary = aggregate(key_rows, {oid: r['score'] for oid, r in key.items()})
    compare_models(primary, read(actual / 'analysis/ANALYSIS_SUMMARY.json')['factorial']['models'], 'primary')
    artifact_hashes = {r['trial_id']: sha((actual/'api_artifacts'/(r['trial_id']+'.json')).read_bytes()) for r in key_rows}
    result = dict(status='PASS', scope='offline independent secondary verification; no scorer/aggregator imports or new calls', planned=160, eligible=152, capture_unknown=8, incomplete_trial_ids=sorted(missing), response_statuses=dict(statuses), source_cases_per_model=20, primary_comparison='PASS', primary_recomputed=primary, new_api_calls=0, validated_api_artifacts=160, api_artifact_hashes_digest=sha(canonical(artifact_hashes)))
    inputs = [actual/'selected20.json', actual/'manifest.jsonl', work/'packet.json', work/'key.json', actual/'SECONDARY_ADJUDICATION_PROTOCOL.json']
    if args.packet_only:
        result['review_status'] = 'NOT_CHECKED_PACKET_ONLY'
    else:
        paths = [work/'REVIEW_A.json', work/'REVIEW_B.json']
        a, b = [validate_review(p, packet) for p in paths]
        inputs += paths
        result['review_status'] = 'PASS'
        result['review_counts'] = [len(a), len(b)]
        consensus, axes = {}, {}
        for axis in ('final', 'content'):
            field = axis + '_label'
            scores = {oid: None for oid in key}
            agreement = collections.Counter()
            for oid in packet:
                left, right = a[oid][field], b[oid][field]
                label = left if left == right and left != 'uncertain' else 'uncertain'
                scores[oid] = {'correct': 1, 'incorrect': 0, 'uncertain': None}[label]
                consensus.setdefault(oid, {})[field] = label
                agreement['identical_labels' if left == right else 'different_labels'] += 1
                agreement['consensus_' + label] += 1
                if 'uncertain' in (left, right):
                    agreement['either_uncertain'] += 1
            axes[axis] = dict(agreement=dict(agreement), models=aggregate(key_rows, scores), capture_unknown=8, consensus_unknown_eligible=sum(scores[oid] is None for oid in packet))
        result['axes'] = axes
        result['consensus'] = consensus
        result['uncertain_eligible_cases'] = [dict(trial_id=key[oid]['trial_id'], source_index=key[oid]['source_index'], **labels) for oid, labels in consensus.items() if 'uncertain' in labels.values()]
        result['limits'] = ['Quote/source/output identity and arithmetic verification does not establish external factual truth or authenticate reviewer independence.', 'Assistant adjudication and mask leakage remain limitations; exact agreement is not independent human validation.', 'Eight incomplete captures remain unknown for both axes, plus any uncertain complete judgments.']
        result['tag_format_agreement'] = sum(a[oid]['tag_format'] == b[oid]['tag_format'] for oid in packet)
        result['reviewer_axes'] = {name: {axis: aggregate(key_rows, {oid: ({'correct': 1, 'incorrect': 0, 'uncertain': None}[review[oid][axis+'_label']] if oid in packet else None) for oid in key}) for axis in ('final', 'content')} for name, review in [('A', a), ('B', b)]}
        captures_path = work/'SECONDARY_CAPTURES.json'
        if captures_path.exists():
            captures = index(read(captures_path), 'opaque_id')
            require(set(captures) == set(key), 'secondary capture IDs')
            for oid, r in key.items():
                x = captures[oid]
                require(all(x[k] == v for k, v in r.items()), 'secondary capture changed original key field')
                for axis in ('final', 'content'):
                    expected = None if oid not in packet else {'correct': 1, 'incorrect': 0, 'uncertain': None}[consensus[oid][axis+'_label']]
                    require(x[axis+'_score'] == expected, 'secondary capture consensus differs')
                expected_format = a[oid]['tag_format'] if oid in packet and a[oid]['tag_format'] == b[oid]['tag_format'] else None
                require(x['tag_consensus'] == expected_format, 'tag consensus differs')
                expected_labels = [{f: review[oid][f] for f in ('final_label', 'content_label', 'tag_format')} for review in (a, b)] if oid in packet else None
                require(x['review_labels'] == expected_labels, 'capture review labels differ')
            result['secondary_captures_comparison'] = 'PASS'
            inputs.append(captures_path)
        if args.summary:
            summary = read(args.summary)
            require((summary['planned'], summary['source_questions'], summary['reviewed'], summary['capture_unknowns']) == (160, 20, 152, 8), 'secondary summary denominators')
            require(summary['new_model_api_calls'] == summary['new_judge_api_calls'] == 0, 'secondary new calls')
            expected_agreement = {f: sum(a[oid][f] == b[oid][f] for oid in packet) for f in ('final_label', 'content_label', 'tag_format')}
            require(summary['agreement'] == expected_agreement, 'secondary agreement differs')
            expected_disagreements = sorted((oid, f, a[oid][f], b[oid][f]) for oid in packet for f in expected_agreement if a[oid][f] != b[oid][f])
            actual_disagreements = sorted((r['opaque_id'], r['dimension'], r['reviewer_a'], r['reviewer_b']) for r in summary['disagreements'])
            require(actual_disagreements == expected_disagreements, 'secondary disagreements differ')
            for axis in ('final', 'content'):
                observed = {}
                for model, data in summary['models'].items():
                    axis_data = data['axes'][axis]
                    observed[model] = dict(source_cases=data['source_cases'], counts={c: dict(planned=v['planned'], known_correct=v['correct'], known_incorrect=v['incorrect'], unknown=v['unknown']) for c, v in axis_data['counts'].items()}, contrasts=axis_data['contrasts'])
                compare_models(axes[axis]['models'], observed, 'secondary ' + axis)
            for model, data in summary['models'].items():
                model_rows = [r for r in key_rows if r['model'] == model]
                formats = {c: dict(collections.Counter((a[r['opaque_id']]['tag_format'] if r['opaque_id'] in packet and a[r['opaque_id']]['tag_format'] == b[r['opaque_id']]['tag_format'] else 'unknown') for r in model_rows if r['condition'] == c)) for c in CONDITIONS}
                require(formats == data['tag_format_counts'], 'tag format counts')
                rule_credit, content_gap = [], []
                for r in model_rows:
                    oid = r['opaque_id']
                    if oid in packet and consensus[oid]['final_label'] == 'incorrect':
                        if r['score'] == 1:
                            rule_credit.append(r['trial_id'])
                        if consensus[oid]['content_label'] == 'correct':
                            content_gap.append(r['trial_id'])
                require(sorted(rule_credit) == sorted(data['rule_credit_with_incorrect_final']), 'rule/final disagreement list')
                require(sorted(content_gap) == sorted(data['correct_content_with_incorrect_final']), 'content/final disagreement list')
            result['secondary_summary_comparison'] = 'PASS'
            inputs.append(args.summary)
    result['input_sha256'] = {str(p.relative_to(root)) if p.is_relative_to(root) else str(p): sha(p.read_bytes()) for p in inputs}
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--packet-only', action='store_true')
    ap.add_argument('--summary', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = audit(args)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'planned', 'eligible', 'capture_unknown', 'review_status')}))

if __name__ == '__main__':
    main()
