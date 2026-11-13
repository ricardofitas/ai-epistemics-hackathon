"""Independent body, raw terminal text and exact-source audit for model smoke."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def sha(x):return hashlib.sha256(x).hexdigest()

def main():
    source=ROOT.parent/'default_contract_model_capture_20261113'
    requests=[json.loads(x) for x in (source/'manifest.jsonl').read_text().splitlines()]
    records=[json.loads(x) for x in (source/'responses.jsonl').read_text().splitlines()]
    by_id={x['trial_id']:x for x in records}
    assert len(by_id)==len(records)==len(requests)==96
    checked=[]
    for request in requests:
        tid=request['trial_id'];record=by_id[tid]
        assert sha(canonical(request['request_payload']))==request['request_sha256']
        assert record.get('request_payload')==request['request_payload']
        assert record.get('request_sha256')==request['request_sha256']
        assert record.get('attempt_count')==1
        journal=source/'stream_journals'/(tid+'.jsonl')
        assert sha(journal.read_bytes())==record['stream_journal_sha256']
        frames=[json.loads(x) for x in journal.read_text().splitlines()]
        endings=[f for f in frames if f.get('event')=='capture_end']
        assert len(endings)==1 and endings[0]['http_status']==record['http_status']
        terminal=[]
        for frame in frames:
            data=frame.get('data')
            if not isinstance(data,dict):continue
            kind=data.get('type') or frame.get('event')
            if kind in ('response.completed','response.incomplete','response.failed','response.cancelled') and not frame.get('partial_frame') and isinstance(data.get('response'),dict):
                terminal.append(data['response'])
        if terminal:
            raw=terminal[-1];assert raw==record['raw_response']
            text='\n'.join(c['text'] for item in raw.get('output',[]) if isinstance(item,dict) and item.get('type')=='message' and item.get('role','assistant')=='assistant' for c in item.get('content',[]) if c.get('type')=='output_text' and isinstance(c.get('text'),str))
            if not text and isinstance(raw.get('output_text'),str):text=raw['output_text']
            if not record.get('used_delta_fallback'):
                assert text==record['output_text']
            assert raw.get('status')==record['response_status']
        assert sha(record['output_text'].encode())==record['output_text_sha256']
        checked.append({'trial_id':tid,'http_status':record['http_status'],'terminal_event':record.get('terminal_event'),
                        'request_and_text_and_journal_verified':True,'completed_nonempty':record.get('completed_nonempty')})
    ordered=sorted(records,key=lambda x:x['started_utc'])
    gaps=[(dt.datetime.fromisoformat(b['started_utc'])-dt.datetime.fromisoformat(a['started_utc'])).total_seconds() for a,b in zip(ordered,ordered[1:])]
    assert min(gaps)>4.9
    report={'checked':len(checked),'completed_nonempty':sum(bool(x['completed_nonempty']) for x in checked),
            'minimum_recorded_start_interval_seconds':min(gaps),
            'method':'Independent request canonicalization, journal hashes, terminal message text reconstruction; no transport module imported.',
            'attempts_per_request':1,'checks':checked}
    (ROOT/'results/MODEL_CAPTURE_INDEPENDENT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))

if __name__=='__main__':main()
