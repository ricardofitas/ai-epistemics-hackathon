"""Run the byte-pinned checker and native scorer on the prospective panel."""
import copy
from collections import Counter
import gzip
import hashlib
import inspect
import io
import json
import logging
import os
from pathlib import Path
import platform
import string
import sys
import tempfile
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'default_contract_audit_20261113'))
sys.path.insert(0, str(ROOT.parent / 'oneeval_contract_checker_20261114'))
import audit_contracts as audit
import verify_native_prompt_wire as native
from check_contract import audit_contract, guarded_inference, InvalidContract


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + '\n')


def compressed(path, rows):
    data = b''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode() + b'\n' for row in rows)
    path.write_bytes(gzip.compress(data, mtime=0))


def source_semantics(name, row):
    if name in ('arc-challenge', 'openbookqa'):
        choices = row['choices']
        labels = [str(value) for value in choices['label']]
        texts = list(choices['text'])
        assert len(labels) == len(texts) and len(labels) == len(set(labels))
        gold = labels.index(str(row['answerKey']))
        question = row['question'] if name == 'arc-challenge' else row['question_stem']
    elif name == 'mmlu':
        texts = list(row['choices'])
        gold = int(row['answer'])
        question = row['question']
    else:
        assert name == 'mmlu-pro'
        texts = list(row['options'])
        gold = int(row['answer_index'])
        question = row['question']
        if row.get('answer') is not None:
            assert str(row['answer']).strip().upper() == string.ascii_uppercase[gold]
    assert isinstance(question, str) and question.strip()
    assert 2 <= len(texts) <= 26 and 0 <= gold < len(texts)
    assert all(isinstance(value, str) and value.strip() for value in texts)
    return texts, gold, question


def components():
    bench_type, runner = audit.load_components()
    namespace = dict(Any=Any, Dict=Dict, List=List, Literal=Literal, Optional=Optional,
                     Union=Union, pd=pd, np=np, json=json, inspect=inspect, get_logger=logging.getLogger)
    native.load_class(native.SUPPORT / 'dataflow/core/prompt.py', 'PromptABC', namespace)
    formatter = native.load_class(native.SUPPORT / 'dataflow/prompts/core_text.py', 'FormatStrPrompt', namespace)
    generator = native.load_class(audit.CAPTURE / 'dataflow_wheel__dataflow__operators__core_text__generate__bench_answer_generator.py', 'BenchAnswerGenerator', namespace, remove_bases=True)
    processor = audit.load_preprocessor()
    processor._resolve_prompt_template.__globals__.update(FormatStrPrompt=formatter, hashlib=hashlib)
    return bench_type, runner, generator, processor


def native_score(rows, entry, predictions, reference_key, BenchInfo, Runner, contract=None):
    values = [dict(row, generated_ans=prediction) for row, prediction in zip(rows, predictions)]
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'predictions.jsonl'
        path.write_text(''.join(audit.compact(row) + '\n' for row in values))
        bench = BenchInfo(bench_name=entry['bench_name'], meta={'artifact_paths':{'records':str(path)}, 'pred_key':'generated_ans', 'ref_key':reference_key})
        result = Runner(max_workers=2).run_bench_with_contract(bench, contract or entry['meta']['evaluation'])
    assert 'error' not in result, result
    return result['primary_metric_result']


