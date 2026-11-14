"""Frozen external validation of the instruction-by-carrier interaction, 14 Nov 2026."""
import argparse
import gzip
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SALT = "AI-Epistemics/independent-questions/2026-11-14/v1"
MODELS = ["gemma-4-31b-it", "qwen3.8-27b", "deepseek-v4-flash", "glm-5.2"]
ARMS = ["free_clear", "free_none", "choice_clear", "choice_none"]
RATES = {  # Adaption official hosted pricing, credits per million non-cached tokens
    "gemma-4-31b-it": (0.09, 0.34), "qwen3.8-27b": (0.039, 1.25),
    "deepseek-v4-flash": (0.045, 0.14), "glm-5.2": (1.40, 4.40)
}
CAP = 6144
SOURCE_PINS = {
    "squad": ["rajpurkar/SQuAD-explorer", "240e165ab706d95bd4323653bb92421f446208cf", "dataset/dev-v1.1.json", "e9a3f913ad1468ebe105b891334ca7b0bc0e2510"],
    "tab": ["lupantech/PromptPG", "869bae8ffb8288ccc3102293b3090ec2aa17f618", "data/tabmwp/problems_test1k.json", "e02ef707d15e555f8a7e74ff31080001fed95e4b"],
    "mixbase64": ["ricardofitas/ai-epistemics-hackathon", "226bb9bb0f0f71be7b0dc0d188d6e960e4460dbf", "experiments/mixeval-semantic-review-20261114/next_ablation/SOURCE_POOL.jsonl.gz", "1232735d070afc7882f481103b5df532f8359c48"]
}
# The SQuAD source stratum is fixed before looking at any new model responses.
SQUAD_TITLES = {
    "Super_Bowl_50", "Warsaw", "Teacher", "Southern_California", "Sky_(United_Kingdom)",
    "Victoria_(Australia)", "Steam_engine", "Amazon_rainforest", "Fresno,_California",
    "Geology", "Newcastle_upon_Tyne", "Victoria_and_Albert_Museum",
    "American_Broadcasting_Company", "Construction", "Private_school", "Harvard_University",
    "Jacksonville,_Florida", "Economic_inequality", "Doctor_Who", "University_of_Chicago",
    "Kenya", "Intergovernmental_Panel_on_Climate_Change", "Prime_number", "Rhine",
    "Scottish_Parliament", "Force"
}

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def digest(value):
    return hashlib.sha256(value).hexdigest()

def norm(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

def draw_key(kind, ident):
    return digest(f"{SALT}|{kind}|{ident}".encode())

def read_sources(folder):
    result = {}
    for name, (_, _, _, expected) in SOURCE_PINS.items():
        raw = (folder / name).read_bytes()
        ident = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes(1) + raw).hexdigest()
        if ident != expected:
            raise ValueError(f"source identity changed: {name}")
        result[name] = raw
    return result

def candidates(raw):
    for article in json.loads(raw["squad"])["data"]:
        if article["title"] not in SQUAD_TITLES:
            continue
        for para in article["paragraphs"]:
            context = para["context"]
            for qa in para["qas"]:
                gold = list(dict.fromkeys(a["text"] for a in qa["answers"]))
                if not gold or not all(context[a["answer_start"]:a["answer_start"]+len(a["text"])] == a["text"] for a in qa["answers"]):
                    continue
                yield dict(dataset="squad", id=qa["id"], question=qa["question"], context=context, gold=gold,
                           unit="", group=article["title"], record_sha=digest(canonical([context,qa])))
    for ident, prob in json.loads(raw["tab"]).items():
        if prob["ques_type"] != "free_text" or prob["ans_type"] not in ("integer_number","decimal_number") or prob["choices"]:
            continue
        context = (prob["table_title"] + "\n" if prob.get("table_title") else "") + prob["table"]
        yield dict(dataset="tabmwp", id=ident, question=prob["question"], context=context, gold=[str(prob["answer"])],
                   unit=prob.get("unit") or "", group=prob["ans_type"], record_sha=digest(canonical(prob)))

