"""Verify the captured sample and review native trim-only option normalization.

The originally executed checker and reports remain immutable. The post-review
adapter applies one normalization already performed by the native preprocessor
only when every option is preserved in its original position.
"""
import gzip
import hashlib
import json
from pathlib import Path
import types
import zipfile

from choice_adapter import align_preserved_options

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'artifact'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read_lines(path):
    raw = gzip.decompress(path.read_bytes())
    return raw, [json.loads(line) for line in raw.splitlines()]


def source_answer(name, record):
    if name in ('arc-challenge', 'openbookqa'):
        labels = list(map(str, record['choices']['label']))
        options = record['choices']['text']
        position = labels.index(str(record['answerKey']))
    elif name == 'mmlu':
        options, position = record['choices'], record['answer']
    else:
        assert name == 'mmlu-pro'
        options, position = record['options'], record['answer_index']
        assert record['answer'].upper() == chr(65 + position)
    assert 0 <= position < len(options)
    return options, position


def main():
    protocol = json.loads((DATA / 'PROTOCOL.json').read_text())
    assert protocol == json.loads((ROOT / 'PROTOCOL.json').read_text())
    assert (DATA / 'GALLERY.json').read_bytes() == (ROOT / 'GALLERY.json').read_bytes()
    assert sha((DATA / 'GALLERY.json').read_bytes()) == protocol['gallery_sha256']
    support = (DATA / 'source_support.zip').read_bytes()
    assert sha(support) == protocol['source_support_sha256']
    with zipfile.ZipFile(DATA / 'source_support.zip') as bundle:
        checker_bytes = bundle.read('oneeval_contract_checker_20261114/check_contract.py')
    assert sha(checker_bytes) == protocol['checker_sha256']
    module = types.ModuleType('frozen_checker_for_post_review')
    exec(compile(checker_bytes, 'byte_verified_frozen_checker', 'exec'), module.__dict__)
    dispositions = json.loads((DATA / 'DISPOSITIONS.json').read_text())
    assert len(dispositions) == 4 and all(row['status'] == 'captured' for row in dispositions)
    reviews = []
    details = []
    output = ROOT / 'reviewed_inputs'
    output.mkdir(exist_ok=True)
    for disposition in dispositions:
        name = disposition['benchmark']
        folder = DATA / 'capture' / name
        raw, full = read_lines(folder / 'SOURCE_ROWS.jsonl.gz')
        assert sha(raw) == disposition['source_rows_sha256']
        assert len(full) == disposition['total_source_rows']
        for part in disposition['parquet_files']:
            assert sha((folder / part['file']).read_bytes()) == part['sha256']
        selected_bytes, selected = read_lines(folder / 'SELECTED.jsonl.gz')
        assert sha(selected_bytes) == disposition['selected_rows_sha256']
        ordering = sorted(range(len(full)), key=lambda i:(sha(canonical(full[i])), i))[:100]
        assert ordering == [row['source_index'] for row in selected]
        for row in selected:
            assert row['record'] == full[row['source_index']]
            assert row['source_sha256'] == sha(canonical(row['record']))
        _, native = read_lines(folder / 'CHECKER_NATIVE.jsonl.gz')
        _, repaired = read_lines(folder / 'CHECKER_REPAIRED.jsonl.gz')
        assert len(native) == len(repaired) == len(selected) == 100
        original = json.loads((folder / 'RESULT.json').read_text())
        assert module.audit_contract(native) == original['native_checker']
        assert module.audit_contract(repaired) == original['repaired_checker']
        reviewed = []
        changed = []
        eligible = 0
        for index, (source, record) in enumerate(zip(selected, native)):
            options, position = source_answer(name, source['record'])
            gold = options[position]
            item = align_preserved_options(record, options, position)
            if item['choices'] == [option.strip() for option in options]:
                eligible += 1
                if item != record:
                    changed.append(index)
                    details.append(dict(benchmark=name, row=index, source_index=source['source_index'],
                        original_gold=gold, displayed_gold=item['choices'][position],
                        original_expected_reference=record['expected_reference'], reviewed_expected_reference=item['expected_reference'],
                        normalization='str.strip on each option; full sequence equal and positions preserved'))
            reviewed.append(item)
        report = module.audit_contract(reviewed)
        revised_bytes = b''.join(canonical(row) + b'\n' for row in reviewed)
        path = output / (name + '.jsonl.gz')
        path.write_bytes(gzip.compress(revised_bytes, mtime=0))
        gate_calls = []
        try:
            module.guarded_inference(reviewed, lambda prompts:gate_calls.append(len(prompts)))
        except module.InvalidContract:
            pass
        assert len(gate_calls) == int(report['status'] == 'PASS')
        reviews.append(dict(benchmark=name, rows=len(reviewed), original_native_checker=original['native_checker'],
            normalization_reviewed_checker=report, sequence_preserving_trim_eligible_rows=eligible,
            adapter_changed_rows=changed, original_records_preserved=True, source_parquet_hashes_verified=True,
            selection_order_verified=True, corrected_source_oracle_score=original['corrected_reference_oracle']['score'],
            original_oracle_controls=original['native_scoring_controls'],
            immutable_checker_sha256=protocol['checker_sha256'], provider_model_calls=0,
            reviewed_input=path.relative_to(ROOT).as_posix(), reviewed_input_sha256=sha(path.read_bytes()),
            diagnostic_backend_calls=len(gate_calls)))
    result = dict(verified_original_panels=4, original_records=400,
        raw_source_records=sum(row['total_source_rows'] for row in dispositions),
        first_pass='Prospective selection and frozen checker, before review of two whitespace-only adapter alerts.',
        review='Post-outcome adapter correction, with all original capture files retained and the checker byte-identical.',
        adapter_false_alerts_corrected=len(details), normalization_details=details,
        provider_model_calls=0, reviews=reviews)
    (ROOT / 'VERIFIED_REVIEW.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['reviews','normalization_details']}, indent=2))
    for row in reviews:
        print(row['benchmark'], row['original_native_checker']['status'], '->', row['normalization_reviewed_checker']['status'], row['normalization_reviewed_checker']['failures'])


if __name__ == '__main__':
    main()
