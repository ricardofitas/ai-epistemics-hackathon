import copy, hashlib, json, os, pathlib, subprocess, sys, tempfile
SCRIPT=pathlib.Path(__file__).resolve().parent/'summarize_advice.py'

def put(path,obj,jsonl=False):
    path.write_text(''.join(json.dumps(x)+'\n' for x in obj) if jsonl else json.dumps(obj))
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def fixture():
    root=pathlib.Path(tempfile.mkdtemp(prefix='impact-synthetic-code-audit-'))
    cases=['synthetic_case_a','synthetic_case_b']; models=[f'synthetic_model_{x}' for x in range(4)]
    arms=['baseline','generic_verification','primary_source_facts']
    protocol={'allocation':{'client_attempts':72},'cases':cases,'models':models,'arms':arms}
    packet=[];key=[];enriched=[];a=[]
    for case in cases:
      for model in models:
       for arm in arms:
        for rep in range(1,4):
         i=len(packet)+1;rid=f'I{i:03d}';tid=f'synthetic_trial_{i:03d}';complete=i!=72
         response=f'Synthetic answer {i} with generic test evidence.'
         packet.append({'response_id':rid,'case_id':case,'response':response,'capture_complete':complete})
         key.append({'response_id':rid,'trial_id':tid})
         enriched.append({'trial_id':tid,'case_id':case,'requested_model':model,'arm':arm,'repetition':rep,'capture_complete':complete,'response':response})
         a.append({'response_id':rid,'unsupported_recommendation':'no' if complete else 'unscorable','actionable_aligned_plan':'yes' if complete else 'unscorable','exact_supporting_passages':[],'mechanisms':[]})
    put(root/'protocol.json',protocol);put(root/'manifest.jsonl',[],True)
    put(root/'review_packet.jsonl',packet,True);put(root/'review_key.jsonl',key,True);put(root/'responses_enriched.jsonl',enriched,True)
    put(root/'a.jsonl',a,True);put(root/'b.jsonl',a,True);put(root/'adjudication.json',{})
    freeze(root)
    return root

def freeze(root):
    put(root/'first_freeze.json',{'first_rating_sha256':{'a':digest(root/'a.jsonl'),'b':digest(root/'b.jsonl')},'packet_sha256':digest(root/'review_packet.jsonl'),'frozen_utc':'2026-11-13T00:00:00+00:00'})
