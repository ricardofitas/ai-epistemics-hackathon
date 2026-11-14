"""Close only the gallery-default GPQA Diamond corpus distinction."""
import json
from audit_positions import HERE, gpqa_frame, load_native
from full_entrypoint import execute, support_classes


def main():
    plan = json.loads((HERE/"sources.json").read_text())
    native = load_native(plan)
    receipts = support_classes(native[-1])
    gallery = json.loads(native[0]["one_eval/utils/bench_table/bench_gallery.json"])["benches"]
    config = next(b for b in gallery if b["bench_name"] == "gpqa")
    assert config["meta"]["download_config"]["config"] == "gpqa_diamond"
    assert config["meta"]["download_config"]["split"] == "train"
    frame, provenance = gpqa_frame(plan, "gpqa_diamond.csv")
    assert len(frame) == 198
    result = execute("gpqa-diamond", frame, config, native, "AB")
    summary = dict(one_eval_revision=plan["one_eval_revision"], source_provenance=provenance,
                   default_download_config=config["meta"]["download_config"], gpqa_diamond=result,
                   dataflow=native[5], added_source_sha256=receipts,new_model_calls=0,
                   boundary="Original complete native API-generation run_eval on author Diamond corpus matching gallery default; exact source-loaded storage/evaluator/report selector with cached constant serving. No installed CLI or real-model inference.")
    (HERE/"diamond-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("DIAMOND_SUMMARY "+json.dumps(summary,separators=(",", ":")),flush=True)


if __name__ == "__main__":
    main()
