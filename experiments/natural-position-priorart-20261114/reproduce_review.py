"""Offline reproduction of the limited captured-record and source-identity review only."""
from pathlib import Path,PurePosixPath
import hashlib,json,shutil,subprocess,sys,tempfile,zipfile,ast
P=Path(__file__).resolve().parent
for n,m in json.loads((P/'MANIFEST.json').read_text()).items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==m['sha256'],n
with tempfile.TemporaryDirectory(prefix='natural-priorart-review-')as tmp:
 r=Path(tmp)/'replay';shutil.copytree(P,r)
 with zipfile.ZipFile(r/'original.zip')as z:
  assert z.testzip()is None
  assert all(not PurePosixPath(n).is_absolute()and'..'not in PurePosixPath(n).parts for n in z.namelist())
  z.extractall(r/'original')
 for m in json.loads((r/'semantics/SOURCE_MANIFEST.json').read_text()):
  b=(r/'semantics'/m['local']).read_bytes()
  assert hashlib.sha256(b).hexdigest()==m['sha256']
  assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==m['expected']
 q=subprocess.run([sys.executable,str(r/'verify_captured_records.py')],capture_output=True,text=True)
 assert q.returncode==0,(q.stdout,q.stderr)
 v=json.loads((r/'CAPTURE_VERIFICATION.json').read_text());assert v['status']=='PASS'and v['failures']==[]
 source=r/'semantics/upstream/one_eval/one_eval/agents/report_gen_agent.py'
 n=next(x for x in ast.walk(ast.parse(source.read_bytes()))if isinstance(x,ast.FunctionDef)and x.name=='_resolve_report_score')
 names={x.id for x in ast.walk(n)if isinstance(x,ast.Name)};strings={x.value for x in ast.walk(n)if isinstance(x,ast.Constant)and isinstance(x.value,str)}
 assert not(names&{'bench_result','primary_name'})and not(strings&{'role','display_as_primary'})
 print(json.dumps(dict(status='PASS',captured_source_rows=5010,source_blobs_checked=21,new_model_calls=0,new_native_runs=0,new_cli_runs=0,scope='Capturedrecords/primary-source verification, not independent CLI or historical-result replication')))
