"""Post-outcome descriptive audit. Reads existing captures; never calls a model/scorer."""
from pathlib import Path
from datetime import datetime, timezone
import collections
import hashlib
import json
import re

P = Path(__file__).resolve().parent
canonical = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
sha = lambda b: hashlib.sha256(b).hexdigest()
responses = [json.loads(x) for x in (P / "responses.jsonl").read_text().splitlines()]
manifest = {r["trial_id"]: r for r in [json.loads(x) for x in (P / "manifest.jsonl").read_text().splitlines()]}
analysis = {r["trial_id"]: r for r in json.loads((P / "ANALYSIS_CAPTURES.json").read_text())}
selected = {r["source_index"]: r for r in json.loads((P / "selected20.json").read_text())}
assert len(responses) == len(manifest) == len(analysis) == 80


def alias_hits(aliases, text):
    hits = []
    for alias in aliases:
        if not alias:
            continue
        pattern = ((r"(?<!\w)" if alias[0].isalnum() else "")
                   + re.escape(alias)
                   + (r"(?!\w)" if alias[-1].isalnum() else ""))
        if re.search(pattern, text, re.I):
            hits.append(alias)
    return hits


rows = []
for response in responses:
    key = response["trial_id"]
    a = analysis[key]
    m = manifest[key]
    s = selected[m["source_index"]]
    record = s["record"]
    assert sha(canonical(record).encode()) == s["source_sha256"] == m["source_sha256"]
    text = response.get("output_text")
    assert text is None or sha(text.encode()) == response["output_text_sha256"]
    row = {
        "trial_id": key,
        "source_index": m["source_index"],
        "source_record_sha256": s["source_sha256"],
        "model": response["requested_model"],
        "condition": m["condition"],
        "response_status": response["response_status"],
        "analysis_status": a["status"],
        "included_in_completed_format_counts": a["status"] == "completed_scored",
        "output_text_sha256": response.get("output_text_sha256"),
        "score_as_previously_saved": a.get("score"),
    }
    if a["status"] == "completed_scored":
        assert response["response_status"] == "completed" and isinstance(text, str)
        tags = list(re.finditer(r"<answer>\s*(.*?)\s*</answer>", text, re.I | re.S))
        terminal = tags[-1] if tags and not text[tags[-1].end():].strip() else None
        prefix = text[:terminal.start()] if terminal else None
        tag = terminal.group(1).strip() if terminal else None
        matches = alias_hits(record["target"], prefix) if prefix is not None else None
        row.update(
            source_question=record["prompt"],
            target_aliases=record["target"],
            output_text=text,
            output_tail_700=text[-700:],
            parsed_as_previously_saved=a["judged"]["parsed"],
            scorer_source_sha256=a["judged"]["source_sha256"],
            terminal_answer_tag_text=tag,
            strict_terminal_A_tag=(tag == "A"),
            output_only_terminal_tag=(terminal is not None and not prefix.strip()),
            output_only_A_tag=(tag == "A" and not prefix.strip()),
            literal_aliases_in_prefix_before_terminal_tag=matches,
            prefix_contains_literal_alias=(bool(matches) if matches is not None else None),
            character_count=len(text),
        )
    rows.append(row)
assert sum(r["included_in_completed_format_counts"] for r in rows) == 69
groups = []
for model in ("gemma-4-31b-it", "qwen3.8-27b"):
    for condition in ("binding_only", "official_typed"):
        rs = [r for r in rows if r["model"] == model and r["condition"] == condition]
        complete = [r for r in rs if r["included_in_completed_format_counts"]]
        strict_A = [r for r in complete if r["strict_terminal_A_tag"]]
        prefix_alias = [r for r in complete if r["prefix_contains_literal_alias"]]
        groups.append({
            "model": model,
            "condition": condition,
            "planned": len(rs),
            "completed": len(complete),
            "unknown": len(rs) - len(complete),
            "common_rule_score_ones": sum(r["score_as_previously_saved"] == 1 for r in complete),
            "strict_terminal_A_tag": len(strict_A),
            "strict_terminal_A_with_rule_score_one": sum(r["score_as_previously_saved"] == 1 for r in strict_A),
            "output_only_A_tag": sum(r["output_only_A_tag"] for r in complete),
            "output_only_any_terminal_tag": sum(r["output_only_terminal_tag"] for r in complete),
            "terminal_tag_payloads": dict(collections.Counter(r["terminal_answer_tag_text"] for r in complete if r["terminal_answer_tag_text"] is not None)),
            "prefix_literal_alias_present": len(prefix_alias),
            "prefix_literal_alias_but_rule_score_zero": [
                r["trial_id"] for r in prefix_alias if r["score_as_previously_saved"] == 0
            ],
            "completed_trial_ids": [r["trial_id"] for r in complete],
            "unknown_trial_ids": [r["trial_id"] for r in rs if not r["included_in_completed_format_counts"]],
        })
by_id = {r["trial_id"]: r for r in rows}


def example(ids, observation):
    return {
        "trial_ids": ids,
        "observation": observation,
        "responses": [{
            key: by_id[trial][key]
            for key in ["trial_id", "source_index", "source_record_sha256", "model", "condition",
                        "source_question", "score_as_previously_saved", "terminal_answer_tag_text",
                        "output_text", "parsed_as_previously_saved"]
        } for trial in ids],
    }


