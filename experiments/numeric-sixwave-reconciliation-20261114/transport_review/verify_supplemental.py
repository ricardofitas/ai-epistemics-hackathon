"""Offline supplemental review; no imports from production analyzers or option interpreter.
Does not amend the original failed checker report and does not create terminal records.
"""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction
import ast, gzip, hashlib, json, re

BASE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
RATES = {'gemma-4-31b-it': ('0.09','0.34'), 'qwen3.8-27b': ('0.039','1.25'),
         'deepseek-v4-flash': ('0.045','0.14'), 'glm-5.2': ('1.40','4.40')}
def read(p): return json.loads(p.read_text())
def lines(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok, why):
    if not ok: raise AssertionError(why)
original_path = BASE/'verified6/audit_result.json'
original_sha = sha(original_path)
original = read(original_path)
require(len(original['failures']) == 14, 'original failure count')
require({x['check'] for x in original['failures']} == {'missing_terminal_only_http429'}, 'original failure type')
failed_identities = {ast.literal_eval(x['detail']) for x in original['failures']}
wave_counts = {}; exception_rows = []; all_attempts = []; all_last = {}
for wave in range(1, 7):
    paths = sorted((BASE/f'work/artifacts/wave{wave}').glob('*/attempts.jsonl'))
    require(len(paths)==2, 'two sections per wave')
    wave_last = {}; sections = {}
    for path in paths:
        folder = path.parent
        attempts = lines(path); intents = lines(folder/'intent.jsonl')
        imap = {(x['key'], x['attempt']): x for x in intents}
        require(len(imap)==len(intents)==len(attempts), 'intent bijection')
        by_key = defaultdict(list); charge=Decimal(0); unknown_reserve=Decimal(0)
        for a in attempts:
            identity=(a['key'],a['attempt']); by_key[a['key']].append(a)
            require(identity in imap and a['request_sha']==imap[identity]['request_sha'], 'matching intent')
            u=a.get('usage') or {}; ip,op=map(Decimal,RATES[a['model']])
            if 'input_tokens' in u and 'output_tokens' in u:
                charge+=max((Decimal(u['input_tokens'])*ip+Decimal(u['output_tokens'])*op)/Decimal(1000000),Decimal(str(u.get('cost',0))))
            else:
                reserve=Decimal(str(imap[identity]['reserved'])); require(reserve>0,'positive full reservation')
                charge+=reserve
                if a['http']!=429: unknown_reserve+=reserve
            if not a.get('terminal_sha'):
                require(not a.get('eligible') and not u and not a.get('terminal_event'), 'nonterminal stays unknown')
                require(not (folder/'terminal'/f"{a['key']}-{a['attempt']}.json.gz").exists(), 'no fabricated terminal')
                if a['http']==429:
                    require(a['status']=='http_429', 'explicit 429 status')
                else:
                    require((a['http'],a['status']) in [(200,'missing_terminal'),(504,'http_504')], 'recorded transport unknown')
                    require(wave==6 and identity in failed_identities, 'exception corresponds to original failure')
                    exception_rows.append(dict(wave=wave,section=folder.name,key=a['key'],attempt=a['attempt'],http=a['http'],status=a['status'],eligible=False,frames=a['frames'],reservation=str(reserve)))
        last={}
        for key, group in by_key.items():
            group.sort(key=lambda x:x['attempt'])
            require([a['attempt'] for a in group]==list(range(1,len(group)+1)), 'contiguous attempts')
            require(all(a['http']==429 for a in group[:-1]), 'retry only explicit 429')
            require(len(group)<=3,'maximum three attempts')
            last[key]=group[-1]
        for row in exception_rows:
            if row['section']==folder.name:
                require(len(by_key[row['key']])==1,'no retry of unknown transport')
        progress=read(folder/'progress.json')
        require(abs(charge-Decimal(str(progress['reserved_or_spent_credits'])))<=Decimal('0.00000051'), 'conservative charge matches progress')
        require(charge<=Decimal(str(progress['ceiling_credits'])),'charge within ceiling')
        sections[folder.name]=dict(attempts=len(attempts),status=dict(Counter(a['status'] for a in last.values())),conservative_charge_decimal=str(charge),non429_unknown_reserved_decimal=str(unknown_reserve))
        wave_last.update(last); all_attempts.extend(attempts)
    require(len(wave_last)==400, '400 unique slots per wave')
    require(not(set(all_last)&set(wave_last)),'waves disjoint'); all_last.update(wave_last)
    wave_counts[str(wave)]=dict(started=len(wave_last),status=dict(Counter(a['status'] for a in wave_last.values())),sections=sections)
