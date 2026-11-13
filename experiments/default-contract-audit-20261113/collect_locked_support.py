"""Capture formatter/storage support source from the exact locked public wheel."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parent
lock=json.loads((ROOT/'LOCKED_DATAFLOW_WHEEL.json').read_text())
with urllib.request.urlopen(lock['url'],timeout=90) as response:raw=response.read(80_000_001)
assert len(raw)<=80_000_000
assert 'sha256:'+hashlib.sha256(raw).hexdigest()==lock['hash']
archive=zipfile.ZipFile(io.BytesIO(raw))
out=ROOT/'locked_support';out.mkdir(exist_ok=True)
receipts=[]
for name in archive.namelist():
    if not name.endswith('.py') or not name.startswith(('dataflow/prompts/','dataflow/core/','dataflow/utils/')):continue
    target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
    data=archive.read(name);target.write_bytes(data)
    receipts.append({'path':name,'sha256':hashlib.sha256(data).hexdigest()})
(out/'SOURCE_RECEIPTS.json').write_text(json.dumps({'wheel':lock,'files':receipts},indent=2)+'\n')
print('Locked formatter/storage sources captured:',len(receipts))
