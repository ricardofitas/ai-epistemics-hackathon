"""Independently verify exact request bodies, final text and streaming journals."""
from collections import Counter
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    capture = ROOT / 'capture'
    requests_bytes = gzip.decompress((ROOT / 'planned_requests.jsonl.gz').read_bytes())
    requests = [json.loads(line) for line in requests_bytes.splitlines()]
    protocol = json.loads((ROOT / 'EXECUTION_PROTOCOL.json').read_text())
    assert sha(requests_bytes) == protocol['manifest_uncompressed_sha256']
    assert sha((ROOT / 'fresh_panel.jsonl.gz').read_bytes()) == protocol['cases_compressed_sha256']
    assert (ROOT / 'fresh_panel.jsonl.gz').read_bytes() == (capture / 'fresh_panel.jsonl.gz').read_bytes()
    assert (capture / 'manifest.jsonl').read_bytes() == requests_bytes
    records_list = [json.loads(line) for line in (capture / 'responses.jsonl').read_text().splitlines()]
    records = {r['trial_id']: r for r in records_list}
    assert len(requests) == len(records_list) == len(records) == 200
    assert set(records) == {r['trial_id'] for r in requests}
    assert len(list((capture / 'api_artifacts').glob('*.json'))) == len(requests)
    checks = []
    for request in requests:
        tid = request['trial_id']
        record = records[tid]
        assert record['attempt_count'] == 1
        assert record['request_payload'] == request['request_payload']
        assert record['requested_model'] == request['request_payload']['model']
        if record.get('returned_model') is not None:
            assert record['returned_model'] == record['requested_model']
        artifact = json.loads((capture / 'api_artifacts' / (tid + '.json')).read_text())
        assert artifact == record
        assert sha(canonical(request['request_payload'])) == record['request_sha256']
        journal = capture / 'stream_journals' / (tid + '.jsonl')
        assert sha(journal.read_bytes()) == record['stream_journal_sha256']
        frames = [json.loads(line) for line in journal.read_text().splitlines()]
        ends = [frame for frame in frames if frame.get('event') == 'capture_end']
        assert len(ends) == 1 and ends[0]['http_status'] == record['http_status']
        terminals = []
        for frame in frames:
            data = frame.get('data')
            if not isinstance(data, dict):
                continue
            kind = data.get('type') or frame.get('event')
            if kind in ('response.completed', 'response.incomplete', 'response.failed', 'response.cancelled') and not frame.get('partial_frame'):
                if isinstance(data.get('response'), dict):
                    terminals.append(data['response'])
        if terminals:
            raw = terminals[-1]
            assert raw == record['raw_response']
            parts = []
            for message in raw.get('output', []):
                if message.get('type') != 'message' or message.get('role', 'assistant') != 'assistant':
                    continue
                parts.extend(c['text'] for c in message.get('content', []) if c.get('type') == 'output_text' and isinstance(c.get('text'), str))
            text = '\n'.join(parts)
            if not text and isinstance(raw.get('output_text'), str):
                text = raw['output_text']
            if not record.get('used_delta_fallback'):
                assert text == record['output_text']
            assert raw.get('status') == record['response_status']
        if record.get('completed_nonempty'):
            assert terminals and record['response_status'] == 'completed'
        assert sha(record['output_text'].encode()) == record['output_text_sha256']
        checks.append(dict(trial_id=tid, request_and_stream_verified=True, terminal_count=len(terminals),
                           completed=bool(record.get('completed_nonempty'))))
    ordered = sorted(records_list, key=lambda r: r['started_utc'])
    gaps = [(dt.datetime.fromisoformat(b['started_utc']) - dt.datetime.fromisoformat(a['started_utc'])).total_seconds()
            for a, b in zip(ordered, ordered[1:])]
    assert min(gaps) > 4.9
    receipt = json.loads((capture / 'EXECUTION_RECEIPT.json').read_text())
    assert receipt['planned'] == receipt['recorded'] == 200
    assert receipt['manifest_sha256'] == sha(requests_bytes)
    index = json.loads((capture / 'ARTIFACT_INDEX.json').read_text())
    assert index['credential_scan_passed'] is True
    for item in index['files']:
        path = capture / item['path']
        assert path.resolve().is_relative_to(capture.resolve())
        assert sha(path.read_bytes()) == item['sha256']
    result = dict(checked_trials=len(checks), complete=sum(r['completed'] for r in checks),
                  minimum_recorded_start_interval_seconds=min(gaps),
                  http_statuses=dict(Counter(str(r['http_status']) for r in records_list)),
                  response_statuses=dict(Counter(str(r['response_status']) for r in records_list)),
                  attempts_per_request=1, no_extra_artifacts=True, artifact_index_verified=True,
                  method='Independent standard-library JSON/SSE reconstruction; no transport module imported.', checks=checks)
    (ROOT / 'CAPTURE_VERIFICATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'checks'}, indent=2))


if __name__ == '__main__':
    main()
