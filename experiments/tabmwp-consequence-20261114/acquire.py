from pathlib import Path
import json, hashlib, urllib.request, concurrent.futures, time
ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT/'acquisition.json').read_text())
out = ROOT.parent/'upstream'
def one(item):
    path, expected = item
    dest = out/path
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        data=dest.read_bytes()
    else:
        with urllib.request.urlopen('https://raw.githubusercontent.com/lupantech/PromptPG/'+manifest['source_rev']+'/'+path, timeout=50) as response:
            data=response.read()
    actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert actual==expected, (path,actual,expected)
    dest.write_bytes(data)
    return dict(path=path,bytes=len(data),git_blob_sha=actual,sha256=hashlib.sha256(data).hexdigest())
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for row in pool.map(one,manifest['blobs'].items()):
        rows.append(row)
        print(json.dumps(row),flush=True)
(ROOT/'acquisition-receipt.json').write_text(json.dumps(dict(revision=manifest['source_rev'],files=rows),indent=2)+'\n')

