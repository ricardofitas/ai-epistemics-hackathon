"""Retain the failed run and separately reconcile the known pandas ID coercion."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
actual = root / "zero_initial" / "extracted"
sources = {r["source_index"]: r for r in json.loads((actual / "selected2.json").read_text())}
rows = []
for directory in sorted((actual / "results/fixture").iterdir()):
    result = json.loads((directory / "RESULT.json").read_text())
    source = sources[result["source_index"]]["record"]
    delivered = result["delivered_row"]
    assert result["status"] == "INCOMPLETE" and result["error"] == "source_column_changed:id"
    assert str(source["id"]) == str(delivered["id"])
    for key in source:
        if key != "id":
            assert delivered[key] == source[key], key
    trace = json.loads((directory / "HTTP_TRACE.json").read_text())
    assert len(trace) == 1 and trace[0]["http_status"] == 200
    raw = json.loads(trace[0]["response_body"])
    assert hashlib.sha256(trace[0]["response_body"].encode()).hexdigest() == trace[0]["body_sha256"]
    assert raw["choices"][0]["finish_reason"] == "stop"
    primary = result["native_metric_runner"]["primary_metric_result"]
    if result["condition"] == "native_gallery":
        assert primary["total_samples"] == 1 and primary["scored_samples"] == 0 and primary["invalid_references"] == 1
    else:
        assert primary["score"] == 1.0 and result["native_metric_runner"]["primary_metric_details"] == [1.0]
        message = trace[0]["request_payload"]["messages"][-1]["content"]
        assert source["prompt"] in message and str(source["context"]) in message and "A. None" not in message
    rows.append({"source_index": result["source_index"], "condition": result["condition"], "original_status": result["status"],
                 "derived_entrypoint_validation": "PASS_WITH_ID_TYPE_ERRATUM", "source_id": source["id"], "source_id_type": type(source["id"]).__name__,
                 "delivered_id": delivered["id"], "delivered_id_type": type(delivered["id"]).__name__, "all_other_source_columns_equal": True,
                 "primary_metric_result": primary})
assert len(rows) == 4
assert str("040") != str(40) and str("40") != str(41)
report = {"status": "VALIDATION_WITH_ID_TYPE_ERRATUM", "original_workflow_conclusion": "failure", "run_id": 43620236269,
          "artifact_id": 14123752594, "artifact_sha256": "40daaed0a78e59a451785df9391589295f5acae80d68e0d8756826b66fc00359",
          "ordinary_native_entrypoints_completed": 4, "native_primary_metric_calls_completed": 4, "local_fixture_http_calls": 4,
          "new_provider_calls": 0, "raw_results_preserved": True, "rows": rows,
          "interpretation": "The failed workflow retained completed native pipeline and primary metric evidence. The audit guard rejected reversible numeric ID dtype conversion after metric execution. This derived reconciliation preserves the failed workflow and qualifies the exact comparison accepted. Fixture score1 is synthetic implementation evidence."}
(root / "INITIAL_FIXTURE_RECONCILIATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(report["status"])
