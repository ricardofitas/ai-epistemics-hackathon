"""Exact finite-cohort gap distortion bounds; no sources, model calls, or repair.

D = (model_b - model_a gap on comparison variants) minus the same gap on
 target variants. Variant weights are normalized within each package. Shared
candidate/variant outcomes have their coefficients combined before bounding,
so an unknown used by both packages is never treated as independent copies.
This helper deliberately does not decide the cohort, variants, or primary gate.
"""
from fractions import Fraction


def rational(value):
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError('Use exact integer, rational string or Fraction')
    return Fraction(value)


def _weights(values):
    if not isinstance(values, dict) or not values:
        raise ValueError('A nonempty variant-weight mapping is required')
    out = {}
    for variant, weight in values.items():
        if not isinstance(variant, str) or not variant:
            raise ValueError('Variant names must be nonempty strings')
        weight = rational(weight)
        if weight <= 0:
            raise ValueError('Every included variant weight must be positive')
        out[variant] = weight
    if sum(out.values()) != 1:
        raise ValueError('Each evaluation package must have total weight one')
    return out


def signed_coefficients(model_a, model_b, comparison_weights, target_weights):
    if not isinstance(model_a, str) or not isinstance(model_b, str) or not model_a or not model_b or model_a == model_b:
        raise ValueError('Two distinct fixed model labels are required')
    comparison, target = map(_weights, (comparison_weights, target_weights))
    coefficients = {}
    for weights, resource_sign in ((comparison, 1), (target, -1)):
        for model, model_sign in ((model_b, 1), (model_a, -1)):
            for variant, weight in weights.items():
                key = model, variant
                coefficients[key] = coefficients.get(key, Fraction(0)) + resource_sign * model_sign * weight
    return {key: c for key, c in coefficients.items() if c}


def family_gap_bounds(predictions, *, model_a, model_b, comparison_weights, target_weights):
    """Sharp bounds under the supplied distinct candidate/variant outcome boxes.

    predictions maps (model, variant) to exact (lower, upper) correctness values.
    Missing keys raise rather than silently create or impute observations.
    """
    coefficients = signed_coefficients(model_a, model_b, comparison_weights, target_weights)
    lower = upper = Fraction(0)
    for key, coefficient in coefficients.items():
        if key not in predictions:
            raise ValueError('Required candidate/variant prediction is absent: ' + repr(key))
        endpoints = predictions[key]
        if not isinstance(endpoints, (tuple, list)) or len(endpoints) != 2:
            raise ValueError('Prediction bounds require two exact endpoints')
        lo, hi = map(rational, endpoints)
        if not 0 <= lo <= hi <= 1:
            raise ValueError('Prediction correctness bounds must lie in [0,1]')
        a, b = coefficient * lo, coefficient * hi
        lower += min(a, b)
        upper += max(a, b)
    return lower, upper


def mean_family_bounds(bounds):
    rows = list(bounds)
    if not rows:
        raise ValueError('Cannot average an empty cohort')
    normalized = []
    for row in rows:
        if not isinstance(row, (tuple, list)) or len(row) != 2:
            raise ValueError('Family bounds require two endpoints')
        lo, hi = map(rational, row)
        if not -2 <= lo <= hi <= 2:
            raise ValueError('Gap distortion family bounds must lie in [-2,2]')
        normalized.append((lo, hi))
    return tuple(sum(row[k] for row in normalized) / len(normalized) for k in (0, 1))
