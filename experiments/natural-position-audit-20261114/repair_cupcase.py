"""Minimal source-preserving native CUPCase adapter repair, separately labelled."""
import copy
import json
import random

from audit_positions import HERE, hf_frame, load_native
from full_entrypoint import execute, support_classes


def main():
    plan = json.loads((HERE/"sources.json").read_text())
    native = load_native(plan)
    receipts = support_classes(native[-1])
    gallery = json.loads(native[0]["one_eval/utils/bench_table/bench_gallery.json"])["benches"]
    original_config = next(x for x in gallery if x["bench_name"] == "cupcase")
    frame, provenance = hf_frame("ofir408/CupCase", "test")
    assert provenance["revision"] == "157a85b1a0fa6d0e25e5209a1cdaf41cf1ff8753"
    config = copy.deepcopy(original_config)
    keys = original_config["meta"]["key_mapping"]["input_choices_key"]
    rng = random.Random(20261114)
    permutations = []
    for row in frame.to_dict("records"):
        choices = [row[k] for k in keys]
        rng.shuffle(choices)
        assert sorted(choices) == sorted(row[k] for k in keys)
        permutations.append(choices)
    frame["neutral_choices"] = permutations
    config["meta"]["key_mapping"]["input_choices_key"] = "neutral_choices"
    config["meta"]["evaluation"]["parser"]["choices_key"] = "neutral_choices"
    # Both declared answer encodings must use the displayed order. The first
    # attempted repair left this gold-first field list in the parser config;
    # resolve_choice_texts prioritizes it and still calls every source gold A.
    config["meta"]["evaluation"]["parser"].pop("choice_text_fields", None)
    previous_template = config["meta"]["prompt"]["user_template"]
    assert previous_template.count("{clean_case_presentation}") == 1
    config["meta"]["prompt"]["user_template"] = previous_template.replace("{clean_case_presentation}", "{question}")
    config["meta"]["prompt"]["template_id"] = "cupcase_source_preserving_repair_20261114"
    result = execute("cupcase-repaired", frame, config, native, "AB")
    summary = dict(one_eval_revision=plan["one_eval_revision"], source_provenance=provenance,
                   repaired_cupcase=result, dataflow=native[5], added_source_sha256=receipts,
                   original_gallery_config=original_config, repaired_gallery_config=config,
                   new_model_calls=0, boundary="Original public run_eval and native classes, separately labelled source-preserving option-order/question-placeholder repair; constant serving cache. No installed CLI or LLM-generated report.")
    (HERE/"repair-summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print("REPAIR_SUMMARY "+json.dumps(summary,separators=(",", ":")),flush=True)


if __name__ == "__main__":
    main()