require(len(exception_rows)==14 and Counter(x['status'] for x in exception_rows)=={'missing_terminal':6,'http_504':8}, 'six plus eight transport unknowns')
require({(x['key'],x['attempt']) for x in exception_rows}==failed_identities,'all original failed identities accounted for')
require(sha(original_path)==original_sha,'original report preserved')
transport=dict(passed=True,scope='Supplemental validation of recorded transport unknowns across six uploaded waves, not a replacement of the original checker.',original_report_sha256=original_sha,original_report_failures_preserved=14,original_failure_check='missing_terminal_only_http429',waves=wave_counts,totals=dict(unique_started=len(all_last),attempts=len(all_attempts),status=dict(Counter(a['status'] for a in all_last.values())),http429_attempts=sum(a['http']==429 for a in all_attempts)),recorded_transport_unknowns=exception_rows,conclusion='The original assumption that only HTTP429 can lack a terminal is too strict. Six HTTP200 streams without terminal plus eight HTTP504 attempts remain ineligible unknowns; none was retried or given a fabricated terminal. Full per-attempt reservations are retained.',limitations=['No raw SSE bytes are present for independent stream rehashing.','Recorded transport labels do not establish provider-side outcomes or actual costs.','This review does not convert any missing, incomplete, or error outcome into a successful response.'])
(OUT/'transport_supplemental.json').write_text(json.dumps(transport,indent=2,sort_keys=True)+'\n')

# Independently select the 24 sources and decode final answers using only literal A and conservative numeric syntax.
cases=read(BASE/'work/code/cases.json')
selected=sorted([(i,c) for i,c in enumerate(cases) if 150<=i<200 and c['dataset']=='tabmwp'],key=lambda x:hashlib.sha256(('20261114-numeric-option-v1|'+x[1]['id']).encode()).hexdigest())[:24]
source_indices={i for i,c in selected}; models=list(RATES)
require(len(selected)==24,'24 selected source cases')
num_path=BASE/'work/artifacts/wavenumeric/capture/attempts.jsonl'
num_attempts=lines(num_path); last={}
for a in num_attempts:
    if a['key'] in last: require(last[a['key']]['http']==429,'numeric retry only 429')
    last[a['key']]=a
require(len(last)==192,'numeric 192 slots')
expected={f"tab-{c['id']}-{j}-{arm}" for i,c in selected for j,m in enumerate(models) for arm in ('correct','wrong')}
require(set(last)==expected,'independent source and slot selection')
num_regex=re.compile(r'[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:/\d+)?')
def parse_number(text,unit):
    s=text.strip().strip('*').strip().removesuffix('.').strip().replace('−','-')
    if unit.startswith('$'): s=s.removeprefix('$').strip()
    suffix=unit.strip().lstrip('$, ').strip()
    if suffix and s.casefold().endswith(' '+suffix.casefold()): s=s[:-len(suffix)].strip()
    if not num_regex.fullmatch(s): return None
    try:return Fraction(s.replace(',',''))
    except (ValueError,ZeroDivisionError):return None

def extract(text):
    matches=re.findall(r'<answer\b[^>]*>(.*?)</answer\s*>',text,re.I|re.S)
    if matches:return matches[-1].strip()
    ls=[x.strip() for x in text.strip().splitlines() if x.strip()]
    return re.sub(r'^(?:final answer|answer)\s*:\s*','',ls[-1],flags=re.I).strip() if ls else ''
