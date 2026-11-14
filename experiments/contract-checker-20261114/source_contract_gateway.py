"""Bounded, offline-testable source -> wire capture -> provider final -> metric gate.

Engineering scope: MixEval free-form rows with explicit ``target`` aliases and
nonstream Chat Completions, using the archived native source-typed profile.
The native braces are intentional. This module performs no prompt repair,
reference-driven answer extraction, network I/O, retries, or model invocation.

Trust anchors are the caller's registry and transport callback. A callback must
return bytes it actually observed at transport (or a named archived capture),
not bytes reconstructed to satisfy this gate. Hash binding detects inconsistent
evidence; it does not prove provider origin, TLS/authentication, semantic answer
correctness, benchmark validity, or that an installed evaluator was executed.
Keep one SourceRegistry instance for a run: it owns the response-ID replay set.

Minimal archive fixture schema:
  selected: [{source_index, source_sha256, record: {id, problem_type:'free-form',
             prompt: str, context: str, target: [nonempty str, ...], ...}}]
  trace: {request_payload: dict, request_sha256: str, http_status: int,
          response_body: str, body_sha256: str, method:'POST', url: str}
  native_result: optional original RESULT.json (retained as a deep copy).
For exact archived request bytes use json.dumps(request_payload,
allow_nan=False).encode('utf-8'); separately verify its archived request hash.
This schema is sufficient for tests, not independent proof of capture origin.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
import math
import re
import threading
from typing import Any, Callable, Mapping

MODEL = 'qwen3.8-27b'
ENDPOINT = 'https://api.prod.adaptionlabs.ai/api/v1/chat/completions'
RENDERER_PROFILE = 'native_install_source_typed_v1_brace_preserving'
SYSTEM = 'You are a helpful assistant specialized in generating answers to questions.'
SUPPORTED_TASK = 'mixeval_freeform'
SUPPORTED_PROVIDER = 'chat_completions'


def canonical_bytes(value: Any) -> bytes:
    """Source/scorer value serialization; deliberately distinct from wire JSON."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_sha256(record: Mapping[str, Any]) -> str:
    return sha256(canonical_bytes(record))


def _digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _valid_record_id(value: Any) -> bool:
    return ((type(value) is str and bool(value.strip())) or
            (type(value) is int and value >= 0))


def _same_record_id(source_id: Any, delivered_id: Any) -> bool:
    """Only lossless canonical nonnegative integer str/int normalization."""
    if not _valid_record_id(source_id) or not _valid_record_id(delivered_id):
        return False
    if type(source_id) is type(delivered_id):
        return source_id == delivered_id
    text, number = ((source_id, delivered_id) if type(source_id) is str
                    else (delivered_id, source_id))
    return text == str(number)


@dataclass(frozen=True)
class PreparedRequest:
    """Immutable callback input; send body verbatim without JSON reserialization."""
    body: bytes
    request_sha256: str
    method: str = 'POST'
    url: str = ENDPOINT
    provider_type: str = SUPPORTED_PROVIDER


@dataclass(frozen=True)
class TransportCapture:
    http_status: int
    actual_request_bytes: bytes
    response_bytes: bytes
    capture_label: str
    method: str = 'POST'
    url: str = ENDPOINT


class SourceRegistry:
    """Copied anchors keyed by (explicit identity, canonical source SHA-256).

    Construction copies records, so later caller mutation cannot rewrite trust.
    Invalid anchors are rejected by run_entrypoint before invoking transport.
    A registry is a run-scoped replay boundary; a fresh registry starts a new run.
    """
    def __init__(self, entries: Mapping[tuple[str, str], Mapping[str, Any]]):
        self._entries = copy.deepcopy(dict(entries))
        self._response_ids: set[str] = set()
        self._lock = threading.Lock()

    @classmethod
    def from_selected(cls, selected: list[dict[str, Any]]) -> 'SourceRegistry':
        entries = {}
        for entry in selected:
            key = (str(entry['source_index']), entry['source_sha256'])
            if key in entries:
                raise ValueError('duplicate_trusted_source_key')
            entries[key] = entry['record']
        return cls(entries)

    def _get(self, key: tuple[str, str]) -> Any:
        return copy.deepcopy(self._entries.get(key))

    def _claim_response_id(self, response_id: str) -> bool:
        with self._lock:
            if response_id in self._response_ids:
                return False
            self._response_ids.add(response_id)
            return True


