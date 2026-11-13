"""Post-hoc descriptive contrast. Never part of the frozen primary analysis."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

root = Path(__file__).resolve().parent
rows_path = root / 'analysis/per_source_family.jsonl'
rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
models = ('gemma-4-31b-it', 'deepseek-v4-flash')
result = {
    'analysis_status': 'post_hoc_exploratory_descriptive_only',
    'definition': '(DeepSeek-Gemma mean accuracy gap on P1/P2) minus (same gap on numerical substitution/paraphrase)',
    'chosen_after_primary_results': True,
    'primary_choice_reversal_result': False,
    'per_source_family_sha256': hashlib.sha256(rows_path.read_bytes()).hexdigest(),
    'bounds_scope': 'Sharp under the frozen independent [0,1] correctness boxes for unknown task scores, on this fixed source cohort; not population confidence intervals.',
    'results': {},
}
for role in ('selection', 'confirmation'):
    selected = [r for r in rows if r['analysis_role'] == role]
    lo = hi = Fraction(0)
    for r in selected:
        for variants, resource_sign in ((('p1', 'p2'), 1), (('numeric', 'paraphrase'), -1)):
            for model, model_sign in ((models[1], 1), (models[0], -1)):
                coefficient = Fraction(resource_sign * model_sign, 2 * len(selected))
                for variant in variants:
                    lower, upper = map(Fraction, r['variants'][variant][model])
                    a, b = coefficient * lower, coefficient * upper
                    lo += min(a, b)
                    hi += max(a, b)
    result['results'][role] = {
        'families': len(selected), 'lower_fraction': str(lo), 'upper_fraction': str(hi),
        'lower_pp': float(100 * lo), 'upper_pp': float(100 * hi),
    }
path = root / 'posthoc_gap_distortion.json'
if path.exists():
    raise SystemExit('Refusing to overwrite existing posthoc analysis')
path.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result['results'], indent=2))