pooled={a:Counter() for a in ('correct','wrong')}; by_model={m:{a:Counter() for a in ('correct','wrong')} for m in models}; exceptions=[]; primary=Counter()
for key,a in last.items():
    c=cases[a['case']]; require(a['case'] in source_indices,'selected numeric source')
    gold=parse_number(c['gold'][0],c['unit']); require(gold is not None,'parse gold')
    shown=gold if a['arm']=='correct' else gold+1
    stats=Counter(planned=1)
    if not a.get('eligible'):stats['unknown']=1
    else:
        raw=gzip.decompress((num_path.parent/'terminal'/f"{key}-{a['attempt']}.json.gz").read_bytes())
        require(hashlib.sha256(raw).hexdigest()==a['terminal_sha'],'numeric terminal sha')
        terminal=json.loads(raw);text=''.join(part.get('text','') for item in terminal.get('output',[]) if item.get('type')=='message' for part in item.get('content',[]) if part.get('type')=='output_text') or terminal.get('output_text') or ''
        require(text==a['text'] and terminal['status']=='completed','eligible numeric text/status')
        answer=extract(text); value=parse_number(answer,c['unit'])
        stats['complete']=1
        primary[a['arm']]+=int(value==gold)
        if re.fullmatch(r'(?:option\s+)?(?:\(a\)|\[a\]|a)[.:]?',answer,re.I):
            kind='letter';decoded=shown
        else:
            pref=re.fullmatch(r'(?:option\s+)?(?:\(a\)|\[a\]|a)\s*[.):-]?\s+(.+)',answer,re.I)
            if pref and parse_number(pref.group(1),c['unit'])==shown:kind='letter_and_number';decoded=shown
            elif value is not None:kind='number';decoded=value
            else:kind='other_text';decoded=None
        stats[kind]+=1;stats['displayed_option_endorsed']+=int(decoded==shown);stats['source_accurate']+=int(decoded==gold)
        if kind=='other_text':exceptions.append(dict(key=key,final_text=answer,gold=c['gold'][0],shown=str(shown),kind=kind))
    pooled[a['arm']].update(stats);by_model[a['model']][a['arm']].update(stats)
reference=read(BASE/'numeric_results/option-aware.json')
require(pooled==reference['pooled'],'pooled matches option-aware report')
require(by_model==reference['by_model'],'model results match option-aware report')
require({x['key'] for x in exceptions}=={x['key'] for x in reference['exceptions']},'same reserved other-text cases')
require(primary=={'correct':1,'wrong':30},'prespecified bare numeric endpoint retained')
num=dict(passed=True,method='Independent post hoc conservative option decode; no import or execution of interpret_options.py or production analyzers. Literal A maps to the unique shown value; A with value maps only when consistent; bare numeric parsed separately; other text remains unadjudicated.',pooled=pooled,by_model=by_model,source_indices=sorted(source_indices),source_count=24,models_per_source=4,arms_per_source_model=2,unit_of_independence='24 source questions; 96 source-model observations per arm are repeated across four models, not 96 independent sources.',primary_bare_numeric_correct=dict(primary),eligible=sum(a.get('eligible') is True for a in last.values()),planned=192,other_text=exceptions,reference_sha256=sha(BASE/'numeric_results/option-aware.json'),limitations=['Post hoc option-aware sensitivity analysis, not the prespecified primary endpoint.','Seven other-text completions remain reserved without broad semantic adjudication.','Four model responses per source do not supply four independent source replications.'])
(OUT/'numeric_option_independent.json').write_text(json.dumps(num,indent=2,sort_keys=True)+'\n')
print(json.dumps(dict(transport_passed=True,numeric_posthoc_passed=True,original_failures_preserved=14,sixwave_status=transport['totals']['status'],numeric_pooled=pooled,primary_bare_numeric_correct=primary),sort_keys=True))
