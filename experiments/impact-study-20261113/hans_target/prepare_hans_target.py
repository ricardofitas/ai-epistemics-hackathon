#!/usr/bin/env python3
"""Prepare a new output-blind HANS external target; never call candidate models."""
import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from collections import Counter
import urllib.request

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
SOURCE = PROJECT / 'paper_research_20261113/consequence/source/hans.tsv'
META = SOURCE.parent / 'hans_source.json'
PRIOR = PROJECT / 'paper_research_20261113/consequence/selected_data.json'
WSC_BUILDER = ROOT.parent / 'wsc/build_experiment.py'
SEEDS = {'sample': 2026111341, 'request_order': 2026111342,
         'opaque_ids': 2026111343, 'input_order': 2026111344,
         'bootstrap': 2026111345}
STRATA = [('ln_subject/object_swap', 'non-entailment'),
          ('le_passive', 'entailment')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode()


def write(path, value, jsonl=False):
    text = (''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in value)
            if jsonl else json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    if path.exists() and path.read_text() != text:
        raise ValueError('Refusing to replace prospective artifact: ' + str(path))
    path.write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default_source = SOURCE if SOURCE.exists() else ROOT / 'source/hans.tsv'
    default_prior = (PRIOR if PRIOR.exists() else
                     ROOT.parents[1] / 'paper-research-wave1-20261113/consequence/selected_data.json')
    parser.add_argument('--source', type=Path, default=default_source)
    parser.add_argument('--source-metadata', type=Path, default=ROOT / 'official_hans_source_metadata.json')
    parser.add_argument('--prior-prepared', type=Path, default=default_prior)
    parser.add_argument('--wsc-builder', type=Path, default=WSC_BUILDER)
    parser.add_argument('--download-source', action='store_true',
                        help='Fetch the exact pinned official source if its cache is absent; no model inference')
    args = parser.parse_args()
    if (ROOT / 'api_artifacts').exists() or (ROOT / 'stream_journals').exists():
        raise ValueError('Never rebuild after inference starts')
    meta = json.loads(args.source_metadata.read_text())
    if not args.source.exists():
        if not args.download_source:
            raise FileNotFoundError('Pinned HANS source cache absent; provide --source or --download-source')
        args.source.parent.mkdir(parents=True, exist_ok=True)
        downloaded = urllib.request.urlopen(meta['url'], timeout=120).read()
        if hashlib.sha256(downloaded).hexdigest() != meta['sha256']:
            raise ValueError('Downloaded source differs from pinned official SHA256')
        args.source.write_bytes(downloaded)
    raw = args.source.read_bytes()
    assert len(raw) == meta['file_bytes'] == 15462062
    assert sha(args.source) == meta['sha256'] == 'c55b62feef9913070e88f38938dc2492018c945ac81f70139346472494124e79'
    git_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert git_blob == meta['git_blob_sha'] == 'e042af242b19708d9c0256c713e873415c0b58a1'
    spec = importlib.util.spec_from_file_location('wsc_builder', args.wsc_builder)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    instruction, models = module.INSTRUCTION, module.MODELS
    prior = [r for r in json.loads(args.prior_prepared.read_text())['items'] if r['suite'] == 'hans']
    assert len(prior) == 20
    excluded_ids = {str(r['source_id']) for r in prior}
    excluded_texts = {(r['sentence1'], r['sentence2']) for r in prior}
    with args.source.open() as f:
        source_rows = list(csv.DictReader(f, delimiter='\t'))
    assert len(source_rows) == 30000
    rng = random.Random(SEEDS['sample'])
    selected, flow = [], []
    for subcase, gold in STRATA:
        raw_pool = [(n, r) for n, r in enumerate(source_rows)
                    if r['subcase'] == subcase and r['gold_label'] == gold]
        assert len(raw_pool) == 1000
        pool, seen = [], set()
        overlap = []
        duplicates = []
        for index, r in raw_pool:
            key = (r['sentence1'], r['sentence2'])
            if r['pairID'] in excluded_ids or key in excluded_texts:
                overlap.append(r['pairID'])
                continue
            if key in seen:
                duplicates.append(r['pairID'])
                continue
            seen.add(key)
            pool.append((index, r))
        assert len(pool) >= 40
        picked = rng.sample(pool, 40)
        flow.append({'subcase': subcase, 'gold_label': gold, 'source_rows': len(raw_pool),
                     'prior_prepared_id_or_text_excluded': overlap,
                     'duplicate_input_rows_excluded_keep_first': duplicates,
                     'eligible_unique_inputs': len(pool), 'selected': 40})
        for index, r in picked:
            selected.append({'source_row_index_zero_based': index, 'source_pair_id': r['pairID'],
                             'premise': r['sentence1'], 'hypothesis': r['sentence2'],
                             'gold_binary': gold, 'subcase': subcase,
                             'template': r['template'], 'heuristic': r['heuristic']})
    random.Random(SEEDS['opaque_ids']).shuffle(selected)
    for n, r in enumerate(selected, 1):
        r['task_id'] = f'K{n:03d}'
    assert len(selected) == len({r['source_pair_id'] for r in selected}) == 80
    assert len({(r['premise'], r['hypothesis']) for r in selected}) == 80
    inputs = selected.copy()
    random.Random(SEEDS['input_order']).shuffle(inputs)
    batches = [inputs[n:n + 8] for n in range(0, 80, 8)]
    manifest = []
    for model in models:
        for batch_index, batch in enumerate(batches, 1):
            model_input = [{'id': r['task_id'], 'premise': r['premise'],
                            'hypothesis': r['hypothesis']} for r in batch]
            payload = {'model': model, 'instructions': instruction,
                       'input': json.dumps(model_input, ensure_ascii=False),
                       'max_output_tokens': 16384, 'temperature': 0.0, 'stream': True,
                       'tools': [], 'tool_choice': 'none', 'agentic_memory': False, 'store': False}
            manifest.append({'trial_id': f'IH-{len(manifest) + 1:03d}',
                             'case_id': 'external_directional_nli_target',
                             'requested_model': model, 'batch_index': batch_index,
                             'task_ids': [r['task_id'] for r in batch],
                             'request_payload': payload,
                             'request_sha256': hashlib.sha256(canonical(payload)).hexdigest()})
    random.Random(SEEDS['request_order']).shuffle(manifest)
    for n, r in enumerate(manifest, 1):
        r['execution_order'] = n
    assert len(manifest) == 40
    for j in manifest:
        assert set(j['request_payload']) == {'model', 'instructions', 'input', 'max_output_tokens',
                                             'temperature', 'stream', 'tools', 'tool_choice',
                                             'agentic_memory', 'store'}
        for r in json.loads(j['request_payload']['input']):
            assert set(r) == {'id', 'premise', 'hypothesis'}
    instruction_file = ROOT / 'classification_instruction.txt'
    if instruction_file.exists() and instruction_file.read_text() != instruction + '\n':
        raise ValueError('Refusing to replace the frozen common classifier instruction')
    instruction_file.write_text(instruction + '\n')
    write(ROOT / 'selected_data.json', {'items': selected, 'official_three_way_gold': False})
    write(ROOT / 'task_key.json', {'rows': [{k: v for k, v in r.items()
                                           if k not in ['premise', 'hypothesis']} for r in selected]})
    write(ROOT / 'manifest.jsonl', manifest, jsonl=True)
    write(ROOT / 'source_receipt.json', {'source_metadata': meta, 'source_sha256_verified': sha(args.source),
                                        'source_git_blob_verified': git_blob,
                                        'prior_prepared_items_sha256': sha(args.prior_prepared),
                                        'prior_hans_ids_excluded': sorted(excluded_ids),
                                        'selection_flow': flow})
    existing = ROOT / 'protocol.json'
    created = (json.loads(existing.read_text())['created_utc'] if existing.exists()
               else dt.datetime.now(dt.timezone.utc).isoformat())
    protocol = {
        'id': 'wsc-independent-hans80-target-v1', 'created_utc': created,
        'status': 'prospective_no_classifier_calls_or_performance_seen',
        'purpose': 'A separately fixed authentic role-sensitive NLI target for the NEW WSC label-conversion consequence study.',
        'old_gate_scope': 'This does NOT activate or reuse the old failed PAWS pilot. Its no-run status remains unchanged. WSC was selected after discovery of Q48; this is exploratory even though the current target is frozen before predictions.',
        'source': {'repository': meta['repository'], 'commit': meta['commit'], 'path': meta['path'],
                   'sha256': meta['sha256'], 'git_blob_sha': git_blob, 'rows': 30000},
        'models': models, 'candidate_selection': 'Same four fixed hosted aliases as WSC, selected before performance; immutable checkpoint identities unavailable.',
        'allocation': {'items': 80, 'strata': {s: 40 for s, _ in STRATA}, 'models': 4,
                       'batch_size': 8, 'batches_per_model': 10, 'requests': 40,
                       'classification_labels': 320, 'maximum_requested_output_tokens': 655360},
        'seeds': SEEDS,
        'sampling': 'For each declared subcase/gold stratum in original source order, exclude the previously prepared20 source IDs or exact input pairs, keep first of exact duplicate pairs, then sample40 without replacement with Python Random(sample seed), using one RNG in the stated stratum order. No observed model-error filter. Unique opaque IDs and shared input batches are separately shuffled.',
        'source_overlap': 'Twenty prior items belong to the unexecuted PAWS protocol; excluding them is data hygiene, not performance selection. Public HANS data are not proven unseen in pretraining.',
        'shared_interface': 'Exact common WSC three-way classifier instruction and payload schema. Only opaque ID, premise and hypothesis transmitted. No suite, source ID, subcase, gold, target or selection role transmitted.',
        'controls': {'max_output_tokens': 16384, 'temperature': 0.0, 'stream': True, 'tools': [],
                     'tool_choice': 'none', 'agentic_memory': False, 'store': False,
                     'history': 'none', 'concurrency': 2, 'socket_timeout_seconds': 120, 'retries': 0},
        'parser': 'Final assistant text must be one complete JSON object, optionally one outer codefence. It must contain predictions with all and only supplied IDs once and labels entailment/contradiction/neutral (casefold allowed). No output repair or extra inference.',
        'capture_quality': 'Require verified HTTP200, content type text/event-stream, terminal response.completed with provider statuscompleted and nonempty final text, no transport error, fallback, format deviation or malformed SSE JSON. Conflicting provider flags remain incomplete, not semantic error.',
        'gold': 'Official binary HANS entailment/non-entailment unchanged. Map both neutral and contradiction predictions to non-entailment. Do not assign official three-way NLI gold.',
        'outcomes': {'per_model': 'Binary accuracy on all80 and separately by the two source strata, label counts, invalid/missing coverage.',
                     'pairwise': 'All six fixed model pairs, same shared item differences; no outcome-selected pairs.',
                     'missing_bounds': 'Each missing/invalid item contributes [0,1] on the fixed80 denominator. No replacing calls or scoring operational absence as a semantic error. Declare robust ordering only for strictly separated conservative score bounds.',
                     'external_consequence': 'Fix unique bad-rule and repaired-rule WSC selection winners using ONLY WSC selection data. Then report repaired-selected minus bad-selected binary accuracy on this HANS80 target. Same winner gives zero, ties/invalid WSC choice indeterminate, and signed negative/null outcomes retained. No choosing among WSC tied winners using HANS scores.',
                     'claim_bound': 'This controlled80-item two-subcase diagnostic is not all HANS, all NLI, or real-world harm. It supplies no normative practical effect threshold. WSC binary repair does not by itself establish the complete original role-tracking claim.'},
        'uncertainty': {'draws': 10000, 'seed': SEEDS['bootstrap'],
                        'unit': 'Paired item resampling jointly across models within each fixed subcase stratum; fixed WSC winners when measuring external consequence.',
                        'interval': 'Two-sided95percentile with NumPy linear quantiles.',
                        'limits': 'Conditional descriptive resampling only: negative stratum has one source template and passive stratum has two, so item bootstrap does not estimate template/domain/batch/provider uncertainty. Tiny fixed source slice, no population inference or significance claim.'},
        'stopping': 'Attempt all40 rows once. Preserve all missing/incomplete/invalid/null/tied outcomes; no error-selected retries, added items/candidates or stop at reversal.',
        'human_review': 'pending; authentic source labels retained, no new human validation claimed',
        'hashes': {n: sha(ROOT / n) for n in ['selected_data.json', 'task_key.json', 'manifest.jsonl',
                                            'source_receipt.json', 'classification_instruction.txt',
                                            'official_hans_source_metadata.json', 'prepare_hans_target.py']},
        'instruction_source_path': '../wsc/build_experiment.py',
        'instruction_source_sha256_at_preparation': sha(args.wsc_builder),
        'runner_sha256': sha(ROOT.parent / 'methods/run_adaption_classification_stream.py'),
        'operational_amendment': {'old_cap': 8192, 'new_cap': 16384,
                                  'reason': 'Prospective common WSC/HANS classification cap increase authorized before classifier inference, based on prior advice token-limit missingness; no source/model/metric/seed changes or retries.',
                                  'superseded_artifacts': 'superseded_8192/',
                                  'snapshot_manifest_sha256': sha(ROOT / 'superseded_8192/snapshot_manifest.json')}}
    if (ROOT / 'analyze_hans_target.py').exists():
        protocol['analysis_sha256'] = sha(ROOT / 'analyze_hans_target.py')
        protocol['capture_audit_source_sha256'] = sha(ROOT.parent / 'methods/capture_audit_source.py')
    write(ROOT / 'protocol.json', protocol)
    checks = {'status': 'PASS_OFFLINE_ONLY', 'no_calls': True, 'source_rows': len(source_rows),
              'selected': len(selected), 'unique_inputs': len({(r['premise'], r['hypothesis']) for r in selected}),
              'strata': dict(Counter(r['subcase'] for r in selected)), 'requests': len(manifest),
              'all_models_same_batches': True, 'no_prior_prepared_id_overlap': not bool({r['source_pair_id'] for r in selected} & excluded_ids),
              'model_facing_metadata': 'Only id/premise/hypothesis plus common instruction',
              'manifest_sha256': sha(ROOT / 'manifest.jsonl'), 'protocol_sha256': sha(ROOT / 'protocol.json')}
    write(ROOT / 'PREPARATION_CHECKS.json', checks)
    print(json.dumps(checks))


if __name__ == '__main__':
    main()
