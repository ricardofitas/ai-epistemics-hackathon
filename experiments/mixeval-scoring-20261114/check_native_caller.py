"""Cross-check exact native rescore caller under documented existing AST scaffold."""
from pathlib import Path
import sys,json,gzip,os
P=Path(__file__).resolve().parent;sys.path[:0]=[str(P/'packages'),str(P/'input')]
import native_scaffold
import pandas as pd
pre,_=native_scaffold.load_native_classes();pre._rescore_choice_single.__globals__['os']=os
obj=pre.__new__(pre)
rows=lambda n:[json.loads(x) for x in gzip.decompress((P/n).read_bytes()).splitlines()]
source={(s['split'],s['source_index']):s['record'] for s in rows('input/SELECTED.jsonl.gz')};captures=rows('CAPTURES.jsonl.gz');reports={}
config=json.loads((P/'input/GALLERY_ENTRY.json').read_text())['meta']['evaluation']['parser']
for split in ['free_form','multiple_choice']:
 records=[]
 for c in captures:
  if c['split']!=split:continue
  records.append({**source[(split,c['source_index'])],'generated_ans':c['captured_text'],'eval_valid':True,'eval_score':0.0})
 f=P/(split+'_native_rescore.jsonl');pd.DataFrame(records).to_json(f,orient='records',lines=True,force_ascii=False)
 stats=obj._rescore_choice_single(str(f),str(P/(split+'_native_stats.json')),{},'generated_ans','target',config);reports[split]=stats
 assert stats['invalid_references']==len(records) and stats['valid_samples']==0
(P/'NATIVE_CALLER_CHECK.json').write_text(json.dumps(dict(status='PASS',panels=reports,scope='Exact native rescore method body under existing AST scaffold; ordinary original parser modules. No full installed OneEval engine.'),indent=2)+'\n');print('Native rescore caller agrees: all49 references excluded, denominator0 in each split')
