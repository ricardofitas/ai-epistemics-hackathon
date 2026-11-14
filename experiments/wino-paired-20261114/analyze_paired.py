"""Analyze the frozen paired panel using source gold and the shipped scorer."""
import copy
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'default_contract_audit_20261113'))
import audit_contracts as audit
from analyze_model_smoke import strict_answer

CONDITIONS = ['native_prompt', 'corrected_prompt']
STRATA = ['contradictory_pair', 'singleton_control']


def lines(path):
    with gzip.open(path, 'rt') as source:
        return [json.loads(line) for line in source]


def bounds(rows):
    n = len(rows)
    correct = sum(row['source_correct'] == 1 for row in rows)
    unknown = sum(row['source_correct'] is None for row in rows)
    return {'planned': n, 'complete': sum(row['completed_nonempty'] for row in rows),
            'correct': correct, 'unknown': unknown,
            'accuracy_if_unknown_zero': correct / n, 'accuracy_bounds': [correct / n, (correct + unknown) / n],
            'http_statuses': dict(Counter(str(row['http_status']) for row in rows)),
            'parsed_answers': dict(Counter(str(row['parsed_answer']) for row in rows))}


def paired_summary(pairs):
    groups = defaultdict(list)
    discordant = Counter()
    unknown_pairs = 0
    for pair in pairs:
        native, fixed = pair['native_prompt']['source_correct'], pair['corrected_prompt']['source_correct']
        # The primary displayed interval uses unknown-as-zero. Sensitivity bounds
        # preserve every unknown in each member of the pair.
        lower = (fixed or 0) - (1 if native is None else native)
        upper = (1 if fixed is None else fixed) - (native or 0)
        groups[(pair['stratum'], pair['group'])].append(((fixed or 0) - (native or 0), lower, upper))
        if native is None or fixed is None:
            unknown_pairs += 1
        else:
            discordant[f'{native}->{fixed}'] += 1
    # Resample the dependency groups within each fixed stratum. All groups in a
    # stratum have the same size, so this also preserves its question weighting.
    by_stratum = defaultdict(list)
    for (stratum, group), values in sorted(groups.items()):
        by_stratum[stratum].append(np.array(values, dtype=float).mean(axis=0))
    rng = np.random.default_rng(20261113)
    bootstrap = np.zeros((10000, 3))
    direct = np.zeros(3)
    for stratum in STRATA:
        if stratum not in by_stratum:
            continue
        values = np.array(by_stratum[stratum])
        weight = sum(pair['stratum'] == stratum for pair in pairs) / len(pairs)
        sampled = rng.integers(0, len(values), size=(10000, len(values)))
        bootstrap += weight * values[sampled].mean(axis=1)
        direct += weight * values.mean(axis=0)
    return {'questions': len(pairs), 'dependency_groups': len(groups),
            'difference_corrected_minus_native_unknown_zero': float(direct[0]),
            'paired_difference_sensitivity_bounds': [float(direct[1]), float(direct[2])],
            'bootstrap_95_percentile_unknown_zero': np.quantile(bootstrap[:, 0], [0.025, 0.975]).tolist(),
            'bootstrap_95_percentile_sensitivity_envelope': [float(np.quantile(bootstrap[:, 1], .025)), float(np.quantile(bootstrap[:, 2], .975))],
            'complete_pair_transitions': dict(discordant), 'unknown_pairs': unknown_pairs,
            'bootstrap_draws': 10000, 'bootstrap_seed': 20261113}


def run_scorer(frame, original_contract, reference_key, Runner, BenchInfo):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'rows.jsonl'
        path.write_text(''.join(audit.compact(row) + '\n' for row in frame.to_dict('records')))
        bench = BenchInfo(bench_name='winogrande', meta={'artifact_paths': {'records': str(path)},
                          'pred_key': 'generated_ans', 'ref_key': reference_key})
        return Runner(max_workers=2).run_bench_with_contract(bench, original_contract)['primary_metric_result']