def audit_panel(entry, disposition):
    from one_eval.metrics.parsers import parse_value
    BenchInfo, Runner, generator, processor = components()
    name = entry['bench_name']
    output = ROOT / 'capture' / name
    selected_bytes = gzip.decompress((output / 'SELECTED.jsonl.gz').read_bytes())
    assert hashlib.sha256(selected_bytes).hexdigest() == disposition['selected_rows_sha256']
    selected = [json.loads(line) for line in selected_bytes.splitlines()]
    source_rows = [item['record'] for item in selected]
    semantics = [source_semantics(name, row) for row in source_rows]
    frame = pd.read_json(io.StringIO(''.join(audit.compact(row) + '\n' for row in source_rows)), lines=True)
    frame, mapping = processor._preprocess_dataframe(frame, name, copy.deepcopy(entry['meta']['key_mapping']), eval_type='key3_q_choices_a')
    original_rows = frame.to_dict('records')
    bench = BenchInfo(bench_name=name, bench_dataflow_eval_type='key3_q_choices_a', meta=copy.deepcopy(entry['meta']))
    template, _ = processor._resolve_prompt_template(bench, 'key3_q_choices_a')
    recorder = native.RecordedServing()
    operator = generator(eval_type='key3_q_choices_a', llm_serving=recorder, prompt_template=template, force_generate=True)
    choice_key = mapping['input_choices_key']
    if isinstance(choice_key, list):
        choice_key = choice_key[0]
    operator.run(storage=native.FrameStorage(frame), input_question_key=mapping['input_question_key'],
                 input_context_key=mapping.get('input_context_key'), input_choices_key=choice_key, output_key='generated_ans')
    if recorder.prompts:
        assert len(recorder.prompts) == len(source_rows)
    records, repaired, row_checks = [], [], []
    for index, (row, original, source) in enumerate(zip(original_rows, source_rows, semantics)):
        texts, source_index, question = source
        gold = texts[source_index]
        displayed = audit.native_display_choices(row, mapping)
        expected = None
        if displayed == texts:
            expected = string.ascii_uppercase[source_index]
        elif displayed is not None and displayed.count(gold) == 1:
            expected = string.ascii_uppercase[displayed.index(gold)]
        prompt = recorder.prompts[index] if recorder.prompts else None
        probe_changed = None
        if prompt is not None:
            probe = operator._build_prompt(eval_type='key3_q_choices_a', question='PROSPECTIVE_QUESTION_NONCE_' + str(index),
                                          context=None, choices=operator._ensure_list(row[choice_key]))
            probe_changed = probe != prompt
        reference = parse_value(row.get(mapping['input_label_key']), entry['meta']['evaluation']['parser'], record=row)
        records.append(dict(schema_version=1, row_id=str(index), kind='choice', prompt=prompt,
                    choices=displayed, correct_text=gold, expected_reference=expected,
                    reference=reference.normalized if reference.ok else None,
                    question_probe_changed=probe_changed, context_required=False, context_probe_changed=None))
        # Prespecified source-bound intervention preserves source choice order.
        fields = {**original, 'question':question,
                  'choices_text':'\n'.join(string.ascii_uppercase[j] + '. ' + value for j, value in enumerate(texts))}
        intended = entry['meta']['prompt']['user_template']
        fixed_prompt = intended.format_map(fields)
        question_key = entry['meta']['key_mapping']['input_question_key']
        changed = {**fields, question_key:'PROSPECTIVE_QUESTION_NONCE_' + str(index), 'question':'PROSPECTIVE_QUESTION_NONCE_' + str(index)}
        label = string.ascii_uppercase[source_index]
        repaired.append(dict(schema_version=1, row_id=str(index), kind='choice', prompt=fixed_prompt,
                    choices=texts, correct_text=gold, expected_reference=label, reference=label,
                    question_probe_changed=intended.format_map(changed) != fixed_prompt,
                    context_required=False, context_probe_changed=None))
        row_checks.append(dict(row=index, source_index=selected[index]['source_index'], source_gold_index=source_index,
                         source_choice_count=len(texts), native_choice_count=len(displayed) if displayed is not None else None,
                         correct_text_in_native_choices=displayed is not None and gold in displayed,
                         source_question_in_prompt=bool(prompt) and question in prompt,
                         question_probe_changes_prompt=probe_changed,
                         native_reference=reference.to_dict()))
    native_report, fixed_report = audit_contract(records), audit_contract(repaired)
    compressed(output / 'CHECKER_NATIVE.jsonl.gz', records)
    compressed(output / 'CHECKER_REPAIRED.jsonl.gz', repaired)
    compressed(output / 'SOURCE_CHECKS.jsonl.gz', row_checks)
    compressed(output / 'NATIVE_PREPROCESSED.jsonl.gz', original_rows)
    # The source-label fixture is kept explicit when its letter does not denote
    # a displayed option. It is never called a feasible oracle in that case.
    labels = [string.ascii_uppercase[source[1]] for source in semantics]
    canonical = ['<answer>' + label + '</answer>' for label in labels]
    text_oracle = [source[0][source[1]] for source in semantics]
    results = []
    letters = list(entry['meta']['evaluation']['parser']['choices'].replace('-', ''))
    labels_allowed = list(string.ascii_uppercase[string.ascii_uppercase.index(letters[0]):string.ascii_uppercase.index(letters[-1]) + 1])
    for predictor, predictions in [('official_letter_fixture', canonical), ('official_text_fixture', text_oracle),
                                   *[('constant_' + letter, ['<answer>' + letter + '</answer>'] * len(source_rows)) for letter in labels_allowed]]:
        score = native_score(original_rows, entry, predictions, mapping['input_label_key'], BenchInfo, Runner)
        results.append(dict(predictor=predictor, **score))
    repaired_rows = [dict(row, choices=semantics[i][0], _canonical_gold=canonical[i]) for i, row in enumerate(original_rows)]
    corrected_contract = copy.deepcopy(entry['meta']['evaluation'])
    corrected_contract['parser'] = dict(type='choice_letter', choices='A-' + string.ascii_uppercase[max(len(s[0]) for s in semantics) - 1], choices_key='choices')
    corrected_score = native_score(repaired_rows, entry, canonical, '_canonical_gold', BenchInfo, Runner, corrected_contract)
    assert corrected_score['score'] == 1 and corrected_score['scored_samples'] == len(source_rows)
    native_calls, fixed_calls = [], []
    try:
        guarded_inference(records, lambda prompts:native_calls.append(len(prompts)))
    except InvalidContract:
        pass
    guarded_inference(repaired, lambda prompts:fixed_calls.append(len(prompts)))
    independent = dict(question_binding_failures=sum(r['question_probe_changes_prompt'] is False for r in row_checks),
                       correct_option_absence=sum(not r['correct_text_in_native_choices'] for r in row_checks),
                       choice_count_mismatch=sum(r['native_choice_count'] != r['source_choice_count'] for r in row_checks))
    assert native_report['failures'].get('question_not_bound', 0) == independent['question_binding_failures']
    assert native_report['failures'].get('correct_choice_missing', 0) == independent['correct_option_absence']
    report = dict(benchmark=name, source_rows=disposition['total_source_rows'], selected_rows=len(source_rows),
                  source_choice_counts=dict(Counter(len(source[0]) for source in semantics)),
                  native_checker=native_report, repaired_checker=fixed_report, independent_checks=independent,
                  native_scoring_controls=results, corrected_reference_oracle=corrected_score,
                  feasible_native_letter_oracle=all(record['choices'] == source[0] for record, source in zip(records, semantics)),
                  original_reference_meaning='Canonical source positions can describe a valid native response only when the source choices remain fully represented in their original order.',
                  native_constructed_backend_calls=len(native_calls), repaired_constructed_backend_calls=len(fixed_calls),
                  provider_model_calls=0)
    dump(output / 'RESULT.json', report)
    print(name, native_report['status'], 'rows', len(source_rows), native_report['failures'], flush=True)
    return report


