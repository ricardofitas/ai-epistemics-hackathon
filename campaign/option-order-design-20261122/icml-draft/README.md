# The Cost of Balance in Order-Sampled Model Comparisons

This ICML working paper studies the variance of a paired accuracy gap when a limited number of answer orders can be evaluated. It treats the one-order-per-option budget across option counts and all position-balanced budgets at four options. The two models receive the same orders on each question. [Read the manuscript](paper.pdf)

## Results

For every number of options $n\ge4$, exact position balance incurs worst-case normalized variance of at least $(n-2)/(n^2-3n+1)$, even for differences of binary correctness. A pair of Latin templates attains the bound at each size from six to ten and at twelve. A necessary and sufficient cycle-histogram criterion gives an exact rational certificate for the twelve-option optimum of 10/109. [Criterion and proof](attainment.tex) An explicit two-square mixture also attains it at twice every prime of at least 131, for all real scores and binary correctness differences. [Infinite-family proof](two-prime-proof.tex) Theorem 1 also gives a sufficient condition for additional balance to increase this risk using counts of swaps between pairs of rows.

Theorem 2 characterizes when the risk equals that of one uniform order. At four and six options, full adjacency keeps the opposite-slot matching fixed within a block. At six this raises the optimum from 4/19 to 1. At eight, nine and ten there are connected designs with risk strictly below one and the certified adjacency lower bounds still exceed their respective position optima.

At five options, the sharp position risk is 9/25. Requiring maximum adjacency coverage raises the correctness optimum into the interval [7/15, 0.47087]. The real-score optimum lies in [0.47084, 0.47087]. The three correctness witnesses giving the new lower bound use only the admissible blocks.

With four calls, the matched 3B evaluations show Williams MSE 0.25% higher on HellaSwag, 3.41% higher on MMLU and 2.32% lower on LogiQA than precedence minimax. In CommonsenseQA the frozen maximum-adjacency sampler had 1.29% lower point MSE than position minimax, with a paired 95% interval from −0.14% to +2.75%. [Matched HellaSwag evidence](https://github.com/ricardofitas/ai-epistemics-hackathon/blob/077d34c223c9d6bad32bfeadbbe9972ac77658e0/evidence/rig-20261123/four-orders-hellaswag-3b/RESULTS.md) · [CommonsenseQA evidence](https://github.com/ricardofitas/ai-epistemics-hackathon/blob/077d34c223c9d6bad32bfeadbbe9972ac77658e0/evidence/rig-20261123/five-orders-commonsenseqa/RESULTS.md)

At four options the paper gives the exact worst-case variance for every balanced budget from four through 24 orders. At eight, the position, precedence and full-adjacency optima are 1/7, 2/11 and 2/5 times single-order variance. Two distinct Williams blocks reduce the original Williams MSE by 60% on every fixed profile. On the same 992 questions per 3B panel, this eight-call design had 7.99% higher point MSE than optimized precedence on HellaSwag, 9.68% higher on MMLU and 1.69% higher on LogiQA. The LogiQA interval spans zero. The package includes the full-order contrast histograms, exact risks, equal-cost baselines and paired intervals. [Eight-call evidence and replay](experiments/eight-calls/README.md)

In a prospective transfer test on ARC-Challenge, OpenBookQA, Cosmos QA and RACE, the eight-call pilot chose precedence in all four cases before the 672 held-out questions were scored. Precedence gave lower held-out MSE in each case. Repeating the pilot-order draws on the fixed calibration questions would pick the lower-risk design with probability 49.6–63.8%. Counting calibration in the full-panel estimate gives 4.50–7.39% higher expected MSE than using precedence throughout at identical call counts. All four simultaneous intervals for the held-out W gain include zero. [Prospective results, registration and public replay](experiments/low-budget-selection/README.md)

The opening figure translates gap MSE into the number of uniformly sampled orders required. A separate registered experiment reorders four labeled demonstrations during text classification on SST-2 and AG News. [Demonstration-order results and replay](experiments/demo-order/README.md)

## Use the samplers

Run the following command to print one six-order block. Each row lists option labels in display order, counted from zero. Use the same block for both models, drawing independently for each new question. The seed makes this example reproducible.

```sh
python3 sample_position.py 6 --seed 17
```

The script implements the sharp position samplers for four through ten options, twelve options, and the proved infinite family (for example, 262 options). The templates and exact mixing probabilities for six through ten are in the certificate package. [Position templates](certificates/position-templates.json)

For four-option questions, draw a block with a specific budget and balance requirement. The precedence sampler balances both position and pairwise precedence. The full sampler also balances directed adjacency. All balanced budgets are multiples of four, including the census at 24.

```sh
python3 four_option_budgets.py 8 precedence --seed 17
```

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

The verifier enumerates every balanced four-option block at four, eight and twelve calls, checks its weighted frame identities and complementary budgets, checks the five-option witnesses and real-score upper bound, and computes all centered eigenvalues of the proposed six- through ten-option and twelve-option samplers. Two implementations use different character formulas. An independent integer calculation checks the ternary frame projectors.

## Build the paper

The sources include both figures and the ICML style files. The following command writes the compiled paper in the current directory.

```sh
tectonic paper.tex
```

The published PDF uses the ICML preprint format. For the anonymous review layout, compile `review.tex` instead. Both builds contain the same scientific text. The figures may be regenerated from the aggregate measurements using Python, ReportLab and Ghostscript with `python3 plot_risk.py`. The manuscript includes an AI disclosure. Human authorship and scientific verification precede conference submission.
