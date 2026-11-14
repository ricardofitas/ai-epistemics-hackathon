"""Offline engineering capsule reproduction. Never executes a model endpoint."""
from pathlib import Path
import hashlib,json,zipfile,subprocess
ROOT=Path(__file__).resolve().parent
EXPECTED={
 'oneeval-native-live-43620987144.zip': 'd898dfd28a0d20708b2731a7fbd899d42aadddb5d0a1b2d1617a7c73c3eb47c8',
 'oneeval-native-offline-rescore-43621794887.zip': '63c982408b442dd5771f52a63cdfa492d5446c0e652eab7471d0b4ac0d0b49db',
}
def main():
 for name,folder in [('oneeval-native-live-43620987144.zip','real'),('oneeval-native-offline-rescore-43621794887.zip','rescore')]:
  p=ROOT/'inputs'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED[name],name
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None
   for n in z.namelist():assert not n.startswith('/') and '..' not in Path(n).parts
   z.extractall(ROOT/folder)
 commands=[['python','-m','unittest','discover','-s','work','-p','test_contract.py'],['python','-m','unittest','discover','-s','work','-p','test_gateway*.py'],['python','work/test_gateway_independent.py'],['python','work/replay_existing.py']]
 checks=[]
 for command in commands:
  p=subprocess.run(command,cwd=ROOT,text=True,capture_output=True);checks.append({'command':command,'exit_code':p.returncode});assert p.returncode==0,(command,p.stdout,p.stderr)
 for f in ['work/INDEPENDENT_GATEWAY_REVIEW.json','work/ARCHIVED_REGRESSION.json']:
  assert json.load(open(ROOT/f))['status']=='PASS'
 result={'status':'PASS','checks':checks,'new_provider_calls':0,'new_installed_native_calls':0,'scope':'Same-executor fresh capsule reproduction; engineering checks on exposed captures, not independent semantic validation.'}
 (ROOT/'PORTABLE_REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
