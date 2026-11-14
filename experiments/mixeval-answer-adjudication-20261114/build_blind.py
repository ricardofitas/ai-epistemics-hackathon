import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;I=P.parent/'package/real-generation'
H=lambda b:hashlib.sha256(b).hexdigest()
s={x['source_index']:x for x in json.load(open(I/'selected20.json'))}
a=json.load(open(I/'ANALYSIS_CAPTURES.json'));m={x['trial_id']:x for x in [json.loads(x) for x in (I/'manifest.jsonl').read_text().splitlines()]}
blind=[];mapping=[]
for row in a:
 tid=row['trial_id']; r=json.load(open(I/'api_artifacts'/(tid+'.json')));source=s[row['source_index']]['record'];oid=H(('fixed-final-audit-v1:'+tid).encode())[:20]
 complete=row['status']=='completed_scored' and row['score'] is not None
 mapping.append(dict(opaque_id=oid,**row,source_sha256=s[row['source_index']]['source_sha256'],output_sha256=H(r.get('output_text','').encode()),included=complete))
 if complete:blind.append(dict(opaque_id=oid,question=source['prompt'],context=source['context'],accepted_references=source['target'],output_text=r['output_text']))
blind.sort(key=lambda x:H(('order-v1:'+x['opaque_id']).encode()))
assert len(blind)==69 and len(mapping)==80 and sum(not x['included'] for x in mapping)==11
(P/'BLINDED_CASES.json').write_text(json.dumps(blind,ensure_ascii=False,indent=2)+'\n')
(P/'PRIVATE_MAPPING.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
(P/'INPUT_PROVENANCE.json').write_text(json.dumps({'archive_sha256':H((P.parent/'inputs/Epistemics_MixEval_integracao_e_geracao_emparelhada_20261114.zip').read_bytes()),'protocol_commit':'eee9572f4a45bd9479ccbe6dd7d9cd0c516454c5','blinded_cases':69,'capture_unknowns':11,'input_files':{str(x.relative_to(I)):H(x.read_bytes()) for x in [I/'selected20.json',I/'ANALYSIS_CAPTURES.json',I/'manifest.jsonl']},'blinded_sha256':H((P/'BLINDED_CASES.json').read_bytes())},indent=2)+'\n')
print('Prepared69blinded cases;11unknowns preserved; no text preview')