report = {
    "status": "POST_OUTCOME_EXPLORATORY_OUTPUT_REVIEW",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "pre_registered": False,
    "review_scope": "Read every69completed final output/tail and stored rule-parser capture. Preserve all80planned cases and11unknown statuses. No new model calls, generation/scoring reruns or scorer changes.",
    "definitions": {
        "terminal_answer_tag": "Last case-insensitive <answer>...</answer> element followed only by whitespace; its stripped payload is retained verbatim.",
        "strict_terminal_A_tag": "Terminal tag payload exactly uppercase A, without extra text.",
        "output_only_A_tag": "Strict terminal A tag with only whitespace before it; a descriptive format count.",
        "prefix_literal_alias_present": "At least one source alias occurs case-insensitively before the terminal answer tag, with a negative word-character lookaround at each alphanumeric alias edge. No terminal tag gives null, not a negative semantic judgment.",
        "prefix_warning": "Alias occurrence is lexical, not a claim that reasoning is correct or that a final answer is correct. Numeric aliases can match intermediate calculations. Negation, contradiction and semantic equivalence are not judged.",
        "score": "Existing optional official RULE-mode score copied unchanged from ANALYSIS_CAPTURES.json. No strict-final-answer score or model-judge score was added.",
        "selection": "Same20fixed source questions, repeated2models x2prompt conditions; source rows/conditions are not independent samples.",
    },
    "source_files": {
        n: {"sha256": sha((P / n).read_bytes()), "bytes": (P / n).stat().st_size}
        for n in ["responses.jsonl", "manifest.jsonl", "ANALYSIS_CAPTURES.json", "ANALYSIS_SUMMARY.json", "selected20.json"]
    },
    "counts": {"planned": 80, "completed_reviewed": 69, "unknown_preserved": 11},
    "groups": groups,
    "main_interpretation": [
        "Qwen completed binding-only outputs include14/18literal A-tag-only responses;16/18end with strictA. Its other2completed outputs contain underlying-task semantic answer payloads No and Washington,D.C., and receive the2common-rule credits.",
        "Gemma completed binding-only outputs contain explanatory prefixes in18/18cases and lexical source aliases in15/18prefixes. Fourteen end with strictA, and7of those14still receive common-rule credit from retained body candidates. This shows that rule-score differences are sensitive to output verbosity and answer extraction, beyond the terminal task-format error.",
        "Five Gemma binding-only cases contain a literal source alias in the explanatory prefix but receive rule0 because saved extracted candidates omit that alias. Qwen's2explanatory binding-only outputs similarly mention an alias but receive0 after extraction of theA-oriented ending.",
        "These observations support a format/instruction-mediated explanation for the measured Qwen sensitivity. They do not identify a loss of underlying knowledge or establish model capability rankings.",
    ],
    "examples": [
        example(["MXG-04-B-Q", "MXG-04-T-Q"], "Same source47: binding-only emits onlyA; typed emitsSommelier, with stored rule0to1."),
        example(["MXG-00-B-G", "MXG-00-B-Q"], "Both finish withA under binding-only. Gemma includes the accepted proverb completion in its prefix and gets rule1; Qwen emits onlyA and gets0. This is descriptive cross-model evidence, not a randomized between-model mechanism estimate."),
        example(["MXG-03-B-Q", "MXG-03-T-Q"], "Qwen binding-only explicitly calculates fewer girls in the prefix, then choosesA; the saved rule parser retainsa. and gives0. Typed emitsGirls and gets1."),
        example(["MXG-14-B-G", "MXG-14-T-G"], "Gemma binding-only namesLindisfarne before endingA, but saved parser retains onlynone and gives0. TypedLindisfarne gets1. This is extraction sensitivity, not proof the binding model lacked the fact."),
        example(["MXG-00-T-Q"], "Typed outputPrepare for the worst gets rule0 againstBut prepare for the worst. The lexical rule's treatment must not be turned into a strict semantic-correctness judgment."),
        example(["MXG-08-B-Q", "MXG-18-B-Q"], "Two Qwen binding-only outputs depart from the offeredA.None answer and returnWashington,D.C./No inside answer tags; they receive rule1."),
    ],
    "causal_limits": [
        "This output review and regex definitions were chosen after outcomes and are exploratory.",
        "The paired prompt intervention preserves source questions, but changes offered options, answer instructions and formatting together. It does not isolate one prompt subcomponent.",
        "Common-rule score sensitivity is not semantic model capability and is not strict final-answer correctness.",
        "Both original and repaired conditions use the same source references and scoring function in the main analysis; this review does not change their scores or uncertainty bounds.",
        "Eleven incomplete responses remain unknown; differing completed subsets must not replace the fixed20-question paired estimand.",
        "Model-specific output styles, existing benchmark/source exposure and this20-question selected panel limit generalization.",
        "No new model calls or scorer runs were made for this review.",
    ],
    "case_text_provenance": "Every completed case keeps its final700-character tail and full saved parser candidates. Full response bytes and aliases remain in responses.jsonl/selected20.json under the recorded hashes; representative examples reproduce full outputs.",
    "cases": [{key: value for key, value in row.items()
               if key not in {"output_text", "source_question", "target_aliases"}}
              for row in rows],
}
(P / "EXPLORATORY_OUTPUT_REVIEW.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({"status": report["status"], "counts": report["counts"], "groups": groups}, ensure_ascii=False))
