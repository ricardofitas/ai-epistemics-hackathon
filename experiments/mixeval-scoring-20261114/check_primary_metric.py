from pathlib import Path
import sys,json,gzip
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'packages'))
from one_eval.metrics.common.general import compute_choice_accuracy
rows=lambda n:[json.loads(x) for x in gzip.decompress((P/n).read_bytes()).splitlines()]
source={(s['split'],s['source_index']):s['record'] for s in rows('input/SELECTED.jsonl.gz')};captures=rows('CAPTURES.jsonl.gz');ev=json.loads((P/'input/GALLERY_ENTRY.json').read_text())['meta']['evaluation'];out={}
for split in ['free_form','multiple_choice']:
 c=[c for c in captures if c['split']==split];records=[source[(x['split'],x['source_index'])] for x in c]
 report=compute_choice_accuracy([x['captured_text'] for x in c],[r['target'] for r in records],records=records,parser=ev['parser'],denominator=ev['denominator'],failure_policy=ev['failure_policy'])
 assert report['score']==0 and report['scored_samples']==0 and report['invalid_references']==len(c) and report['details']==[None]*len(c)
 out[split]=report
(P/'PRIMARY_METRIC_CHECK.json').write_text(json.dumps(dict(status='PASS',panels=out,ordinary_unmodified_import=True,ast_projection=False,meaning='Native primary metric reports numeric0with zero scored samples. This is not evidence of0model accuracy.'),indent=2)+'\n');print('Native original primary metric: both scores0, zero valid/scored denominators; all49references excluded')
