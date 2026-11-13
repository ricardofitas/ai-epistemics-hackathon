"""Preserve exact backend package source and runtime, excluding unrelated web assets."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

root=Path(__file__).resolve().parent
engine=Path(sys.argv[1]).resolve()
commit=subprocess.check_output(['git','-C',str(engine),'rev-parse','HEAD'],text=True).strip()
assert commit=='59bb367bd8565f347266a48ac1230af0b5131b97'
subprocess.run(['git','-C',str(engine),'diff','--exit-code'],check=True)
names=subprocess.check_output(['git','-C',str(engine),'ls-files'],text=True).splitlines()
selected=[name for name in names if (name.startswith(('evalscope/','requirements/')) or name in ['pyproject.toml','setup.py','README.md','LICENSE']) and not name.startswith(('evalscope/web/dist/','evalscope/web/node_modules/'))]
archive=root/'EVALSCOPE_BACKEND_SOURCE.tar.gz'
receipts=[]
with tarfile.open(archive,'w:gz') as output:
    for name in selected:
        path=engine/name
        if not path.is_file():continue
        assert path.resolve().is_relative_to(engine)
        output.add(path,arcname=name,recursive=False)
        receipts.append({'path':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(root/'ENGINE_SOURCE_RECEIPTS.json').write_text(json.dumps({'commit':commit,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':receipts},indent=2)+'\n')
print('Backend source captured',len(receipts),'files',archive.stat().st_size,'bytes')
