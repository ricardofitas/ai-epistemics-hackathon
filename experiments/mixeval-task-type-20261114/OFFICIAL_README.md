---
license: apache-2.0
task_categories:
- text2text-generation
- text-generation
- text-retrieval
- question-answering
language:
- en
pretty_name: MixEval
size_categories:
- 1K<n<10K
tags:
- benchmark
- llm-evaluation
- large-language-models
- large-language-model
- dynamic-benchmark
- benchmark-mixture
- large-multimodality-models
- large-multimodal-models
- llm-training
- foundation-models
- benchmarking-suite
- machine-learning
- deep-learning
configs:
- config_name: MixEval
  data_files:
  - split: free_form
    path: "data/mixeval-jsonl/mixeval/free-form.jsonl"
  - split: multiple_choice
    path: "data/mixeval-jsonl/mixeval/multiple-choice.jsonl"
- config_name: MixEval_Hard
  data_files:
  - split: free_form
    path: "data/mixeval-jsonl/mixeval-hard/free-form.jsonl"
  - split: multiple_choice
    path: "data/mixeval-jsonl/mixeval-hard/multiple-choice.jsonl"
---

<p align="center" width="100%">
<img src="resources/imgs/header.png"  width="100%" height="100%">
</p>
<p align="center"><a href="https://mixeval.github.io/">🏠 Homepage</a> | <a href="https://github.com/Psycoy/MixEval/">👨‍💻 Github</a> | <a href="https://mixeval.github.io/#leaderboard">🏆 Leaderboard</a> | <a href="https://arxiv.org/abs/2406.06565">📜 arXiv</a> | <a href="https://beneficial-chips-08e.notion.site/Don-t-Build-Random-Evals-Principles-for-General-Purpose-Model-Evaluation-bd5a85ba10f447bc9ac560050f67270b">📝 blog</a> | <a href="https://huggingface.co/papers/2406.06565">🤗 HF Paper</a> | <a href="https://x.com/NiJinjie/status/1798182749049852411">𝕏 Twitter</a></p>
</p>

---

<p align="center" width="60%">
<img src="resources/imgs/arena_cost.jpg" width="60%">
</p>

*Benchmark correlations (%) with Chatbot Arena Elo, against the total costs of evaluating a single GPT-3.5-Turbo-0125 model. MixEval and MixEval-Hard show the highest correlations with Arena Elo and Arena Elo (En) among leading benchmarks. We reference the crowdsourcing price for Amazon Mechanical Turk ($0.05 per vote) when estimating the cost of evaluating a single model on Chatbot Arena (approximately $2,936). Chatbot Arena is prohibitively expensive, while MixEval and MixEval-Hard are cheap and cost-effective alternatives. For more details, please refer to our paper.*

<br>


# Attention❗

**This dataset repository is mainly for users wishing to load `MixEval` and `MixEval-Hard` manually with their custom evaluation code.**

