from pathlib import Path
import sys,json,collections,hashlib
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import pyarrow.parquet as pq
R=Path(__file__).parent
res=json.loads((R/'RESULT.json').read_text());verify={}
for name,folder in [('medmcqa','medmcqa'),('medconceptsqa','medconcepts')]:
 c=collections.Counter(); n=collections.Counter()
 for f in sorted((R/'sources'/folder).rglob('*.parquet')):
  if name=='medmcqa':
   t=pq.read_table(f,columns=['cop']);feature=json.loads(t.schema.metadata[b'huggingface'])['info']['features']['cop'];assert feature=={'names':['a','b','c','d'],'_type':'ClassLabel'}
   n.update(str(x.as_py()) for x in t.column('cop'));c['rows']+=len(t);assert set(n)<=set('0123')
  else:
   t=pq.read_table(f,columns=['answer_id','answer','option1','option2','option3','option4'])
   for r in t.to_pylist():
    c['rows']+=1;n[str(r['answer_id'])]+=1
    norm=lambda x:' '.join(str(x).split()).casefold()
    choices=[norm(r['option'+str(i)]) for i in range(1,5)]
    matches=[i for i in range(4) if choices[i]==norm(r['answer'])]
    if len(matches)==1:c['unique']+=1;c['agrees' if r['answer_id']=='ABCD'[matches[0]] else 'disagrees']+=1
    else:c['unknown']+=1
 expected=res['datasets'][name];assert dict(n)==expected['stored_reference_counts'];assert c['rows']==expected['counts']['rows']
 if name=='medmcqa':assert expected['counts']['native_reference_agrees']==c['rows'];assert expected['counts']['naive_one_based_disagrees_or_invalid']==c['rows']
 else:
  assert c['unique']==expected['counts']['unique_answer_text_match'];assert c['agrees']==expected['counts'].get('native_reference_agrees',0);assert c['disagrees']==expected['counts'].get('native_reference_disagrees',0)
 verify[name]=dict(c)
(R/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps({'status':'PASS','method':'Separate source-schema and text-identity implementation; no native parser or production analyzer imported','results':verify},indent=2)+'\n');print(verify)