def main():
    protocol = json.loads((ROOT / 'PROTOCOL.json').read_text())
    assert hashlib.sha256((ROOT.parent / 'oneeval_contract_checker_20261114/check_contract.py').read_bytes()).hexdigest() == protocol['checker_sha256']
    # Load the unmodified parser before importing it inside a panel function.
    audit.load_components()
    entries = {entry['bench_name']:entry for entry in json.loads((ROOT / 'GALLERY.json').read_text())['benches']}
    dispositions = json.loads((ROOT / 'DISPOSITIONS.json').read_text())
    reports = []
    for disposition in dispositions:
        if disposition['status'] != 'captured':
            reports.append(dict(benchmark=disposition['benchmark'], status='source_unavailable'))
        else:
            try:
                reports.append(audit_panel(entries[disposition['benchmark']], disposition))
            except Exception as error:
                reports.append(dict(benchmark=disposition['benchmark'], status='audit_failed', error_type=type(error).__name__, error=str(error)))
        dump(ROOT / 'RESULTS.json', reports)
    dump(ROOT / 'EXECUTION.json', dict(python=platform.python_version(), run_id=os.environ.get('GITHUB_RUN_ID'),
        commit=os.environ.get('GITHUB_SHA'), provider_model_calls=0, framework_commit=protocol['framework_commit'],
        checker_sha256=protocol['checker_sha256'], dispositions=dispositions, audited_panels=sum('native_checker' in r for r in reports)))


if __name__ == '__main__':
    main()
