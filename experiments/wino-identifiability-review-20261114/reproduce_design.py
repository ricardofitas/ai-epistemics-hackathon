"""Reproduce this design-only audit from the two original ZIPs, offline; no provider access."""
from pathlib import Path,PurePosixPath
import zipfile,tarfile,io,base64,hashlib,json,subprocess,sys
R=Path(__file__).parent
for aid,digest in [('14137518822','eb18b401f553fcf9a8542c73a6ecfcfcf2c7e8004883e66ce8867cf5e72d37b9'),('14137354329','e55450fc0d5a334794b2fe54604d9979670d164cd185b95cc583f21a7957d4a4')]:
 p=R/(aid+'.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None;assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in z.namelist());z.extractall(R/aid)
 root=R/aid;raw=base64.b64decode(''.join(p.read_text() for p in sorted(root.glob('payload-*.b64'))),validate=True)
 expected='2d1bb28fa38d9e63d2679e8de3135c6c4b69ccb59655d3b82627b38cb6e1cbbf' if aid=='14137518822' else json.load(open(root/'PAYLOAD_RECEIPT.json'))['sha256'];assert hashlib.sha256(raw).hexdigest()==expected
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as t:
  assert all(not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and not m.issym() and not m.islnk() for m in t.getmembers());t.extractall(R/(aid+'_payload'),filter='data')
subprocess.run([sys.executable,str(R/'audit_design.py')],check=True,stdout=subprocess.DEVNULL)
subprocess.run([sys.executable,str(R/'verify_bound_independent.py')],check=True)
