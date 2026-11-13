"""Post-analysis direct API confirmation of the largest effect and close reversal."""
import gzip
import json
from pathlib import Path
import sys
import tempfile

import analyze_real_outputs as analysis

def main():
    BenchInfo, Runner = analysis.load_components()
    observations = []
    cases = [('MMLUPRO', 'TAM', 'terminal_network', 6),
             ('MMLUPRO', 'TAM', 'terminal_network', None),
             ('MMLU', 'TAM', 'terminal_all_agents', None),
             ('MMLU', 'XG-Guard', 'terminal_all_agents', None)]
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / 'rows.jsonl'
        for dataset, system, cohort, seed in cases:
            source = analysis.CAPTURE / (dataset + '__' + system + '.json.gz')
            records, _ = analysis.terminal_rows(json.loads(gzip.decompress(source.read_bytes())))
            if cohort == 'terminal_all_agents':
                records = [{'id': row['id'] + [agent], 'prediction': value, 'answer': row['answer']}
                           for row in records for agent, value in enumerate(row['agent_final_answers'])]
            order = analysis.order_indices(records, dataset, seed)
            path.write_text(''.join(analysis.compact(records[index]) + '\n' for index in order))
            bench = BenchInfo(bench_name=dataset + '__' + system,
                             meta={'artifact_paths': {'records': str(path)}, 'pred_key': 'prediction', 'ref_key': 'answer'})
            args = {'parser': {'type': 'choice_letter', 'choices': 'A-J' if dataset == 'MMLUPRO' else 'A-D'},
                    'denominator': 'valid_only'}
            values = {}
            for name in ('choice_accuracy', 'accuracy', 'acc'):
                result = Runner(max_workers=8).run_bench(bench, [{'name': name, 'args': args}])['metrics'][name]
                values[name] = result['score']
            assert abs(values['accuracy'] - values['acc']) < 1e-12
            observations.append({'dataset': dataset, 'system': system, 'cohort': cohort,
                                 'order': 'source' if seed is None else 'sha256_seed_' + str(seed),
                                 'workers': 8, 'scores': values})
    output = analysis.ROOT / 'results' / 'POST_ANALYSIS_DIRECT_CONFIRMATION.json'
    output.write_text(json.dumps({'selection': 'Post-analysis verification of observed extrema; not a new replication cohort.',
                                 'observations': observations}, indent=2) + '\n')
    print(json.dumps(observations, indent=2))

if __name__ == '__main__':
    main()
