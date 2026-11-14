"""Independent saved-artifact/source reconciliation, without native reruns."""
import ast
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import re
from types import SimpleNamespace

import numpy as np

P = Path(__file__).resolve().parents[1]
I = P / 'integration'
canonical = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
digest = lambda value: hashlib.sha256(canonical(value).encode()).hexdigest()
text_hash = lambda value: hashlib.sha256(value.encode()).hexdigest()


class Draws:
    def __init__(self):
        self.rng = random.Random(42)
        self.values = []

    def choice(self, choices):
        answer = self.rng.choice(choices)
        self.values.append(answer)
        return answer


def load_rules():
    path = I / 'support/official/mix_eval/utils/metric_utils.py'
    names = {'find_all_sub', 'parse_multi_choice_response_rule', 'check_is_number',
             'normalize_str', 'extract_numbers', 'parse_freeform_response_rule',
             'eval_multi_choice', 'eval_freeform_rule'}
    nodes = [node for node in ast.parse(path.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == len(names)
    rng = Draws()
    scope = {'re': re, 'np': np, 'random': rng}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), 'exec'), scope)
    return scope, rng


def main():
    frozen = json.loads((I / 'FROZEN_IMPLEMENTATION.json').read_text())
    manifest = frozen['files']
    for name, meta in manifest.items():
        assert hashlib.sha256((I / name).read_bytes()).hexdigest() == meta['sha256'], name
    public = P / 'public-replay'
    selected = [json.loads(x) for x in gzip.decompress((public / 'input/SELECTED.jsonl.gz').read_bytes()).splitlines()]
    sources = {(row['split'], row['source_index']): row['record'] for row in selected}
    captures = [json.loads(x) for x in gzip.decompress((public / 'CAPTURES.jsonl.gz').read_bytes()).splitlines()]
    capture_by_id = {row['split'] + ':' + str(sources[row['split'], row['source_index']]['id']): row for row in captures}
    assert len(captures) == len(capture_by_id) == 49
    official = I / 'support/official/mix_eval/prompts/evaluation_prompts.py'
    prompt_scope = {'__name__': 'independent_pinned_official_prompts'}
    exec(compile(official.read_bytes(), str(official), 'exec'), prompt_scope)
    helper_sha = hashlib.sha256((I / 'support/official/mix_eval/utils/metric_utils.py').read_bytes()).hexdigest()
    vendor_manifest = json.loads((I / 'VENDORED_MODULES.json').read_text())
    generator_ast = ast.parse((I / 'vendor/dataflow/operators/core_text/generate/bench_answer_generator.py').read_text())
    generator_class = next(node for node in generator_ast.body if isinstance(node, ast.ClassDef) and node.name == 'BenchAnswerGenerator')
    constructor = next(node for node in generator_class.body if isinstance(node, ast.FunctionDef) and node.name == '__init__')
    defaults = dict(zip([arg.arg for arg in constructor.args.args][-len(constructor.args.defaults):], constructor.args.defaults))
    native_system_prompt = ast.literal_eval(defaults['system_prompt'])
    derived_path_resolutions = {}
    def resolve_origin(raw_origin):
        marker = '/integration/vendor/'
        assert isinstance(raw_origin, str) and raw_origin.count(marker) == 1
        suffix = raw_origin.split(marker, 1)[1]
        assert suffix in vendor_manifest
        relative = Path(suffix)
        assert not relative.is_absolute() and '..' not in relative.parts
        local = (I / 'vendor' / relative).resolve()
        assert local.is_relative_to((I / 'vendor').resolve())
        assert hashlib.sha256(local.read_bytes()).hexdigest() == vendor_manifest[suffix]['sha256']
        # Raw artifact paths identify the original execution. Resolve a strict
        # manifest-listed suffix locally; never rewrite raw RESULT metadata.
        original_available = Path(raw_origin).is_file()
        if original_available:
            assert hashlib.sha256(Path(raw_origin).read_bytes()).hexdigest() == vendor_manifest[suffix]['sha256']
        derived_path_resolutions[raw_origin] = {'original_path': raw_origin, 'resolved_local_path': str(local),
                                               'original_path_available': original_available,
                                               'sha256': vendor_manifest[suffix]['sha256']}
        return local
    summaries = []
    corrected_provenance = []
    native_id_coercions = 0
    seen_public_ids = set()
    for split, expected_n in [('free_form', 17), ('multiple_choice', 32)]:
        bundle = json.loads((I / 'inputs' / (split + '.json')).read_text())
        result = json.loads((I / 'results' / split / 'RESULT.json').read_text())
        assert result['status'] == 'PASS'
        assert result['installed_distribution'] is False
        assert result['native_primary_metric_stage_executed'] is False
        assert result['new_model_calls'] == 0 and result['generation_calls'] == 1
        assert result['shim_events'] == [] and result['native_return_role'] == 'diagnostic'
        assert result['source_rows'] == result['scored_rows'] == expected_n
        records = bundle['records']
        assert len(records) == len(bundle['outputs']) == len(result['score_captures']) == expected_n
        ids = [split + ':' + str(record['id']) for record in records]
        assert result['coverage'] == {'source_ids': ids, 'complete': True}
        public_ids = [key for key in capture_by_id if key.startswith(split + ':')]
        assert ids == public_ids
        seen_public_ids.update(ids)
        outputs = {row['case_id']: row for row in bundle['outputs']}
        prompts = [prompt_scope['construct_prompt_freeform' if split == 'free_form' else 'construct_prompt_multichoice'](record) for record in records]
        assert len(result['serving_requests']) == 1
        assert result['serving_requests'][0]['prompts'] == prompts
        assert result['serving_requests'][0]['system_prompt'] == native_system_prompt
        for origin in result['module_origins'].values():
            resolve_origin(origin)
        for origin in result['entry_points'].values():
            resolve_origin(origin)
        steps = list((I / 'results' / split / 'native').glob('*_steps/step_step2.jsonl'))
        assert len(steps) == 1
        derived_path_resolutions['native_detail_' + split] = {
            'original_path': result['native_return']['detail_path'], 'resolved_local_path': str(steps[0].resolve()),
            'resolution': 'Strict local native result directory lookup, not the old absolute artifact path',
        }
        native_rows = [json.loads(line) for line in steps[0].read_text().splitlines()]
        assert len(native_rows) == expected_n
        functions, rng = load_rules()
        args = SimpleNamespace(model_type='ChatModel')
        scores = []
        for key, record, capture, native in zip(ids, records, result['score_captures'], native_rows):
            public_capture = capture_by_id[key]
            original = sources[public_capture['split'], public_capture['source_index']]
            assert record == original
            source_sha = digest(original)
            assert bundle['expected_sources'][key] == outputs[key]['source_sha256'] == source_sha
            response = outputs[key]['response']
            assert response == public_capture['captured_text']
            response_sha = text_hash(response)
            assert bundle['expected_responses'][key] == capture['response_sha256'] == response_sha
            assert native['_case_id'] == key
            assert json.loads(native['_source_json']) == original
            assert digest(json.loads(native['_source_json'])) == source_sha
            assert native['generated_ans'] == response
            for field in ['problem_type', 'prompt', 'target', 'benchmark_name', 'options', 'context']:
                assert native[field] == original[field], (key, field)
            assert str(native['id']) == str(original['id'])
            native_id_coercions += type(native['id']) is not type(original['id'])
            before = len(rng.values)
            if split == 'free_form':
                parsed = functions['parse_freeform_response_rule'](args, response)
                score = float(functions['eval_freeform_rule'](original['target'], parsed))
                assert sorted(map(repr, capture['parsed'])) == sorted(map(repr, parsed))
            else:
                labels = [chr(65 + j) for j in range(len(original['options']))]
                parsed = functions['parse_multi_choice_response_rule'](args, response, labels, dict(zip(labels, original['options'])))
                score = float(functions['eval_multi_choice'](labels[original['target'][0]], parsed))
                assert capture['parsed'] == parsed
            assert capture['score'] == native['eval_score'] == score
            assert native['eval_valid'] is True and native['eval_error'] == ''
            assert capture['random_fallback'] == (len(rng.values) > before)
            assert capture['random_draws'] == rng.values[before:]
            assert capture['case_id'] == key and capture['status'] == 'PASS'
            # Retain the original capture issue; recover record provenance
            # from independently reconciled inputs and native source carrier.
            assert capture['source_sha256'] == helper_sha
            assert capture['source_sha256'] != source_sha
            corrected_provenance.append({'case_id': key, 'original_public_source_index': public_capture['source_index'],
                                         'source_record_sha256': source_sha, 'scorer_source_sha256': helper_sha,
                                         'response_sha256': response_sha,
                                         'raw_capture_source_sha256': capture['source_sha256']})
            scores.append(score)
        stats = result['native_return']['stats']
        assert stats['role'] == 'diagnostic' and stats['display_as_primary'] is False
        assert stats['total_samples'] == stats['valid_samples'] == expected_n
        assert result['typed_rule_mean'] == sum(scores) / expected_n
        assert math.isclose(stats['accuracy'], sum(scores) / expected_n, abs_tol=1e-9)
        summaries.append({'split': split, 'rows': expected_n, 'correct': sum(scores),
                          'native_total_samples': stats['total_samples'], 'native_valid_samples': stats['valid_samples'],
                          'independent_score_mean': sum(scores) / expected_n, 'random_fallback_draws': list(rng.values),
                          'legacy_native_metric_label': stats['metric'],
                          'actual_scoring_mode': result['scoring_mode']})
    assert seen_public_ids == set(capture_by_id)
    controls = json.loads((P / 'reviewer/COVERAGE_CONTROL_VERIFICATION.json').read_text())
    assert controls['status'] == 'PASS' and len(controls['controls']) == 10
    assert all(c['passed'] and c['typed_rule_mean'] is None and c['local_generation_batches'] == 0 for c in controls['controls'])
    for name, meta in manifest.items():
        assert hashlib.sha256((I / name).read_bytes()).hexdigest() == meta['sha256']
    erratum = {
        'status': 'DERIVED_PROVENANCE_ERRATUM_RAW_RESULTS_PRESERVED',
        'issue': 'score_captures dictionaries assign source_sha256 for the source record, then unpack adapter result whose source_sha256 means official helper code. The latter overwrites the former in all49rows.',
        'effect': 'Source/response association guards and scores were independently verified. The raw capture source_sha256 field identifies scorer code, not the source record. No native rerun or raw RESULT rewrite occurred.',
        'corrected_rows': corrected_provenance,
        'legacy_metric_label_issue': 'Native diagnostic metric labels any_math_verify/parse_choice_acc remain inherited configuration labels after declared private scoring-method replacements. They do not describe the actual official optional-rule algorithm. Actual mode and all replacements remain explicit.',
    }
    (P / 'reviewer/SOURCE_PROVENANCE_ERRATUM.json').write_text(json.dumps(erratum, indent=2) + '\n')
    report = {
        'status': 'PASS_WITH_PROVENANCE_ERRATUM', 'reviewer': 'separate scoring_review agent',
        'frozen_protocol_commit': '0e2616f099b5f5defb395f3d545b3736c23b063a',
        'frozen_files_verified': len(manifest), 'source_rows_reconciled': 49,
        'request_prompts_reconstructed': 49, 'response_bytes_reconciled': 49,
        'official_rule_scores_independently_reexecuted': 49,
        'local_serving_batches': 2, 'new_provider_model_calls': 0,
        'native_entrypoint_reruns_by_reviewer': 0,
        'native_primary_metric_stage_executed': False, 'installed_distribution': False,
        'dependency_shim_invocations_reported': 0, 'coverage_controls_passed': 10,
        'native_id_type_coercions_preserving_case_association': native_id_coercions,
        'source_hash_capture_key_collisions': len(corrected_provenance),
        'derived_path_resolutions': list(derived_path_resolutions.values()),
        'native_system_prompt_verified_from_constructor_default': native_system_prompt,
        'retained_verifier_development_assumption': 'Initial review assumed an empty system prompt. Integration correctly retains the pinned native generator default, unlike the separate paired real-generation payloads. Assertion corrected from exact constructor source; no scientific artifacts changed.',
        'panels': summaries,
        'scope': 'Saved full-module native orchestration artifacts and exact source/requests/responses/storage/statistics reconciled; official rule scorer independently re-executed. Local captured-output provider and explicit package/dependency facades. Neither full installed distribution nor new model/transport execution.',
    }
    (P / 'reviewer/NATIVE_INTEGRATION_VERIFICATION.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
