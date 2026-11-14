"""Independently reconcile installed native rescoring with the original captures."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


SOURCE_RUN = 43620987144
RESCORE_RUN = 43621794887
SOURCE_ARCHIVE_SHA = "d898dfd28a0d20708b2731a7fbd899d42aadddb5d0a1b2d1617a7c73c3eb47c8"
RESCORE_ARCHIVE_SHA = "63c982408b442dd5771f52a63cdfa492d5446c0e652eab7471d0b4ac0d0b49db"
PROTOCOL_SHA = "8b1b6c5473138490083b3c2390b4555352bcbee9e3aa9e3ef53f68367c2ef000"
PROTOCOL_COMMIT = "433db326114f242cd3600b50cb328c67f075a64c"
ORIGINS = {
    "one_eval.metrics.runner": "d599a3665c2594fc1bce9b9c3cf664d704fd0cfcff57146961abeb4ac359b706",
    "one_eval.metrics.common.general": "dd7104eee19c829f3ddb5dd1faec0b97a230b253ab41b615d20b6799699d06a7",
}


def read(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def verify(rescore_root, source_root, archive, source_archive):
    root = Path(rescore_root).resolve()
    source_root = Path(source_root).resolve()
    errors = []

    def check(condition, label):
        if not condition:
            errors.append(label)

    check(digest(Path(archive).read_bytes()) == RESCORE_ARCHIVE_SHA, "rescore_archive_sha")
    check(digest(Path(source_archive).read_bytes()) == SOURCE_ARCHIVE_SHA, "source_archive_sha")
    preserved_members = 0
    for archive_path, extracted_root in ((archive, root), (source_archive, source_root)):
        with zipfile.ZipFile(archive_path) as zipped:
            for name in zipped.namelist():
                if name.endswith("/"):
                    continue
                target = (extracted_root / name).resolve()
                check(target.is_relative_to(extracted_root), "archive_path_escape:" + name)
                check(target.is_file() and target.read_bytes() == zipped.read(name),
                      "retained_archive_file:" + name)
                preserved_members += 1
    protocol_path = root / "PROTOCOL.json"
    protocol = read(protocol_path)
    launch = read(root / "LAUNCH.json")
    check(digest(protocol_path.read_bytes()) == PROTOCOL_SHA == launch.get("protocol_sha256"),
          "protocol_sha")
    check(launch.get("protocol_commit") == PROTOCOL_COMMIT, "protocol_commit")
    check(protocol.get("maximum_provider_calls") == 0
          and protocol.get("maximum_judge_calls") == 0
          and launch.get("maximum_provider_calls") == 0, "zero_call_limits")
    check(protocol.get("original_run_id") == SOURCE_RUN
          and protocol.get("original_artifact_sha256") == SOURCE_ARCHIVE_SHA,
          "source_capture_protocol_binding")
    for name, expected in protocol["frozen_files"].items():
        path = root / name
        check(path.is_file() and digest(path.read_bytes()) == expected,
              "frozen_file:" + name)
    workflow = (root / "oneeval-native-offline-rescore-20261114.yml").read_text()
    check("secrets." not in workflow and "ADAPTION_API_KEY" not in workflow,
          "no_provider_credential_in_workflow")
    check("python offline_rescore.py" in workflow and "python native_probe.py" not in workflow,
          "workflow_rescores_without_generation_entrypoint")
    summary = read(root / "RESCORE_SUMMARY.json")
    check(summary.get("status") == "PASS" and summary.get("new_provider_calls") == 0,
          "rescore_completion_and_zero_calls")
    origins = summary.get("native_module_origins", {})
    check(set(origins) == set(ORIGINS), "native_metric_origin_set")
    for name, expected in ORIGINS.items():
        entry = origins.get(name, {})
        check(entry.get("sha256") == expected and "/site-packages/" in entry.get("path", ""),
              "unchanged_installed_metric:" + name)
    inputs = read(root / "RESCORE_INPUTS.json")
    expected_cells = {(index, condition) for index in (40, 200)
                      for condition in ("native_gallery", "source_typed")}
    check(len(inputs) == 4 and {(entry["source_index"], entry["condition"]) for entry in inputs} == expected_cells,
          "all_four_original_cells")
    rows = summary.get("rows", [])
    check(len(rows) == 4 and {(entry["source_index"], entry["condition"]) for entry in rows} == expected_cells,
          "all_four_rescored_cells")
    by_summary = {(entry["source_index"], entry["condition"]): entry for entry in rows}
    slots = []
    response_ids = []
    source_records = {entry["source_index"]: entry for entry in read(source_root / "selected2.json")}
    for entry in inputs:
        index, condition = entry["source_index"], entry["condition"]
        name = f"{index}_{condition}"
        source_directory = source_root / "results" / "real" / name
        original_result = read(source_directory / "RESULT.json")
        original_trace = read(source_directory / "HTTP_TRACE.json")
        check(len(original_trace) == 1, "one_original_http_attempt:" + name)
        original_trace = original_trace[0]
        raw_body = original_trace["response_body"]
        raw = json.loads(raw_body)
        content = raw["choices"][0]["message"]["content"]
        source = source_records[index]
        check(entry["source"] == source["record"]
              and digest(canonical(entry["source"])) == entry["source_sha256"] == source["source_sha256"],
              "source_record_identity:" + name)
        check(entry["raw_body"] == raw_body
              and digest(raw_body.encode()) == entry["raw_body_sha256"] == original_trace["body_sha256"],
              "raw_response_body_identity:" + name)
        check(entry["request_sha256"] == original_trace["request_sha256"],
              "request_identity:" + name)
        check(entry["response_id"] == raw["id"], "response_id_identity:" + name)
        check(entry["delivered_row"] == original_result["delivered_row"],
              "original_delivered_row_identity:" + name)
        check(entry["original_metric_result"] == original_result["native_metric_runner"],
              "original_native_metric_identity:" + name)
        check(entry["bench"] == read(source_directory / "BENCH.json"),
              "original_bench_configuration_identity:" + name)
        response_ids.append(raw["id"])
        directory = root / "results" / name
        records = [json.loads(line) for line in (directory / "records.jsonl").read_text().splitlines()
                   if line.strip()]
        check(len(records) == 1, "one_rescored_record:" + name)
        row = records[0]
        check(set(row) == set(entry["delivered_row"]) | {"provider_final_content"},
              "only_one_appended_field:" + name)
        check(row.get("provider_final_content") == content, "verbatim_provider_final_content:" + name)
        check(all(row.get(key) == value for key, value in entry["delivered_row"].items()),
              "all_original_columns_preserved:" + name)
        result = read(directory / "RESULT.json")
        check(result == by_summary[(index, condition)], "summary_row_identity:" + name)
        for key in ("source_index", "condition", "response_id", "source_sha256", "request_sha256", "raw_body_sha256"):
            check(result.get(key) == entry[key], "rescore_linkage:" + name + ":" + key)
        check(result.get("provider_final_content_sha256") == digest(content.encode()),
              "final_content_hash:" + name)
        check(result.get("original_generated_ans_sha256") == digest(row["generated_ans"].encode()),
              "original_generated_text_hash:" + name)
        original_metric = result["original_metric_result"]
        rescored = result["rescored_metric_result"]
        old_primary = original_metric["primary_metric_result"]
        new_primary = rescored["primary_metric_result"]
        expected_key = "provider_final_content" if condition == "source_typed" else "generated_ans"
        check(result.get("prediction_key") == expected_key, "selected_prediction_key:" + name)
        check({key: value for key, value in new_primary.items() if key != "score"}
              == {key: value for key, value in old_primary.items() if key != "score"},
              "native_metric_configuration_and_denominator_preserved:" + name)
        check(rescored["num_samples"] == original_metric["num_samples"] == 1,
              "same_single_source_denominator:" + name)
        if condition == "source_typed":
            check(old_primary["score"] == 0 and new_primary["score"] == 1
                  and rescored["primary_metric_details"] == [1.0]
                  and original_metric["primary_metric_details"] == [0.0],
                  "typed_installed_native_repair:" + name)
        else:
            check(old_primary == new_primary and new_primary["scored_samples"] == 0
                  and new_primary["invalid_references"] == 1
                  and rescored["primary_metric_details"] == [None],
                  "original_gallery_unscorable_preserved:" + name)
        slots.append({"source_index": index, "condition": condition,
                      "response_id": raw["id"], "prediction_key": expected_key,
                      "source_and_all_original_columns_unchanged": True,
                      "original_native_score": old_primary["score"],
                      "rescored_native_score": new_primary["score"],
                      "native_scored_samples": new_primary["scored_samples"],
                      "interpretation": "UNSCORABLE_REFERENCE" if condition == "native_gallery" else "KNOWN_EXACT_MATCH_ONE"})
    check(len(response_ids) == len(set(response_ids)) == 4, "same_four_distinct_responses")
    return {"status": "PASS" if not errors else "FAIL", "rescore_run_id": RESCORE_RUN,
            "original_run_id": SOURCE_RUN, "rescore_archive_sha256": RESCORE_ARCHIVE_SHA,
            "source_archive_sha256": SOURCE_ARCHIVE_SHA,
            "protocol_sha256": PROTOCOL_SHA, "protocol_commit": PROTOCOL_COMMIT,
            "original_and_rescore_archive_members_preserved": preserved_members,
            "source_rows": 2, "preserved_response_slots": 4,
            "new_provider_calls": 0, "new_judge_calls": 0,
            "installed_metric_origins_unchanged": 2, "slots": slots, "errors": errors,
            "scope": "Independent reconciliation of retained engineering replay artifacts against original live captures. Expected effects were known before this replay. No independent source sample, model generation or provider dispatch occurred in the rescore workflow. Native metrics and original columns remain preserved."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rescore_root", type=Path)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source-archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.rescore_root, args.source_root, args.archive, args.source_archive)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "preserved_response_slots": 4,
                      "new_provider_calls": 0, "errors": report["errors"]}))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
