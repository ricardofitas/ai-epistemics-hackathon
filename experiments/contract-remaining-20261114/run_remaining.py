"""Execute a frozen, zero-provider-call expansion on previously unselected rows."""
import sys,json,gzip,hashlib,zipfile,shutil,importlib.util,traceback,datetime
from pathlib import Path
BASE=Path(sys.argv[1]).resolve()
OUT=Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True,exist_ok=True)
WORK=OUT/'work'
WORK.mkdir(exist_ok=True)
data=BASE/'artifact'
protocol=json.loads((OUT/'PROTOCOL.json').read_text())
def sha(x):return hashlib.sha256(x).hexdigest()
def read(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
def write(p,rows):
 raw=b''.join(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()+b'\n' for x in rows)
 p.write_bytes(gzip.compress(raw,mtime=0));return sha(raw)
support=data/'source_support.zip'
assert sha(support.read_bytes())==json.loads((data/'PROTOCOL.json').read_text())['source_support_sha256']
with zipfile.ZipFile(support) as z:z.extractall(WORK)
target=WORK/'holdout'
shutil.copytree(data,target,dirs_exist_ok=True)
sys.path.insert(0,str(BASE));sys.path.insert(0,str(target))
import audit_holdout as native
from choice_adapter import align_preserved_options
assert sha((WORK/'oneeval_contract_checker_20261114/check_contract.py').read_bytes())==protocol['frozen_checker_sha256']
native.audit.load_components()
gallery={e['bench_name']:e for e in json.loads((target/'GALLERY.json').read_text())['benches']}
dispositions=json.loads((target/'DISPOSITIONS.json').read_text())
reports=[]
for disposition in dispositions:
 name=disposition['benchmark']; folder=target/'capture'/name
 try:
  allrows=read(folder/'SOURCE_ROWS.jsonl.gz')
  old=read(folder/'SELECTED.jsonl.gz'); excluded={r['source_index'] for r in old}
  assert len(excluded)==100
  selected=[dict(source_index=i,source_sha256=sha(native.audit.compact(r).encode()),record=r) for i,r in enumerate(allrows) if i not in excluded]
  assert len(selected)+len(excluded)==len(allrows)
  disposition['selected_rows_sha256']=write(folder/'SELECTED.jsonl.gz',selected)
  native_result=native.audit_panel(gallery[name],disposition)
  records=read(folder/'CHECKER_NATIVE.jsonl.gz')
  revised=[align_preserved_options(r,*native.source_semantics(name,s['record'])[:2]) for r,s in zip(records,selected)]
  reviewed=native.audit_contract(revised)
  write(folder/'CHECKER_REVIEWED.jsonl.gz',revised)
  changed=[dict(row=i,source_index=selected[i]['source_index']) for i,(a,b) in enumerate(zip(records,revised)) if a!=b]
  result=dict(benchmark=name,status='completed',source_rows=len(allrows),excluded_previous_rows=len(excluded),new_rows=len(selected),selection_disjoint=True,
   native=native_result,reviewed_checker=reviewed,adapter_changed_rows=changed,
   source_capture_sha256=sha((folder/'SOURCE_ROWS.jsonl.gz').read_bytes()),selected_gzip_sha256=sha((folder/'SELECTED.jsonl.gz').read_bytes()))
 except Exception as e:
  result=dict(benchmark=name,status='execution_error',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
 reports.append(result)
 (OUT/'RESULTS.json').write_text(json.dumps(reports,indent=2,ensure_ascii=False)+'\n')
 print(name,result['status'],result.get('new_rows'),result.get('reviewed_checker',{}).get('failures'),flush=True)
(OUT/'EXECUTION.json').write_text(json.dumps(dict(completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),provider_model_calls=0,source_acquisition_requests=0,python=sys.version,panels=len(reports),errors=sum(x['status']!='completed' for x in reports)),indent=2)+'\n')

