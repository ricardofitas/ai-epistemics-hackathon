#!/usr/bin/env python3
"""Validate exact source metadata without joining runs to relevance labels."""
import argparse
from collections import Counter
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import runpy


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.directory
    module = runpy.run_path(str(root / 'evaluate_runs.py'), run_name='source_metadata_preflight_only')
    receipt = json.loads((root / 'source/download_receipt.json').read_text())
    registry = json.loads((root / 'candidate_registry.json').read_text())
    records = {r['run_tag']:r for r in receipt['records']}
    assert receipt['registry_sha256'] == digest((root / 'candidate_registry.json').read_bytes())
    qrecord = records['MATCHING_QRELS']
    qrels = root / 'source' / qrecord['local_file']
    assert digest(qrels.read_bytes()) == qrecord['sha256']
    topics = module['qrel_topics'](qrels)
    levels = Counter(line.split()[3] for line in qrels.read_text().splitlines() if line.strip())
    run_records = []
    for candidate in registry['candidates']:
        record = records[candidate['run_tag']]
        assert record['url'] == candidate['url'] and not record.get('error_type')
        raw = (root / 'source' / record['local_file']).read_bytes()
        assert digest(raw) == record['sha256']
        plain = gzip.decompress(raw)
        assert digest(plain) == record['uncompressed_sha256']
        structure = module['run_structure'](plain)
        run_records.append({'run_tag':candidate['run_tag'], 'metadata_status':'pass',
                            'row_count':structure['rows'], 'missing_topics':structure['missing_topics'],
                            'short_topics':structure['short_topics']})
    result = {'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'status':'PASS_SOURCE_METADATA_ONLY', 'source_records_verified':127,
              'qrels_sha256':qrecord['sha256'], 'qrels_topics':topics,
              'qrels_token_counts':dict(sorted(levels.items())),
              'judged_nonnegative_rows':sum(n for token,n in levels.items() if int(token)>=0),
              'unjudged_in_pool_markers':levels['-1'], 'run_count':len(run_records),
              'all_planned_runs_retained':len(run_records)==126,
              'run_metadata':run_records,
              'evaluator_sha256':digest((root / 'evaluate_runs.py').read_bytes()),
              'preflight_script_sha256':digest(Path(__file__).read_bytes()),
              'scorer_invoked':False, 'candidate_effectiveness_computed':False,
              'run_qrel_join_performed':False}
    output = args.output or root/'SOURCE_PREFLIGHT.json'
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'run_metadata','qrels_topics'}}))


if __name__=='__main__':
    main()
