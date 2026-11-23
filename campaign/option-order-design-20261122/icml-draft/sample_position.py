"""Draw a certified position-minimax block of displayed option sequences."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
from random import Random


CERTIFICATES = Path(__file__).resolve().parent / "certificates"


def sample_position(n, rng):
    """Pass a fresh draw to both models on one question. Slots and labels are zero-based."""
    if n == 4:
        rows = [[(s+i) % n for s in range(n)] for i in range(n)]
    elif n == 5:
        pins = json.loads((CERTIFICATES/"position-certificate.json").read_text())
        rows = [list(map(int,row)) for row in pins["base_block"]]
    elif 6 <= n <= 10:
        templates = json.loads((CERTIFICATES/"position-templates.json").read_text())[str(n)]
        first_weight = Fraction(templates[0]["weight"])
        choose_first = rng.randrange(first_weight.denominator) < first_weight.numerator
        rows = templates[0 if choose_first else 1]["rows"]
    else:
        raise ValueError("The certified samplers cover four through ten options.")
    labels = rng.sample(range(n),n)
    slots = rng.sample(range(n),n)
    return [[labels[r[s]] for s in slots] for r in rows]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("options",type=int,choices=range(4,11))
    parser.add_argument("--seed",type=int)
    args = parser.parse_args()
    print(json.dumps(sample_position(args.options,Random(args.seed))))
