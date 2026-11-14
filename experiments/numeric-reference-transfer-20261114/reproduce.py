"""Download immutable originals, verify LFS hashes, then rerun offline reference checks. No models."""
from pathlib import Path
import json,hashlib,urllib.request,subprocess,sys
R=Path(__file__).parent
for key,repo in [('medmcqa','openlifescienceai/medmcqa'),('medconcepts','ofir408/MedConceptsQA')]:
 rev=json.loads((R/'sources'/f'{key}_metadata.json').read_text())['sha']
 for entry in json.loads((R/'sources'/f'{key}_file_metadata.json').read_text()):
  if entry['path'].endswith('.parquet') and ('validation-' in entry['path'] if key=='medmcqa' else 'test-' in entry['path']):
   p=R/'sources'/key/entry['path'];p.parent.mkdir(parents=True,exist_ok=True)
   if not p.exists():p.write_bytes(urllib.request.urlopen(f'https://huggingface.co/datasets/{repo}/resolve/{rev}/{entry["path"]}',timeout=120).read())
   assert p.stat().st_size==entry['size'];assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['lfs']['oid']
# pyarrow19.0.1 must be installed; optional local deps directory is supported.
subprocess.run([sys.executable,str(R/'evaluate.py')],check=True)
subprocess.run([sys.executable,str(R/'independent_verify.py')],check=True)
