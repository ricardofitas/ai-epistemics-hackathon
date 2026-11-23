# The Cost of Balance in Order-Sampled Model Comparisons

This ICML working paper studies the variance of a paired accuracy gap when each model can see as many orders as there are answer choices. The two models receive the same orders on each question. [Read the manuscript](paper.pdf)

## Results

For every number of options $n\ge4$, exact position balance incurs worst-case normalized variance of at least $(n-2)/(n^2-3n+1)$, even for differences of binary correctness. A pair of Latin templates attains the bound at each size from six to ten. Theorem 1 also gives a sufficient condition for additional balance to increase this risk using counts of swaps between pairs of rows.

Theorem 2 characterizes when the risk equals that of one uniform order. At four and six options, full adjacency keeps the opposite-slot matching fixed within a block. At six this raises the optimum from 4/19 to 1. At eight, nine and ten there are connected designs with risk strictly below one and the certified adjacency lower bounds still exceed their respective position optima.

At five options, the sharp position risk is 9/25. Requiring maximum adjacency coverage raises the correctness optimum into the interval [7/15, 0.47087]. The real-score optimum lies in [0.47084, 0.47087]. The three correctness witnesses giving the new lower bound use only the admissible blocks.

The matched 3B evaluations show Williams MSE 0.25% higher on HellaSwag, 3.41% higher on MMLU and 2.32% lower on LogiQA than precedence minimax. In CommonsenseQA the frozen maximum-adjacency sampler had 1.29% lower point MSE than position minimax, with a paired 95% interval from −0.14% to +2.75%. [Matched HellaSwag evidence](https://github.com/ricardofitas/ai-epistemics-hackathon/blob/077d34c223c9d6bad32bfeadbbe9972ac77658e0/evidence/rig-20261123/four-orders-hellaswag-3b/RESULTS.md) · [CommonsenseQA evidence](https://github.com/ricardofitas/ai-epistemics-hackathon/blob/077d34c223c9d6bad32bfeadbbe9972ac77658e0/evidence/rig-20261123/five-orders-commonsenseqa/RESULTS.md)

## Use the samplers

Run the following command to print one six-order block. Each row lists option labels in display order, counted from zero. Use the same block for both models, drawing independently for each new question. The seed makes this example reproducible.

```sh
python3 sample_position.py 6 --seed 17
```

The script implements the sharp position samplers for four through ten options. The templates and exact mixing probabilities for six through ten are in the certificate package. [Position templates](certificates/position-templates.json)

## Reproduce the proofs

From this directory, run the verifier with Python 3.10 or newer. The second command also checks the three larger adjacency lower bounds against Ian Wanless's published exhaustive row-complete Latin-square catalogue. It retrieves three small files from Monash and verifies their SHA-256 digests. [Catalogue and enumeration counts](https://users.monash.edu.au/~iwanless/data/RCLS/)

```sh
python3 -B verify_all.py --small
python3 -B verify_all.py
```

For an offline replay of the full table, supply local copies of `catalogue.redRCLS8`, `catalogue.redRCLS9` and `catalogue.redRCLS10`.

```sh
python3 -B verify_all.py --catalogue-dir /path/to/catalogue
```

The verifier enumerates the small supports, checks the five-option witnesses and real-score upper bound, and computes all centered eigenvalues of the proposed six- through ten-option samplers. Two implementations use different character formulas. An independent integer calculation checks the ternary frame projectors.

## Build the paper

The sources include both figures and the ICML style files. The following command writes the compiled paper in the current directory.

```sh
tectonic paper.tex
```

The published PDF uses the ICML preprint format. For the anonymous review layout, compile `review.tex` instead. Both builds contain the same scientific text. The figures may be regenerated from the aggregate measurements using Python, ReportLab and Ghostscript with `python3 plot_risk.py`. The manuscript includes an AI disclosure. Human authorship and scientific verification precede conference submission.
