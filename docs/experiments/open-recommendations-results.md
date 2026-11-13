# Open-ended recommendation study: six sourced research scenarios

> Follow-up note: the later [two-model/prompt-form comparison](model-prompt-factorial-results.md) found two wrong temporal-fit recommendations in one scenario. The zero-failure counts below describe this initial cohort only; its original labels and conclusions were not changed.

**Date:** 2026-11-12. **Status:** Prospectively frozen exploratory pre-sprint experiment, using one inherited agent configuration. Two blinded agent reviewers independently assigned `no` to all 24 primary unsupported-recommendation labels, with no uncertain/unscorable answers or disagreements. A separate bounded source audit identified no confirmed factual contradictions in the claims it checked.

## Research question and design

Do research assistants recommend evaluations supporting a stated scientific claim when the researcher supplies an ordinary request, without candidate benchmark descriptions, answer keys, metric definitions, or defective scoring code? This extends the earlier guided CivilComments and MC2 pilots.

Three curators prepared the case-specific evidence and generic protocol without seeing new subject responses. An independent pre-run review requested a harmonized primary criterion: factual errors are separate unless they materially support an unsupported sufficiency recommendation; qualified uncertainty and verified alternatives remain acceptable. The coordinator applied that clarification before sampling and directly checked primary sources for the six cases.

| Case | Research goal | Critical distinction |
| --- | --- | --- |
| Python functions | Functional correctness under equal sampling resources | Executable/semantic correctness and comparable sampling |
| Maintainer productivity | Reduced human time to acceptable repository fixes | Human workflow time versus autonomous patch success |
| Physics reviews | Fewer invented references and better claim support | Reference existence, evidential support and target domain |
| Translation | English-to-German online news from late 2019 | Appropriate source period, direction and comparable scoring |
| Worked mathematics | More logically correct written solutions | Derivation correctness versus final-answer scoring |
| Corrupted images | Improvement for every tested corruption type | Per-condition improvement versus an aggregate score |

The six source-backed scenarios span five domain clusters; the two software scenarios have distinct source publications/outcomes but share a domain. Source notes, critical requirements and acceptable qualified alternatives were withheld from subjects. Curated examples do not exhaust valid evaluations.

Each case received two repetitions in each of two conditions: baseline organization guidance and an explicit claim/task/data/metric/inference check, giving 24 requested responses. Both additions contain 34 whitespace-delimited words; focus, semantics and token counts can still differ. Both conditions request evaluation, supported claim/decision, limitations/sufficiency and confidence, plus primary source names if known. Answers use existing knowledge only, with no external retrieval. This is more open than the supplied-evidence pilots, but still asks explicitly for limitations and is not a fully unconstrained workflow.

## Provenance and capture

The casepack, complete manifest, wrapper, rubric and pre-run review were committed before sampling at `9ea15d7d7350bc6a7a26dee5942b261b47c99d31` (21:38:47 UTC). Subjects used `collaboration.spawn_agent`, `fork_turns="none"`, with no model/reasoning overrides. The inherited configuration is session-reported `gpt-6.1-sol`; exact provider snapshot and sampling controls were not surfaced. Platform system/developer instructions remain applicable.

Each opaque launcher permits only reading its prompt file and writing/hashing its own raw answer, prohibiting other files, browsing and delegation. This is instruction-based agent file delivery, not stateless API or filesystem sandbox enforcement. Raw answer bytes were written by subjects and checked against their final SHA256 acknowledgments, avoiding coordinator transcription. All 24 prompts match the frozen hashes; all 24 final artifacts postdate the freeze, are distinct, and meet the 300-word limit. Artifact write times are not provider timestamps.

Two fresh agents independently rated an anonymized case/answer packet using the frozen rubric and sources; condition, repeat, model and trial sequence were concealed. A separate fresh agent checked substantive benchmark/source claims against primary documentation. Reviewers share the subjects' model family; human review is pending. Original ratings and factual-verification coverage are retained, including unresolved implementation details rather than declaring unverified claims false.

## Results

| Case | Baseline unsupported | Structured unsupported |
| --- | ---: | ---: |
| Python functions | 0/2 | 0/2 |
| Maintainer productivity | 0/2 | 0/2 |
| Physics citations | 0/2 | 0/2 |
| Late-2019 news translation | 0/2 | 0/2 |
| Mathematical process correctness | 0/2 | 0/2 |
| Each tested image corruption | 0/2 | 0/2 |
| Total | 0/12 | 0/12 |

Both reviewers rated all 24 recommendations aligned. Their primary-source checks covered all six cases. The separate factual auditor grouped 19 substantive claims and retained 81 exact response passages across all 24 answers. It found no direct contradiction, while preserving unresolved implementation/provenance details: an unspecified PRM800K distribution comparison, the meaning of hidden tests, and an unexecuted exact SacreBLEU dataset alias. These were not converted into confirmed errors.

The answers proposed direct human workflow measurements for maintainer time, assessment of generated mathematical reasoning rather than answer-only scores, physics-domain bibliographic and support checks, and per-corruption comparisons for an each-type claim. All four translation answers qualified their recollection of the exact source-news dates and asked for verification; the official WMT20 task page confirms the proposed late-2019 match. These are successful claim-to-evaluation judgments under this study's protocol.

## Scope and research implication

One inherited model configuration and six selected scenarios cannot estimate how frequently research assistants give wrong advice across research. Repetitions are not independent source cases. Closed retrieval, explicit requests for limitations, selected cases and same-family reviewers constrain generalization. No inference about human adoption or downstream harm follows from the answers.

The initial failure hypothesis was not observed in these six cases. With no detected primary failures in either condition, this experiment supplies no evidence that the added checklist improves advice. It should not be framed as proof that assistants generally choose suitable benchmarks.

The earlier guided pilots contained another 24 responses without identified primary failures; those are separate designs and must not be pooled into a general 48-trial failure-rate estimate. They provide a cumulative workflow record, not 48 independent research cases.

The next useful contrast is a second model/interface and a genuinely minimal benchmark-advice request, because both current conditions explicitly ask for limitations and sufficiency. Keep the source case key fixed, preserve appropriate qualifications/alternatives, obtain human review, and avoid adding known implementation defects as supposed novel recommendation failures.

## Reproduce and inspect

The frozen design and all captured answers, hash acknowledgments, review packets/key, ratings, source-check records and metadata are in [`experiments/open-recommendations-20261112`](../../experiments/open-recommendations-20261112). Source URLs and pinned Git blobs are preserved in the casepack.

```bash
python3 scripts/summarize_open_recommendations.py experiments/open-recommendations-20261112
```

The collector script documents prompt/artifact validation and anonymization. Its original launch paths belong to the recorded workspace; reproducing new model samples requires fresh contexts with the exact recorded prompts and explicit interface/version disclosure. Summary reproduction uses the archived JSONL files without model access.
