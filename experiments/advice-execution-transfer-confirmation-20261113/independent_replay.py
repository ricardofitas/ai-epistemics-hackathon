"""Recompute transfer aggregates from original captures without importing its analyser."""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def numeric(value):
    if not isinstance(value, str):
        return None
    atom = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
    if not re.fullmatch(atom + '(?:/' + atom + ')?', value.strip()):
        return None
    try:
        parts = value.strip().split('/')
        return F(parts[0]) if len(parts) == 1 else F(parts[0]) / F(parts[1])
    except (ValueError, ZeroDivisionError):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    root = args.directory
    findings = []
    journal_checks = 0
    for stage in ['reviews', 'solvers']:
        manifest_path = root / stage / 'manifest.jsonl'
        response_path = root / stage / 'responses.jsonl'
        if not response_path.exists():
            findings.append(stage + ': no aggregate capture')
            continue
        manifest = read_lines(manifest_path)
        captured = read_lines(response_path)
        actual = {r['trial_id']: r for r in captured}
        assert len(actual) == len(captured) == len(manifest), stage
        assert set(actual) == {r['trial_id'] for r in manifest}, stage
        for planned in manifest:
            record = actual[planned['trial_id']]
            if record.get('local_capture_error'):
                findings.append(planned['trial_id'] + ': retained local capture uncertainty')
                continue
            assert record['attempt_count'] == 1
            assert record['request_payload'] == planned['request_payload']
            payload = json.dumps(planned['request_payload'], sort_keys=True, ensure_ascii=False,
                                 separators=(',', ':'), allow_nan=False).encode()
            assert hashlib.sha256(payload).hexdigest() == record['request_sha256'] == planned['request_sha256']
            journal = root / stage / 'stream_journals' / (planned['trial_id'] + '.jsonl')
            assert hashlib.sha256(journal.read_bytes()).hexdigest() == record['stream_journal_sha256']
            journal_checks += 1
    summary = json.loads((root / 'analysis_summary.json').read_text())
    if summary['transfer']['families']:
        requests = read_lines(root / 'solvers/manifest.jsonl')
        captures = {r['trial_id']: r for r in read_lines(root / 'solvers/responses.jsonl')}
        totals = defaultdict(Counter)
        labels = Counter()
        for request in requests:
            record = captures[request['trial_id']]
            label = 'capture_incomplete'
            resolved = None
            complete = (record.get('http_status') == 200 and record.get('completed_nonempty') is True
                        and record.get('response_status') == 'completed'
                        and record.get('terminal_event_seen') is True
                        and record.get('stream_incomplete') is False
                        and record.get('used_delta_fallback') is False
                        and record.get('transport_error') is None)
            if complete:
                text = record.get('output_text', '').strip()
                matches = re.findall(r'<answer>([^<>]+)</answer>', text)
                label = 'answer_format_unresolved'
                if len(matches) == 1 and text.endswith('</answer>'):
                    answer, gold = numeric(matches[0]), numeric(request['gold'])
                    label = 'answer_numeric_unresolved'
                    if answer is not None and gold is not None:
                        resolved = int(answer == gold)
                        label = 'correct' if resolved else 'wrong'
            counts = totals[request['request_payload']['model'], request['variant']]
            counts['n'] += 1
            counts['correct'] += resolved == 1
            counts['unknown'] += resolved is None
            labels[label] += 1
        assert dict(labels) == summary['transfer']['labels']
        bounds = {}
        for (model, variant), counts in totals.items():
            lower = F(counts['correct'], counts['n'])
            upper = F(counts['correct'] + counts['unknown'], counts['n'])
            expected = summary['transfer']['accuracy'][model][variant]
            assert (str(lower), str(upper)) == (expected['lower'], expected['upper'])
            bounds[model, variant] = (lower, upper)
        contrasts = []
        for result in summary['transfer']['pairs']:
            a, b = result['pair']
            al, ah = bounds[a, 'added_operation']; bl, bh = bounds[b, 'added_operation']
            at = [sum((bounds[a, v][j] for v in ('numeric', 'paraphrase')), F()) / 2 for j in (0, 1)]
            bt = [sum((bounds[b, v][j] for v in ('numeric', 'paraphrase')), F()) / 2 for j in (0, 1)]
            lower = al - bh - at[1] + bt[0]
            upper = ah - bl - at[0] + bt[1]
            assert str(lower) == result['distortion']['lower']
            assert str(upper) == result['distortion']['upper']
            contrasts.append({'pair': result['pair'], 'lower': str(lower), 'upper': str(upper)})
    else:
        contrasts = []
    report = {'status': 'independent_code_path_agrees', 'journal_hash_checks': journal_checks,
              'planned_payloads_match_capture': True, 'attempts_per_captured_request': 1,
              'transfer_contrasts': contrasts, 'retained_capture_notes': findings,
              'review': 'Independent arithmetic implementation by the coordinator; external human validation pending'}
    (root / 'INDEPENDENT_REPLAY.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
