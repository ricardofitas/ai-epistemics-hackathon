# Exploratory ranking sensitivity on the actual factorial panel

The primary artifact passes the existing independently committed verifier. There are 160 planned and attempted requests, 152 eligible complete scores and eight incomplete scores. The complete ZIP SHA256 is `7f464eba93330fb19742b850aa4349eeb1804a8b45eaf4664e375b2af2ee8d6d`.

This derivative was designed after the primary aggregate results were visible. Its ranking claim is exploratory. The primary endpoint remains the pinned official optional RULE score on the original 20-source panel. The eight incomplete outputs remain unknown in the input file.

| Custom diagnostic condition | Gemma accepted /20 | Qwen accepted /20 | Qwen minus Gemma, percentage points |
|---|---:|---:|---:|
| Free-form instruction, appended carrier absent | 14 | 15–18 | +5 to +20 |
| Free-form instruction, appended `A. None` present | 15 | 15–16 | 0 to +5 |
| Choice instruction, appended carrier absent | 16 | 16–18 | 0 to +10 |
| Choice instruction, appended `A. None` present | 8 | 0–2 | −40 to −30 |

The selected transition from choice instruction with `A. None` to free-form instruction with the carrier absent produces a strict model-ranking reversal in **all 256 joint binary assignments** of the eight unknown scores. The Qwen-relative-to-Gemma shift is **35 to 60 percentage points**, or seven to twelve net accepted responses on the same 20 sources. Gemma's absolute change is +30 points and Qwen's change ranges from +65 to +90 points.

The source-level certificate contains eight sources with a known positive relative shift, nine with a known zero relative shift, and three with uncertain contributions. The eight positive sources contribute nine net accepted responses. Source809 can reduce this shift by up to two, while sources281 and860 can add up to three. This yields the same seven-to-twelve total bounds through paired source arithmetic. All 20 exact contributions are retained in `RANKING_SENSITIVITY.json` and all 80 paired within-condition outcomes in `SOURCE_PAIRED_OUTCOMES.tsv`.

## Sensitivity to predeclared source caveats

The exclusions below were selected after results for secondary sensitivity analysis. The underlying three source caveats were documented before generation. Every nonempty subset of source860 (historical office ambiguity), source571 (multi-part/reference interpretation) and source281 (intrinsic Yes/No choices) was excluded in a separate calculation. Every one of the seven retained panels preserves the strict reversal under all 256 original unknown assignments. Assignments to excluded slots have no effect on a retained panel.

Removing all three leaves 17 paired source cases. The Qwen-minus-Gemma difference is −41.176 to −35.294 points under choice plus `A. None`, and +5.882 to +11.765 under free-form plus absent carrier. The relative shift is +41.176 to +52.941 points. These exclusions supplement the unchanged 20-source analysis.

## Interpretation and reproduction

The bounds describe incomplete-output sensitivity in a fixed panel. The same sources repeat across models and conditions. Population uncertainty and model capability are outside this calculation. RULE acceptance can arise from factual content in a rationale followed by a symbolic final answer. The result therefore concerns the ranking assigned by that specific endpoint. Separate masked semantic review can address a different endpoint.

The four conditions use a constructed diagnostic template. Full installed native-provider and default-model-judge results require separate evidence.

The retained raw download is `../factorial_actual/mixeval-factorial-43615821403.zip`; its extracted experiment root is `../factorial_actual/extracted/`. The verification code is the previously committed `../factorial_final_verification/verify.py`. None of these calculations makes provider or judge calls.

Run the following commands from the repository working directory. The scripts also accept absolute input/output paths.

```bash
python3 factorial_final_verification/verify.py factorial_actual/extracted --output ranking_analysis/PRIMARY_VERIFICATION.json
python3 ranking_analysis/analyze_ranking.py
python3 ranking_analysis/verify_ranking.py
```

`analyze_ranking.py` exhaustively enumerates the 256 assignments. `verify_ranking.py` independently derives all endpoints using signed coefficients and exact fractions, without importing the enumeration implementation. Its 55 checks cover all four condition gaps, the reversal and relative shift, seven caveat panels, and all 20 source contributions. Input and implementation identities are retained in `INPUT_PROVENANCE.json`.
