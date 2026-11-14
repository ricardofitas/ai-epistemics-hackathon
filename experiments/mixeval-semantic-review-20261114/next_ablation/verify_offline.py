import hashlib,importlib.util,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('analysis',ROOT/'analyze.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
plans=[json.loads(l) for l in (ROOT/'manifest.jsonl').read_text().splitlines()]
def fixture(f):return [{'trial_id':r['trial_id'],'request_sha256':r['request_sha256'],'verified_complete':True,'score':f(r)} for r in plans]
checks=[]
for name,f,expected in [('equal_allcorrect',lambda r:1,(0,0)),('pure_instruction',lambda r:int(r['instruction']=='free_form'),(1,0)),('pure_carrier',lambda r:int(r['options_carrier']=='absent'),(0,0)),('conjunction',lambda r:int(r['condition']=='free_form__absent'),(1,1))]:
 out=mod.analyze(fixture(f))
 for model,x in out['models'].items():
  assert x['contrasts']['instruction_freeform_minus_choice_at_absent']['lower']==expected[0]
  assert x['contrasts']['interaction_instruction_gain_absent_minus_present']['lower']==expected[1]
 checks.append(name)
allmissing=mod.analyze([])
for model,x in allmissing['models'].items():
 assert sum(y['unknown'] for y in x['counts'].values())==80
 assert x['contrasts']['interaction_instruction_gain_absent_minus_present']['lower']==-2
 assert x['contrasts']['interaction_instruction_gain_absent_minus_present']['upper']==2
checks.append('allmissing_preserves160slots_and_interaction_bounds')
f=fixture(lambda r:1)
for name,bad in [('duplicate',f+[f[0]]),('unknown_id',[{**f[0],'trial_id':'no'}]),('bad_hash',[{**f[0],'request_sha256':'wrong'}]),('unverified',[{**f[0],'verified_complete':False}])]:
 try:mod.analyze(bad)
 except ValueError:checks.append(name+'_rejected')
 else:raise AssertionError(name)
receipt={'status':'PASS','checks':checks,'new_model_calls':0,'new_judge_calls':0,'purpose':'Constructed offline verification of coverage, identity and factorial contrast arithmetic. Not empirical results.'}
(ROOT/'OFFLINE_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
