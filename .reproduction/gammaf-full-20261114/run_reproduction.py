"""Bounded public-source bootstrap and offline reproduction; no model endpoints."""
from __future__ import annotations
import argparse, datetime, hashlib, json, math, os, pathlib, subprocess, sys, tempfile, time, urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
HANDOFF = ROOT/'swarmlab-gammaf/gammaf_handoff'
OUT = HERE/'out'
clock = time.monotonic
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name, data):
    OUT.mkdir(exist_ok=True); (OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise RuntimeError('Unexpected source redirect')
def blob_hash(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def acquire(entry, destination, url, *, opener=None, deadline=None):
    """Single-attempt bounded fetch; verify length and Git object before install."""
    if destination.exists():
        data=destination.read_bytes()
        if len(data)==entry['bytes'] and blob_hash(data)==entry['blob']:
            return {'status':'already_verified','bytes':len(data),'blob':entry['blob'],'sha256':hashlib.sha256(data).hexdigest()}
        raise ValueError('Existing source contradicts pinned manifest')
    request=urllib.request.Request(url,headers={'User-Agent':'GAMMAF-pinned-offline-reproduction/1'})
    op=opener or urllib.request.build_opener(NoRedirect())
    chunks=[];size=0
    with op.open(request,timeout=30) as response:
        if getattr(response,'status',200)!=200:raise ValueError('Source HTTP status')
        while True:
            if deadline is not None and clock()>=deadline:raise TimeoutError('Bootstrap deadline')
            chunk=response.read(65536)
            if not chunk:break
            size+=len(chunk)
            if size>entry['bytes']:raise ValueError('Source exceeds pinned byte count')
            chunks.append(chunk)
    data=b''.join(chunks)
    if len(data)!=entry['bytes'] or blob_hash(data)!=entry['blob']:raise ValueError('Source integrity mismatch')
    # Parse exactly the authenticated bytes before exposing them to the loader.
    decoded=json.loads(data)
    if not isinstance(decoded,dict) or not isinstance(decoded.get('items'),list):raise ValueError('Source schema')
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.verified-',dir=destination.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,destination)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return {'status':'downloaded_verified','bytes':len(data),'blob':entry['blob'],'sha256':hashlib.sha256(data).hexdigest()}
def bootstrap(protocol, deadline):
    manifest_path=HANDOFF/'gamma_sources.json'
    assert digest(manifest_path)==protocol['sources_manifest_sha256']
    manifest=json.loads(manifest_path.read_text());entries={k:v for k,v in manifest['files'].items() if k!='summary'}
    assert manifest['repo']=='pmateo-uc3m/GAMMAF' and manifest['commit']==protocol['upstream_commit']
    assert len(entries)==28 and sum(x['bytes'] for x in entries.values())==111232152
    done=[];write('BOOTSTRAP.json',{'status':'in_progress','utc':now(),'expected':28,'verified':done})
    for key,e in sorted(entries.items()):
        assert e['path'].startswith('experiments-Information-Sciences/experiment1/results/summary-exp1-scores/')
        assert '..' not in pathlib.PurePosixPath(e['path']).parts
        url='https://raw.githubusercontent.com/'+manifest['repo']+'/'+manifest['commit']+'/'+e['path']
        receipt=acquire(e,HANDOFF/'_source'/e['path'],url,deadline=deadline)
        done.append({'key':key,'path':e['path'],**receipt})
        write('BOOTSTRAP.json',{'status':'PASS' if len(done)==28 else 'in_progress','utc':now(),'expected':28,'verified':done,'total_bytes':sum(x['bytes'] for x in done),'new_model_calls':0})
    return done
def preflight():
    p=json.loads((HERE/'PROTOCOL.json').read_text())
    for name,expected in p['frozen_files'].items():assert digest(HERE/name)==expected,name
    assert digest(ROOT/p['workflow_path'])==p['workflow_sha256']
    assert digest(HANDOFF/'gamma_sources.json')==p['sources_manifest_sha256']
    assert digest(ROOT/'artifacts/results.json')==p['original_results_sha256']
    assert digest(HANDOFF/'gamma_debates.jsonl.gz')==p['terminal_projection_sha256']
    for path,expected in p['original_code_sha256'].items():assert digest(ROOT/path)==expected,path
    assert len(p['original_code_sha256'])>=8
    assert p['new_model_calls']==p['new_judge_calls']==0
    write('PREFLIGHT.json',{'status':'PASS','utc':now(),'protocol_sha256':digest(HERE/'PROTOCOL.json'),'base_commit':p['base_commit'],'new_model_calls':0})
    return p
def command(args, log, deadline):
    remaining=max(1,int(deadline-clock()))
    with (OUT/log).open('w') as stream:
        r=subprocess.run(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=remaining,check=False)
    return r.returncode
def same(a,b):
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11)
    if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b
def compare():
    old=json.loads((ROOT/'artifacts/results.json').read_text());new=json.loads((OUT/'reproduced/results.json').read_text())
    checks={}
    for key in ['clean','theory']:checks[key+'_all_values']=same(old[key],new[key])
    for key in ['tuning','full','held_out','cells_16','within_stratum_delta_pp','strata','verdict']:
        checks['guard_'+key]=same(old['guard'][key],new['guard'][key])
    checks['guard_stats_same']=same(old['guard']['stats'],new['guard']['stats'])
    # Original global shadow fields are intentionally corrected, not replicated.
    for key in ['events','control_events','contaminated_debates','detector_debates','control_debates','detector_rate_percent','control_rate_percent','by_task','by_graph','by_method','debates_with_event_by_round','examples']:
        checks['shadow_unchanged_'+key]=same(old['shadow'][key],new['shadow'][key])
    sh=new['shadow'];checks['shadow_population_counts']=(sh['detector_contaminated_debates'],sh['control_contaminated_debates'],sh['contaminated_debates'])==(217,323,540)
    checks['shadow_correct_combined_rate']=same(sh['contamination_rate_percent'],100*540/6859)
    checks['shadow_correct_combined_mean']=same(sh['mean_events_per_contaminated_debate'],1892/540)
    checks['shadow_correct_detector_mean']=same(sh['detector_mean_events_per_contaminated_debate'],559/217)
    checks['no_strict_six_method_superiority']=new['guard']['verdict']['beats_all_six_strictly'] is False
    # Inferential distribution version sensitivity is reported separately.
    material={k:v for k,v in checks.items() if k!='guard_stats_same'}
    result={'status':'PASS' if all(material.values()) else 'DIFFERENCES_REQUIRING_REVIEW','checks':checks,'guard_stats_status':'PASS' if checks['guard_stats_same'] else 'VERSION_OR_COMPUTATION_DIFFERENCE','shadow':{k:v for k,v in sh.items() if not isinstance(v,(list,dict))},'guard_verdict':new['guard']['verdict'],'scope':'Unchanged full runner after isolated aggregation patch, raw archived conversations; offline reaggregation, no model generation or new benchmark population','new_model_calls':0,'new_judge_calls':0}
    write('COMPARISON.json',result)
    return result
def run():
    started=clock();deadline=started+900;p=preflight()
    assert os.environ.get('GITHUB_RUN_ATTEMPT')=='1'
    assert os.environ.get('GITHUB_REF')=='refs/heads/'+p['execution_branch']
    launch=json.loads((HERE/'LAUNCH.json').read_text())
    assert launch['protocol_sha256']==digest(HERE/'PROTOCOL.json')
    assert launch['planned_model_calls']==launch['planned_judge_calls']==0
    assert launch['base_commit']==p['base_commit']
    bootstrap(p,deadline)
    assert command(['git','apply','--check',str(HERE/'shadow_population_accounting.patch')],'patch_check.log',deadline)==0
    assert command(['git','apply',str(HERE/'shadow_population_accounting.patch')],'patch_apply.log',deadline)==0
    tests=command([sys.executable,'-m','pytest','-q','tests','--junitxml='+str(OUT/'junit.xml')],'pytest.log',deadline)
    suite=ET.parse(OUT/'junit.xml').getroot();counts={k:sum(int(x.get(k,'0')) for x in suite.iter('testsuite')) for k in ['tests','errors','failures','skipped']}
    write('TESTS.json',{'returncode':tests,**counts,'raw_files_verified':28,'new_model_calls':0})
    if tests:raise RuntimeError('Archive or focused tests failed; inspect pytest.log')
    assert counts['tests']==38 and counts['errors']==counts['failures']==0
    rc=command([sys.executable,'scripts/run_hackathon_experiments.py','--handoff',str(HANDOFF),'--out',str(OUT/'reproduced'),'--only','all','--bootstrap','10000','--seed','20261112','--no-figures'],'runner.log',deadline)
    if rc:raise RuntimeError('Full runner failed; inspect runner.log')
    result=compare()
    assert digest(ROOT/'artifacts/results.json')==p['original_results_sha256']
    assert digest(HANDOFF/'gamma_debates.jsonl.gz')==p['terminal_projection_sha256']
    write('FINAL.json',{'status':result['status'],'utc':now(),'elapsed_seconds':clock()-started,'frozen_original_results_unchanged':True,'frozen_terminal_projection_unchanged':True,'raw_files_verified':28,'raw_bytes':111232152,'tests':counts,'new_model_calls':0,'new_judge_calls':0,'run_id':os.environ.get('GITHUB_RUN_ID'),'execution_sha':os.environ.get('GITHUB_SHA')})
def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['preflight','run']);a=parser.parse_args()
    try:preflight() if a.mode=='preflight' else run()
    except Exception as e:
        write('STOP.json',{'utc':now(),'error_type':type(e).__name__,'error':str(e),'new_model_calls':0,'new_judge_calls':0});raise
if __name__=='__main__':main()