def payload(case, model, arm, case_index=None):
    instruction = ("Give the factual answer to the question in free form." if arm.startswith("free") else
                   "Select the best answer from the provided options.")
    parts = ["Answer the source question using its context when relevant.", instruction,
             "Question:\n" + case["question"], "Context:\n" + case["context"]]
    if arm.endswith("none"):
        parts.append("Options:\nA. None")
    parts.append("Put your final answer in <answer>...</answer> tags.")
    return dict(model=model, input="\n\n".join(parts), temperature=0, max_output_tokens=(4096 if case_index is not None and case_index % 4 in (0, 1) else CAP),
                stream=True, tools=[], agentic_memory=False, store=False, tool_choice="none")

def select(raw):
    prior = {norm(json.loads(line)["record"]["prompt"]) for line in gzip.decompress(raw["mixbase64"]).splitlines()}
    buckets = {"squad": [], "tabmwp": []}
    for r in candidates(raw):
        if norm(r["question"]) in prior or not r["gold"] or not all(x.strip() for x in r["gold"]):
            continue
        if len(payload(r, MODELS[0], "choice_none")["input"].encode()) > 3900:
            continue
        buckets[r["dataset"]].append(r)
    selected = {}
    for ds, rows in buckets.items():
        rows.sort(key=lambda r: draw_key(ds,r["id"]))
        seen_q, seen_p, groups = set(), set(), Counter()
        take = []
        for r in rows:
            q, ctx = norm(r["question"]), norm(r["context"])
            if q in seen_q or ctx in seen_p:
                continue
            if ds=="squad" and groups[r["group"]] >= 6:
                continue
            take.append(r)
            seen_q.add(q)
            seen_p.add(ctx)
            groups[r["group"]] += 1
            if len(take) == 100:
                break
        if len(take) != 100:
            raise ValueError(f"insufficient unique {ds} sources")
        selected[ds] = take
    return [r for pair in zip(selected["squad"], selected["tabmwp"]) for r in pair]

def trials(cases):
    rows = []
    for i, r in enumerate(cases):
        # Each 16-case block contains each model and arm at each serial position.
        for position in range(4):
            for slot in range(4):
                # Alternating datasets get different Latin rotations rather than a fixed model confound.
                offset = i // 2 + i % 2
                mi = (slot + offset) % 4
                ai = (position + mi + offset // 4) % 4
                model, arm = MODELS[mi], ARMS[ai]
                request = payload(r, model, arm, i)
                rows.append({"key":f"{r['dataset']}-{r['id']}-m{mi}-a{ai}", "case":i,
                             "model":model,"arm":arm,"request_sha":digest(canonical(request))})
    return rows

def audit(cases, rows):
    if len(cases)!=200 or Counter(r["dataset"] for r in cases)!={"squad":100,"tabmwp":100}:
        raise ValueError("source coverage")
    if len(rows)!=3200 or len({r["key"] for r in rows})!=3200:
        raise ValueError("trial identities")
    from collections import defaultdict
    coverage=defaultdict(set)
    upper=0.
    for r in rows:
        pay=payload(cases[r["case"]],r["model"],r["arm"],r["case"])
        if digest(canonical(pay)) != r["request_sha"]:
            raise ValueError("request identity")
        coverage[r["case"]].add((r["arm"],r["model"]))
        # UTF-8 byte length plus 1024 for model-side chat framing.
        tokens=len(pay["input"].encode())+1024
        pin,pout=RATES[r["model"]]
        upper+=(tokens*pin+pay["max_output_tokens"]*pout)/1e6
    if any(len(c)!=16 for c in coverage.values()) or upper>=50:
        raise ValueError(f"coverage or credit bound {upper}")
    return dict(cases=len(cases),slots=len(rows),input_output_full_max_credits=upper,
                max_requests_per_model=800,output_caps=[4096,CAP],source_sha=digest(canonical(cases)),
                manifest_sha=digest(canonical(rows)))

if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("folder",type=Path);p.add_argument("out",type=Path);a=p.parse_args()
    c=select(read_sources(a.folder));r=trials(c);receipt=audit(c,r)
    a.out.mkdir(parents=True,exist_ok=True)
    for name,value in (("cases",c),("manifest",r),("design_receipt",receipt)):
        (a.out/(name+".json")).write_bytes(canonical(value))
    print(json.dumps(receipt,indent=2))
