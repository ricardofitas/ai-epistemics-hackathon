"""Frozen-source transfer; stdlib; no provider, model or native engine execution."""
import json,hashlib,zipfile,urllib.request,gzip,copy,traceback
from pathlib import Path
from collections import Counter
from check_contract import audit_contract,guarded_inference,InvalidContract
from source_bound import audit_with_source,guarded_source_inference
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def save(n,v):(P/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def zipped(n,v):(P/n).write_bytes(gzip.compress(b''.join(canon(x)+b'\n' for x in v),mtime=0))
protocol=json.loads((P/'PROTOCOL.json').read_text());source=protocol['source'];attempts=[];errors=[];selected=[];results=[]
try:
 assert sha((P/'check_contract.py').read_bytes())==protocol['frozen_checker_sha256']
 assert sha((P/'source_bound.py').read_bytes())==protocol['frozen_wrapper_sha256']
 for name,url in [('official_loader.py','https://huggingface.co/datasets/allenai/social_i_qa/resolve/'+source['revision']+'/social_i_qa.py'),('official_archive.zip',source['official_archive'])]:
  try:
   with urllib.request.urlopen(url,timeout=45) as r:raw=r.read(10_000_001);status=r.status
   assert len(raw)<=10_000_000
   (P/name).write_bytes(raw);attempts.append(dict(url=url,status=status,bytes=len(raw),sha256=sha(raw)))
  except Exception as e:attempts.append(dict(url=url,status='ERROR',error=repr(e)));raise
 save('ACQUISITION.json',attempts)
 assert sha((P/'official_archive.zip').read_bytes())==source['expected_archive_sha256']
 z=zipfile.ZipFile(P/'official_archive.zip')
 def member(name):
  names=[x for x in z.namelist() if x.rsplit('/',1)[-1]==name];assert len(names)==1;return names[0]
 rowbytes=z.read(member(source['rows_member']));labelbytes=z.read(member(source['labels_member']))
 (P/'dev.jsonl').write_bytes(rowbytes);(P/'dev-labels.lst').write_bytes(labelbytes)
 rows=[json.loads(x) for x in rowbytes.splitlines()];labels=[int(x) for x in labelbytes.splitlines()];assert len(rows)==len(labels)
 inventory=[dict(source_index=i,record=r,label=y,source_sha256=sha(canon(dict(record=r,label=y)))) for i,(r,y) in enumerate(zip(rows,labels))]
 selected=sorted(inventory,key=lambda x:(x['source_sha256'],x['source_index']))[:100];zipped('SELECTED.jsonl.gz',selected)
 for s in selected:
  r=s['record'];y=s['label'];idx=s['source_index']
  for cond in protocol['conditions']:
   try:
    assert y in [1,2,3]
    ctx=r['context'];q=r['question'];opts=[r[k] for k in ['answerA','answerB','answerC']];pos=y-1
    assert all(isinstance(x,str) and x.strip() for x in [ctx,q]+opts)
    shown=list(opts);displaypos=pos
    if cond=='coherent_permutation':shown=opts[1:]+opts[:1];displaypos=(pos-1)%3
    elif cond=='distractor_drop':
     wrong=next(i for i in range(3) if i!=pos);shown.pop(wrong);displaypos=pos-int(wrong<pos)
    def render(c,question):
     if cond=='question_omission':question=''
     if cond=='context_omission':c=''
     return c+'\n'+question+'\n'+'\n'.join(chr(65+i)+'. '+v for i,v in enumerate(shown))+'\nSelect a letter.'
    prompt=render(ctx,q);label=chr(65+displaypos)
    rec=dict(schema_version=1,row_id=str(idx)+':'+cond,kind='choice',prompt=prompt,choices=shown,correct_text=opts[pos],expected_reference=label,reference=label,question_probe_changed=render(ctx,'QUESTION_NONCE_'+str(idx))!=prompt,context_required=True,context_probe_changed=render('CONTEXT_NONCE_'+str(idx),q)!=prompt,source_question=ctx+'\n'+q,source_choices=opts,source_correct_index=pos)
    if cond=='missing_source':
     for k in ['source_question','source_choices','source_correct_index']:rec.pop(k)
    a=audit_contract([rec]);b=audit_with_source([rec]);calls={}
    for name,gate in [('v1',guarded_inference),('v2',guarded_source_inference)]:
     seen=[]
     try:gate([rec],lambda prompts:seen.append(prompts))
     except InvalidContract:pass
     calls[name]=len(seen)
    results.append(dict(source_index=idx,condition=cond,record=rec,v1=a,v2=b,counting_function_invocations=calls,disposition='completed'))
   except Exception as e:results.append(dict(source_index=idx,condition=cond,disposition='ERROR',error=repr(e)));errors.append(dict(source_index=idx,condition=cond,error=repr(e)))
 summary=dict(status='completed_with_errors' if errors else 'completed',official_split_rows=len(rows),selected_source_rows=len(selected),unique_context_question_pairs=len({(s['record']['context'],s['record']['question']) for s in selected}),independent_context_groups=len({s['record']['context'] for s in selected}),condition_variants=len(results),new_model_calls=0,conditions=[dict(condition=c,rows=sum(x['condition']==c for x in results),statuses={v:dict(Counter(x[v]['status'] for x in results if x['condition']==c and x['disposition']=='completed')) for v in ['v1','v2']},counting_function_invocations={v:sum(x['counting_function_invocations'][v] for x in results if x['condition']==c and x['disposition']=='completed') for v in ['v1','v2']}) for c in protocol['conditions']],source_revision=source['revision'],source_archive_sha256=sha((P/'official_archive.zip').read_bytes()),scope=protocol['stage'],limits=[protocol['exposure_limit'],protocol['units'],'Known fault mechanisms applied to a held-out source family; custom adapter, not native evaluator fault discovery.'])
 zipped('RESULTS.jsonl.gz',results);save('SUMMARY.json',summary)
except Exception as e:errors.append(dict(stage='acquisition_or_setup',error=repr(e),traceback=traceback.format_exc()));save('SUMMARY.json',dict(status='blocked',new_model_calls=0,errors=errors))
finally:save('ACQUISITION.json',attempts);save('ERRORS.json',errors)
print((P/'SUMMARY.json').read_text())
