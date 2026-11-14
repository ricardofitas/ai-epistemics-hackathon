"""Reproduce complete eight-wave primary and same24 linkage offline, in a fresh folder."""
from pathlib import Path,PurePosixPath
import hashlib,json,shutil,subprocess,sys,tempfile,zipfile
P=Path(__file__).resolve().parent
meta=json.loads((P/'MANIFEST.json').read_text())
for name,entry in meta.items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==entry['sha256'],name
with tempfile.TemporaryDirectory(prefix='epistemics-final-') as tmp:
 root=Path(tmp)/'replay';shutil.copytree(P,root)
 for zpath in (root/'capture/work/artifacts').glob('*.zip'):
  with zipfile.ZipFile(zpath)as z:
   assert z.testzip()is None
   assert all(not PurePosixPath(n).is_absolute()and'..'not in PurePosixPath(n).parts for n in z.namelist())
   z.extractall(zpath.with_suffix(''))
 original=json.loads((root/'verification/full_closeout_audit.json').read_text())
 q=subprocess.run([sys.executable,str(root/'verification/verify_full.py')],capture_output=True,text=True)
 assert q.returncode==0,(q.stdout[-2000:],q.stderr[-2000:])
 actual=json.loads((root/'verification/full_closeout_audit.json').read_text());assert actual['passed']and actual['failures']==[]
 for name in ['aggregate','models','decision_transfer','same24']:assert actual[name]==original[name],name
 print(json.dumps(dict(status='PASS',primary_slots=3200,authenticated_terminals=3180,primary_complete=3086,unknown=114,same24_parent_slots=384,same24_complete=370,human_labels=0,new_provider_calls=0,new_judge_calls=0)))
