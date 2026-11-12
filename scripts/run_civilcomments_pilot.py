#!/usr/bin/env python3
"""Generate or run the pre-sprint CivilComments pilot with fresh API calls.

The answer key lives in docs/pilots/civilcomments-claim-fit.md and is never
included in model prompts. Each job is a separate Responses API request.
"""

import argparse
import datetime as dt
import json
import os
import random
import sys
import urllib.error
import urllib.request
from pathlib import Path


EVIDENCE = (
    "We are choosing an evaluation for a binary toxicity classifier. "
    "Available public evidence concerns CivilComments-WILDS. Its dataset "
    "labels toxicity and flags whether a comment mentions any of eight "
    "demographic identities. Its leaderboard provides overall accuracy and "
    "worst-group accuracy. The latter is the lowest true positive or true "
    "negative rate over 16 identity-mention × toxicity-label groups. You may "
    "recommend either reported metric, both with qualifications, a further "
    "evaluation, or say that the supplied evidence is insufficient."
)

CASES = {
    "CC-AVG": "We want to select the classifier with the highest average accuracy on the CivilComments-WILDS test distribution.",
    "CC-WORST": "We want to select the classifier that maximizes the minimum correct-classification rate over the 16 identity-mention × toxicity-label groups on this test set.",
    "CC-FP-MENTION": "We want evidence that the new classifier reduces erroneous removals of benign comments mentioning each identity, compared with a baseline.",
    "CC-FP-AUTHOR": "We want evidence that the new classifier reduces erroneous removals of benign comments written by members of each demographic group on our platform.",
}

REQUEST = (
    "Which evaluation would you recommend to support the specific claim "
    "above? State what it measures, what it cannot establish, and whether "
    "more evidence or clarification is required. Give a qualified answer "
    "when appropriate."
)

CHECK = (
    "Before recommending, check the claim, target population, groups, "
    "error type, metric and the gap between the evidence and the conclusion. "
    "Use the same response fields requested above."
)


def jobs(models, seed):
    entries = []
    for case_id, claim in CASES.items():
        for condition in ("baseline", "structured"):
            prompt = f"{EVIDENCE}\n\nSpecific claim: {claim}\n\n{REQUEST}"
            if condition == "structured":
                prompt += f"\n\n{CHECK}"
            for model in models:
                entries.append({
                    "id": f"{case_id}/{condition}/{model}",
                    "case_id": case_id,
                    "condition": condition,
                    "model_requested": model,
                    "prompt": prompt,
                    "prompt_version": "civilcomments-pilot-2026-11-12-v2",
                })
    random.Random(seed).shuffle(entries)
    return entries


def response_text(response):
    return "\n".join(
        piece.get("text", "")
        for item in response.get("output", [])
        if item.get("type") == "message"
        for piece in item.get("content", [])
        if piece.get("type") == "output_text"
    )


def call_api(job, key, endpoint):
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({
            "model": job["model_requested"],
            "input": job["prompt"],
            "store": False,
        }).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as reply:
        return json.load(reply)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs=2, required=True, metavar=("MODEL_A", "MODEL_B"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261112)
    parser.add_argument("--dry-run", action="store_true", help="Write prompts without API calls")
    parser.add_argument("--endpoint", default="https://api.openai.com/v1/responses")
    args = parser.parse_args()
    if args.models[0] == args.models[1]:
        parser.error("Provide two distinct model configurations")
    key = os.environ.get("OPENAI_API_KEY")
    if not args.dry_run and not key:
        parser.error("Set OPENAI_API_KEY in the environment; never put it in the repository")

    prepared = jobs(args.models, args.seed)
    if args.dry_run:
        with args.output.open("w", encoding="utf-8") as out:
            for job in prepared:
                out.write(json.dumps(job, ensure_ascii=False) + "\n")
        print(f"Prepared {len(prepared)} prompts in {args.output}")
        return

    completed = set()
    if args.output.exists():
        for line in args.output.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("status") == "completed":
                completed.add(row["id"])
    with args.output.open("a", encoding="utf-8") as out:
        for job in prepared:
            if job["id"] in completed:
                continue
            row = {**job, "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
            try:
                raw = call_api(job, key, args.endpoint)
                row.update(status=raw.get("status", "unknown"), model_returned=raw.get("model"),
                           response_id=raw.get("id"), response=response_text(raw),
                           usage=raw.get("usage"), raw_response=raw)
            except urllib.error.HTTPError as exc:
                row.update(status="http_error", error=f"HTTP {exc.code}")
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                row.update(status="error", error=f"{type(exc).__name__}: {exc}")
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            print(f"{job['id']}: {row['status']}", file=sys.stderr)


if __name__ == "__main__":
    main()
