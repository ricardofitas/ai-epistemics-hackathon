#!/usr/bin/env python3
"""Audit every attempted frozen SSE request; optionally make an advice review packet."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re

from capture_audit_source import audit_capture, instant


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value, jsonl=False, immutable=False):
    data = (''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in value)
            if jsonl else json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    if path.exists() and immutable:
        if path.read_text() != data:
            raise ValueError('Refusing to replace an immutable review packet/key')
        return
    path.write_text(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory', type=Path)
    ap.add_argument('--freeze-commit', required=True)
    ap.add_argument('--freeze-time', required=True)
    ap.add_argument('--manifest-sha256', required=True)
    ap.add_argument('--advice-review', action='store_true')
    ap.add_argument('--packet-seed', type=int, default=2026111331)
    args = ap.parse_args()
    p = args.directory
    if not re.fullmatch('[0-9a-f]{40}', args.freeze_commit):
        raise ValueError('Require verified Git freeze commit')
    if digest(p / 'manifest.jsonl') != args.manifest_sha256:
        raise ValueError('Manifest differs from externally verified freeze')
    jobs, records = rows(p / 'manifest.jsonl'), rows(p / 'responses.jsonl')
    job_ids = [r['trial_id'] for r in jobs]
    captures = {r['trial_id']: r for r in records}
    if len(set(job_ids)) != len(jobs) or len(captures) != len(records) or set(captures) != set(job_ids):
        raise ValueError('Missing, duplicate or unplanned attempts')
    freeze = instant(args.freeze_time)
    enriched = []
    for job in jobs:
        raw = captures[job['trial_id']]
        checks = audit_capture(p, job, raw, freeze)
        metadata = {k: v for k, v in job.items() if k != 'request_payload'}
        enriched.append({**raw, **metadata, **checks,
                         'capture_complete': checks['completion_verified'],
                         'response': raw.get('output_text', '')})
    receipt = load(p / 'run_metadata.json')
    if receipt.get('requested') != len(jobs) or receipt.get('recorded') != len(jobs) or receipt.get('retries') != 0:
        raise ValueError('Run receipt differs from planned one-attempt allocation')
    write(p / 'responses_enriched.jsonl', enriched, jsonl=True)
    if args.advice_review:
        shuffled = enriched.copy()
        random.Random(args.packet_seed).shuffle(shuffled)
        packet, key = [], []
        for n, r in enumerate(shuffled, 1):
            rid = f'I{n:03d}'
            packet.append({'response_id': rid, 'case_id': r['case_id'],
                           'response': r['response'], 'capture_complete': r['capture_complete'],
                           'incomplete_details': r.get('incomplete_details')})
            key.append({'response_id': rid, 'trial_id': r['trial_id']})
        write(p / 'review_packet.jsonl', packet, jsonl=True, immutable=True)
        write(p / 'review_key.jsonl', key, jsonl=True, immutable=True)
    complete = sum(r['capture_complete'] for r in enriched)
    integrity = {'freeze_commit': args.freeze_commit, 'freeze_utc': args.freeze_time,
                 'manifest_sha256': args.manifest_sha256, 'attempted': len(jobs),
                 'capture_complete': complete, 'capture_incomplete': len(jobs) - complete,
                 'all_attempts_accounted_for': True,
                 'all_verified': all(r['capture_integrity'] == 'verified' for r in enriched),
                 'all_starts_after_freeze': all(instant(r['started_utc']) > freeze for r in enriched),
                 'response_status_counts': dict(Counter(str(r.get('response_status')) for r in enriched)),
                 'terminal_status_mismatches': sum(bool(r.get('event_status_mismatch')) for r in enriched),
                 'reported_usage_cost_sum': sum((r.get('usage') or {}).get('cost') or 0 for r in enriched),
                 'billing_limit': 'Reported usage is not account debit, verified complete billing or USD conversion.',
                 'run_receipt': receipt, 'human_review': 'pending'}
    if args.advice_review:
        integrity['review_packet_sha256'] = digest(p / 'review_packet.jsonl')
        integrity['review_key_sha256'] = digest(p / 'review_key.jsonl')
    write(p / 'integrity.json', integrity)
    print(json.dumps(integrity))


if __name__ == '__main__':
    main()
