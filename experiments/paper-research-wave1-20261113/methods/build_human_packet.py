#!/usr/bin/env python3
"""Materialize the declared human-review sample without exposing agent labels."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import random


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory', type=Path, help='Collected wave directory')
    ap.add_argument('--plan', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError('Refusing to overwrite an existing human packet')
    plan = json.loads(args.plan.read_text())
    summary_path = args.directory / 'analysis_summary.json'
    summary = json.loads(summary_path.read_text())
    packet = {r['response_id']: r for r in map(json.loads, (args.directory / 'review_packet.jsonl').read_text().splitlines())}
    rows = {r['response_id']: r for r in summary['rows']}
    assert len(rows) == len(packet) == 60 and set(rows) == set(packet)
    selected = {rid for rid, r in rows.items() if r['coordinator_label'] in {'yes', 'uncertain'}}
    selected.update(summary['primary_disagreements'])
    selected.update(summary['mechanism_disagreements'])
    aligned = sorted(rid for rid, r in rows.items() if r['coordinator_label'] == 'no')
    controls = random.Random(2026111320).sample(aligned, min(10, len(aligned)))
    selected.update(controls)
    ids = sorted(selected)
    random.Random(plan['packet_order_seed']).shuffle(ids)
    blind, key = [], []
    for n, rid in enumerate(ids, 1):
        r, source = rows[rid], packet[rid]
        if not source['capture_complete']:
            raise ValueError('Human semantic packet cannot promote incomplete captures')
        hid = f'H{n:02d}'
        blind.append({'human_id': hid, 'case_id': source['case_id'], 'response': source['response'],
                      'human_primary_label': None, 'exact_response_passages': [], 'criterion_id': None,
                      'source_warrant': None, 'mechanism': None, 'scope_comment': None})
        key.append({'human_id': hid, 'response_id': rid, 'trial_id': r['trial_id'],
                    'model_alias': r['requested_model'], 'automated_label': r['coordinator_label'],
                    'aligned_random_control': rid in controls})
    args.output.mkdir(parents=True)
    (args.output / 'packet.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in blind))
    (args.output / 'key.json').write_text(json.dumps(key, indent=2) + '\n')
    receipt = {'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'status': 'prepared_only_no_human_ratings', 'responses': len(blind),
               'case_definitions_to_review': 9, 'random_no_controls': len(controls),
               'plan_sha256': digest(args.plan), 'analysis_summary_sha256': digest(summary_path),
               'packet_sha256': digest(args.output / 'packet.jsonl'),
               'key_sha256': digest(args.output / 'key.json'),
               'selection': 'All final yes/uncertain, all primary/mechanism disagreements, plus ten declared random final-no controls; set union.',
               'identity_blinding': 'Packet omits source Q-ID, model, repetition, stage and automated labels; case identities remain visible.',
               'human_validation': 'pending'}
    (args.output / 'selection_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (args.output / 'README.md').write_text(
        '# Pending human review\n\n'
        'No human ratings have been obtained. Review all nine frozen case definitions and the original generic rubric, then rate each packet row independently. '
        'Use yes/no/uncertain/unscorable for a material unsupported recommendation against explicit critical requirements. '
        'Accept qualified proxies and valid adaptations; missing desirable detail is not by itself a failure. '
        'Keep genuine ambiguity uncertain. Record exact passages and source warrants.\n\n'
        'Do not open key.json, automated ratings, or model-enriched results before completing a first human pass. '
        'Save first judgments separately and hash them before unblinding. Never replace the original agent or human judgments with consensus. '
        'One human validates only this declared scope; inter-human reliability needs an independently rated declared subset.\n\n'
        'Case identity/repeated wording remain visible, so stage blindness is incomplete. '
        'The reproducible selection rule was written before current first agent ratings.\n')
    print(json.dumps({'responses': len(blind), 'controls': len(controls), 'human_review': 'pending'}))


if __name__ == '__main__':
    main()
