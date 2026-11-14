from pathlib import Path
import sys,json,hashlib,collections,datetime
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import pyarrow,pyarrow.parquet as pq
from native.choice import ChoiceLetterParser
R=Path(__file__).parent
G=json.loads((R/'gallery.json').read_text())['benches'];P=ChoiceLetterParser()
out={'executed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pyarrow':pyarrow.__version__,'scope':'Reference parsing only, not model accuracy, ordinary metric, generation or CLI. Full fixed split; no sampling.','datasets':{}}
for name,key in [('medmcqa','medmcqa'),('medconceptsqa','medconcepts')]:
 b=next(b for b in G if b['bench_name']==name);cfg=b['meta']['evaluation']['parser'];km=b['meta']['key_mapping'];labelkey=km['input_label_key'];cols=[labelkey]+km['input_choices_key']+(['answer'] if name=='medconceptsqa' else [])
 files=sorted((R/'sources'/key).rglob('*.parquet'));ct=collections.Counter();labels=collections.Counter();witness=[]
 for f in files:
  t=pq.read_table(f,columns=cols);rows=t.to_pylist()
  for i,row in enumerate(rows):
   value=row[labelkey];labels[str(value)]+=1;ct['rows']+=1
   native=P.parse(value,config=cfg,record=row);expected=None
   if name=='medmcqa':
    # Pinned HF card declares stored ClassLabel names 0:a,1:b,2:c,3:d. Raw author JSON convention is not substituted.
    expected='ABCD'[value] if isinstance(value,int) and not isinstance(value,bool) and 0<=value<4 else None
   else:
    norm=lambda s:' '.join(str(s).split()).casefold()
    matches=['ABCD'[j] for j,k in enumerate(km['input_choices_key']) if norm(row[k])==norm(row['answer'])]
    ct['unique_answer_text_match' if len(matches)==1 else 'ambiguous_or_missing_answer_text']+=1
    if len(matches)==1:expected=matches[0]
   ct['native_parse_ok' if native.ok else 'native_parse_invalid']+=1
   if expected is None:ct['source_unknown']+=1
   else:
    ct['source_identified']+=1;ct['native_reference_agrees' if native.ok and native.normalized==expected else 'native_reference_disagrees']+=1
   # Prespecified naive global 1-based conversion, only applicable to numeric values.
   raw=str(value).strip();glob='ABCD'[int(raw)-1] if raw.isdigit() and 1<=int(raw)<=4 else None
   if raw.isdigit():
    ct['numeric_rows']+=1
    if expected is not None:ct['naive_one_based_agrees' if glob==expected else 'naive_one_based_disagrees_or_invalid']+=1
   if expected is not None and (not native.ok or native.normalized!=expected) and len(witness)<20:
    witness.append({'file':f.name,'row_ordinal':i,'raw_reference':value,'native':native.to_dict(),'expected_by_answer_text_or_ClassLabel':expected,'record_sha256':hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True).encode()).hexdigest()})
  del rows,t
 out['datasets'][name]={'counts':dict(ct),'stored_reference_counts':dict(labels),'witnesses':witness,'files':[{'path':str(f.relative_to(R)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files],'source_revision':json.loads((R/'sources'/f'{key}_metadata.json').read_text())['sha'],'config':cfg}
(R/'RESULT.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps(out,ensure_ascii=False)[:12000])
