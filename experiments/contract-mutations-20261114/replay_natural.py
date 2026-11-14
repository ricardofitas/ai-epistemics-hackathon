"""Development regression: source-bound wrapper on already observed natural captures."""
import sys,json,gzip,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(ROOT))
from source_bound import audit_with_source
def read(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
panels=[]
for name in ['arc-challenge','openbookqa','mmlu','mmlu-pro']:
 folder=BASE/'work/holdout/capture'/name
 selected=read(folder/'SELECTED.jsonl.gz');records=read(folder/'CHECKER_REVIEWED.jsonl.gz')
 assert len(selected)==len(records)
 enriched=[]
 for s,r in zip(selected,records):
  source=s['record'];q=source.get('question',source.get('question_stem'))
  if name in ['arc-challenge','openbookqa']:
   opts=source['choices']['text'];pos=list(map(str,source['choices']['label'])).index(str(source['answerKey']))
  else:opts=source['choices'] if name=='mmlu' else source['options'];pos=int(source['answer'] if name=='mmlu' else source['answer_index'])
  enriched.append(dict(r,source_question=q,source_choices=opts,source_correct_index=pos))
 report=audit_with_source(enriched)
 panels.append(dict(benchmark=name,rows=len(records),report=report,original_capture_sha256=hashlib.sha256((folder/'CHECKER_REVIEWED.jsonl.gz').read_bytes()).hexdigest()))
result=dict(scope='Development regression on previously observed natural rows; not an independent holdout',provider_calls=0,panels=panels)
(ROOT/'NATURAL_REPLAY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

