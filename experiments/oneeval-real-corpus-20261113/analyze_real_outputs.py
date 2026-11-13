"""Frozen retrospective alias-invariance audit on byte-verified real outputs."""
import gzip
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
REPRO = ROOT.parent / 'oneeval_alias_evidence_20261113'
if not REPRO.is_dir():
    REPRO = ROOT.parent / 'oneeval-alias-audit-20261113'
CAPTURE = ROOT.parent / 'oneeval_real_corpus_capture_20261113' / 'capture'
if not CAPTURE.is_dir():
    CAPTURE = ROOT / 'capture'
sys.path.insert(0, str(REPRO))
from reproduce_alias import load_components


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def terminal_rows(data):
    grouped = {}
    padded = 0
    for source_index, row in enumerate(data['items']):
        key = (row['topology'], row['question_index'])
        group = grouped.setdefault(key, [])
        if row['padded']:
            padded += 1
            continue
        group.append((source_index, row))
    selected = []
    for key, group in grouped.items():
        assert group, ('no real round', key)
        rounds = [row['round'] for _, row in group]
        assert len(rounds) == len(set(rounds)), ('duplicate real rounds', key)
        assert len({row['ground_truth'] for _, row in group}) == 1, ('changing gold', key)
        source_index, row = max(group, key=lambda value: value[1]['round'])
        selected.append({'id': list(key), 'prediction': row['final_answer'],
                         'answer': row['ground_truth'], 'source_row_index': source_index,
                         'terminal_round': row['round'], 'included': row['included'],
                         'agent_final_answers': row['agent_final_answers'],
                         'n_agents': row['n_agents'],
                         'malicious_agent_indexes': row['malicious_agent_indexes']})
    return selected, {'source_items': len(data['items']), 'padded_items': padded,
                      'terminal_groups': len(selected),
                      'terminal_included_false': sum(not x['included'] for x in selected)}


def formula(details, workers, parallel):
    valid = [x for x in details if x is not None]
    canonical = sum(valid) / len(valid) if valid else 0.0
    if not parallel or len(details) <= 100:
        return canonical
    size = math.ceil(len(details) / workers)
    chunks = [details[i:i + size] for i in range(0, len(details), size)]
    if all(isinstance(x, (int, float)) for x in details):
        return sum(details) / len(details)
    weighted = 0.0
    for chunk in chunks:
        selected = [x for x in chunk if x is not None]
        score = sum(selected) / len(selected) if selected else 0.0
        weighted += score * len(chunk)
    return weighted / len(details)


def order_indices(records, dataset, seed):
    if seed is None:
        return list(range(len(records)))
    def key(index):
        payload = 'oneeval-real-corpus-20261113|' + str(seed) + '|' + dataset + '|' + compact(records[index]['id'])
        return hashlib.sha256(payload.encode()).digest()
    return sorted(range(len(records)), key=key)


