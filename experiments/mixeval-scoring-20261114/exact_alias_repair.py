"""Exploratory source-exact-alias guard; primary official rule results stay unchanged."""
import json,gzip,hashlib,sys,random
from pathlib import Path
P=Path(__file__).resolve().parent
rows=lambda n:[json.loads(x) for x in gzip.decompress((P/n).read_bytes()).splitlines()]
sys.path[:0]=[str(P/'packages'),str(P)]
import source_typed_contract as contract
random.seed(42)
source={(s['split'],s['source_index']):s['record'] for s in rows('input/SELECTED.jsonl.gz')}
def apply(item,text):
 r=source[(item['split'],item['source_index'])];v=contract.evaluate(r,text,item['split']);assert v['original_official_rule_score']==item['typed']['score'];return v
real=[dict(split=c['split'],source_index=c['source_index'],public_row=c['public_row'],text_sha256=c['captured_text_sha256'],guard=apply(c,c['captured_text'])) for c in rows('CAPTURES.jsonl.gz')]
fixtures=[dict(split=c['split'],source_index=c['source_index'],fixture=c['fixture'],guard=apply(c,c['output'])) for c in rows('ORACLE_FIXTURES.jsonl.gz')]
report=dict(status='complete',stage='Exploratory exact-alias repair; not an independent validation',prior_official_rule_counterexamples_preserved=True,rule='If a freeform captured text equals an accepted source alias under edge trim/casefold, return1; otherwise retain original officialrule result. No change to original official files or initial experiment.',real_outputs=len(real),real_score_changes=sum(x['guard']['changed'] for x in real),real_typed_correct={split:sum(x['guard']['score'] for x in real if x['split']==split) for split in ['free_form','multiple_choice']},synthetic_oracle_fixtures=len(fixtures),synthetic_oracle_passes=sum(x['guard']['score'] for x in fixtures),synthetic_oracle_repairs=sum(x['guard']['changed'] for x in fixtures),new_model_requests=0,limits='Source aliases are an explicit trust assumption. This guard enforces exact accepted-answer reflexivity; it does not validate approximate rule-based semantic grading or default model-judge agreement.')
(P/'EXACT_ALIAS_REPAIR.json').write_text(json.dumps(dict(summary=report,real=real,fixtures=fixtures),indent=2)+'\n');print(json.dumps(report))
