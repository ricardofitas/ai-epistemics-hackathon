"""Reproduce the source/identity audit and analyzer controls offline, without inference."""
from pathlib import Path
import zipfile,tarfile,io,base64,json,hashlib,subprocess,sys
R=Path(__file__).parent
z=R/'Epistemics_originalidade_e_replicacao_64_pares_20261115.zip';assert hashlib.sha256(z.read_bytes()).hexdigest()=='6b22df00a4c8b1b5b19f862a0966b0fa82b320ab7bb22e8036894390e1a25e3c'
with zipfile.ZipFile(z) as f:
 assert f.testzip() is None;assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in f.namelist());f.extractall(R/'originality/content')
for aid,sha in [('14137518822','eb18b401f553fcf9a8542c73a6ecfcfcf2c7e8004883e66ce8867cf5e72d37b9'),('14138164416','6d67f79cdf91f1a0cbef1a31fb4d40384de403d94fe624a1fcb6d32f21c9ae91')]:
 p=R/(aid+'.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  if aid=='14138164416':(R/'old_intents.jsonl').write_bytes(z.read('execution_track/capture/intent.jsonl'))
  else:
   assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(R/'frozen')
f=R/'frozen';raw=base64.b64decode(''.join(p.read_text() for p in sorted(f.glob('payload-*.b64'))),validate=True);assert hashlib.sha256(raw).hexdigest()=='2d1bb28fa38d9e63d2679e8de3135c6c4b69ccb59655d3b82627b38cb6e1cbbf'
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as t:
 for n in ['wino_track/cases.json','wino_track/manifest.jsonl']:
  p=R/'payload'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(n).read())
subprocess.run([sys.executable,str(R/'audit_replication.py')],check=True)
subprocess.run([sys.executable,str(R/'analyse_pair_replication.py'),'--self-test','--out',str(R/'ANALYZER_SELF_TEST.json')],check=True)
