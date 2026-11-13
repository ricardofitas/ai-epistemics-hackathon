"""Offline witness through unmodified One-Eval metric entry points."""
import ast
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import sys
import tempfile
import types
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent


def load_components():
    # Graph/LLM orchestration is not exercised. Load the original BenchInfo
    # dataclass AST unchanged, with a standard-library logger for this local test.
    logger = types.ModuleType('one_eval.logger')
    logger.get_logger = logging.getLogger
    sys.modules['one_eval.logger'] = logger
    tree = ast.parse((ROOT / 'one_eval/core/state.py').read_text())
    bench_ast = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'BenchInfo')
    state = types.ModuleType('one_eval.core.state')
    state.__dict__.update({'dataclass': dataclass, 'field': field,
                           'Any': Any, 'Dict': Dict, 'List': List, 'Optional': Optional})
    sys.modules[state.__name__] = state
    exec(compile(ast.Module(body=[bench_ast], type_ignores=[]), 'original_BenchInfo', 'exec'), state.__dict__)
    import one_eval.metrics.common.general
    from one_eval.core.metric_registry import get_metric_fn
    from one_eval.metrics.runner import MetricRunner
    assert get_metric_fn('choice_accuracy') is get_metric_fn('accuracy') is get_metric_fn('acc')
    return state.BenchInfo, MetricRunner


def main():
    BenchInfo, MetricRunner = load_components()
    predictions = {'A': ['A'] * 51 + ['B'] + [''] * 49,
                   'B': ['A'] * 76 + ['B'] * 25}
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        for system, values in predictions.items():
            path = Path(temporary) / (system + '.jsonl')
            path.write_text(''.join(json.dumps({'id': i, 'prediction': p, 'answer': 'A'}) + '\n'
                                    for i, p in enumerate(values)))
            bench = BenchInfo(bench_name='synthetic_supported_contract', meta={
                'artifact_paths': {'records': str(path)}, 'pred_key': 'prediction', 'ref_key': 'answer'})
            for workers in (1, 2, 4):
                for name in ('choice_accuracy', 'accuracy', 'acc'):
                    config = {'name': name, 'priority': 'primary',
                              'args': {'parser': {'type': 'choice_letter', 'choices': 'A-D'},
                                       'denominator': 'valid_only'}}
                    result = MetricRunner(max_workers=workers).run_bench(bench, [config])
                    metric = result['metrics'][name]
                    rows.append({'system': system, 'workers': workers, 'metric_name': name,
                                 'score': metric['score'], 'details_length': len(metric.get('details', [])),
                                 'returned_metadata': sorted(metric)})
    output = {'source_commit': '8aba20ad17ee2c7d2391162ac03ffaebcbb17506',
              'scope': 'Unmodified metric registry/parser/general scorer/MetricRunner. Original BenchInfo AST and stdlib logger replace unneeded graph dependency imports.',
              'same_registered_function_for_all_three_names': True, 'data': {
                  'A': {'correct': 51, 'wrong': 1, 'abstain': 49},
                  'B': {'correct': 76, 'wrong': 25, 'abstain': 0}}, 'results': rows}
    (ROOT / 'alias_witness.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
