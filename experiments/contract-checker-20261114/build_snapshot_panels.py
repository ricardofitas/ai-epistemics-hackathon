"""Build checker inputs from pinned One-Eval methods and native EvalScope captures."""
import copy
import gzip
import hashlib
import inspect
import io
import json
import logging
from pathlib import Path
import string
import sys
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
sys.path.insert(0, str(WORKSPACE / 'default_contract_audit_20261113'))
import audit_contracts as audit
import verify_native_prompt_wire as native
from source_contracts import normalize_record, render_typed_prompt, UnscorableSource
from check_contract import audit_contract


def read_gzip(path):
    with gzip.open(path, 'rt') as source:
        return [json.loads(line) for line in source]


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def visible_text(messages):
    parts = []
    for message in messages:
        content = message['content']
        if isinstance(content, str):
            parts.append(content)
        else:
            parts.extend(piece.get('text', '') for piece in content)
    return '\n'.join(parts)


def preserve_panel(name, rows, metadata):
    directory = ROOT / 'panels'
    directory.mkdir(exist_ok=True)
    payload = ('\n'.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) for row in rows) + '\n').encode()
    path = directory / (name + '.jsonl.gz')
    path.write_bytes(gzip.compress(payload, mtime=0))
    report = audit_contract(rows)
    report['panel'] = name
    report['provenance'] = metadata
    report['input_file'] = str(path.relative_to(ROOT))
    report['input_sha256'] = digest_bytes(path.read_bytes())
    (directory / (name + '.report.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(name, report['status'], len(rows), report['failures'], flush=True)
    return report


def original_generator():
    bench_type, _ = audit.load_components()
    namespace = dict(Any=Any, Dict=Dict, List=List, Literal=Literal, Optional=Optional,
                     Union=Union, pd=pd, np=np, json=json, inspect=inspect, get_logger=logging.getLogger)
    native.load_class(native.SUPPORT / 'dataflow/core/prompt.py', 'PromptABC', namespace)
    formatter = native.load_class(native.SUPPORT / 'dataflow/prompts/core_text.py', 'FormatStrPrompt', namespace)
    generator = native.load_class(audit.CAPTURE / 'dataflow_wheel__dataflow__operators__core_text__generate__bench_answer_generator.py', 'BenchAnswerGenerator', namespace, remove_bases=True)
    processor = audit.load_preprocessor()
    processor._resolve_prompt_template.__globals__.update(FormatStrPrompt=formatter, hashlib=hashlib)
    return bench_type, generator, processor


def oneeval_panels():
    bench_type, generator, processor = original_generator()
    from one_eval.metrics.parsers import parse_value
    gallery = json.loads((audit.ROOT / 'GALLERY_SELECTED.json').read_text())['benches']
    gallery = {entry['bench_name']: entry for entry in gallery}
    dispositions = json.loads((audit.CAPTURE / 'DATASET_DISPOSITIONS.json').read_text())
    reports = []
    prior_wire = read_gzip(audit.ROOT / 'results/NATIVE_PROMPT_WIRE_HASHES.jsonl.gz')
    wire_lookup = {(r['bench'], r['split'], r['row']):r for r in prior_wire}
    for disposition in dispositions:
        if disposition['status'] != 'captured':
            continue
        name, split = disposition['bench'], disposition['split']
        source_bytes = gzip.decompress((audit.CAPTURE / disposition['rows_file']).read_bytes())
        assert digest_bytes(source_bytes) == disposition['rows_sha256']
        source_rows = [json.loads(line) for line in source_bytes.splitlines()]
        entry = gallery[name]
        frame = pd.read_json(io.StringIO(source_bytes.decode()), lines=True)
        frame, mapping = processor._preprocess_dataframe(frame, name, copy.deepcopy(entry['meta']['key_mapping']), eval_type='key3_q_choices_a')
        before = frame.to_dict('records')
        bench = bench_type(bench_name=name, bench_dataflow_eval_type='key3_q_choices_a', meta=copy.deepcopy(entry['meta']))
        template, _ = processor._resolve_prompt_template(bench, 'key3_q_choices_a')
        recorder = native.RecordedServing()
        operator = generator(eval_type='key3_q_choices_a', llm_serving=recorder, prompt_template=template, force_generate=True)
        choice_key = mapping['input_choices_key']
        if isinstance(choice_key, list):
            choice_key = choice_key[0]
        operator.run(storage=native.FrameStorage(frame), input_question_key=mapping['input_question_key'],
                     input_context_key=mapping.get('input_context_key'), input_choices_key=choice_key, output_key='generated_ans')
        intended = entry['meta']['prompt']['user_template']
        needed = {field for _, field, _, _ in string.Formatter().parse(intended) if field}
        native_records = []
        repaired_records = []
        for index, (source, record) in enumerate(zip(source_rows, before)):
            source_choices, source_index = audit.semantic_source(name, source)
            gold = str(source_choices[source_index]) if source_index is not None else None
            displayed = audit.native_display_choices(record, mapping)
            expected = None
            if source_index is not None and displayed is not None:
                if displayed == source_choices:
                    expected = chr(65 + source_index)
                elif displayed.count(gold) == 1:
                    expected = chr(65 + displayed.index(gold))
            parsed = parse_value(record.get(mapping['input_label_key']), entry['meta']['evaluation']['parser'], record=record)
            prompt = recorder.prompts[index] if recorder.prompts else None
            context_key = mapping.get('input_context_key')
            context = operator._normalize_context(record.get(context_key)) if context_key else None
            context_required = bool(context) and bool({context_key, 'context'} & needed)
            question_changed = context_changed = None
            if prompt is not None:
                choices = operator._ensure_list(record[choice_key])
                question = str(record[mapping['input_question_key']])
                probe = operator._build_prompt(eval_type='key3_q_choices_a', question='CHECKER_QUESTION_NONCE_' + str(index), context=context, choices=choices)
                question_changed = probe != prompt
                context_probe = operator._build_prompt(eval_type='key3_q_choices_a', question=question, context='CHECKER_CONTEXT_NONCE_' + str(index), choices=choices)
                context_changed = context_probe != prompt if context_required else None
                prior = wire_lookup[(name, split, index)]
                assert digest_bytes(prompt.encode()) == prior['prompt_sha256']
                assert question_changed == prior['question_mutation_changed']
            native_records.append(dict(schema_version=1, row_id=str(index), kind='choice', prompt=prompt,
                choices=displayed, correct_text=gold, expected_reference=expected,
                reference=parsed.normalized if parsed.ok else None,
                question_probe_changed=question_changed, context_required=context_required,
                context_probe_changed=context_changed, probe_origin='Pinned native formatter methods executed offline'))
            try:
                fixed = normalize_record(name, source, str(index), permute=True)
            except UnscorableSource:
                continue
            key_mapping = entry['meta']['key_mapping']
            fixed_prompt = render_typed_prompt(source, fixed, key_mapping, intended)
            q_key = key_mapping['input_question_key']
            q_probe = render_typed_prompt({**source, q_key:'CHECKER_QUESTION_NONCE_' + str(index)}, fixed, key_mapping, intended)
            c_key = key_mapping.get('input_context_key')
            needs_context = bool(c_key and source.get(c_key) and {c_key, 'context'} & needed)
            c_probe = render_typed_prompt({**source, c_key:'CHECKER_CONTEXT_NONCE_' + str(index)}, fixed, key_mapping, intended) if needs_context else None
            fixed_label = fixed['_contract_reference'][8:-9]
            assert fixed_label in string.ascii_uppercase
            repaired_records.append(dict(schema_version=1, row_id=str(index), kind='choice', prompt=fixed_prompt,
                choices=fixed['choices'], correct_text=fixed['_contract_gold_text'], expected_reference=fixed_label,
                reference=fixed_label, question_probe_changed=q_probe != fixed_prompt,
                context_required=needs_context, context_probe_changed=c_probe != fixed_prompt if needs_context else None,
                probe_origin='Explicit source-bound correction executed offline'))
        metadata = dict(framework='One-Eval', commit='8aba20ad17ee2c7d2391162ac03ffaebcbb17506',
                        dataflow='1.0.10', benchmark=name, split=split, raw_source_sha256=disposition['rows_sha256'])
        reports.append(preserve_panel('oneeval__' + name + '__' + split, native_records, metadata))
        if repaired_records:
            assert len(repaired_records) == len(source_rows)
            reports.append(preserve_panel('repaired__' + name + '__' + split, repaired_records, dict(metadata, variant='typed source correction')))
    return reports


def evalscope_panels():
    reports = []
    root = WORKSPACE / 'second_engine_contracts_20261113/capture/evidence'
    for directory in sorted(root.iterdir()):
        setup = json.loads((directory / 'SETUP.json').read_text())
        raw = read_gzip(directory / 'RAW_RECORDS.jsonl.gz')
        samples = read_gzip(directory / 'NATIVE_PRE_FORMAT_SAMPLES.jsonl.gz')
        ready = read_gzip(directory / 'NATIVE_READY_SAMPLES.jsonl.gz')
        probes = read_gzip(directory / 'SOURCE_CHECKS.jsonl.gz')
        assert len(raw) == len(samples) == len(ready) == len(probes) == setup['samples']
        name = setup['name']
        records = []
        for index, (record, sample, final, probe) in enumerate(zip(raw, samples, ready, probes)):
            if name == 'winogrande':
                expected = {'1':'A', '2':'B'}[str(record['answer'])]
            elif name == 'hellaswag':
                expected = 'ABCD'[int(record['label'])]
            elif name == 'boolq':
                assert type(record['answer']) is bool
                expected = 'A' if record['answer'] else 'B'
            elif name == 'pubmedqa':
                expected = record['answer'].upper()
            else:
                expected = record['answer']
                if 'answer_index' in record:
                    assert expected == string.ascii_uppercase[record['answer_index']]
            prompt = visible_text(final['input'])
            assert digest_bytes(prompt.encode()) == probe['wire_sha256']
            choices = sample['choices']
            gold = choices[ord(expected) - 65] if choices else expected
            records.append(dict(schema_version=1, row_id=str(index), kind='choice' if choices else 'freeform',
                prompt=prompt, choices=choices, correct_text=gold, expected_reference=expected,
                reference=sample['target'], question_probe_changed=probe['question_mutation_changes_prompt'],
                context_required=name in ['boolq', 'pubmedqa'], context_probe_changed=probe['context_mutation_changes_prompt'],
                probe_origin='Native installed-package mutation outcomes from the immutable prior capture'))
        metadata = dict(framework='EvalScope', commit=setup['source_commit'], dataset=setup['dataset_id'],
                        benchmark=name, split=setup['eval_split'], raw_source_sha256=digest_bytes((directory / 'RAW_RECORDS.jsonl.gz').read_bytes()),
                        probe_capture_sha256=digest_bytes((directory / 'SOURCE_CHECKS.jsonl.gz').read_bytes()),
                        probe_reexecution_this_stage=False)
        reports.append(preserve_panel('evalscope__' + name, records, metadata))
    return reports


if __name__ == '__main__':
    results = oneeval_panels() + evalscope_panels()
    (ROOT / 'PANEL_RESULTS.json').write_text(json.dumps(results, indent=2) + '\n')
