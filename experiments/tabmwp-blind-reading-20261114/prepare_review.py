"""Create a gold-blind, 40-item double-read packet after funded attribution completes."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def priority(row):
    digest=hashlib.sha256(("TabMWP-human-20261114|"+row["key"]).encode()).digest()
    return digest

def prepare(judge_dir, destination):
    source=json.loads((judge_dir/"cases.json").read_bytes())
    dest=Path(destination)
    dest.mkdir(parents=True,exist_ok=True)
    remaining={g:sorted((r for r in source if r["group"]==g),key=priority)
               for g in ("first_credited","first_wrong","control")}
    chosen=remaining["first_credited"][:16]+remaining["first_wrong"][:16]+remaining["control"][:8]
    assert len({r["key"] for r in chosen})==40
    pages=[];keys=[]
    for row in sorted(chosen,key=priority):
        id_=hashlib.sha256(("blinded-tbmwp-"+row["key"]).encode()).hexdigest()[:12]
        pages.append(dict(id=id_,question=row["question"],options=row["options"],
                          archived_reply=row["raw"],reader_option_or_unresolved=None))
        keys.append(dict(id=id_,source_question=row["pid"],judge_key=row["key"],stratum=row["group"],
                         official_answer=row["gold"],control=row["control"]))
    (dest/"blind.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in pages))
    (dest/"key.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in keys))
    (dest/"INSTRUCTIONS.md").write_text(
        "# Independent reading of 40 archived replies\n\n"
        "Give each reader only blind.jsonl and this instruction. Read each archived reply, "
        "using the question and options to interpret its meaning. Record the displayed option number only "
        "when the reply itself identifies an option. Record UNRESOLVED when its meaning is insufficient "
        "or ambiguous. Do not solve the benchmark question. Two readers should finish independently; keep "
        "their first labels and resolve disagreement separately. Keep key.jsonl and the model judges' "
        "responses unavailable until both initial readings have been archived.\n\n"
        "Record each initial judgment against the supplied item identifier.\n")
    return len(pages)

if __name__=="__main__":
    import sys
    print(prepare(Path(sys.argv[1]),Path(sys.argv[2])))
