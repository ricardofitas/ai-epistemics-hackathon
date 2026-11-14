"""Check explicitly normalized local evaluation contracts before inference.

The checker consumes JSONL or gzip JSONL. Source adapters provide official
answer semantics, displayed choices, the actual parsed reference and measured
question/context mutation probes. No model endpoint is called.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path


class InvalidContract(ValueError):
    def __init__(self, report):
        super().__init__('Evaluation contract is ' + report['status'])
        self.report = report


def read_records(path):
    path = Path(path)
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def audit_contract(records):
    failures = Counter()
    missing_checks = Counter()
    examples = defaultdict(list)
    official_positions = Counter()
    prompt_targets = defaultdict(Counter)
    counts = Counter()
    ids = set()

    def finding(code, row_id, incomplete=False):
        target = missing_checks if incomplete else failures
        target[code] += 1
        if len(examples[code]) < 5:
            examples[code].append(row_id)

    for index, record in enumerate(records):
        counts['records'] += 1
        row_id = str(record.get('row_id', index))
        if row_id in ids:
            finding('duplicate_row_id', row_id)
        ids.add(row_id)
        if record.get('schema_version') != 1:
            finding('unsupported_schema', row_id, incomplete=True)
            continue
        prompt = record.get('prompt')
        if not isinstance(prompt, str) or not prompt.strip():
            finding('prompt_unavailable', row_id)
        else:
            for field, required in [('question', True), ('context', record.get('context_required', False))]:
                if not required:
                    continue
                probe = record.get(field + '_probe_changed')
                if type(probe) is not bool:
                    finding(field + '_probe_unavailable', row_id, incomplete=True)
                elif not probe:
                    finding(field + '_not_bound', row_id)
        gold = record.get('correct_text')
        if not isinstance(gold, str) or not gold.strip():
            finding('source_gold_unavailable', row_id)
            continue
        counts['source_gold_available'] += 1
        expected = record.get('expected_reference')
        kind = record.get('kind')
        if kind == 'choice':
            choices = record.get('choices')
            if not isinstance(choices, list) or len(choices) < 2 or len(choices) > 26:
                finding('choices_unresolved', row_id)
                continue
            if any(not isinstance(choice, str) or not choice.strip() for choice in choices):
                finding('invalid_choice_text', row_id)
                continue
            if gold not in choices:
                finding('correct_choice_missing', row_id)
                continue
            labels = [chr(65 + j) for j in range(len(choices))]
            if expected not in labels:
                finding('source_reference_unresolved', row_id, incomplete=True)
                continue
            if choices[labels.index(expected)] != gold:
                finding('source_adapter_inconsistent', row_id, incomplete=True)
                continue
        elif kind == 'freeform':
            if expected != gold:
                finding('source_adapter_inconsistent', row_id, incomplete=True)
                continue
        else:
            finding('unsupported_task_kind', row_id, incomplete=True)
            continue
        reference = record.get('reference')
        if reference is None or reference == '':
            finding('native_reference_invalid', row_id)
        elif reference != expected:
            finding('reference_changed_answer', row_id)
        counts['source_scorable_rows'] += 1
        official_positions[expected] += 1
        if isinstance(prompt, str) and prompt.strip():
            prompt_targets[prompt][expected] += 1
    mixed = [counter for counter in prompt_targets.values() if len(counter) > 1]
    if mixed:
        failures['conflicting_gold_for_same_prompt_groups'] = len(mixed)
    covered = sum(sum(counter.values()) for counter in prompt_targets.values())
    maximum = sum(max(counter.values()) for counter in prompt_targets.values())
    attention = []
    if counts['source_scorable_rows'] > 1 and len(official_positions) == 1:
        attention.append('one_constant_answer_is_perfect_on_the_source_targets')
    if not counts['records']:
        missing_checks['empty_input'] = 1
    status = 'FAIL' if failures else 'INCOMPLETE' if missing_checks else 'PASS'
    return dict(status=status, counts=dict(counts), failures=dict(failures), incomplete_checks=dict(missing_checks),
                examples=dict(examples), source_target_counts=dict(official_positions), attention=attention,
                input_collisions=dict(visible_prompts=len(prompt_targets), covered_rows=covered,
                    rows_in_conflicting_groups=sum(sum(c.values()) for c in mixed),
                    minimum_deterministic_errors=covered - maximum,
                    empirical_prompt_only_accuracy_ceiling=maximum / covered if covered else None),
                model_calls=0)


def require_valid_contract(records):
    report = audit_contract(records)
    if report['status'] != 'PASS':
        raise InvalidContract(report)
    return report


def guarded_inference(records, generate):
    """Call a user-supplied generation function after a complete contract check."""
    rows = list(records)
    require_valid_contract(rows)
    return generate([row['prompt'] for row in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = audit_contract(read_records(args.input))
    report['input_sha256'] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end='')
    return {'PASS': 0, 'FAIL': 1, 'INCOMPLETE': 2}[report['status']]



def run_source_bound_evaluation(*args, **kwargs):
    """Run the bounded source/request/structured-final gate before scoring.

    Public engineering entrypoint for MixEval free-form, non-stream Chat
    Completions under the declared native profile. Unsupported profiles are
    INCOMPLETE before dispatch. See source_contract_gateway.run_entrypoint for
    the explicit callback/capture trust boundary and scorer interface.
    Existing normalized-contract audits and command-line behavior are unchanged.
    """
    from source_contract_gateway import run_entrypoint
    return run_entrypoint(*args, **kwargs)

if __name__ == '__main__':
    raise SystemExit(main())
