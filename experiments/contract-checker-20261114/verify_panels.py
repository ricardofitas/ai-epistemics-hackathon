"""Check CLI exit codes and the inference guard against the immutable panels."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from check_contract import InvalidContract, guarded_inference, read_records

ROOT = Path(__file__).resolve().parent


def main():
    reports = json.loads((ROOT / 'PANEL_RESULTS.json').read_text())
    checked = []
    for report in reports:
        name = report['panel']
        expected = 'PASS' if name.startswith(('repaired__', 'evalscope__')) or name == 'oneeval__medmcqa__validation' else 'FAIL'
        assert report['status'] == expected, (name, report['status'])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            process = subprocess.run([sys.executable, str(ROOT / 'check_contract.py'), str(ROOT / report['input_file']), '--output', str(output)], capture_output=True, text=True)
            assert process.returncode == (0 if expected == 'PASS' else 1), process.stderr
            emitted = json.loads(output.read_text())
            assert emitted['status'] == expected
            assert emitted['counts'] == report['counts']
            assert emitted['failures'] == report['failures']
        calls = []
        def measured_backend(prompts):
            calls.append(len(prompts))
            return len(prompts)
        try:
            answer = guarded_inference(read_records(ROOT / report['input_file']), measured_backend)
            assert expected == 'PASS' and answer == report['counts']['records']
        except InvalidContract as error:
            assert expected == 'FAIL' and error.report['status'] == 'FAIL'
        assert len(calls) == (1 if expected == 'PASS' else 0)
        checked.append(dict(panel=name, expected=expected, observed=report['status'], rows=report['counts']['records'],
                            constructed_backend_invocations=len(calls), cli_exit_verified=True))
    # Compare the newly computed limits to the separate prior raw-input audit.
    reference = ROOT / 'reference_evidence/prompt_collision_results.json'
    previous = json.loads(reference.read_text())
    wino = next(r for r in reports if r['panel'] == 'oneeval__winogrande__validation')
    assert wino['input_collisions']['minimum_deterministic_errors'] == previous['systems']['One-Eval native']['unavoidable_errors'] == 309
    assert wino['failures']['reference_changed_answer'] == 628
    sciq = next(r for r in reports if r['panel'] == 'oneeval__sciq__test')
    assert sciq['failures']['context_not_bound'] == 884
    assert sciq['failures']['native_reference_invalid'] == 3
    assert sciq['failures']['reference_changed_answer'] == 3
    assert sciq['attention']
    lab = next(r for r in reports if 'lab-bench' in r['panel'] and r['panel'].startswith('oneeval__'))
    assert lab['failures']['correct_choice_missing'] == 33
    receipt = dict(panels=len(checked), checked_records=sum(r['rows'] for r in checked),
                   outcomes=dict(Counter(r['observed'] for r in checked)),
                   model_provider_calls=0, prior_independent_exact_counts_matched=True, panels_checked=checked,
                   scope='Selected regression panel with repeated source records across original, repaired and healthy configurations. Counts are not independent questions or a prevalence estimate.')
    (ROOT / 'VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k:v for k,v in receipt.items() if k != 'panels_checked'}, indent=2))


if __name__ == '__main__':
    main()