**We recommend you to directly use the default [Click-and-Go Evaluation Suite](https://github.com/Psycoy/MixEval) to evaluate models on `MixEval` and `MixEval-Hard`, it's easier and fairer!**

> Refer to [here](https://github.com/Psycoy/MixEval/#quick-start) for a quick start of the evaluation suite. You can smoothly register new models (either proprietary or open-source) in a few steps.

> If you choose to use your custom evaluation code, please refer to the formats and protocols specified [here](https://github.com/Psycoy/MixEval/blob/main/docs/how_to_use_your_own_eval_code.md).

<br>

# Updates

[2024-09-27] MixEval is accepted to Neurips 2024. 

[2024-06-01] ⌛Current dynamic benchmark version: `2024-06-01`. See [here](https://github.com/Psycoy/MixEval) for the latest version.

<br>

# Overview
We introduce MixEval, a ground-truth-based dynamic benchmark derived from off-the-shelf benchmark mixtures, which evaluates LLMs with a highly capable model ranking (i.e., 0.96 correlation with Chatbot Arena) while running locally and quickly (6% the time and cost of running MMLU), with its queries being stably and effortlessly updated every month to avoid contamination.

The MixEval consists of two benchmarks: `MixEval` and `MixEval-Hard`, both updated with our fast, stable pipeline periodically. Both of them contain two splits, i.e., free-form and multiple-choice. Below presents the their relationships:

```
 MixEval (dynamic)
    │
    ├── MixEval
    │   ├──free-form.jsonl
    │   └──multiple-choice.jsonl
    │
    └── MixEval-Hard
        ├──free-form.jsonl
        └──multiple-choice.jsonl
```

Below presents the key statistics of `MixEval` and `MixEval-Hard`. With dynamic benchmarking, the numbers may vary slightly while the number of queries will not change.
<p align="center" width="100%">
<img src="resources/imgs/mixeval_keystats.png" width="80%">
</p>
<!-- 
| Entry        | # Queries | Avg. # Toks per Query | Avg. # Inputs | Avg. # Toks per Input | Min # Toks per Input | Max # Toks per Input | English Ratio | Eval Type |
|:-------------|:---------:|:-------------:|:-------------:|:--------------:|:-------------:|:--------------:|:-------------:|:--------:|
| MixEval      | 4000      | 23            | 0.3           | 41.3           | 6             | 954            | 95.15%        | Ground    |
| MixEval-Hard | 1000      | 27.3          | 0.4           | 47.3           | 7             | 954            | 95.22%        | Truth     | -->


> For more evaluation details, please refer to the [Github](https://github.com/Psycoy/MixEval/) repository.

> See our [paper](https://arxiv.org/abs/2406.06565) and [homepage](https://mixeval.github.io/) for more technical details!

<br>

# Load Dataset

To load `MixEval` benchmark, simply run:
```
from datasets import load_dataset 
# datasets>=2.18.0

dataset = load_dataset("MixEval/MixEval", 'MixEval')
```

To load `MixEval-Hard` benchmark, simply run:
```
from datasets import load_dataset 
# datasets>=2.18.0

dataset = load_dataset("MixEval/MixEval", 'MixEval_Hard')
```

<br>

# What is MixEval?

**MixEval** is an approach that bridges the gap between real-world user queries and efficient, reproducible evaluation by leveraging user queries mined from the web and matching them with similar queries from existing benchmarks. **MixEval** is also the proposed benchmark built with this approach.

**MixEval-Hard** is the hard version of MixEval, designed to enhance the benchmark's ability to distinguish strong models. It is sampled from MixEval based on model evaluation results, with a higher probability of selecting harder queries. To address distribution deviation, we introduce a rejective sampling process to ensure that the distribution of MixEval-Hard aligns with that of wild queries.

**Dynamic evaluation** is introduced to mitigate the contamination issue. We periodically update the data points in MixEval and MixEval-Hard using our fast, stable pipeline, which performs benchmark mixture with a different batch of wild queries from the same distribution, showing low variance (0.36 Std. on a 0-100 scale) and significant version difference (85% unique query ratio).

<br>

# Why to Use MixEval Benchmarks?
MixEval offers five significant advantages for practitioners: 
- **Accurate** model ranking, demonstrated by a 0.96 correlation with Chatbot Arena1.
- **Fast**, **cheap** and **reproducible** execution, requiring only 6% the time and cost of MMLU and with no dependence on human input.
- **Dynamic** benchmarking enabled by low-effort and stable updating mechanism.
- A **comprehensive** and **less biased** query distribution, as it bases queries on a large-scale web corpus.
- A **fair** grading process, ensured by the ground-truth-based grading mechanism.

<br>

# How Effective is MixEval as a Benchmark Mixture Approach?
MixEval is effective as
- MixEval and MixEval-Hard achieve the highest correlation with Arena Elo and Arena Elo (En) among all benchmarks.
- MixEval improves the correlation with Arena Elo and Arena Elo (En) across all its main benchmark splits.
- MixEval outperforms both benchmark-level and uniform mixtures. 
- MixEval effectively maps real-world user queries to ground-truth-based benchmarks.

<br>

# 📑 Citation

If you found this repository useful, please consider 📑**citing**:

```
@article{ni2024mixeval,
  title={MixEval: Deriving Wisdom of the Crowd from LLM Benchmark Mixtures},
  author={Ni, Jinjie and Xue, Fuzhao and Yue, Xiang and Deng, Yuntian and Shah, Mahir and Jain, Kabir and Neubig, Graham and You, Yang},
  journal={arXiv preprint arXiv:2406.06565},
  year={2024}
}
```