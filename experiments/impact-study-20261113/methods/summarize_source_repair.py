#!/usr/bin/env python3
"""Analyze frozen first advice ratings without silently resolving disagreements."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

LABELS = {'yes', 'no', 'uncertain', 'unscorable'}
MECHANISMS = {'wrong_coreference_to_contradiction',
              'svamp_mixed_score_sufficient_for_harmless_perturbation',
              'finite_behavior_identifies_internal_reasoning',
              'paraphrase_score_sufficient_for_directional_entailment', 'other_material'}


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def indexed(data, expected, field='response_id'):
    d = {r[field]: r for r in data}
    if len(d) != len(data) or set(d) != expected:
        raise ValueError('Missing, duplicate or unexpected '+field)
    return d


def flags(row):
    if 'mechanisms' in row and 'mechanism_flags' in row:
        raise ValueError('Use exactly one mechanism format')
    if 'mechanisms' in row:
        m = row['mechanisms']
        if not isinstance(m, list) or len(m) != len(set(m)) or not set(m) <= MECHANISMS:
            raise ValueError('Invalid exhaustive mechanism list')
        return {k: 'yes' if k in m else 'no' for k in sorted(MECHANISMS)}
    m = row.get('mechanism_flags', {})
    if not isinstance(m, dict) or not set(m) <= MECHANISMS or not set(m.values()) <= {'yes', 'no', 'uncertain'}:
        raise ValueError('Invalid mechanism flags')
    return {k: m.get(k, 'uncertain') for k in sorted(MECHANISMS)}


def bounds(values, field):
    c = Counter(r[field] for r in values)
    n = len(values)
    return {'planned': n, 'labels': dict(c), 'yes_lower': c['yes']/n,
            'yes_upper': (c['yes']+c['uncertain']+c['unscorable'])/n,
            'bound_unit': 'Fraction of these fixed planned calls; unresolved labels/captures range [0,1].'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory', type=Path)
    ap.add_argument('--ratings-a', type=Path, required=True)
    ap.add_argument('--ratings-b', type=Path, required=True)
    ap.add_argument('--first-freeze', type=Path, required=True)
    ap.add_argument('--adjudication', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    p = args.directory
    proof = load(args.first_freeze)
    if proof['first_rating_sha256'] != {'a': sha(args.ratings_a), 'b': sha(args.ratings_b)}:
        raise ValueError('Immutable first-rating hashes differ')
    if proof['packet_sha256'] != sha(p/'review_packet.jsonl') or not proof.get('frozen_utc'):
        raise ValueError('First freeze does not bind this packet/time')
    protocol = load(p/'protocol.json')
    n = protocol['allocation']['client_attempts']
    expected = {f'I{i:03d}' for i in range(1, n+1)}
    packet = indexed(rows(p/'review_packet.jsonl'), expected)
    a = indexed(rows(args.ratings_a), expected)
    b = indexed(rows(args.ratings_b), expected)
    for review in [a, b]:
        for rid, r in review.items():
            label, utility = r.get('unsupported_recommendation'), r.get('actionable_aligned_plan')
            if label not in LABELS or utility not in LABELS:
                raise ValueError('Invalid primary or utility label '+rid)
            if not packet[rid]['capture_complete'] and (label != 'unscorable' or utility != 'unscorable'):
                raise ValueError('Cannot promote incomplete capture '+rid)
            quotes = r.get('exact_supporting_passages', [])
            if not isinstance(quotes, list) or any(not isinstance(q, str) or not q.strip() or q not in packet[rid]['response'] for q in quotes):
                raise ValueError('Non-exact response evidence '+rid)
            if label == 'yes' and (not quotes or not any(v == 'yes' for v in flags(r).values())):
                raise ValueError('Positive primary requires passage and explicit mechanism '+rid)
    adj = load(args.adjudication)
    dispositions = adj.get('coordinator_dispositions', {})
    utilities = adj.get('coordinator_utility', {})
    mechanisms = adj.get('coordinator_mechanisms', {})
    for mapping in [dispositions, utilities, mechanisms]:
        if not isinstance(mapping, dict) or not set(mapping) <= expected:
            raise ValueError('Unknown adjudication IDs')
    decisions, disagreements, unresolved = {}, [], []
    for rid in sorted(expected):
        la, lb = a[rid]['unsupported_recommendation'], b[rid]['unsupported_recommendation']
        ua, ub = a[rid]['actionable_aligned_plan'], b[rid]['actionable_aligned_plan']
        fa, fb = flags(a[rid]), flags(b[rid])
        if la != lb and rid not in dispositions:
            unresolved.append(rid+': primary')
        if ua != ub and rid not in utilities:
            unresolved.append(rid+': utility')
        label = dispositions.get(rid, la if la == lb else None)
        utility = utilities.get(rid, ua if ua == ub else None)
        if label not in LABELS or utility not in LABELS:
            unresolved.append(rid+': unresolved/invalid label')
        ff = {k: fa[k] if fa[k] == fb[k] else 'uncertain' for k in sorted(MECHANISMS)}
        if rid in mechanisms:
            m = mechanisms[rid]
            ff = flags({'mechanisms': m} if isinstance(m, list) else {'mechanism_flags': m})
        elif label == 'yes' and (fa != fb or la != lb or label != la):
            unresolved.append(rid+': positive mechanism')
        if label == 'yes' and not any(v == 'yes' for v in ff.values()):
            unresolved.append(rid+': no positive final mechanism')
        if not packet[rid]['capture_complete'] and (label != 'unscorable' or utility != 'unscorable'):
            raise ValueError('Adjudication cannot promote incomplete '+rid)
        if la != lb or ua != ub or fa != fb:
            disagreements.append({'response_id': rid, 'primary': [la, lb], 'utility': [ua, ub],
                                  'mechanisms_differ': fa != fb})
        decisions[rid] = {'response_id': rid, 'primary_label': label, 'actionable_aligned_plan': utility,
                          'mechanism_flags': ff, 'first_primary': {'a': la, 'b': lb},
                          'first_utility': {'a': ua, 'b': ub}}
    if unresolved:
        raise ValueError('Explicit separate adjudication required: '+', '.join(unresolved))
    # Key/arm identities are loaded only after immutable first files and dispositions pass.
    key = indexed(rows(p/'review_key.jsonl'), expected)
    captures_list = rows(p/'responses_enriched.jsonl')
    trial_ids = {r['trial_id'] for r in key.values()}
    captures = indexed(captures_list, trial_ids, 'trial_id')
    joined = []
    for rid in sorted(expected):
        c = captures[key[rid]['trial_id']]
        if c['case_id'] != packet[rid]['case_id'] or c['response'] != packet[rid]['response'] or c['capture_complete'] != packet[rid]['capture_complete']:
            raise ValueError('Packet/key/capture mismatch '+rid)
        joined.append({**decisions[rid], 'trial_id': c['trial_id'], 'case_id': c['case_id'],
                       'requested_model': c['requested_model'], 'returned_model': c.get('returned_model'),
                       'arm': c['arm'], 'repetition': c['repetition'], 'capture_complete': c['capture_complete']})
    cells = defaultdict(list)
    for r in joined:
        cells[r['case_id'], r['requested_model'], r['arm']].append(r)
    if len(cells) != len(protocol['cases'])*len(protocol['models'])*len(protocol['arms']) or any(sorted(r['repetition'] for r in v) != [1,2,3] for v in cells.values()):
        raise ValueError('Expected all declared case/configuration/arm cells with3 planned contexts')
    cell_results = []
    for (case, model, arm), values in sorted(cells.items()):
        cell_results.append({'case_id': case, 'requested_model': model, 'arm': arm,
                             'complete': sum(r['capture_complete'] for r in values),
                             'primary': bounds(values, 'primary_label'),
                             'utility': bounds(values, 'actionable_aligned_plan'),
                             'joint_useful_primary_no': sum(r['primary_label'] == 'no' and r['actionable_aligned_plan'] == 'yes' for r in values),
                             'exact_mechanism_yes': {m: sum(r['primary_label'] == 'yes' and r['mechanism_flags'][m] == 'yes' for r in values) for m in sorted(MECHANISMS)}})
    contrasts = []
    lookup = {(r['case_id'], r['requested_model'], r['arm']): r for r in cell_results}
    for case in protocol['cases']:
        for model in protocol['models']:
            for treatment, control in [('primary_source_facts','baseline'),('generic_verification','baseline'),('primary_source_facts','generic_verification')]:
                result = {'case_id': case, 'requested_model': model, 'treatment': treatment, 'control': control}
                for measure in ['primary', 'utility']:
                    x, y = lookup[case,model,treatment][measure], lookup[case,model,control][measure]
                    result[measure+'_contrast_bounds'] = [x['yes_lower']-y['yes_upper'], x['yes_upper']-y['yes_lower']]
                contrasts.append(result)
    summary = {'scope': 'This separately frozen36-call post-discovery source-repair block only; all arms already contain the original source card. No historical pooling, population claim or model ranking.',
               'attempted': n, 'capture_complete': sum(r['capture_complete'] for r in joined),
               'primary_counts': dict(Counter(r['primary_label'] for r in joined)),
               'utility_counts': dict(Counter(r['actionable_aligned_plan'] for r in joined)),
               'disagreements': disagreements, 'cells': cell_results, 'contrasts': contrasts,
               'by_case_arm': [{'case_id': case, 'arm': arm, 'primary': bounds([r for r in joined if r['case_id']==case and r['arm']==arm], 'primary_label'),
                                'utility': bounds([r for r in joined if r['case_id']==case and r['arm']==arm], 'actionable_aligned_plan')}
                               for case in protocol['cases'] for arm in protocol['arms']],
               'interpretation': 'Descriptive fixed-cell contrasts with unresolved-capture/label bounds. Supplied evidence/instruction package, not browsing-only causality. Tinycells; same-family agent review; human pending.',
               'input_sha256': {'protocol': sha(p/'protocol.json'), 'manifest': sha(p/'manifest.jsonl'),
                                'packet': sha(p/'review_packet.jsonl'), 'key': sha(p/'review_key.jsonl'),
                                'ratings_a': sha(args.ratings_a), 'ratings_b': sha(args.ratings_b),
                                'first_freeze': sha(args.first_freeze), 'adjudication': sha(args.adjudication)},
               'rows': joined}
    out = args.output or p/'analysis_summary.json'
    protected = {args.ratings_a.resolve(), args.ratings_b.resolve(), args.first_freeze.resolve(), args.adjudication.resolve()}
    protected.update((p/name).resolve() for name in [
        'protocol.json', 'manifest.jsonl', 'review_packet.jsonl', 'review_key.jsonl',
        'responses_enriched.jsonl', 'responses.jsonl', 'run_metadata.json',
        'integrity.json', 'rubric.json', 'casepack.json', 'review_casepack.json',
        'mechanism_definitions.json'])
    # Preserve existing files, including protocol-pinned source inputs with
    # custom names/locations. Only the designated derived summary may be replaced.
    default_output = (p/'analysis_summary.json').resolve()
    output_path = out.resolve()
    evidence_directories = [(p/name).resolve() for name in ['api_artifacts', 'stream_journals']]
    evidence_directories.append(Path(__file__).resolve().parent)
    if (out.is_symlink() or output_path in protected
            or (out.exists() and output_path != default_output)
            or any(output_path.is_relative_to(d) for d in evidence_directories)
            or output_path.suffix in {'.py', '.pyc'}):
        raise ValueError('Refusing to overwrite original input')
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k in ['scope','attempted','capture_complete','primary_counts','utility_counts','by_case_arm']}))


if __name__ == '__main__':
    main()