def main():
    BenchInfo, Runner = load_components()
    spec = importlib.util.spec_from_file_location('one_eval.metrics.real_audit_fixed', REPRO / 'patched/runner.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    FixedRunner = module.MetricRunner
    receipts = json.loads((CAPTURE / 'SOURCE_RECEIPTS.json').read_text())
    assert len(receipts) == 21
    sources, actual_checks, score_rows, count_rows, row_audits = [], [], [], [], []
    aligned = {}
    output = ROOT / 'results'
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        for source in receipts:
            raw = gzip.decompress((CAPTURE / source['local_file']).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == source['sha256']
            assert hashlib.sha1(('blob ' + str(len(raw)) + '\0').encode() + raw).hexdigest() == source['git_blob_sha']
            dataset, system_json = source['path'].split('/')[-2:]
            system = system_json.removesuffix('.json')
            records, selection = terminal_rows(json.loads(raw))
            gold_map = {compact(x['id']): x['answer'] for x in records}
            if dataset in aligned:
                assert gold_map == aligned[dataset], ('unaligned system cohorts', dataset, system)
            else:
                aligned[dataset] = gold_map
            sources.append({'dataset': dataset, 'system': system, **source, **selection})
            agents = []
            for row in records:
                assert len(row['agent_final_answers']) == row['n_agents']
                for agent, response in enumerate(row['agent_final_answers']):
                    agents.append({'id': row['id'] + [agent], 'prediction': response,
                                   'answer': row['answer'], 'source_row_index': row['source_row_index'],
                                   'terminal_round': row['terminal_round'],
                                   'is_malicious_agent': agent in row['malicious_agent_indexes']})
            parser = {'type': 'choice_letter', 'choices': {'CSQA': 'A-E', 'MMLU': 'A-D', 'MMLUPRO': 'A-J'}[dataset]}
            for cohort, cohort_records in [('terminal_network', records), ('terminal_all_agents', agents)]:
                path = work / 'current.jsonl'
                def bench_for(indices):
                    path.write_text(''.join(compact(cohort_records[i]) + '\n' for i in indices))
                    return BenchInfo(bench_name=dataset + '__' + system,
                                     meta={'artifact_paths': {'records': str(path)},
                                           'pred_key': 'prediction', 'ref_key': 'answer'})
                def run(runner_type, bench, name, workers, args):
                    result = runner_type(max_workers=workers).run_bench(bench, [{'name': name, 'priority': 'primary', 'args': args}])
                    metric = result['metrics'][name]
                    assert 'error' not in metric, metric
                    return metric
                source_indices = list(range(len(cohort_records)))
                bench = bench_for(source_indices)
                for denominator in ('valid_only', 'total'):
                    args = {'parser': parser, 'denominator': denominator}
                    baseline = run(Runner, bench, 'choice_accuracy', 2, args)
                    details = baseline['details']
                    assert len(details) == len(cohort_records)
                    expected = formula(details, 1, False)
                    assert abs(baseline['score'] - expected) < 1e-12
                    count_rows.append({'cohort': cohort, 'dataset': dataset, 'system': system,
                                       'denominator': denominator,
                                       **{key: baseline[key] for key in ('score', 'total_samples', 'scored_samples',
                                          'valid_predictions', 'parse_failed', 'empty_output', 'invalid_references')}})
                    if denominator == 'valid_only':
                        for index, record in enumerate(cohort_records):
                            row_audits.append({'cohort': cohort, 'dataset': dataset, 'system': system,
                                               'id': record['id'], 'source_row_index': record['source_row_index'],
                                               'terminal_round': record['terminal_round'],
                                               'score_or_excluded': details[index],
                                               'prediction_parse': baseline['artifacts']['parse_results'][index]['pred'],
                                               'reference_parse': baseline['artifacts']['parse_results'][index]['ref']})
                    for name in ('choice_accuracy', 'accuracy', 'acc'):
                        contract = Runner(max_workers=8).run_bench_with_contract(bench, {'primary_metric': name, **args})
                        assert abs(contract['primary_metric_result']['score'] - expected) < 1e-12
                        actual_checks.append({'cohort': cohort, 'dataset': dataset, 'system': system,
                                              'denominator': denominator, 'route': 'contract', 'name': name,
                                              'workers': 8, 'order': 'source', 'score': contract['primary_metric_result']['score']})
                    # Every name/worker pair is actually invoked for the network primary.
                    # For the descriptive agent secondary, all aliases are proven function-identical;
                    # invoke accuracy at every worker count and both aliases at the extreme counts.
                    for name in ('choice_accuracy', 'accuracy', 'acc'):
                        for workers in (1, 2, 4, 8):
                            if cohort == 'terminal_all_agents' and name != 'accuracy' and workers not in (1, 8):
                                continue
                            metric = run(Runner, bench, name, workers, args)
                            wanted = formula(details, workers, name != 'choice_accuracy')
                            assert abs(metric['score'] - wanted) < 1e-12, (dataset, system, name, workers, metric['score'], wanted)
                            actual_checks.append({'cohort': cohort, 'dataset': dataset, 'system': system,
                                                  'denominator': denominator, 'route': 'original_run_bench',
                                                  'name': name, 'workers': workers, 'order': 'source',
                                                  'score': metric['score'], 'scored_samples_present': 'scored_samples' in metric})
                            if cohort == 'terminal_network' or (name == 'accuracy' and workers in (2, 8)):
                                repaired = run(FixedRunner, bench, name, workers, args)
                                assert abs(repaired['score'] - expected) < 1e-12
                                assert repaired['scored_samples'] == baseline['scored_samples']
                                actual_checks.append({'cohort': cohort, 'dataset': dataset, 'system': system,
                                                      'denominator': denominator, 'route': 'patched_run_bench',
                                                      'name': name, 'workers': workers, 'order': 'source', 'score': repaired['score']})
                    for seed in (None, *range(10)):
                        indices = order_indices(cohort_records, dataset, seed)
                        reordered = [details[i] for i in indices]
                        order = 'source' if seed is None else 'sha256_seed_' + str(seed)
                        for workers in (1, 2, 4, 8):
                            for name in ('choice_accuracy', 'accuracy', 'acc'):
                                value = formula(reordered, workers, name != 'choice_accuracy')
                                score_rows.append({'cohort': cohort, 'dataset': dataset, 'system': system,
                                                   'denominator': denominator, 'name': name,
                                                   'workers': workers, 'order': order, 'score': value,
                                                   'canonical_score': expected,
                                                   'delta_pp': 100 * (value - expected), 'method': 'exact_chunk_reducer_replay'})
                        if seed in (0, 9) and cohort == 'terminal_network':
                            reordered_bench = bench_for(indices)
                            for workers in (2, 8):
                                metric = run(Runner, reordered_bench, 'accuracy', workers, args)
                                wanted = formula(reordered, workers, True)
                                assert abs(metric['score'] - wanted) < 1e-12
                                actual_checks.append({'cohort': cohort, 'dataset': dataset, 'system': system,
                                                      'denominator': denominator, 'route': 'original_run_bench',
                                                      'name': 'accuracy', 'workers': workers, 'order': order,
                                                      'score': metric['score']})
                            bench = bench_for(source_indices)
                print(dataset, system, cohort, 'verified', len(cohort_records), flush=True)
    comparisons, top_sets = [], []
    dimensions = {}
    for row in score_rows:
        if row['name'] != 'accuracy':
            continue
        key = (row['cohort'], row['dataset'], row['denominator'], row['workers'], row['order'])
        dimensions.setdefault(key, {})[row['system']] = row
    def sign(x):
        return 0 if abs(x) < 1e-12 else (1 if x > 0 else -1)
    for key, systems in dimensions.items():
        assert len(systems) == 7
        labels = ('cohort', 'dataset', 'denominator', 'workers', 'order')
        tags = dict(zip(labels, key))
        base_max = max(x['canonical_score'] for x in systems.values())
        alias_max = max(x['score'] for x in systems.values())
        before = sorted(k for k, v in systems.items() if abs(v['canonical_score'] - base_max) < 1e-12)
        after = sorted(k for k, v in systems.items() if abs(v['score'] - alias_max) < 1e-12)
        top_sets.append({**tags, 'canonical_top': before, 'alias_top': after, 'changed': before != after})
        for a, b in itertools.combinations(sorted(systems), 2):
            old = systems[a]['canonical_score'] - systems[b]['canonical_score']
            new = systems[a]['score'] - systems[b]['score']
            comparisons.append({**tags, 'system_a': a, 'system_b': b,
                                'canonical_gap_pp': 100 * old, 'alias_gap_pp': 100 * new,
                                'strict_reversal': sign(old) * sign(new) == -1,
                                'tie_created': sign(old) != 0 and sign(new) == 0,
                                'tie_broken': sign(old) == 0 and sign(new) != 0})
    dump(output / 'SOURCE_AND_COHORT_AUDIT.json', sources)
    dump(output / 'COUNTS_AND_CANONICAL_SCORES.json', count_rows)
    dump(output / 'ACTUAL_API_CHECKS.json', actual_checks)
    (output / 'ALL_SCORE_REPLAYS.jsonl.gz').write_bytes(gzip.compress((''.join(compact(x) + '\n' for x in score_rows)).encode(), mtime=0))
    (output / 'ALL_PAIR_COMPARISONS.jsonl.gz').write_bytes(gzip.compress((''.join(compact(x) + '\n' for x in comparisons)).encode(), mtime=0))
    (output / 'ROW_PARSE_AUDIT.jsonl.gz').write_bytes(gzip.compress((''.join(compact(x) + '\n' for x in row_audits)).encode(), mtime=0))
    dump(output / 'TOP_SET_COMPARISONS.json', top_sets)
    summary = {'source_files': len(sources), 'source_identity_all_verified': True,
               'within_dataset_gold_and_group_alignment': True,
               'new_inference_calls': 0, 'actual_api_invocations_verified': len(actual_checks),
               'exact_score_replay_combinations': len(score_rows),
               'strict_reversal_rows': sum(x['strict_reversal'] for x in comparisons),
               'top_set_change_rows': sum(x['changed'] for x in top_sets),
               'primary_network_rows': sum(x['total_samples'] for x in count_rows if x['cohort'] == 'terminal_network' and x['denominator'] == 'valid_only'),
               'secondary_agent_rows': sum(x['total_samples'] for x in count_rows if x['cohort'] == 'terminal_all_agents' and x['denominator'] == 'valid_only'),
               'cohorts': {}}
    for cohort in ('terminal_network', 'terminal_all_agents'):
        relevant = [x for x in score_rows if x['cohort'] == cohort]
        counts = [x for x in count_rows if x['cohort'] == cohort and x['denominator'] == 'valid_only']
        pairs = [x for x in comparisons if x['cohort'] == cohort]
        summary['cohorts'][cohort] = {'max_absolute_change_pp': max(abs(x['delta_pp']) for x in relevant),
                                     'strict_reversal_rows': sum(x['strict_reversal'] for x in pairs),
                                     'parse_failed': sum(x['parse_failed'] for x in counts),
                                     'empty_output': sum(x['empty_output'] for x in counts),
                                     'invalid_references': sum(x['invalid_references'] for x in counts),
                                     'max_change_example': max(relevant, key=lambda x: abs(x['delta_pp']))}
    dump(output / 'SUMMARY.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
