#!/usr/bin/env python3
"""Prepare exact prospective requests; never perform inference."""
from collections import Counter
from copy import deepcopy
import datetime as dt
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
OUT = ROOT / "study"
MODELS = ["gemma-4-31b-it", "glm-5.2", "qwen3.8-27b", "deepseek-v4-flash"]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def prompt(case):
    for key in ["natural_prompt", "prompt", "exact_prompt", "case_prompt", "research_request", "question"]:
        if isinstance(case.get(key), str) and case[key].strip():
            return case[key]
    raise ValueError("Case has no model-facing prompt")


def main():
    OUT.mkdir(exist_ok=True)
    if (OUT / "api_artifacts").exists():
        raise ValueError("Do not rebuild an experiment after inference")
    filenames = ["factscore_case.json", "drop_case.json", "gsmsymbolic_case.json",
                 "squad2_case.json", "scienceworld_case.json", "preference_case.json"]
    cases = [read(ROOT / "curation" / name) for name in filenames]
    for case in cases:
        case["study_role"] = "new_screen"
    source = read(WORK / "open_study/casepack.json")["cases"]
    wmt = next(deepcopy(c) for c in source if c.get("id", c.get("case_id")) == "open_mt_news_ende_late2019")
    selected = [wmt, read(WORK / "new_pilots_20261113/hans_case.json"),
                read(WORK / "new_pilots_20261113/beir_case.json")]
    for case in selected:
        case["study_role"] = "selected_recurrence"
    cases.extend(selected)
    for case in cases:
        case.setdefault("id", case.get("case_id"))
        case["model_facing_prompt"] = prompt(case)
    assert len({c["id"] for c in cases}) == 9
    assert prompt(wmt) == "I want to compare two English-to-German systems on held-out online news from late 2019. Which public test set and scoring setup should I use?"
    write(OUT / "casepack.json", {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
          "source_cases": 9, "new_families": 6, "selected_existing_cases": 3,
          "visibility": "Only model_facing_prompt and common instructions sent; sources/criteria/examples withheld",
          "cases": cases})
    jobs = []
    for case in cases:
        repetitions = 1 if case["study_role"] == "new_screen" else 3
        for model in MODELS:
            for repetition in range(1, repetitions + 1):
                payload = {"model": model, "input": prompt(case),
                           "instructions": "Answer the research question from existing knowledge. Aim for 180–240 words and do not exceed 300 words. Do not browse or use external tools. Do not ask a follow-up question.",
                           "max_output_tokens": 8192, "temperature": 0.7,
                           "tools": [], "tool_choice": "none", "agentic_memory": False,
                           "store": False, "stream": True}
                jobs.append({"case_id": case["id"], "stage": case["study_role"],
                             "repetition": repetition, "requested_model": model,
                             "request_payload": payload})
    random.Random(2026111312).shuffle(jobs)
    for i, job in enumerate(jobs, 1):
        job.update(trial_id=f"PR-{i:02d}", execution_order=i)
    assert Counter(j["stage"] for j in jobs) == {"new_screen": 24, "selected_recurrence": 36}
    (OUT / "manifest.jsonl").write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs))
    protocol = {
        "id": "paper-research-wave1-20261113", "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "allocation": {"requested": 60, "new_screen": 24, "selected_recurrence": 36,
                       "new_families": 6, "selected_cases": 3, "model_configurations": 4,
                       "new_repeats_per_cell": 1, "selected_repeats_per_cell": 3},
        "breadth_goal": {"before": 15, "after_if_sampled": 21, "next_target": 25},
        "models": MODELS, "model_selection": "Same four previously operational configurations; chosen before this wave; aliases are not immutable weight revisions.",
        "randomization": {"seed": 2026111312, "generator": "Python Random.shuffle over six new cases, then WMT/HANS/BEIR, listed models, ascending repetition"},
        "controls": {"stream": True, "temperature": 0.7, "max_output_tokens": 8192,
                     "tools": [], "tool_choice": "none", "agentic_memory": False, "store": False,
                     "previous_response_id": "omitted", "concurrency": 2, "socket_timeout_seconds": 120},
        "timeout_scope": "Per blocking socket operation, not hard total wall-clock",
        "stopping": "Attempt all 60 frozen rows once; no client retries, replacements or stopping after positive results. Preserve empty/error/incomplete/fallback captures. Additional samples need separately dated freeze.",
        "maximum_requested_output_tokens": 491520,
        "cost_scope": "At current documented short-input hosted rates this cap is expected below 2 credits if prices apply. Actual reported usage.cost retained; missing charges, account debit/balance and USD equivalence unknown.",
        "rubric": "Original material-unsupported-sufficiency rule unchanged. Historical six-case/24-call bookkeeping overridden by nine cases/60 attempts. Qualified proxies/adaptations and verified alternatives accepted; missing desirable detail not failure; genuine ambiguity uncertain.",
        "hashes": {"rubric": sha(WORK / "open_design/rubric.json"), "casepack": sha(OUT / "casepack.json"),
                   "manifest": sha(OUT / "manifest.jsonl"), "runner": sha(ROOT / "run_adaption_stream_pilot.py"),
                   "prereview": sha(ROOT / "PRE_REVIEW.json")},
        "target_mechanisms": {
            "open_mt_news_ende_late2019": "wrong_source_news_period",
            "NEW-HANS-ROLES": "paraphrase_score_sufficient_for_directional_entailment",
            "NEW-BEIR-COVID-RETRIEVAL-POSITIVE": "nonsignificance_implies_equivalence"},
        "prospective_scope_clarifications": "The original WMT/HANS/BEIR question and case requirements are unchanged. Prior PAWS directionality and nonsignificance-equivalence scope interpretations apply prospectively under the original rule to every applicable answer, not just previously failed models.",
        "recurrence": "Code exact target mechanism separately from any primary error. Another error is not recurrence of the known mechanism. Report new three-context cells separately from historical discovery. Two-of-three same-mechanism flag is descriptive, not significance, prevalence or publication guarantee. Later five-context/wording stages require separate freezes.",
        "review": "Two fresh model/repetition/stage-blind first agent reviews; case definitions and primary facts supplied. Freeze complete first ratings before unblinding. Independent factual check and separate transparent adjudication. Same-family judges are not human validation.",
        "capture": "Prefer terminal provider final text; missing terminal/delta fallback/format deviation is flagged, not silently promoted to completion. Durable sanitized journals retained. Stream is a transport change; WMT cap is higher than its original native API pilot. This tests recurrence under recorded new settings, not identical historic provider conditions.",
        "evidence_ladder": "EVIDENCE_LADDER.md and ladder.json raise support requirements, never retrospectively change original response labels or add traps.",
        "unused_wording_probes": "Six heldout_paraphrases.json strings remain unsampled, add zero families, require fidelity prereview before any later calls. Full file contains evaluator metadata and must not be transmitted.",
        "optional_consequence_gate": "A separately frozen PAWS/HANS performance feasibility pilot may proceed only if at least one configuration has >=2/3 verified target-mechanism recurrences in this wave. It is not part of these 60; all requests/nulls retained, no reversal presumed, data provenance must be adequate.",
        "scope": "Curated source families, shared domain clusters and post-discovery case selection; no representative error prevalence or general model ranking. New source families are not necessarily new domains.",
        "human_review": "pending", "timing": "13 November 2026 event day1; exact public kickoff hour unverified; preserve earlier work as dated preparation."}
    write(OUT / "protocol.json", protocol)
    probes = [json.loads(s) for s in (ROOT / "transport_probe/responses.jsonl").read_text().splitlines()]
    assert len(probes) == 4 and all(r["completed_nonempty"] and r["terminal_event_seen"] and r["output_text"].strip() == "OK" for r in probes)
    write(ROOT / "LIVE_TRANSPORT_CHECK.json", {"probe_calls": 4, "complete_OK": 4,
          "terminal_events_seen": 4, "provider_aliases": [r["returned_model"] for r in probes],
          "scope": "Generic operational probes only; excluded from recommendation sample counts; not proof of no future timeouts."})
    print(json.dumps({"requested": len(jobs), "new_screen": 24, "selected_recurrence": 36,
                      "case_ids": [c["id"] for c in cases], "manifest_sha256": protocol["hashes"]["manifest"]}))


if __name__ == "__main__":
    main()