def main():
    capture = ROOT / 'capture'
    cases = {row['source_row']: row for row in lines(ROOT / 'fresh_panel.jsonl.gz')}
    manifest = lines(ROOT / 'planned_requests.jsonl.gz')
    response_rows = [json.loads(line) for line in (capture / 'responses.jsonl').read_text().splitlines()]
    responses = {row['trial_id']: row for row in response_rows}
    assert len(cases) == 50 and len(manifest) == len(response_rows) == len(responses) == 200
    assert set(responses) == {row['trial_id'] for row in manifest}
    rows = []
    for request in manifest:
        response = responses[request['trial_id']]
        case = cases[request['source_row']]
        assert request['request_payload']['input'] == case[request['condition']]
        assert response['request_payload'] == request['request_payload']
        completed = bool(response.get('completed_nonempty'))
        parsed = strict_answer(response.get('output_text'), ['A', 'B']) if completed else None
        rows.append(dict(trial_id=request['trial_id'], source_row=request['source_row'],
                         stratum=case['stratum'], group=case['dependency_group'],
                         model=request['request_payload']['model'], condition=request['condition'],
                         gold=case['gold'], completed_nonempty=completed, http_status=response.get('http_status'),
                         response_status=response.get('response_status'), parsed_answer=parsed,
                         source_correct=None if parsed is None else int(parsed == case['gold'])))
    models = sorted({row['model'] for row in rows})
    condition_scores = []
    paired_scores = []
    collisions = []
    for model in models:
        for stratum in [*STRATA, 'all_frozen_panel']:
            selected = [row for row in rows if row['model'] == model and (stratum == 'all_frozen_panel' or row['stratum'] == stratum)]
            for condition in CONDITIONS:
                within = [row for row in selected if row['condition'] == condition]
                condition_scores.append(dict(model=model, stratum=stratum, condition=condition, **bounds(within)))
            item_pairs = defaultdict(dict)
            for row in selected:
                item_pairs[row['source_row']][row['condition']] = row
            pairs = [dict(native_prompt=p['native_prompt'], corrected_prompt=p['corrected_prompt'],
                          group=p['native_prompt']['group'], stratum=p['native_prompt']['stratum']) for p in item_pairs.values()]
            paired_scores.append(dict(model=model, stratum=stratum, **paired_summary(pairs)))
        paired_groups = defaultdict(list)
        for row in rows:
            if row['model'] == model and row['condition'] == 'native_prompt' and row['stratum'] == 'contradictory_pair':
                paired_groups[row['group']].append(row)
        for group, members in paired_groups.items():
            assert len(members) == 2 and {row['gold'] for row in members} == {'A', 'B'}
            collisions.append(dict(model=model, group=group, parsed_answers=[m['parsed_answer'] for m in members],
                                   same_answer=members[0]['parsed_answer'] is not None and members[0]['parsed_answer'] == members[1]['parsed_answer'],
                                   known_correct=sum(m['source_correct'] == 1 for m in members),
                                   unknown=sum(m['source_correct'] is None for m in members)))

    # Replay the exact raw outputs with one native parsing/scoring implementation.
    # Only the reference field is changed between these two paths.
    raw_source = lines(audit.CAPTURE / 'winogrande__validation.jsonl.gz')
    gallery = json.loads((audit.ROOT / 'GALLERY_SELECTED.json').read_text())['benches']
    entry = next(e for e in gallery if e['bench_name'] == 'winogrande')
    contract = entry['meta']['evaluation']
    BenchInfo, Runner = audit.load_components()
    score_replays = []
    for model in models:
        for stratum in [*STRATA, 'all_frozen_panel']:
            for condition in CONDITIONS:
                selected = [row for row in rows if row['model'] == model and row['condition'] == condition
                            and (stratum == 'all_frozen_panel' or row['stratum'] == stratum)]
                records = []
                for row in selected:
                    source = copy.deepcopy(raw_source[row['source_row']])
                    # The selection canonicalizer sorts source keys.
                    expected_hash = hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
                    assert expected_hash == cases[row['source_row']]['source_sha256']
                    source['generated_ans'] = responses[row['trial_id']].get('output_text') or ''
                    source['_canonical_gold'] = '<answer>' + row['gold'] + '</answer>'
                    records.append(source)
                frame, mapping = audit.load_preprocessor()._preprocess_dataframe(pd.DataFrame(records), 'winogrande',
                                  copy.deepcopy(entry['meta']['key_mapping']), eval_type='key3_q_choices_a')
                for predictor in ['model', 'always_A', 'always_B']:
                    current = frame.copy()
                    if predictor != 'model':
                        current['generated_ans'] = '<answer>' + predictor[-1] + '</answer>'
                    shipped = run_scorer(current, contract, mapping['input_label_key'], Runner, BenchInfo)
                    fixed = run_scorer(current, contract, '_canonical_gold', Runner, BenchInfo)
                    score_replays.append(dict(model=model, stratum=stratum, condition=condition, predictor=predictor,
                                             shipped=shipped, source_reference=fixed))
                    if predictor != 'model':
                        assert fixed['score'] == .5
                        assert shipped['score'] == float(predictor == 'always_B')
                    else:
                        from one_eval.metrics.parsers import parse_value
                        predicted = [parse_value(r['generated_ans'], contract['parser'], record=r) for r in current.to_dict('records')]
                        source_score = sum(p.ok and p.normalized == row['gold'] for p, row in zip(predicted, selected)) / len(selected)
                        native_score = sum(p.ok and p.normalized == 'B' for p in predicted) / len(predicted)
                        assert abs(source_score - fixed['score']) < 1e-12
                        assert abs(native_score - shipped['score']) < 1e-12
    result = dict(planned_requests=200, recorded_requests=len(rows), complete_responses=sum(r['completed_nonempty'] for r in rows),
                  unique_source_questions=50, independent_prompt_groups=35,
                  selection='Frozen diagnostic strata, enriched for native input collisions, source labels balanced. Overall values use the 30/20 panel mix.',
                  condition_scores=condition_scores, paired_scores=paired_scores, native_collision_group_responses=collisions,
                  raw_output_reference_replays=score_replays,
                  uncertainty='Paired cluster bootstrap within each frozen stratum. Intervals are percentile intervals for each comparison; no simultaneous coverage or population prevalence inference is claimed. Unknown-as-zero and sensitivity bounds are reported together.')
    (ROOT / 'ROW_ANALYSIS.json').write_text(json.dumps(rows, indent=2) + '\n')
    (ROOT / 'RESULTS.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ['planned_requests','recorded_requests','complete_responses']}))
    print(json.dumps(paired_scores, indent=2))


if __name__ == '__main__':
    main()
