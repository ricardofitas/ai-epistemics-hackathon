"""Recreate native visible inputs and compute the empirical per-prompt ceiling.

The default workspace contains the two earlier research captures. Each result
uses the WinoGrande validation gold supplied by the source dataset.
"""
import copy
from collections import Counter, defaultdict
import gzip
import hashlib
import inspect
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
sys.path.insert(0, str(WORKSPACE / 'default_contract_audit_20261113'))

import audit_contracts as audit
import verify_native_prompt_wire as native
from source_contracts import normalize_record, render_typed_prompt


def gzip_rows(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        return [json.loads(line) for line in stream]


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def recover_native_inputs(name, rows, entry):
    bench_type, _ = audit.load_components()
    namespace = dict(Any=Any, Dict=Dict, List=List, Literal=Literal,
                     Optional=Optional, Union=Union, pd=pd, np=np, json=json,
                     inspect=inspect, get_logger=logging.getLogger)
    native.load_class(native.SUPPORT / 'dataflow/core/prompt.py', 'PromptABC', namespace)
    formatter = native.load_class(native.SUPPORT / 'dataflow/prompts/core_text.py', 'FormatStrPrompt', namespace)
    generator = native.load_class(audit.CAPTURE / 'dataflow_wheel__dataflow__operators__core_text__generate__bench_answer_generator.py', 'BenchAnswerGenerator', namespace, remove_bases=True)
    preprocessor = audit.load_preprocessor()
    preprocessor._resolve_prompt_template.__globals__.update(FormatStrPrompt=formatter, hashlib=hashlib)
    mapping = copy.deepcopy(entry['meta']['key_mapping'])
    frame, mapping = preprocessor._preprocess_dataframe(pd.DataFrame(rows), name, mapping, eval_type='key3_q_choices_a')
    bench = bench_type(bench_name=name, bench_dataflow_eval_type='key3_q_choices_a', meta=copy.deepcopy(entry['meta']))
    template, _ = preprocessor._resolve_prompt_template(bench, 'key3_q_choices_a')
    recorder = native.RecordedServing()
    operator = generator(eval_type='key3_q_choices_a', llm_serving=recorder, prompt_template=template, force_generate=True)
    operator.run(storage=native.FrameStorage(frame), input_question_key=mapping['input_question_key'],
                 input_context_key=mapping.get('input_context_key'), input_choices_key=mapping['input_choices_key'], output_key='generated_ans')
    assert len(recorder.prompts) == len(rows)
    return recorder.prompts


def summarize(prompts, targets):
    # Group by full visible string, not by a digest or by dataset metadata.
    groups = defaultdict(list)
    for index, prompt in enumerate(prompts):
        groups[prompt].append(index)
    maximum_correct = 0
    mixed = []
    for prompt, indices in groups.items():
        labels = Counter(targets[i] for i in indices)
        maximum_correct += max(labels.values())
        if len(labels) > 1:
            mixed.append(dict(prompt_sha256=digest(prompt), rows=indices, targets=dict(labels)))
    return dict(rows=len(targets), distinct_prompts=len(groups), repeated_prompt_groups=sum(len(indices) > 1 for indices in groups.values()),
                mixed_gold_groups=len(mixed), rows_in_mixed_groups=sum(len(group['rows']) for group in mixed),
                unavoidable_errors=len(targets) - maximum_correct, maximum_correct=maximum_correct,
                deterministic_visible_input_accuracy_ceiling=maximum_correct / len(targets)), mixed


def main():
    name = 'winogrande'
    rows = gzip_rows(audit.CAPTURE / 'winogrande__validation.jsonl.gz')
    targets = [{'1': 'A', '2': 'B'}[r['answer']] for r in rows]
    gallery = json.loads((audit.ROOT / 'GALLERY_SELECTED.json').read_text())['benches']
    entry = next(row for row in gallery if row['bench_name'] == name)
    original = recover_native_inputs(name, rows, entry)
    recorded = [r for r in gzip_rows(audit.ROOT / 'results/NATIVE_PROMPT_WIRE_HASHES.jsonl.gz') if r['bench'] == name and r['split'] == 'validation']
    assert all(r['row'] == i and r['prompt_sha256'] == digest(original[i]) for i, r in enumerate(recorded))
    assert len(recorded) == len(rows) == 1267
    corrected = [render_typed_prompt(r, normalize_record(name, r, str(i), permute=False), entry['meta']['key_mapping'], entry['meta']['prompt']['user_template']) for i, r in enumerate(rows)]
    second = WORKSPACE / 'second_engine_contracts_20261113/capture/evidence/winogrande__modelscope'
    other_raw = gzip_rows(second / 'RAW_RECORDS.jsonl.gz')
    other_ready = gzip_rows(second / 'NATIVE_READY_SAMPLES.jsonl.gz')
    other_checks = gzip_rows(second / 'SOURCE_CHECKS.jsonl.gz')
    assert len(other_raw) == len(other_ready) == len(other_checks) == len(rows)
    other_prompts = []
    for index, (source, other, ready, check) in enumerate(zip(rows, other_raw, other_ready, other_checks)):
        assert all(other[k] == source[k] for k in ('sentence', 'option1', 'option2', 'answer'))
        assert ready['target'] == targets[index]
        assert len(ready['input']) == 1 and ready['input'][0]['role'] == 'user'
        visible = ready['input'][0]['content']
        assert digest(visible) == check['wire_sha256']
        other_prompts.append(visible)
    systems = {}
    collisions = []
    evidence = []
    for index, row in enumerate(rows):
        evidence.append({'row': index, 'sentence': row['sentence'], 'options': [row['option1'], row['option2']],
                         'source_one_based_gold': row['answer'], 'oneeval_native': original[index],
                         'oneeval_source_bound': corrected[index], 'evalscope_native': other_prompts[index]})
    evidence_bytes = ('\n'.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) for row in evidence) + '\n').encode()
    (HERE / 'validated_rows.jsonl.gz').write_bytes(gzip.compress(evidence_bytes, mtime=0))
    for backend, prompts in [('One-Eval native', original), ('One-Eval source-bound renderer', corrected), ('EvalScope native', other_prompts)]:
        systems[backend], groups = summarize(prompts, targets)
        if backend == 'One-Eval native':
            collisions = groups
    # An independent check uses the archived hashes only; for two labels the
    # number of unavoidable errors equals the sum of the smaller class count.
    hash_counts = defaultdict(Counter)
    for row, target in zip(recorded, targets):
        hash_counts[row['prompt_sha256']][target] += 1
    independently_counted = sum(min(c['A'], c['B']) for c in hash_counts.values())
    assert independently_counted == systems['One-Eval native']['unavoidable_errors']
    report = dict(benchmark=name, split='labelled validation (diagnostic override in One-Eval)',
                  quantity='Maximum accuracy on this fixed corpus for a deterministic answer that depends only on the exact visible prompt, evaluated with source-correct gold. Sum the within-prompt majority counts, then divide by N.',
                  selection='Exploratory analysis after observing the prompt-formatting defect.',
                  native_one_eval='8aba20ad17ee2c7d2391162ac03ffaebcbb17506', dataflow='1.0.10',
                  native_evalscope='59bb367bd8565f347266a48ac1230af0b5131b97',
                  verified_source_rows_and_order=len(rows), model_inference_requests=0,
                  evidence_rows_uncompressed_sha256=hashlib.sha256(evidence_bytes).hexdigest(),
                  systems=systems, independent_hash_check_unavoidable_errors=independently_counted,
                  scope='Finite-corpus upper bound. A 100% ceiling only indicates absence of conflicting targets for identical visible prompts. Measured model accuracy and third-party impact remain distinct quantities.')
    (HERE / 'prompt_collision_results.json').write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'mixed_prompt_groups.json.gz').write_bytes(gzip.compress(json.dumps(collisions, separators=(',', ':')).encode(), mtime=0))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
