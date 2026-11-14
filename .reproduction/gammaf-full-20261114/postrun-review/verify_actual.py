"""Read-only independent reconciliation of the completed reproduction artifact."""
import datetime,hashlib,json,math,pathlib,zipfile,xml.etree.ElementTree as ET
H=pathlib.Path(__file__).resolve().parent;A=H/'actual/extracted'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gitsha(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def equal(a,b):
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 if isinstance(a,(float,int)) and isinstance(b,(float,int)):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
 return a==b
archive=H/'actual/GAMMAF_full_reproduction_43616684768.zip'
archive_sha='9dd29ff3b8283fee0a5949075b5d322fb68a9a54b32801f9f76c05a99caea224'
assert sha(archive)==archive_sha
with zipfile.ZipFile(archive) as z:
 files=[i for i in z.infolist() if not i.is_dir()]
 assert len({i.filename for i in files})==len(files)
 for i in files:assert (A/i.filename).read_bytes()==z.read(i)
final=read(A/'FINAL.json');pref=read(A/'PREFLIGHT.json');boot=read(A/'BOOTSTRAP.json');tests=read(A/'TESTS.json');reported=read(A/'COMPARISON.json');new=read(A/'reproduced/results.json');run=read(H/'ACTUAL_RUN_PROVENANCE.json');protocol=read(H/'PROTOCOL.json')
assert final['run_id']=='43616684768' and final['execution_sha']=='80b5546034be2f854f637575b52016f5066c9262'
assert run['id']==43616684768 and run['head_sha']==final['execution_sha'] and run['head_branch']==protocol['execution_branch'] and run['run_attempt']==1 and run['event']=='push' and run['conclusion']=='success' and run['status']=='completed'
assert pref['protocol_sha256']==sha(H/'PROTOCOL.json') and pref['base_commit']==protocol['base_commit']
identities=read(H/'verification_inputs/original_checkout_identities.json')
assert set(pref['authenticated_checkout_files'])==set(identities) and len(identities)==13
for path,m in identities.items():assert pref['authenticated_checkout_files'][path]==m
for local,path in [('original_results.json','artifacts/results.json'),('original_source_manifest.json','swarmlab-gammaf/gammaf_handoff/gamma_sources.json')]:
 b=(H/'verification_inputs'/local).read_bytes();assert len(b)==identities[path]['bytes'] and gitsha(b)==identities[path]['git_blob'] and hashlib.sha256(b).hexdigest()==identities[path]['sha256']
old=read(H/'verification_inputs/original_results.json');source=read(H/'verification_inputs/original_source_manifest.json')
assert source['commit']==protocol['upstream_commit'] and source['repo']==protocol['upstream_repository']
expected={k:v for k,v in source['files'].items() if k!='summary'}
actual={r['key']:r for r in boot['verified']};assert len(actual)==len(boot['verified'])==28 and actual.keys()==expected.keys()
for key,rec in actual.items():
 for field in ['path','bytes','blob']:assert rec[field]==expected[key][field]
 assert len(rec['sha256'])==64 and all(c in '0123456789abcdef' for c in rec['sha256']) and rec['status']=='downloaded_verified'
assert sum(r['bytes'] for r in actual.values())==boot['total_bytes']==111232152
assert boot['status']=='PASS' and final['raw_files_verified']==28 and final['raw_bytes']==111232152
root=ET.parse(A/'junit.xml').getroot();cases=list(root.iter('testcase'));assert len(cases)==38
assert not any(list(c.iter('failure')) or list(c.iter('error')) or list(c.iter('skipped')) for c in cases)
count={k:sum(int(s.get(k,'0')) for s in root.iter('testsuite')) for k in ['tests','errors','failures','skipped']}
assert count==final['tests']=={k:tests[k] for k in count}=={'tests':38,'errors':0,'failures':0,'skipped':0} and tests['returncode']==0
assert '38 passed' in (A/'pytest.log').read_text()
assert (A/'patch_check.log').read_bytes()==(A/'patch_apply.log').read_bytes()==b''
checks={k+'_all_values':equal(old[k],new[k]) for k in ['clean','theory']}
for k in ['tuning','full','held_out','cells_16','within_stratum_delta_pp','strata','verdict']:
 checks['guard_'+k]=equal(old['guard'][k],new['guard'][k])
checks['guard_stats_same']=equal(old['guard']['stats'],new['guard']['stats'])
for k in ['events','control_events','contaminated_debates','detector_debates','control_debates','detector_rate_percent','control_rate_percent','by_task','by_graph','by_method','debates_with_event_by_round','examples']:
 checks['shadow_unchanged_'+k]=equal(old['shadow'][k],new['shadow'][k])
s=new['shadow'];checks['shadow_population_counts']=(s['detector_contaminated_debates'],s['control_contaminated_debates'],s['contaminated_debates'])==(217,323,540)
checks['shadow_correct_combined_rate']=equal(s['contamination_rate_percent'],100*540/6859)
checks['shadow_correct_combined_mean']=equal(s['mean_events_per_contaminated_debate'],1892/540)
checks['shadow_correct_detector_mean']=equal(s['detector_mean_events_per_contaminated_debate'],559/217)
checks['no_strict_six_method_superiority']=new['guard']['verdict']['beats_all_six_strictly'] is False
assert checks==reported['checks'] and len(checks)==27 and all(checks.values())
disc=new['clean']['discrepancy'];assert disc['totals']['disagreements']==227 and disc['totals']['false_credits']==156 and disc['totals']['missed_credits']==71 and disc['totals']['debates']==9600 and disc['controls']=={'debates':1600,'disagreements':0}
tuning=new['guard']['tuning'];assert tuning['tune_questions']==80 and tuning['held_questions']==320 and tuning['evaluated']==784 and tuning['tune_debates']==1920 and tuning['held_debates']==7680
log=(A/'runner.log').read_text();assert 'loaded 11200 debates' in log and 'trajectories: 11200 debates with a raw round grid' in log and 'reference match (227/156/71, 0 control): True' in log and "strict 'outperforms all six' claim is NOT supported" in log
assert final['frozen_original_results_unchanged'] is final['frozen_terminal_projection_unchanged'] is True
assert final['new_model_calls']==final['new_judge_calls']==boot['new_model_calls']==reported['new_model_calls']==reported['new_judge_calls']==0
figures=sorted(p.relative_to(A).as_posix() for p in A.rglob('*.png'))
result={'status':'PASS','verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':run['id'],'execution_sha':run['head_sha'],'run_provenance_independently_retrieved':True,'artifact_sha256':archive_sha,'artifact_files_exactly_match_extraction':len(files),'original_git_identities_verified':13,'source_manifest_authenticated':True,'raw_source_receipts_match_all28pinned_paths_sizes_blobs':True,'raw_files':28,'raw_bytes':111232152,'junit_testcases':38,'junit_failures':0,'junit_errors':0,'junit_skipped':0,'independently_recomputed_comparison_checks':27,'all_27_pass':True,'terminal_discrepancies':{'detector_debates':9600,'disagreements':227,'false_credits':156,'missed_credits':71,'control_debates':1600,'control_disagreements':0},'guard_verdict':new['guard']['verdict'],'shadow_corrected':{k:s[k] for k in ['detector_contaminated_debates','control_contaminated_debates','contaminated_debates','detector_rate_percent','control_rate_percent','contamination_rate_percent','mean_events_per_contaminated_debate','detector_mean_events_per_contaminated_debate']},'figures_present_despite_no_figures_flag':figures,'earlier_failures':'Workflow YAML/preflight setup failures occurred before source downloads/model use. They are engineering attempts, not model experiments or scientific results. Original source SHA pins were normalized text snapshots, corrected to authentic Gitblob identities; derivative patch EOF context corrected without semantic AST changes.','scope':'Independent artifact/receipt/aggregation verification without rerunning analysis or downloading raw sources. Sourcebyte authentication occurred in pinned GitHub runner; rawcache absent from uploaded artifact. Archived conversations, offline guard reaggregation, task-stratified retrospective holdout; no prospective/live superiority or message-causal claim.','new_model_calls':0,'new_judge_calls':0}
(H/'FINAL_INDEPENDENT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
