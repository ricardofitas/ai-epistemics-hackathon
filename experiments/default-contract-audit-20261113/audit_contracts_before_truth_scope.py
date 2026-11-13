"""Executable validity checks of default contracts on frozen real source rows.

All predictions here are explicitly constructed controls, not model responses.
The original One-Eval parser/scorer/MetricRunner and preprocessing methods run
unchanged; the graph/serving imports are replaced by the documented data-only scaffold.
"""
import ast
import copy
import gzip
import hashlib
import json
import logging
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT.parent / 'default_contract_source_capture_20261113' / 'capture'
REPRO = ROOT.parent / 'oneeval_alias_evidence_20261113'
if not REPRO.is_dir():
    REPRO = ROOT.parent / 'oneeval-alias-audit-20261113'
sys.path.insert(0, str(REPRO))
from reproduce_alias import load_components


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), default=str)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')


def load_preprocessor():
    source = ROOT / 'upstream/dataflow_eval_tool.py'
    tree = ast.parse(source.read_text())
    node = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'DataFlowEvalTool')
    namespace = {'pd': pd, 'json': json, 're': re, 'Path': Path,
                 'Any': Any, 'Dict': Dict, 'List': List, 'Optional': Optional,
                 'log': logging.getLogger('source_preprocessing')}
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future, node], type_ignores=[]))
    exec(compile(module, str(source), 'exec'), namespace)
    return namespace['DataFlowEvalTool'].__new__(namespace['DataFlowEvalTool'])


def semantic_source(name, row):
    """Independent, explicit source-specific gold semantics; no heuristic parser."""
    if name == 'sciq':
        return [row[k] for k in ('correct_answer', 'distractor1', 'distractor2', 'distractor3')], 0
    if name == 'winogrande':
        answer = str(row['answer']).strip()
        return [row['option1'], row['option2']], int(answer) - 1 if answer else None
    if name == 'boolq':
        assert isinstance(row['answer'], bool)
        return ['true', 'false'], 0 if row['answer'] else 1
    if name == 'pubmedqa':
        choices = ['yes', 'no', 'maybe']
        return choices, choices.index(row['final_decision'])
    if name == 'medmcqa':
        return [row[k] for k in ('opa', 'opb', 'opc', 'opd')], int(row['cop'])
    if name == 'hellaswag':
        return row['endings'], int(row['label'])
    if name == 'piqa':
        return [row['sol1'], row['sol2']], int(row['label'])
    if name == 'lab-bench-language-agent-biology-benchmark':
        return [row['ideal'], *row['distractors']], 0
    raise ValueError(name)


def native_display_choices(row, mapping):
    key = mapping.get('input_choices_key')
    if not isinstance(key, str) or key not in row:
        return None
    value = row[key]
    return [str(x) for x in value] if isinstance(value, list) else None


