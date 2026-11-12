# Exploratory pre-sprint audit: substituted benchmark references in an AI-generated report

**Prepared:** 2026-11-12. **Status:** Reanalysis of one released run from an existing study. This is a concrete inconsistency in an archived AI-scientist output, not a new assistant experiment or an estimate of error frequency. Declare it as pre-existing work if used in the sprint.

## What was checked

Luo, Kasirzadeh and Shah's [study of autonomous AI scientists](https://pmc.ncbi.nlm.nih.gov/articles/PMC13663820/) released the [AIScientistPitfalls repository](https://github.com/niharshah/AIScientistPitfalls). I checked the first complete Agent Laboratory example in its `BenchmarkIssue` archive (`research_dir_0_lab_1`) against the benchmark reference table in the released SPR task. The source artifacts are:

- [SPR task specification](https://github.com/niharshah/AIScientistPitfalls/blob/main/SPR%20Task/BenchmarkIssue/SPR.md), which lists reference accuracies for 20 synthetic benchmarks;
- the agent's [generated experiment code](https://github.com/niharshah/AIScientistPitfalls/blob/main/AgentLaboratory/generated_research/BenchmarkIssue/research_dir/research_dir_0_lab_1/src/run_experiments.py), which assigns `sota_baseline` four assumed example values;
- the [execution output](https://github.com/niharshah/AIScientistPitfalls/blob/main/AgentLaboratory/generated_research/BenchmarkIssue/research_dir/research_dir_0_lab_1/src/experiment_output.log), which prints four model test accuracies and repeats the substituted values;
- the [generated report](https://github.com/niharshah/AIScientistPitfalls/blob/main/AgentLaboratory/generated_research/BenchmarkIssue/research_dir/research_dir_0_lab_1/report.txt), which presents those values as its SOTA comparison and says its classifier consistently underperforms.

The task's reference figures are **supplied values in a synthetic experimental setup**. This audit does not independently establish that they are genuine external state-of-the-art results. Also, the public archive does not by itself establish the exact prompt or intermediate messages received by this particular run. The directly verified claim is that the released task specification, generated code, log and report disagree.

## Same run, different reference values

All accuracies are percentages. The last two columns calculate the archived test accuracy minus the indicated reference, in percentage points. Positive means above that reference. They are conditional comparisons of released numbers; the classifier was not rerun here.

| Benchmark | Archived test accuracy | Reference in released task | Reference used in code, log and report | Difference vs. task | Difference vs. report |
| --- | ---: | ---: | ---: | ---: | ---: |
| SFRFG | 57.6 | 55.1 | 85.0 | +2.5 | −27.4 |
| IJSJF | 58.5 | 60.8 | 80.0 | −2.3 | −21.5 |
| GURSG | 58.5 | 52.3 | 83.0 | +6.2 | −24.5 |
| TSHUY | 59.4 | 54.7 | 82.0 | +4.7 | −22.6 |

The report's conclusion of underperformance on **four of four** follows from the four substituted baselines. Using the released task's references with the *same logged test accuracies* instead yields **three above, one below**. The code explicitly describes its replacement numbers as *assumed* examples; the report does not qualify its comparison this way. This is a benchmark-reference integrity failure that propagates into the scientific interpretation. It should be kept distinct from a model recommending the wrong benchmark and from the paper's broader population-level findings.

## Reproduce the file-to-file comparison

[`scripts/audit_spr_baselines.py`](../../scripts/audit_spr_baselines.py) reads the four original files and checks that the code, log and report match before comparing them with the task. Download the linked original text files, then run:

```bash
python3 scripts/audit_spr_baselines.py SPR.md run_experiments.py experiment_output.log report.txt
```

The script returns the four rows plus `changed_reference_values = 4`, `positive_differences_with_supplied_references = 3`, and `positive_differences_with_agent_baselines = 0`. It was run on the downloaded original text from the four linked repository files. Source files are linked, not copied into this repository.

## Fit to this project's objective

This example supplies an **observed AI-generated evaluation error** with a checkable consequence: replacing benchmark references changes the reported conclusion. It complements the CivilComments and HANS pilots, which show evaluation-choice consequences but do not contain observed assistant errors. A future controlled experiment could ask independent assistants to choose appropriate evaluations and verify supplied benchmark references, retaining raw outputs and prompt versions. This archived run is an exploratory external case study and must not be counted among newly sampled assistant responses or independent replications of the Luo et al. study.
