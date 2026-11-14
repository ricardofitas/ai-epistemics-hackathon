"""Reproduce this four-wave snapshot offline; never contact an inference provider."""
import hashlib,json,pathlib,shutil,subprocess,sys,tempfile,zipfile
P=pathlib.Path(__file__).resolve().parent
meta=json.loads((P/'CAPTURE_PROVENANCE.json').read_text())
assert meta['available_waves']==[1,2,3,4] and meta['not_yet_available_waves']==[5,6,7,8]
with tempfile.TemporaryDirectory(prefix='epistemics-four-wave-') as tmp:
 root=pathlib.Path(tmp)
 shutil.copytree(P/'code',root/'code',ignore=shutil.ignore_patterns('capture','results','__pycache__'))
 (root/'artifacts').mkdir();(root/'code/capture').mkdir()
 for wave in meta['available_waves']:
  a=next(a for a in meta['artifacts'] if a['name']==f'contract-transfer-wave-{wave}-{meta["source_run"]}')
  archive=P/f'artifacts/wave{wave}.zip';b=archive.read_bytes()
  assert 'sha256:'+hashlib.sha256(b).hexdigest()==a['digest']
  shutil.copyfile(archive,root/f'artifacts/wave{wave}.zip')
  with zipfile.ZipFile(archive) as z:
   assert z.testzip() is None
   for n in z.namelist():
    part=pathlib.PurePosixPath(n)
    assert not part.is_absolute() and '..' not in part.parts and part.parts[0] in {f's{wave-1}-front',f's{wave-1}-back'}
   z.extractall(root/f'artifacts/wave{wave}')
  for d in (root/f'artifacts/wave{wave}').iterdir():shutil.copytree(d,root/'code/capture'/d.name)
 subprocess.run([sys.executable,str(root/'code/aggregate.py')],check=True,capture_output=True,text=True)
 actual=json.loads((root/'code/results/summary.json').read_text())
 expected=json.loads((P/'code/results/summary.json').read_text())
 assert actual==expected
 # A parameterized independent implementation rechecks all originals; it does not import production analyzers.
 for wave in meta['available_waves']:
  a=next(a for a in meta['artifacts'] if f'wave-{wave}-' in a['name'])
  subprocess.run([sys.executable,str(P/'independent_wave4/audit_wave.py'),'--run-root',str(root),'--wave',str(wave),'--output',str(root/f'verified{wave}'),'--zip-sha256',a['digest'].split(':')[1]],check=True,capture_output=True,text=True)
 # Finite observation boundary: uploaded waves only. Missing records do not prove remote slots unattempted.
 assert (actual['started_unique'],actual['eligible'],actual['explicit_429'])==(1600,1548,23)
 print(json.dumps(dict(status='PASS',uploaded_waves_verified=4,planned_waves=8,source_cases_visible=100,started_slots_visible=1600,complete_visible=1548,incomplete_visible=52,missing_artifact_slots=1600,new_provider_calls=0,full_study_complete=False)))