def _native_payload(source: Mapping[str, Any]) -> dict[str, Any]:
    user = ('Context:\n{' + source['context'] + '}\n\nQuestion:\n{' +
            source['prompt'] + '}\nAnswer the question in free text. '
            'Output only the factual answer, without an answer tag.')
    # Order and float spelling reproduce requests' archived JSON encoder.
    return {'model': MODEL, 'messages': [{'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': user}], 'top_p': 1.0,
            'max_tokens': 4096, 'temperature': 0.0}


def _numeric(value: Any) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _loads_unique(raw: bytes) -> Any:
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('nonfinite_json_number')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=object_pairs,
                      parse_constant=invalid_constant)


def run_entrypoint(
    registry: SourceRegistry,
    source_key: tuple[str, str],
    source_record: Mapping[str, Any],
    reference: list[str],
    transport: Callable[[PreparedRequest], TransportCapture],
    *,
    task_type: str = SUPPORTED_TASK,
    provider_type: str = SUPPORTED_PROVIDER,
    native_request_bytes: bytes | None = None,
    delivered_row: Mapping[str, Any] | None = None,
    original_native_result: Any = None,
    metric_adapter: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
    scorer_sha256: str | None = None,
) -> dict[str, Any]:
    """Own the full gate; every failure is a report, with at most one transport.

    ``source_key`` is ``(str(source_index), source_sha256)``. ``reference`` must
    equal the trusted alias list exactly, including order. Optional supplied
    native wire bytes must equal this renderer's bytes exactly. A delivered row
    may normalize only id via canonical nonnegative integer str/int roundtrip;
    every other trusted source
    field must survive unchanged. Existing provider_final_content is rejected.

    A metric callback receives an isolated copy of the row, with only the new
    provider_final_content column. Its caller-supplied scorer_sha256 identifies
    the scorer implementation/configuration manifest, not its metric result.
    Output keeps separate source, request, response, final, scorer and result
    hashes. Numeric aggregate scores require an eligible numeric per-row detail;
    e.g. aggregate zero with [None] is UNSCORABLE, never an observed zero score.
    Diagnostic scores are bounded to [0, 1] and must equal the single row's
    detail. Known counts must be integers in [0, 1]; null means unavailable.
    Registry lookup identity is separate from the source record's own id.
    """
    report: dict[str, Any] = {
        'status': 'INCOMPLETE', 'failures': [], 'transport_calls': 0,
        'metric_calls': 0, 'renderer_profile': RENDERER_PROFILE,
        'task_type': task_type, 'provider_type': provider_type,
        'source_key': copy.deepcopy(source_key), 'source_sha256': None,
        'request_sha256': None, 'response_sha256': None,
        'provider_final_content_sha256': None, 'scorer_sha256': scorer_sha256,
        'metric_result_sha256': None,
        'original_native_result': copy.deepcopy(original_native_result),
        'trust_scope': 'Caller-supplied registry and observed capture; no independent provider authentication or semantic correctness claim.',
    }

    def stop(code: str, status: str = 'INVALID') -> dict[str, Any]:
        report['status'] = status
        report['failures'].append(code)
        return report

    if task_type != SUPPORTED_TASK or provider_type != SUPPORTED_PROVIDER:
        return stop('unsupported_task_or_provider', 'INCOMPLETE')
    if not isinstance(registry, SourceRegistry):
        return stop('trusted_registry_unavailable', 'INCOMPLETE')
    if (not isinstance(source_key, tuple) or len(source_key) != 2 or
        not isinstance(source_key[0], str) or not source_key[0] or not _digest(source_key[1])):
        return stop('invalid_source_key')
    anchor = registry._get(source_key)
    if anchor is None:
        return stop('trusted_source_unavailable', 'INCOMPLETE')
    try:
        source = copy.deepcopy(dict(source_record))
        report['source_sha256'] = source_sha256(source)
        if source_sha256(anchor) != source_key[1] or report['source_sha256'] != source_key[1]:
            return stop('source_hash_mismatch')
        if canonical_bytes(source) != canonical_bytes(anchor):
            return stop('source_record_mismatch')
        if anchor.get('problem_type') != 'free-form':
            return stop('unsupported_source_problem_type', 'INCOMPLETE')
        if not _valid_record_id(anchor.get('id')):
            return stop('invalid_source_record_id')
        if not isinstance(anchor.get('prompt'), str) or not anchor['prompt'].strip():
            return stop('invalid_source_prompt')
        if not isinstance(anchor.get('context'), str):
            return stop('unsupported_context_type', 'INCOMPLETE')
        aliases = anchor.get('target')
        if (not isinstance(aliases, list) or not aliases or
            any(not isinstance(a, str) or not a.strip() for a in aliases)):
            return stop('invalid_alias_reference')
        if type(reference) is not list or canonical_bytes(reference) != canonical_bytes(aliases):
            return stop('reference_mismatch')
        if metric_adapter is not None and (not callable(metric_adapter) or not _digest(scorer_sha256)):
            return stop('scorer_identity_unavailable', 'INCOMPLETE')
        row = copy.deepcopy(source if delivered_row is None else dict(delivered_row))
        for key, value in anchor.items():
            if key not in row or (not _same_record_id(value, row[key]) if key == 'id' else canonical_bytes(row[key]) != canonical_bytes(value)):
                return stop('delivered_source_field_changed:' + key)
        if 'provider_final_content' in row:
            return stop('provider_final_column_already_exists')
        payload = _native_payload(anchor)
        body = json.dumps(payload, allow_nan=False).encode('utf-8')
        report['request_sha256'] = sha256(body)
        report['request_payload'] = copy.deepcopy(payload)
        report['request_bytes'] = body
        if native_request_bytes is not None and (type(native_request_bytes) is not bytes or native_request_bytes != body):
            return stop('native_request_profile_mismatch')
        if not callable(transport):
            return stop('transport_unavailable', 'INCOMPLETE')
    except (TypeError, ValueError, KeyError, OverflowError, UnicodeError):
        return stop('invalid_source_or_request')

    request = PreparedRequest(body=body, request_sha256=sha256(body))
    report['transport_calls'] = 1
    try:
        capture = transport(request)
    except Exception as exc:
        report['transport_error_type'] = type(exc).__name__
        return stop('transport_error', 'INCOMPLETE')
    if not isinstance(capture, TransportCapture):
        return stop('invalid_capture_type', 'INCOMPLETE')
    if type(capture.actual_request_bytes) is not bytes or type(capture.response_bytes) is not bytes:
        return stop('capture_bytes_unavailable', 'INCOMPLETE')
    report['actual_request_sha256'] = sha256(capture.actual_request_bytes)
    report['response_sha256'] = sha256(capture.response_bytes)
    report['raw_response_bytes'] = capture.response_bytes
    report['http_status'] = capture.http_status
    report['capture_label'] = capture.capture_label
    if not isinstance(capture.capture_label, str) or not capture.capture_label.strip():
        return stop('capture_provenance_unavailable', 'INCOMPLETE')
    if capture.actual_request_bytes != body or capture.method != request.method or capture.url != request.url:
        return stop('actual_request_binding_mismatch')
    if type(capture.http_status) is not int or capture.http_status != 200:
        return stop('non_200_http_status', 'INCOMPLETE')
    try:
        raw = _loads_unique(capture.response_bytes)
        report['raw_response'] = copy.deepcopy(raw)
        if not isinstance(raw, dict) or raw.get('object') != 'chat.completion':
            return stop('unsupported_response_object', 'INCOMPLETE')
        if 'error' in raw:
            return stop('provider_error_envelope', 'INCOMPLETE')
        if raw.get('model') != MODEL:
            return stop('response_model_mismatch')
        response_id = raw.get('id')
        if not isinstance(response_id, str) or not response_id.strip():
            return stop('missing_response_id')
        report['response_id'] = response_id
        # Claim observed IDs even for later incomplete responses. No retries.
        if not registry._claim_response_id(response_id):
            return stop('duplicate_response_id')
        choices = raw.get('choices')
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            return stop('ambiguous_or_missing_choice', 'INCOMPLETE')
        choice = choices[0]
        if type(choice.get('index')) is not int or choice['index'] != 0:
            return stop('invalid_choice_index')
        if choice.get('finish_reason') != 'stop':
            return stop('completion_not_stopped', 'INCOMPLETE')
        message = choice.get('message')
        if not isinstance(message, dict) or message.get('role') != 'assistant':
            return stop('invalid_assistant_message')
        if any(message.get(field) for field in
               ('tool_calls', 'function_call', 'audio', 'refusal', 'annotations')):
            return stop('unsupported_assistant_payload', 'INCOMPLETE')
        content = message.get('content')
        if not isinstance(content, str) or not content.strip():
            return stop('empty_or_nontext_final', 'INCOMPLETE')
        final_bytes = content.encode('utf-8')
    except (ValueError, TypeError, KeyError, UnicodeError):
        return stop('malformed_response', 'INCOMPLETE')

    row['provider_final_content'] = content  # Verbatim, never strip/parse tags.
    report['provider_final_content'] = content
    report['provider_final_content_sha256'] = sha256(final_bytes)
    report['delivered_row'] = copy.deepcopy(row)
    if metric_adapter is None:
        report['status'] = 'VERIFIED_WITHOUT_METRIC'
        return report
    report['metric_calls'] = 1
    try:
        metric = copy.deepcopy(metric_adapter(copy.deepcopy(row)))
        report['metric_result'] = metric
        report['metric_result_sha256'] = sha256(canonical_bytes(metric))
    except Exception as exc:
        report['metric_error_type'] = type(exc).__name__
        return stop('metric_adapter_error', 'INCOMPLETE')
    if not isinstance(metric, Mapping) or 'error' in metric:
        return stop('invalid_metric_result', 'UNSCORABLE')
    primary = metric.get('primary_metric_result')
    details = metric.get('primary_metric_details')
    if not isinstance(primary, Mapping) or not _numeric(primary.get('score')):
        return stop('metric_score_unavailable', 'UNSCORABLE')
    count_keys = ('total_samples', 'scored_samples', 'valid_predictions',
                  'parse_failed', 'empty_output', 'invalid_references',
                  'rescored_rows', 'num_samples')
    for container in (metric, primary):
        for key in count_keys:
            value = container.get(key)
            if value is not None and (type(value) is not int or not 0 <= value <= 1):
                return stop('invalid_metric_count:' + key, 'UNSCORABLE')
        for key in ('num_samples', 'total_samples'):
            if container.get(key) is not None and container[key] != 1:
                return stop('metric_sample_count_mismatch:' + key, 'UNSCORABLE')
        if (container.get('scored_samples') == 0 or container.get('valid_predictions') == 0 or
            any(container.get(key) == 1 for key in ('invalid_references', 'parse_failed', 'empty_output'))):
            return stop('no_eligible_per_row_metric_detail', 'UNSCORABLE')
    if (not isinstance(details, list) or len(details) != 1 or not _numeric(details[0]) or
        primary.get('scored_samples') == 0 or
        any(primary.get(key) == 1 for key in ('invalid_references', 'parse_failed', 'empty_output'))):
        return stop('no_eligible_per_row_metric_detail', 'UNSCORABLE')
    if not (0 <= primary['score'] <= 1 and 0 <= details[0] <= 1):
        return stop('diagnostic_metric_out_of_range', 'UNSCORABLE')
    if primary['score'] != details[0]:
        return stop('aggregate_detail_mismatch', 'UNSCORABLE')
    report['eligible_metric_score'] = primary['score']
    report['eligible_metric_rows'] = 1
    report['status'] = 'SCORED'
    return report


