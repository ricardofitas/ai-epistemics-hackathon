"""Draw a certified position-minimax block of displayed option sequences."""

import argparse
from fractions import Fraction
import json
from math import isqrt
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
    elif 6 <= n <= 10 or n == 12:
        templates = json.loads((CERTIFICATES/"position-templates.json").read_text())[str(n)]
        first_weight = Fraction(templates[0]["weight"])
        choose_first = rng.randrange(first_weight.denominator) < first_weight.numerator
        rows = templates[0 if choose_first else 1]["rows"]
    elif n % 2 == 0 and n // 2 >= 131 and all(n // 2 % k for k in range(2, isqrt(n // 2) + 1)):
        p = n // 2
        weight = Fraction((n-3)*(n-1), n*n-3*n+1)
        shifts = rng.randrange(weight.denominator) < weight.numerator
        if shifts:
            rows = [[(slot+i) % n for slot in range(n)] for i in range(n)]
        else:
            rows = [[2*((x+(-1)**c*i+b*c) % p)+(c^b)
                     for x in range(p) for c in (0,1)] for b in (0,1) for i in range(p)]
    else:
        raise ValueError("Use 4 through 10, 12, or twice a prime of at least 131.")
    labels = rng.sample(range(n),n)
    slots = rng.sample(range(n),n)
    return [[labels[r[s]] for s in slots] for r in rows]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("options",type=int)
    parser.add_argument("--seed",type=int)
    args = parser.parse_args()
    print(json.dumps(sample_position(args.options,Random(args.seed))))
