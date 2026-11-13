"""Prospectively fixed JSON and exact rational answer codec; zero model calls."""
import json
import re
from fractions import Fraction

_DECIMAL = re.compile(r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")


def numeric(value):
    """Exact integers, finite decimals/exponents or ratios; optional $/valid commas.

    No units, answer extraction, rounding tolerance, approximation, or code eval.
    The provider contract requires strings, avoiding JSON floating-point loss.
    """
    if not isinstance(value, str):
        raise ValueError("Numeric answer must be a JSON string")
    text = value.strip().replace("−", "-")
    if text.startswith("$"):
        text = text[1:].strip()
    if len(text) > 128 or any(abs(int(x)) > 100 for x in re.findall(r"[eE]([+-]?\d+)", text)):
        raise ValueError("Numeric representation exceeds frozen finite parsing bounds")
    parts = text.split("/")
    if not 1 <= len(parts) <= 2 or any(not _DECIMAL.fullmatch(x.strip()) for x in parts):
        raise ValueError("Not a supported exact numeric string")
    values = [Fraction(x.strip().replace(",", "")) for x in parts]
    if len(values) == 2:
        if values[1] == 0:
            raise ValueError("Zero denominator")
        return values[0] / values[1]
    return values[0]


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Duplicate JSON key")
        out[key] = value
    return out


def parse_answers(text, expected):
    """Whole final JSON only; one optional outer JSON code fence is accepted."""
    text = text.strip()
    if text.startswith("```"):
        match = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
        if not match:
            raise ValueError("Invalid outer code fence")
        text = match.group(1)
    parsed = json.loads(text, object_pairs_hook=_unique_object,
                        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    if not isinstance(parsed, dict) or set(parsed) != set(expected):
        raise ValueError("Final JSON must contain every exact requested ID once and no extras")
    return parsed


def score_answer(value, gold):
    if isinstance(value, str) and value.strip().upper() == "ABSTAIN":
        return {"label": "abstain", "parsed_answer": None,
                "score_lower": 0, "score_upper": 0, "format_valid": True}
    try:
        answer = numeric(value)
    except (ValueError, ZeroDivisionError, OverflowError):
        return {"label": "unknown", "parsed_answer": None,
                "score_lower": 0, "score_upper": 1, "format_valid": False}
    correct = int(answer == numeric(gold))
    return {"label": "valid" if correct else "wrong", "parsed_answer": str(answer),
            "score_lower": correct, "score_upper": correct, "format_valid": True}
