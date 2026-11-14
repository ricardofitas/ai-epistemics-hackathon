"""Compare task-aware adapter with all saved official-rule captures."""
from collections import Counter
import copy
import gzip
import hashlib
import json
from pathlib import Path
import random
import sys

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P))
from scoring_adapter import score_case


def main():
    frozen = json.loads((P / 'FROZEN_IMPLEMENTATION.json').read_text())
    for name, digest in frozen.items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == digest
    selected = [json.loads(line) for line in gzip.decompress((P / 'SELECTED.jsonl.gz').read_bytes()).splitlines()]
    lookup = {(s['split'], s['source_index']): s['record'] for s in selected}
    captures = [json.loads(line) for line in gzip.decompress((P / 'SCORING_CAPTURES.jsonl.gz').read_bytes()).splitlines()]
    official = [c for c in captures if c['condition'] == 'official_rule_type_dispatch']
    assert len(official) == 800
    rng = random.Random(42)
    errors = []
    grouped = Counter()
    random_draws = []
    retained_alias_misses = []
    for capture in official:
        record = lookup[capture['split'], capture['source_index']]
        original = copy.deepcopy(record)
        observed = score_case(record, capture['constructed_response'], rng)
        expected = capture['result']
        identity = {key: capture[key] for key in ['split', 'source_index', 'output_family']}
        if observed['status'] != 'PASS':
            errors.append(dict(identity, reason='valid_source_not_scored', result=observed))
            continue
        parsed_equal = (sorted(map(repr, observed['parsed'])) == sorted(map(repr, expected['parsed']))) if isinstance(observed['parsed'], list) else observed['parsed'] == expected['parsed']
        if not parsed_equal or observed['score'] != expected['eval_score'] or observed['random_fallback'] != expected['random_fallback']:
            errors.append(dict(identity, reason='capture_mismatch', observed=observed, expected=expected))
        assert original == record
        grouped[capture['split'] + ':' + capture['output_family']] += 1
        random_draws.extend(observed['random_draws'])
        if capture['split'] == 'free_form' and capture['output_family'] == 'source_first_reference' and observed['score'] == 0:
            retained_alias_misses.append(capture['source_index'])
    free = next(s['record'] for s in selected if s['split'] == 'free_form')
    mc = next(s['record'] for s in selected if s['split'] == 'multiple_choice')
    def changed(source, **values):
        result = copy.deepcopy(source)
        result.update(values)
        return result
    bad_cases = [
        ('source_none', None, '', random.Random(1)),
        ('unknown_problem_type', changed(free, problem_type='unsupported'), '', random.Random(1)),
        ('problem_type_list', changed(free, problem_type=[]), '', random.Random(1)),
        ('problem_type_dict', changed(free, problem_type={}), '', random.Random(1)),
        ('missing_prompt', changed(free, prompt=None), '', random.Random(1)),
        ('empty_benchmark', changed(free, benchmark_name=''), '', random.Random(1)),
        ('invalid_context', changed(free, context=['x']), '', random.Random(1)),
        ('missing_response', free, None, random.Random(1)),
        ('empty_targets', changed(free, target=[]), '', random.Random(1)),
        ('nontext_freeform_alias', changed(free, target=[1]), '', random.Random(1)),
        ('nonlist_freeform_options', changed(free, options={}), '', random.Random(1)),
        ('unsupported_QuAc_prompt', changed(free, benchmark_name='QuAc'), '', random.Random(1)),
        ('choice_one_option', changed(mc, options=['one']), '', random.Random(1)),
        ('choice_bool_target', changed(mc, target=[True]), '', random.Random(1)),
        ('choice_string_target', changed(mc, target=['0']), '', random.Random(1)),
        ('choice_index_outside', changed(mc, target=[len(mc['options'])]), '', random.Random(1)),
        ('choice_blank_text', changed(mc, options=['one', ' ']), '', random.Random(1)),
        ('choice_alphabet_overflow', changed(mc, options=[str(i) for i in range(27)]), '', random.Random(1)),
        ('choice_missing_rng', mc, '', None),
    ]
    malformed_results = []
    for name, record, response, bad_rng in bad_cases:
        try:
            result = score_case(record, response, bad_rng)
        except Exception as exc:
            result = {'status': 'UNHANDLED_EXCEPTION', 'exception': repr(exc)}
        ok = result['status'] == 'INCOMPLETE' and result['score'] is None
        malformed_results.append({'case': name, 'passed': ok, 'result': result})
        if not ok:
            errors.append({'malformed_case': name, 'reason': 'did_not_fail_closed', 'result': result})
    expected_draws = json.loads((P / 'COUNTEREXAMPLES.json').read_text())['official_empty_MC_probe']['guesses']
    assert random_draws == [draw['result'] for draw in expected_draws]
    assert set(retained_alias_misses) == {1425, 1248}
    for name, digest in frozen.items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == digest
    report = {
        'status': 'PASS' if not errors else 'FAIL',
        'adapter_sha256': hashlib.sha256((P / 'scoring_adapter.py').read_bytes()).hexdigest(),
        'reviewer': 'separate delegated scoring_review agent',
        'official_capture_comparisons': len(official), 'panel_coverage': dict(grouped),
        'same_random_seed_and_order': True, 'random_fallback_draws_matched': len(random_draws),
        'preserved_official_first_alias_miss_indices': retained_alias_misses,
        'source_records_unchanged': True,
        'malformed_source_or_response_cases': len(bad_cases),
        'malformed_cases_passed': sum(case['passed'] for case in malformed_results),
        'malformed_case_details': malformed_results,
        'frozen_files_unchanged': len(frozen), 'provider_model_calls': 0,
        'errors': errors,
        'scope': 'Integration wrapper equivalence to pinned optional official-rule captures, including its imperfect alias parsing and random fallback. No default model-judge mode, model outputs or leaderboard score.',
    }
    (P / 'ADAPTER_VERIFICATION.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ['malformed_case_details', 'panel_coverage']}))


if __name__ == '__main__':
    main()
