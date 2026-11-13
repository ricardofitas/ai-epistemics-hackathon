"""Controlled alias/hardware/order checks and upstream score-agent invocation."""
import asyncio
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
import types

from reproduce_alias import ROOT, load_components


def scorer_result(runner_class, bench, name, workers, args):
    return runner_class(max_workers=workers).run_bench(bench, [{'name': name, 'priority': 'primary', 'args': args}])['metrics'][name]


def main():
    BenchInfo, OriginalRunner = load_components()
    spec = importlib.util.spec_from_file_location('one_eval.metrics.runner_fixed', ROOT / 'patched/runner.py')
    fixed = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = fixed
    spec.loader.exec_module(fixed)
    FixedRunner = fixed.MetricRunner
    args = {'parser': {'type': 'choice_letter', 'choices': 'A-D'}, 'denominator': 'valid_only'}
    boundary, order, invariance = [], [], []
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        for n in (99, 100, 101, 128, 257):
            correct = (n + 1) // 2
            values = ['A'] * correct + ['B'] + [''] * (n - correct - 1)
            path = folder / f'{n}.jsonl'
            def write(data):
                path.write_text(''.join(json.dumps({'id': i, 'prediction': p, 'answer': 'A'}) + '\n'
                                        for i, p in enumerate(data)))
            write(values)
            bench = BenchInfo(bench_name='alias_boundary', meta={'artifact_paths': {'records': str(path)}})
            canonical = scorer_result(OriginalRunner, bench, 'choice_accuracy', 2, args)['score']
            for workers in (1, 2, 4, 8):
                alias = scorer_result(OriginalRunner, bench, 'accuracy', workers, args)['score']
                boundary.append({'n': n, 'workers': workers, 'canonical': canonical, 'alias': alias})
                for name in ('choice_accuracy', 'accuracy', 'acc'):
                    repaired = scorer_result(FixedRunner, bench, name, workers, args)
                    assert abs(repaired['score'] - canonical) < 1e-12
                    assert repaired['scored_samples'] == correct + 1
                    invariance.append({'n': n, 'workers': workers, 'name': name, 'score': repaired['score']})
            # Default-total denominator is an unaffected control even with abstentions.
            total_args = {**args, 'denominator': 'total'}
            total = scorer_result(OriginalRunner, bench, 'choice_accuracy', 2, total_args)['score']
            assert abs(total - correct / n) < 1e-12
            assert abs(scorer_result(OriginalRunner, bench, 'accuracy', 2, total_args)['score'] - total) < 1e-12
            if n == 101:
                for seed in range(20):
                    shuffled = list(values)
                    random.Random(seed).shuffle(shuffled)
                    write(shuffled)
                    before = scorer_result(OriginalRunner, bench, 'accuracy', 2, args)['score']
                    after = scorer_result(FixedRunner, bench, 'accuracy', 2, args)['score']
                    assert abs(after - canonical) < 1e-12
                    order.append({'permutation_seed': seed, 'original_alias_score': before, 'fixed': after})
                write(values)
                # The dedicated contract scorer is an explicitly unaffected control.
                for name in ('choice_accuracy', 'accuracy', 'acc'):
                    primary = OriginalRunner(max_workers=2).run_bench_with_contract(bench, {'primary_metric': name, **args})
                    assert abs(primary['primary_metric_result']['score'] - canonical) < 1e-12
        # Invoke the unmodified public workflow agent's run method. Its graph/LLM
        # base is not used by this scoring phase, so an inert base suffices.
        base = types.ModuleType('one_eval.core.agent'); base.CustomAgent = object
        sys.modules[base.__name__] = base
        sys.modules['one_eval.core.state'].NodeState = types.SimpleNamespace
        from one_eval.agents.score_calc_agent import ScoreCalcAgent
        import one_eval.agents.score_calc_agent as score_agent_module
        import one_eval.metrics.runner as native_runner
        native_runner.cpu_count = lambda: 3  # Explicit three-CPU host, two workers.
        fixed.cpu_count = lambda: 3
        pipeline = []
        for system, values in {'A': ['A']*51+['B']+['']*49, 'B': ['A']*76+['B']*25}.items():
            for name in ('choice_accuracy', 'accuracy'):
                path = folder / f'agent_{system}_{name}.jsonl'
                path.write_text(''.join(json.dumps({'id': i, 'prediction': p, 'answer': 'A'})+'\n' for i,p in enumerate(values)))
                bench = BenchInfo(bench_name=system, meta={'eval_detail_path': str(path), 'pred_key': 'prediction', 'ref_key': 'answer'})
                state = types.SimpleNamespace(benches=[bench], metric_plan={system:[{'name':name,'priority':'primary','args':args}]},
                                              eval_results={}, result={}, request={'language':'en'})
                for version, runner in [('original', OriginalRunner), ('fixed', FixedRunner)]:
                    score_agent_module.MetricRunner = runner
                    asyncio.run(ScoreCalcAgent().run(state))
                    metric = state.eval_results[system]['metrics'][name]
                    if version == 'fixed':
                        expected = 51/52 if system == 'A' else 76/101
                        assert abs(metric['score'] - expected) < 1e-12
                    pipeline.append({'system': system, 'version': version, 'metric_name': name, 'score': metric['score'],
                                     'step3_file_written': Path(bench.meta['eval_step3_path']).exists(),
                                     'computed': state.result['ScoreCalcAgent']['computed'],
                                     'failed': state.result['ScoreCalcAgent']['failed']})
    report = {'source_commit':'8aba20ad17ee2c7d2391162ac03ffaebcbb17506',
              'controlled_data_only':True, 'source_functions_and_agent_run_unmodified':True,
              'orchestration_scaffold':'Original BenchInfo dataclass; inert graph base and stdlib logger; three-CPU host for public score-agent check.',
              'boundary_and_workers':boundary, 'permutation_checks':order, 'patch_invariance_checks':len(invariance),
              'default_total_denominator_control':'unaffected', 'dedicated_contract_scoring_control':'unaffected',
              'public_score_agent_results':pipeline,
              'scope':'Affected run_bench and ScoreCalcAgent pathway with supported selective denominator. Dedicated run_bench_with_contract path remains invariant in these controls.',
              'deployment_or_real_model_rank_reversal_claim':False}
    (ROOT/'alias_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'patch_invariance_checks':len(invariance),'order_checks':len(order),'score_agent':pipeline,
                      'original_alias_permutation_range':[min(r['original_alias_score'] for r in order),max(r['original_alias_score'] for r in order)]}))


if __name__ == '__main__':
    main()