def main():
    BenchInfo, Runner = load_components()
    preprocess = load_preprocessor()
    gallery = json.loads(gzip.decompress((CAPTURE / 'one_eval__utils__bench_table__bench_gallery.json.gz').read_bytes()))
    gallery = {x['bench_name']: x for x in gallery['benches']}
    dispositions = json.loads((CAPTURE / 'DATASET_DISPOSITIONS.json').read_text())
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    summaries, predictor_results, row_audit, repaired_results, rotation_results = [], [], [], [], []
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        for disposition in dispositions:
            if disposition['status'] != 'captured':
                summaries.append({**disposition, 'audited': False})
                continue
            name, split = disposition['bench'], disposition['split']
            source_bytes = gzip.decompress((CAPTURE / disposition['rows_file']).read_bytes())
            assert hashlib.sha256(source_bytes).hexdigest() == disposition['rows_sha256']
            source_rows = [json.loads(x) for x in source_bytes.splitlines()]
            assert len(source_rows) == disposition['rows']
            # Native tool reads JSONL into pandas before preprocessing.
            source_path = temp / 'source.jsonl'
            source_path.write_bytes(source_bytes)
            frame = pd.read_json(source_path, lines=True)
            entry = copy.deepcopy(gallery[name])
            mapping = copy.deepcopy(entry['meta']['key_mapping'])
            frame, mapping = preprocess._preprocess_dataframe(frame, name, mapping, eval_type=entry['bench_dataflow_eval_type'])
            native_rows = frame.to_dict(orient='records')
            assert len(native_rows) == len(source_rows)
            eval_contract = entry['meta']['evaluation']
            letters = list(chr(x) for x in range(ord(eval_contract['parser']['choices'][0]), ord(eval_contract['parser']['choices'][-1])+1))
            semantic = [semantic_source(name, row) for row in source_rows]
            gold_available = sum(index is not None for _, index in semantic)
            unresolved = {}
            for key, value in mapping.items():
                columns = value if isinstance(value, list) else [value]
                missing = [column for column in columns if isinstance(column, str) and column not in frame.columns]
                if missing:
                    unresolved[key] = missing
            display_ok, gold_visible, wrong_choice_count = 0, 0, 0
            for i, (native, (choices, gold_index)) in enumerate(zip(native_rows, semantic)):
                displayed = native_display_choices(native, mapping)
                if displayed is not None:
                    display_ok += 1
                    wrong_choice_count += len(displayed) != len(choices)
                    if gold_index is not None and str(choices[gold_index]) in displayed:
                        gold_visible += 1
                row_audit.append({'bench': name, 'split': split, 'row': i,
                                  'source_gold': source_rows[i].get(entry['meta']['key_mapping']['input_label_key']),
                                  'semantic_gold_index': gold_index,
                                  'semantic_choice_count': len(choices),
                                  'native_displayed_choices': displayed,
                                  'semantic_gold_visible': displayed is not None and gold_index is not None and str(choices[gold_index]) in displayed})
            native_results = []
            prediction_path = temp / 'predictions.jsonl'
            def score(predictions, use_repair=False, choice_values=None, gold_letters=None):
                rows = copy.deepcopy(native_rows)
                for i, row in enumerate(rows):
                    row['generated_ans'] = predictions[i]
                    if use_repair:
                        row['_contract_gold_letter'] = gold_letters[i]
                        row['_contract_choices'] = choice_values[i]
                prediction_path.write_text(''.join(compact(row) + '\n' for row in rows))
                bench = BenchInfo(bench_name=name, bench_dataflow_eval_type=entry['bench_dataflow_eval_type'], meta={
                    'artifact_paths': {'records': str(prediction_path)}, 'pred_key': 'generated_ans',
                    'ref_key': '_contract_gold_letter' if use_repair else mapping['input_label_key']})
                contract = copy.deepcopy(eval_contract)
                if use_repair:
                    contract['parser'] = {'type': 'choice_letter', 'choices': 'A-' + chr(64 + len(choice_values[0])), 'choices_key': '_contract_choices'}
                result = Runner(max_workers=2).run_bench_with_contract(bench, contract)
                assert 'error' not in result, result
                primary = result['primary_metric_result']
                return primary, result
            available = gold_available == len(source_rows)
            oracle_letters = ['<answer>' + chr(65 + index) + '</answer>' if index is not None else '' for choices, index in semantic]
            oracle_text = [str(choices[index]) if index is not None else '' for choices, index in semantic]
            predictors = [('constant_' + letter, ['<answer>' + letter + '</answer>'] * len(native_rows), letter) for letter in letters]
            if available:
                predictors += [('semantic_oracle_letter', oracle_letters, None), ('semantic_oracle_text', oracle_text, None)]
            for predictor, predictions, constant in predictors:
                primary, full = score(predictions)
                true_score = None if not available else (
                    1.0 if predictor.startswith('semantic_oracle') else
                    sum(chr(65 + index) == constant for choices, index in semantic) / len(semantic))
                report = {'bench': name, 'split': split, 'role': disposition['role'],
                          'predictor': predictor, 'prediction_kind': 'constructed_diagnostic_control',
                          'native_prompt_fields_resolved': not bool(unresolved),
                          'semantic_source_accuracy': true_score, **primary}
                predictor_results.append(report)
                native_results.append(report)
                if predictor == 'semantic_oracle_letter':
                    for audit, parsed in zip(row_audit[-len(source_rows):], full['primary_metric_artifacts']['parse_results']):
                        audit['native_oracle_pred_parse'] = parsed['pred']
                        audit['native_reference_parse'] = parsed['ref']
            summary = {'bench': name, 'split': split, 'role': disposition['role'], 'audited': True,
                       'rows': len(source_rows), 'source_gold_available': gold_available,
                       'unresolved_input_fields': unresolved, 'native_complete_choices_rows': display_ok,
                       'native_gold_visible_rows': gold_visible, 'native_choice_count_mismatch_rows': wrong_choice_count,
                       'preprocessed_key_mapping': mapping,
                       'gallery_readiness': entry['meta'].get('readiness'),
                       'native_oracle_letter_score': next((x['score'] for x in native_results if x['predictor']=='semantic_oracle_letter'), None),
                       'native_oracle_letter_scored_samples': next((x['scored_samples'] for x in native_results if x['predictor']=='semantic_oracle_letter'), None),
                       'native_best_constant': max((x for x in native_results if x['predictor'].startswith('constant_')), key=lambda x:x['score'])}
            summaries.append(summary)
            if available:
                choice_values = [list(choices) for choices, _ in semantic]
                for predictor, predictions, constant in predictors:
                    if predictor == 'semantic_oracle_text':
                        continue
                    primary, _ = score(predictions, use_repair=True, choice_values=choice_values, gold_letters=oracle_letters)
                    truth = 1.0 if predictor == 'semantic_oracle_letter' else sum(chr(65+index)==constant for _,index in semantic)/len(semantic)
                    assert primary['scored_samples'] == len(semantic)
                    assert abs(primary['score'] - truth) < 1e-12
                    repaired_results.append({'bench': name, 'split': split, 'predictor': predictor,
                                             'repair': 'explicit source label semantics, complete choices and canonical gold letter',
                                             'score': primary['score'], 'semantic_source_accuracy': truth,
                                             'scored_samples': primary['scored_samples']})
                if name == 'sciq':
                    order = sorted(range(len(source_rows)), key=lambda i: hashlib.sha256(
                        ('default-contract-audit-20261113|' + str(i) + '|' + source_rows[i]['question']).encode()).digest())
                    shifts = {index: rank % 4 for rank, index in enumerate(order)}
                    rotated_choices, rotated_gold = [], []
                    for i, (choices, original_index) in enumerate(semantic):
                        shift = shifts[i]
                        rotated_choices.append(choices[shift:] + choices[:shift])
                        rotated_gold.append(chr(65 + (original_index-shift) % 4))
                    for predictor in ('constant_A','constant_B','constant_C','constant_D','semantic_oracle_letter'):
                        tagged_gold = ['<answer>' + letter + '</answer>' for letter in rotated_gold]
                        predictions = tagged_gold if predictor == 'semantic_oracle_letter' else ['<answer>' + predictor[-1] + '</answer>']*len(semantic)
                        primary, _ = score(predictions, use_repair=True, choice_values=rotated_choices, gold_letters=tagged_gold)
                        truth = 1.0 if predictor == 'semantic_oracle_letter' else rotated_gold.count(predictor[-1])/len(semantic)
                        assert abs(primary['score'] - truth)<1e-12
                        rotation_results.append({'bench': name,'split':split,'predictor':predictor,'score':primary['score'],
                                                 'gold_position_counts':{letter:rotated_gold.count(letter) for letter in 'ABCD'},
                                                 'rotation_rule':'Source-hash-sorted rows assigned cyclic shifts 0,1,2,3; no model outcomes used'})
            print(name, split, 'audited', len(source_rows), flush=True)
            dump(out / 'CHECKPOINT_COHORT_AUDIT.json', summaries)
            dump(out / 'CHECKPOINT_NATIVE_RESULTS.json', predictor_results)
    dump(out / 'COHORT_AUDIT.json', summaries)
    dump(out / 'NATIVE_PREDICTOR_RESULTS.json', predictor_results)
    dump(out / 'REPAIRED_CONTRACT_RESULTS.json', repaired_results)
    dump(out / 'SCIQ_BALANCED_ROTATION_RESULTS.json', rotation_results)
    (out / 'ROW_AUDIT.jsonl.gz').write_bytes(gzip.compress((''.join(compact(x)+'\n' for x in row_audit)).encode(), mtime=0))
    dump(out / 'SUMMARY.json', {'source_panels_planned': len(dispositions), 'source_panels_captured': sum(x['status']=='captured' for x in dispositions),
                                'source_rows_audited': len(row_audit), 'constructed_predictor_runs':len(predictor_results),
                                'repaired_predictor_runs':len(repaired_results), 'balanced_rotation_runs':len(rotation_results),
                                'new_model_calls':0, 'controls_are_not_model_outputs':True,
                                'scope':'Actual native preprocessing and primary scorer on real source rows; generator/model inference not run. Blocked prompt construction is recorded separately from scored fixture replay.'})

if __name__ == '__main__':
    main()