def run(root,output=None):
    cmd=[sys.executable,'-B',str(SCRIPT),str(root),'--ratings-a',str(root/'a.jsonl'),'--ratings-b',str(root/'b.jsonl'),'--first-freeze',str(root/'first_freeze.json'),'--adjudication',str(root/'adjudication.json')]
    if output: cmd+=['--output',str(output)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    return {'returncode':result.returncode,'stderr':result.stderr.strip().splitlines()[-1:]}

def rows(root,name): return [json.loads(s) for s in (root/name).read_text().splitlines()]

def suite():
    results={}
    root=fixture();r=run(root);s=json.loads((root/'analysis_summary.json').read_text())
    results['valid_72_rows_24_cells_24_contrasts']={'pass':r['returncode']==0 and len(s['rows'])==72 and len(s['cells'])==24 and len(s['contrasts'])==24}
    cell=next(c for c in s['cells'] if c['complete']==2)
    results['incomplete_preserved_bounds']={'pass':s['capture_complete']==71 and cell['primary']['yes_lower']==0 and cell['primary']['yes_upper']==1/3 and cell['utility']['yes_lower']==2/3 and cell['utility']['yes_upper']==1}
    root=fixture();a=rows(root,'a.jsonl');a[0]['unsupported_recommendation']='yes';a[0]['exact_supporting_passages']=['Synthetic answer 1'];a[0]['mechanisms']=['other_material'];put(root/'a.jsonl',a,True);freeze(root)
    results['unadjudicated_primary_blocked']={'pass':run(root)['returncode']!=0}
    root=fixture();b=rows(root,'b.jsonl');b[0]['actionable_aligned_plan']='no';put(root/'b.jsonl',b,True);freeze(root)
    results['unadjudicated_utility_blocked']={'pass':run(root)['returncode']!=0}
    root=fixture();put(root/'adjudication.json',{'coordinator_dispositions':{'I001':'yes'}})
    r=run(root);results['consensus_no_promotion_requires_positive_mechanism']={'pass':r['returncode']!=0,'observed':r}
    root=fixture();put(root/'responses.jsonl',[{'synthetic_original':'must_survive'}],True);original=(root/'responses.jsonl').read_bytes();r=run(root,root/'responses.jsonl')
    results['raw_aggregate_protected']={'pass':r['returncode']!=0 and (root/'responses.jsonl').read_bytes()==original,'observed':r}
    root=fixture();r=run(root,root/'review_packet.jsonl');results['packet_protected']={'pass':r['returncode']!=0}
    root=fixture();put(root/'adjudication.json',{'coordinator_dispositions':{'I001':'yes'},'coordinator_mechanisms':{'I001':['other_material']}})
    results['explicit_positive_promotion_accepted']={'pass':run(root)['returncode']==0}
    for label in ['no','uncertain']:
      root=fixture()
      for filename in ['a.jsonl','b.jsonl']:
        data=rows(root,filename);data[0]['unsupported_recommendation']=label;data[0]['mechanisms']=['other_material'];put(root/filename,data,True)
      freeze(root);put(root/'adjudication.json',{'coordinator_dispositions':{'I001':'yes'}})
      results[f'consensus_{label}_positive_promotion_needs_coordinator_mechanism']={'pass':run(root)['returncode']!=0}
    for mapping in [[],{'other_material':'uncertain'}]:
      root=fixture();put(root/'adjudication.json',{'coordinator_dispositions':{'I001':'yes'},'coordinator_mechanisms':{'I001':mapping}})
      results['final_primary_yes_rejects_'+('empty' if isinstance(mapping,list) else 'uncertain')+'_mechanism']={'pass':run(root)['returncode']!=0}
    root=fixture();(root/'a.jsonl').write_text((root/'a.jsonl').read_text()+'\n')
    results['immutable_first_hash_rejected']={'pass':run(root)['returncode']!=0}
    for name in ['run_metadata.json','rubric.json','custom_protocol_source.txt','api_artifacts/synthetic.json','stream_journals/synthetic.jsonl']:
      root=fixture();target=root/name;target.parent.mkdir(exist_ok=True);target.write_text('Synthetic original input bytes.\n');original=target.read_bytes();r=run(root,target)
      results['output_protects_'+name]={'pass':r['returncode']!=0 and target.read_bytes()==original}
    for name in ['api_artifacts/new.json','stream_journals/new.jsonl']:
      root=fixture();target=root/name;target.parent.mkdir(exist_ok=True);r=run(root,target)
      results['output_protects_future_'+name]={'pass':r['returncode']!=0 and not target.exists()}
    root=fixture();target=root/'synthetic_analysis.py';r=run(root,target)
    results['python_output_rejected']={'pass':r['returncode']!=0 and not target.exists()}
    root=fixture();target=root/'custom_analysis.json';r=run(root,target)
    results['new_custom_analysis_output_accepted']={'pass':r['returncode']==0 and target.exists()}
    root=fixture();first=run(root);second=run(root)
    results['designated_summary_can_be_refreshed']={'pass':first['returncode']==0 and second['returncode']==0}
    root=fixture();target=root/'synthetic_original_source.json';target.write_text('Original synthetic source.\n');original=target.read_bytes();(root/'analysis_summary.json').symlink_to(target)
    results['designated_summary_symlink_rejected']={'pass':run(root)['returncode']!=0 and target.read_bytes()==original}
    root=fixture();data=rows(root,'responses_enriched.jsonl');data.pop();put(root/'responses_enriched.jsonl',data,True)
    results['missing_planned_capture_rejected']={'pass':run(root)['returncode']!=0}
    root=fixture();data=rows(root,'responses_enriched.jsonl');data[0]['response']='Changed synthetic capture text.';put(root/'responses_enriched.jsonl',data,True)
    results['packet_key_capture_text_mismatch_rejected']={'pass':run(root)['returncode']!=0}
    root=fixture();data=rows(root,'responses_enriched.jsonl');data[0]['repetition']=2;put(root/'responses_enriched.jsonl',data,True)
    results['duplicate_context_cell_rejected']={'pass':run(root)['returncode']!=0}
    root=fixture();proof=json.loads((root/'first_freeze.json').read_text());proof['packet_sha256']='0'*64;put(root/'first_freeze.json',proof)
    results['unbound_first_packet_rejected']={'pass':run(root)['returncode']!=0}
    root=fixture();data=rows(root,'a.jsonl');data[0]['unsupported_recommendation']='yes';data[0]['exact_supporting_passages']=['Synthetic answer 1'];data[0]['mechanisms']=['other_material'];put(root/'a.jsonl',data,True);freeze(root);(root/'review_key.jsonl').unlink();r=run(root)
    results['adjudication_checked_before_key_read']={'pass':r['returncode']!=0 and 'Explicit separate adjudication required' in str(r['stderr'])}
    return results

def capture_collector_suite():
    import importlib.util
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('synthetic_capture_audit_source',SCRIPT.parent/'capture_audit_source.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    root=fixture()
    captures=rows(root,'responses_enriched.jsonl')
    jobs=[];records=[]
    (root/'api_artifacts').mkdir();(root/'stream_journals').mkdir()
    for i,c in enumerate(captures,1):
      job={k:c[k] for k in ['trial_id','case_id','requested_model','arm','repetition']}
      job['request_payload']={'model':'synthetic_requested_model','input':f'Synthetic request {i}','stream':True}
      jobs.append(job);tid=job['trial_id']
      if i==72:
        raw={'trial_id':tid,'attempt_count':1,'local_capture_error':'Fabricated local capture failure','started_utc':'2026-11-13T00:00:01+00:00','output_text':''}
      else:
        provider={'status':'incomplete' if i==71 else 'completed','output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':f'Synthetic answer {i}.'}]}]}
        events=[{'event':'response.completed','data':{'type':'response.completed','response':provider}},
                {'event':'capture_end','http_status':200,'terminal_event':'response.completed','transport_error':None}]
        put(root/'stream_journals'/f'{tid}.jsonl',events,True)
        text=provider['output'][0]['content'][0]['text']
        raw={'trial_id':tid,'attempt_count':1,'request_payload':job['request_payload'],
             'request_sha256':audit.sha(audit.canonical(job['request_payload'])),'output_text':text,
             'output_text_sha256':audit.sha(text.encode()),'started_utc':'2026-11-13T00:00:01+00:00',
             'ended_utc':'2026-11-13T00:00:02+00:00','stream_journal_sha256':digest(root/'stream_journals'/f'{tid}.jsonl'),
             'terminal_event_seen':True,'used_delta_fallback':False,'stream_incomplete':False,
             'stream_format_deviation':False,'completed_nonempty':i!=71,'http_status':200,
             'terminal_event':'response.completed','transport_error':None,'stream_frame_count':1,'stream_json_error_count':0,
             'raw_response':provider,'response_status':provider['status']}
      records.append(raw);put(root/'api_artifacts'/f'{tid}.json',raw)
    put(root/'manifest.jsonl',jobs,True);put(root/'responses.jsonl',records,True)
    put(root/'run_metadata.json',{'requested':72,'recorded':72,'retries':0})
    for name in ['review_packet.jsonl','review_key.jsonl','responses_enriched.jsonl']:(root/name).unlink()
    cmd=[sys.executable,'-B',str(SCRIPT.parent/'collect_block.py'),str(root),'--freeze-commit','a'*40,'--freeze-time','2026-11-13T00:00:00+00:00','--manifest-sha256',digest(root/'manifest.jsonl'),'--advice-review']
    before={str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file()}
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: return {'synthetic_collector_executes':{'pass':False,'stderr':r.stderr}}
    enriched=rows(root,'responses_enriched.jsonl');packet=rows(root,'review_packet.jsonl');integrity=json.loads((root/'integrity.json').read_text())
    results={
      'all_72_complete_failed_captures_bookkept':{'pass':len(enriched)==72 and len(packet)==72 and integrity['attempted']==72 and integrity['capture_complete']==70 and integrity['capture_incomplete']==2},
      'provider_terminal_status_mismatch_retained_incomplete':{'pass':enriched[70]['capture_complete'] is False and enriched[70]['event_status_mismatch'] is True},
      'local_capture_failure_retained_unverifiable_incomplete':{'pass':enriched[71]['capture_complete'] is False and enriched[71]['capture_integrity']=='unverifiable_local_capture_error'},
      'synthetic_raw_evidence_not_modified':{'pass':all(digest(root/name)==value for name,value in before.items())}}
    packet_bytes=(root/'review_packet.jsonl').read_bytes();key_bytes=(root/'review_key.jsonl').read_bytes()
    r2=subprocess.run(cmd,capture_output=True,text=True)
    results['packet_key_idempotent']={'pass':r2.returncode==0 and packet_bytes==(root/'review_packet.jsonl').read_bytes() and key_bytes==(root/'review_key.jsonl').read_bytes()}
    first=jobs[0];raw=records[0];raw['request_sha256']='0'*64;put(root/'api_artifacts'/f"{first['trial_id']}.json",raw)
    try:
      audit.audit_capture(root,first,raw,audit.instant('2026-11-13T00:00:00+00:00'))
      rejected=False
    except ValueError as error:
      rejected='Wire hash mismatch' in str(error)
    results['changed_wire_hash_rejected']={'pass':rejected}
    return results

if __name__=='__main__':
    results={'analysis':suite(),'capture_collector':capture_collector_suite()}
    print(json.dumps(results,indent=2))
    raise SystemExit(0 if all(check['pass'] for group in results.values() for check in group.values()) else 1)
