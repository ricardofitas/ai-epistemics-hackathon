"""Offline reproduction from authenticated final/frozen originals. No API or model calls."""
from pathlib import Path,PurePosixPath
import zipfile,tarfile,base64,io,json,hashlib,subprocess,sys
R=Path(__file__).parent
spec={'14139829847':('final_capture','649c1ab2870df6642382e1e9c819d9529f0d1ce000dc8b19ac9b9a7184495847'),'14139407391':('14139407391','79fed862369fdfbb2a58533fc6065800f3e63c34656cd20d17b7b589f6155e12'),'14138164416':('14138164416','6d67f79cdf91f1a0cbef1a31fb4d40384de403d94fe624a1fcb6d32f21c9ae91'),'14138939635':('14138939635','db15efd1add202273dafcf759858369f00e9bc3ca20283618f4bb840391fb42c')}
for aid,(folder,expected) in spec.items():
 p=R/(aid+'.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None;assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in z.namelist());z.extractall(R/folder)
f=R/'14139407391';raw=base64.b64decode(''.join(p.read_text() for p in sorted(f.glob('payload-*.b64'))),validate=True);assert hashlib.sha256(raw).hexdigest()==json.load(open(f/'PAYLOAD_RECEIPT.json'))['payload_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as t:
 members=t.getmembers();assert all(not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and not m.issym() for m in members)
 for m in members:
  if m.isfile() or m.islnk():
   if m.islnk():assert not PurePosixPath(m.linkname).is_absolute() and '..' not in PurePosixPath(m.linkname).parts
   p=R/'payload'/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(m).read())
for script,args in [('verify_snapshot.py',['final_capture/compact_execution/capture']),('verify_fallback_witness.py',[]),('final_reconciliation.py',[])]:subprocess.run([sys.executable,str(R/script),*args],check=True)
print('PASS offline replay of final identities, outcomes, resource ledger and unchanged source extractor witness')
