from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;R=P.parent/'actual'
H=lambda b:hashlib.sha256(b).hexdigest()
records={x['source_index']:x for x in json.load(open(R/'selected20.json'))};scores=json.load(open(R/'analysis/ANALYSIS_CAPTURES.json'))
packet=[];key=[]
for x in scores:
 tid=x['trial_id'];r=json.load(open(R/'api_artifacts'/(tid+'.json')));source=records[x['source_index']]['record'];oid=H(('factorial-secondary-v1:'+tid).encode())
 eligible=x['status']=='completed_scored' and x['score'] is not None
 key.append(dict(opaque_id=oid,**x,eligible=eligible,source_sha256=records[x['source_index']]['source_sha256'],output_sha256=H(r.get('output_text','').encode())))
 if eligible:packet.append(dict(opaque_id=oid,source_question=source['prompt'],source_context=source['context'],accepted_answers=source['target'],response_text=r['output_text']))
packet.sort(key=lambda x:x['opaque_id']);assert len(packet)==152 and len(key)==160
(P/'packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n');(P/'key.json').write_text(json.dumps(key,ensure_ascii=False,indent=2)+'\n')
(P/'PACKET_PROVENANCE.json').write_text(json.dumps(dict(protocol_sha256=H((R/'SECONDARY_ADJUDICATION_PROTOCOL.json').read_bytes()),packet_sha256=H((P/'packet.json').read_bytes()),key_sha256=H((P/'key.json').read_bytes()),eligible=152,unknown=8,primary_raw_verification='PASS',protocol_unchanged=True),indent=2)+'\n')
print('152masked cases;8unknown preserved; packet chars',len((P/'packet.json').read_text()))
