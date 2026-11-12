# Exploratory pre-sprint audit: inconsistent benchmark references in released artifacts

**Prepared:** 2026-11-12. **Status:** Provisional comparison of one released run with a public task specification from an existing study. This is an inconsistency between archived files, not a verified model error against its exact input prompt, a new assistant experiment, or an estimate of error frequency. Declare it as pre-existing work if used in the sprint.

## What was checked

Luo, Kasirzadeh and Shah's [study of autonomous AI scientists](https://pmc.ncbi.nlm.nih.gov/articles/PMC13663820/) released the [AIScientistPitfalls repository](https://github.com/niharshah/AIScientistPitfalls). I checked the first complete Agent Laboratory example in its `BenchmarkIssue` archive (`research_dir_0_lab_1`) against the benchmark reference table in the released SPR task. The source artifacts are:

- [SPR task specification](https://github.com/niharshah/AIScientistPitfalls/blob/main/SPR%20Task/BenchmarkIssue/SPR.md), which lists reference accuracies for 20 synthetic benchmarks;
- the agent's [generated experiment code](https://github.com/niharshah/AIScientistPitfalls/blob/main/AgentLaboratory/generated_research/BenchmarkIssue/research_dir/research_dir_0_lab_1/src/run_experiments.py), which assigns `sota_baseline` four assumed example values;
- the [execution output](https://github.com/niharshah/AIScientistPitfalls/blob/main/AgentLaboratory/generated_research/BenchmarkIssue/research_dir/research_dir_0_lab_1/src/experiment_output.log), which prints four model test accuracies and repeats the substituted values;
- the [generated report](https://github.com/niharshah/AIScientistPitfalls/blob/main/AgentLaboratory/generated_research/BenchmarkIssue/research_dir/research_dir_0_lab_1/report.txt), which presents those values as its SOTA comparison and says its classifier consistently underperforms.

The task's reference figures are **supplied values in a synthetic experimental setup**. This audit does not independently establish that they are genuine external state-of-the-art results. The exact prompt and benchmark-name-to-reference mapping received by this particular run have **not** been reconstructed. The related [auditor source](https://github.com/niharshah/AIScientistPitfalls/blob/main/pitfall_detection/pitfall_detection.py) explicitly permutes rows and identifiers for a separate detection procedure; it cannot be used as a trace of this run. The directly verified observation is that the released task specification (range 52.3–72.6%), generated code (four assumed baselines of 80–85%), log and report disagree. Whether this is a failure relative to what the agent actually saw is unresolved.

## Same run, different reference values

All accuracies are percentages. The last two columns calculate the archived test accuracy minus the indicated reference, in percentage points. Positive means above that reference. **The comparison with the task is conditional on the released task table being the table used for this run, with the same name-to-score mapping.** The classifier was not rerun here.

| Benchmark | Archived test accuracy | Reference in released task | Reference used in code, log and report | Difference vs. task | Difference vs. report |
| --- | ---: | ---: | ---: | ---: | ---: |
| SFRFG | 57.6 | 55.1 | 85.0 | +2.5 | −27.4 |
| IJSJF | 58.5 | 60.8 | 80.0 | −2.3 | −21.5 |
| GURSG | 58.5 | 52.3 | 83.0 | +6.2 | −24.5 |
| TSHUY | 59.4 | 54.7 | 82.0 | +4.7 | −22.6 |

The report's conclusion of underperformance on **four of four** follows from the four baselines hardcoded in this released code. Using the released task's name-to-score mapping with the *same logged test accuracies* instead yields **three above, one below**. The code explicitly describes its numbers as *assumed* examples; the report does not qualify its comparison this way. This is a **candidate benchmark-reference integrity issue**, with an apparent change in scientific interpretation under the stated matching assumption. It should be kept distinct from a verified wrong benchmark recommendation and from the paper's broader population-level findings.

## Reproduce the file-to-file comparison

[`scripts/audit_spr_baselines.py`](../../scripts/audit_spr_baselines.py) reads the four original files and checks that the code, log and report match before comparing them with the task. Download the linked original text files, then run:

```bash
python3 scripts/audit_spr_baselines.py SPR.md run_experiments.py experiment_output.log report.txt
```

The script returns the four rows plus `changed_reference_values = 4`, `positive_differences_with_supplied_references = 3`, and `positive_differences_with_agent_baselines = 0`. It was run on the downloaded original text from the four linked repository files. Source files are linked, not copied into this repository.

## Fit to this project's objective

This example supplies an **AI-generated evaluation report** with a checkable cross-file discrepancy and a conditional conclusion change. It is not yet a confirmed error relative to the agent's actual instructions. Before using it as a scored failure, locate the original run prompt, benchmark order and name-to-score mapping, or reproduce the scenario in a controlled fresh run with complete traces. A future experiment could ask independent assistants to choose appropriate evaluations and verify supplied benchmark references, retaining raw outputs and prompt versions. This archived case must not be counted among newly sampled assistant responses or independent replications of the Luo et al. study.
