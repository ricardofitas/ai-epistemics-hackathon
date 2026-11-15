"""Offline replay of frozen hashes, first real terminals, and independent bounds. No API."""
from pathlib import Path
import zipfile,tarfile,base64,hashlib,json,io,subprocess,sys
R=Path(__file__).parent
pins={'14143821883':'08c940274d828ed297430e66f146c062a7b3bb4a3b3ba86a8d433b98e251374d','14144275362':'23ebd3b5cf2238182995813e14b54622494493f93f8d6d36352c75c3c426445f','14143324169':'4dc4294364484b32fa125445c9841cfb7f7494b37ab7f3dd5e588196f008f29a','14143559450':'ac19c5de71b73a636fb17a590c348ed8327c97577592616b695ac4f5f36488fa'}
for aid,h in pins.items():
 p=R/(aid+'.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()==h
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None;assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(R/aid)
 if aid in ['14143821883','14144275362']:
  f=R/aid;raw=base64.b64decode(''.join(p.read_text() for p in sorted(f.glob('payload-*.b64'))),validate=True);assert hashlib.sha256(raw).hexdigest()==json.load(open(f/'PAYLOAD_RECEIPT.json'))['payload_sha256']
  with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as t:
   assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and not m.issym() and not m.islnk() for m in t.getmembers());t.extractall(R/(aid+'_payload'),filter='data')
 else:
  for p in (R/aid).glob('*.zip'):
   with zipfile.ZipFile(p) as z:assert z.testzip() is None;assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(R/(aid+'_wave'))
subprocess.run([sys.executable,str(R/'verify_observation.py')],check=True)
ledger=[]
for line in (R/'14143324169_wave/analysis/LEDGER.jsonl').read_text().splitlines():
 r=json.loads(line)
 if r['complete']:ledger.append(dict(r,response_available=True,comparison_known=True))
(R/'KNOWN_NATIVE_LEDGER.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in ledger))
subprocess.run([sys.executable,str(R/'analyse_pair_replication.py'),'--spec',str(R/'14143821883_payload/confirmatory_wino/SELECTION_PREVIOUSLY_FIXED.json'),'--native-ledger',str(R/'KNOWN_NATIVE_LEDGER.jsonl'),'--out',str(R/'INDEPENDENT_WINO_BOUNDS.json')],check=True)
a=json.load(open(R/'INDEPENDENT_WINO_BOUNDS.json'));b=json.load(open(R/'14143324169_wave/analysis/RESULTS.json'));assert [100*x for x in a['primary_planned_pair_mean_identification_bounds']]==b['primary']['finite_planned_sharp_interaction_bounds_pp']
print('PASS exact initial response identities and fullplanned bounds; no model requests')
