"""Independent child-agent arithmetic/provenance check; no model or network calls."""
from pathlib import Path
from collections import Counter
import gzip,hashlib,json,re,string,zipfile

ROOT=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def normalize(x):
    s=x.lower().translate(str.maketrans('','',string.punctuation))
    return ' '.join(re.sub(r'\b(a|an|the)\b',' ',s).split())
def parse_final(text):
    matches=re.findall(r'<answer\b[^>]*>(.*?)</answer\s*>',text,flags=re.I|re.S)
    if matches:return matches[-1].strip(),'tag'
    lines=[x.strip() for x in text.strip().splitlines() if x.strip()]
    return (re.sub(r'^(?:final answer|answer)\s*:\s*','',lines[-1],flags=re.I).strip(),'last_line') if lines else ('','empty')
def f1(pred,gold):
    a,b=normalize(pred).split(),normalize(gold).split()
    n=sum((Counter(a)&Counter(b)).values())
    return 0 if n==0 else 2*n/(len(a)+len(b))
def dummy(text):
    return bool(re.fullmatch(r'(?:[\(\[]?a[\)\].:]?(?:\s*[-:.)]?\s*none(?: of the above)?)?|none(?: of the above)?)\s*[.!]?',text,re.I))
def payload(case,model,arm,index):
    instructions='Give the factual answer to the question in free form.' if arm.startswith('free') else 'Select the best answer from the provided options.'
    parts=['Answer the source question using its context when relevant.',instructions,'Question:\n'+case['question'],'Context:\n'+case['context']]
    if arm.endswith('none'):parts+=['Options:\nA. None']
    parts+=['Put your final answer in <answer>...</answer> tags.']
    return dict(model=model,input='\n\n'.join(parts),temperature=0,max_output_tokens=4096 if index%4 in (0,1) else 6144,
                stream=True,tools=[],agentic_memory=False,store=False,tool_choice='none')