def make_installed_metric_runner_adapter(bench_configuration: Mapping[str, Any], records_path: str):
    """Return an explicit original One-Eval MetricRunner adapter (not tested here).

    On invocation, writes the supplied single row to the caller-selected path,
    then imports/calls the installed original runner; there is no substitute
    evaluator. Use a unique path per callback/run. Caller hashes its scorer
    implementation plus full configuration manifest for scorer_sha256.
    This helper cannot establish official MixEval judge compatibility.
    """
    from pathlib import Path
    config = copy.deepcopy(dict(bench_configuration))
    def adapter(row):
        from one_eval.core.state import BenchInfo
        from one_eval.metrics.runner import MetricRunner
        import one_eval.metrics.common.general  # ordinary metric registration
        path = Path(records_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation avoids accidentally replacing preserved artifacts.
        with path.open('xb') as stream:
            stream.write(canonical_bytes(row) + b'\n')
        local_config = copy.deepcopy(config)
        local_config['dataset_cache'] = str(path)
        meta = local_config.setdefault('meta', {})
        meta['artifact_paths'] = {'records': str(path)}
        meta['pred_key'] = 'provider_final_content'
        meta['ref_key'] = 'target'
        return MetricRunner(max_workers=1).run_bench_with_contract(
            BenchInfo(**local_config), copy.deepcopy(meta['evaluation']))
    return adapter
