from pathlib import Path
import hashlib
p=Path(__file__).resolve().parent
b=b''.join(x.read_bytes() for x in sorted((p/'raw').glob('results.zip.part*')))
assert hashlib.sha256(b).hexdigest()=='b1a4a40ea417a0faff8578cfe2cdbebc3f660516e1fb69ace580b807a1ad8bad'
(p/'results.zip').write_bytes(b)
print('Verified results.zip written')