def main():
    report=json.loads((ROOT/'RESULT.json').read_bytes())
    cases=json.loads((ROOT/'cases.json').read_bytes())
    ledger=[json.loads(x) for x in (ROOT/'OFFICIAL_SCORE_LEDGER.jsonl').read_bytes().splitlines()]
    witness=json.loads((ROOT/'WITNESS.json').read_bytes())
    archive_rows=json.loads((ROOT/'ACQUISITION.json').read_bytes())
    zip_file_members=0
    for archive in archive_rows:
        p=ROOT/'inputs'/(archive['name']+'.zip')
        assert sha(p.read_bytes())==archive['sha256']
        with zipfile.ZipFile(p) as z:
            for name in z.namelist():
                if name.endswith('/'):continue
                assert z.read(name)==(ROOT/'inputs'/archive['name']/name).read_bytes(),name
                zip_file_members+=1
    for name,expected in json.loads((ROOT/'SOURCE_PINS.json').read_bytes()).items():
        b=(ROOT/name).read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==expected
    raw_source=(ROOT/'squad-dev-original.json').read_bytes()
    assert hashlib.sha1(b'blob '+str(len(raw_source)).encode()+b'\0'+raw_source).hexdigest()=='e9a3f913ad1468ebe105b891334ca7b0bc0e2510'
    original={}
    for art in json.loads(raw_source)['data']:
        for para in art['paragraphs']:
            for qa in para['qas']:original[qa['id']]=(para['context'],qa)
    selected={c['id']:c for c in cases if c['dataset']=='squad'}
    for ident,c in selected.items():
        context,qa=original[ident]
        assert context==c['context'] and qa['question']==c['question']
        assert c['gold']==list(dict.fromkeys(a['text'] for a in qa['answers']))
        assert c['record_sha']==sha(canonical([context,qa]))
        assert all(context[a['answer_start']:a['answer_start']+len(a['text'])]==a['text'] for a in qa['answers'])
    attempts={};locations={}
    for p in (ROOT/'inputs').glob('contract-transfer-wave-*/s*/attempts.jsonl'):
        for line in p.read_bytes().splitlines():
            row=json.loads(line);key=row['key'],row['attempt'];assert key not in attempts
            attempts[key]=row;locations[key]=p.parent
    finals={}
    for key,row in sorted(attempts.items()):
        if row['key'] in finals:assert finals[row['key']]['http']==429
        finals[row['key']]=row
    index={};models=set();arms=set();unknown=0;terminals=0
    for row in ledger:
        case=cases[row['case_index']];assert case['dataset']=='squad' and case['id']==row['source_id']
        a=finals[row['key']];expected=payload(case,row['model'],row['arm'],row['case_index'])
        assert sha(canonical(expected))==a['request_sha']==row['request_sha']
        assert case['record_sha']==row['source_record_sha']
        known=bool(a['eligible']);assert known==row['eligible']
        if a.get('terminal_sha'):
            b=gzip.decompress((locations[(a['key'],a['attempt'])]/'terminal'/f"{a['key']}-{a['attempt']}.json.gz").read_bytes())
            assert sha(b)==a['terminal_sha'];terminal=json.loads(b)
            assert terminal['output_text']==a['text'] and sha(a['text'].encode())==a['output_sha']==row['output_sha']
            assert terminal['id']==a['response_id'] and terminal['model']==a['returned_model']==row['model']
            assert known==(a['http']==200 and terminal['status']=='completed')
            terminals+=1
        answer,extraction=parse_final(a.get('text',''));assert answer==row['final'] and extraction==row['extraction_route']
        if known:
            em=int(any(normalize(answer)==normalize(g) for g in case['gold']))
            partial=max(f1(answer,g) for g in case['gold'])
            assert em==row['official_em'] and abs(partial-row['official_f1'])<1e-12
            assert dummy(answer)==row['dummy']
        else:
            assert row['official_em'] is None and row['official_f1'] is None and row['dummy'] is None
            unknown+=1
        key=row['model'],case['id'],row['arm'];assert key not in index
        index[key]=row;models.add(row['model']);arms.add(row['arm'])
    assert len(selected)==100 and len(ledger)==1600 and len(models)==4 and len(arms)==4
    verified_pairs={}
    for model in models:
        counts=Counter()
        sums={}
        for arm in arms:
            rows=[index[(model,ident,arm)] for ident in selected]
            lo=sum(r['official_em'] or 0 for r in rows);missing=sum(not r['eligible'] for r in rows)
            f=sum(r['official_f1'] or 0 for r in rows)
            expected=report['summary'][model][arm]
            assert expected['official_em_lower']==lo and expected['official_em_upper']==lo+missing
            assert abs(expected['official_f1_lower']-f)<1e-10 and abs(expected['official_f1_upper']-(f+missing))<1e-10
            assert expected['unknown']==missing
            sums[arm]=(lo,lo+missing)
        for ident in selected:
            c=index[(model,ident,'choice_clear')];n=index[(model,ident,'choice_none')]
            if not(c['eligible'] and n['eligible']):counts['unknown_pair']+=1
            elif c['official_em'] and not n['official_em']:
                counts['clear_correct_none_wrong']+=1;counts['clear_correct_none_dummy']+=n['dummy']
            elif n['official_em'] and not c['official_em']:counts['none_correct_clear_wrong']+=1
            elif c['official_em']:counts['both_correct']+=1
            else:counts['both_wrong']+=1
        counts['drop_lower_pp']=sums['choice_clear'][0]-sums['choice_none'][1]
        counts['drop_upper_pp']=sums['choice_clear'][1]-sums['choice_none'][0]
        expected=report['pairs'][model]
        assert all(counts[k]==expected.get(k,0) for k in set(counts)|set(expected))
        verified_pairs[model]=dict(counts)
    w=selected[witness['source']['id']];assert w==witness['source']
    assert w['id']=='5711541350c2381900b54a70' and w['gold']==['British']
    assert 'British engineer Arthur Woolf' in w['context'] and w['question']=='What nationality was Arthur Woolf?'
    for block in witness['models']:
        model=block['model'];assert set(block['rows'])=={'choice_clear','choice_none','free_none'}
        for arm,row in block['rows'].items():assert row==index[(model,w['id'],arm)]
        assert normalize(block['rows']['choice_clear']['final'])=='british'
        assert normalize(block['rows']['free_none']['final'])=='british'
        assert dummy(block['rows']['choice_none']['final'])
        j=block['rows']['choice_clear']['case_index'];c=payload(w,model,'choice_clear',j);n=payload(w,model,'choice_none',j)
        assert n['input'].replace('Options:\nA. None\n\n','')==c['input']
        assert {k:v for k,v in n.items() if k!='input'}=={k:v for k,v in c.items() if k!='input'}
    assert len(witness['models'])==4
    assert report['complete']==1539 and report['unknown']==unknown==61
    assert report['closure']['one_eval_native_squad_generation']=='NOT_EXECUTED'
    assert report['closure']['natural_supported_native_fault_attribution']=='UNESTABLISHED'
    out=dict(status='PASS',reviewer='Independent child assistant, not human certification',
      zip_files_authenticated=len(archive_rows),extracted_zip_members_byte_checked=zip_file_members,
      source_cases_checked=100,planned_slots_checked=1600,terminal_objects_checked=terminals,
      complete=1539,unknown=61,witness_all_four_models_verified=True,
      paired_results=verified_pairs,
      findings=[
       'All four British/Arthur Woolf witness finals and source spans match authenticated raw captures.',
       'The only choice-arm request change is the deliberately added sole A. None option; free_none controls retain British.',
       'Normalized EM and F1 scores, missing-response extremes, pair counts and quoted bounds independently match.',
       'This is a controlled task-contract perturbation, not an information-equivalent format-only change.',
       'The official SQuAD scorer correctly penalizes wrong final answers relative to the original factual task; this analysis does not establish an official scorer bug.',
       'The official scorer execution revalidates existing captures/endpoints; it is not a new independent model experiment or new raw discovery.',
       'The stated scope accurately leaves ordinary native One-Eval SQuAD execution and changed published scientific conclusions unestablished.'
      ],new_model_calls=0,new_judge_calls=0,new_external_calls=0)
    (ROOT/'INDEPENDENT_AGENT_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
