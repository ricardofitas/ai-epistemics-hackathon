"""Serialize judgments made by root from the masked packet, before unmasking."""
import json,pathlib,datetime
p=pathlib.Path(__file__).resolve().parent
rows=[json.loads(l) for l in (p/'packet.jsonl').read_text().splitlines()]
final={0:'No',3:'Correct answer is 0.5 hours',4:'Smoke it.',7:'Lindisfarne (Holy Island)',11:'Prepare for the worst.',12:'but prepare for the worst.',16:'<answer>No</answer>',23:'Sommelier',24:'Sommelier',25:'Accounts',27:'Coal mining.',30:'Washington, D.C.',35:'25 years',36:'A diamond.',37:'Mark Twain',39:'Lindisfarne',42:'climates',43:'Washington, D.C.',45:'financial transactions',46:'Climate zones (world climates)',47:'Girls',50:'Coal miner',54:'No.',55:'25 years',57:'Fewer girls.',58:'Aromatherapy',59:'The Pike Place Market.',60:'Washington, D.C.',61:'<answer>No</answer>',62:'A diamond',66:'0.5 hours'}
content={**final,2:'unique to Buddhism',5:'2042 - 2017 = 25',8:'called **aromatherapy**',10:'correct answer (Pike Place Market)',13:'down by 0.5 hours',17:'called a **sommelier**',19:'was **Mark Twain**',22:'neighborhood in **Washington, D.C.**',29:'nightclubs and music venues',34:'there were fewer girls.',40:'occurs primarily in coal mining',48:'recording the increases and decreases in specific accounts',49:'so there were fewer girls.',63:'**Isle of Lindisfarne**',64:'quality and value of **diamonds**',65:'but prepare for the worst.',67:'tobacco used for smoking'}
out=[]
for i,r in enumerate(rows):
 text=r['response_text'];f='correct' if i in final else 'incorrect';c='correct' if i in content else 'incorrect'
 fe=final.get(i,text.strip()[-140:]);ce=content.get(i,'')
 assert fe in text and (not ce or ce in text),(i,fe,ce)
 reason='Explicit final factual answer agrees with source semantics.' if f=='correct' else ('Final choice tag does not identify a factual source answer; rationale separately assessed.' if '<answer>A' in text else 'Supplied answer does not endorse the source answer.')
 if i==26:reason='Blending tobacco is a different stated action from smoking it; smoking not explicitly endorsed.'
 if i==45:reason='Financial transactions/debits/credits/account balances describe the requested ledger accounts; accepted as direct semantic equivalent.'
 if i==29:reason='Music venues are explicitly identified in rationale; final tag remains non-informative.'
 out.append({'opaque_id':r['opaque_id'],'final_label':f,'content_label':c,'final_excerpt':fe,'content_excerpt':ce,'reason':reason})
(p/'reviewer_a.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in out))
(p/'REVIEWER_A_RECEIPT.json').write_text(json.dumps({'reviewer':'root assistant','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'masked_records_read':len(rows),'key_read_before_completion':False,'final_correct':len(final),'content_correct':len(content)},indent=2)+'\n')
print({'reviewed':len(rows),'final_correct':len(final),'content_correct':len(content)})
