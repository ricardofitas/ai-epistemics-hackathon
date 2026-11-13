"""Freeze a small, source-stratified consequence smoke test before model outputs."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT.parent / 'default_contract_source_capture_20261113' / 'capture'
MODELS = ['gemma-4-31b-it', 'qwen3.8-27b']

def compact(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def sha(x):
    return hashlib.sha256(x).hexdigest()

def main():
    out = ROOT / 'model_smoke'
    out.mkdir(exist_ok=True)
    dispositions = json.loads((CAPTURE / 'DATASET_DISPOSITIONS.json').read_text())
    gallery = json.loads((ROOT / 'GALLERY_SELECTED.json').read_text())
    gallery = {b['bench_name']: b for b in gallery['benches']}
    cases = []
    for bench, split, class_count in [('winogrande', 'validation', 2), ('sciq', 'test', 1), ('hellaswag', 'validation', 4)]:
        disposition = next(x for x in dispositions if x['bench']==bench and x['split']==split)
        raw = gzip.decompress((CAPTURE / disposition['rows_file']).read_bytes())
        assert sha(raw)==disposition['rows_sha256']
        rows = [json.loads(x) for x in raw.splitlines()]
        def label(row):
            return int(row['answer'])-1 if bench=='winogrande' else int(row['label']) if bench=='hellaswag' else 0
        groups = [[] for _ in range(class_count)]
        for index, row in enumerate(rows):
            key = sha(('default-contract-model-smoke-20261113|'+bench+'|'+str(index)+'|'+compact(row)).encode())
            groups[label(row)].append((key,index))
        selected = sorted(index for group in groups for _,index in sorted(group)[:12//class_count])
        assert len(selected)==12
        # Source selection is stratified by gold class without any model outcomes.
        for rank,index in enumerate(selected):
            row=rows[index]
            if bench=='winogrande':choices=[row['option1'],row['option2']]
            elif bench=='sciq':choices=[row[k] for k in ('correct_answer','distractor1','distractor2','distractor3')]
            else:choices=row['endings']
            variants=['native_order','balanced_order'] if bench=='sciq' else ['native_order']
            for variant in variants:
                shift=rank%4 if variant=='balanced_order' else 0
                displayed=choices[shift:]+choices[:shift]
                gold=(label(row)-shift)%len(choices)
                fields={**row,'choices_text':'\n'.join(chr(65+i)+'. '+str(value) for i,value in enumerate(displayed))}
                template=gallery[bench]['meta']['prompt']['user_template']
                prompt=template.format_map(fields)
                cases.append({'case_id':bench.replace('-','_')+'_'+str(index)+'_'+variant,
                              'bench':bench,'split':split,'row_index':index,'variant':variant,
                              'source_rows_sha256':disposition['rows_sha256'],
                              'source_row_sha256':sha(compact(row).encode()),'source_row':row,
                              'displayed_choices':displayed,'gold_letter':chr(65+gold),'prompt':prompt})
    requests=[]
    for case in cases:
        for model in MODELS:
            tid='DC-'+sha((case['case_id']+'|'+model).encode())[:18]
            payload={'model':model,'input':case['prompt'],'temperature':0,'max_output_tokens':4096,
                     'stream':True,'tools':[],'agentic_memory':False,'store':False,'tool_choice':'none'}
            requests.append({'trial_id':tid,'case_id':case['case_id'],'bench':case['bench'],
                             'variant':case['variant'],'gold_letter':case['gold_letter'],
                             'request_sha256':sha(compact(payload).encode()),'request_payload':payload})
    requests.sort(key=lambda x:sha(('default-contract-smoke-order|'+x['trial_id']).encode()))
    assert len(cases)==48 and len(requests)==96
    case_bytes=(json.dumps(cases,ensure_ascii=False,indent=2)+'\n').encode()
    request_bytes=(''.join(compact(x)+'\n' for x in requests)).encode()
    (out/'cases.json').write_bytes(case_bytes)
    (out/'manifest.jsonl').write_bytes(request_bytes)
    for name,data in [('cases.json',case_bytes),('manifest.jsonl',request_bytes)]:
        (out/(name+'.gz.b64')).write_text(base64.b64encode(gzip.compress(data,mtime=0)).decode()+'\n')
    protocol={'date':'2026-11-13','models':MODELS,'requests':96,'cases':48,'base_source_rows':36,
              'purpose':'Small prospective model-response consequence check after source-level defects were found; not a population performance estimate.',
              'source_selection':'Fixed SHA256 ordering within source gold classes, 12 rows per benchmark; WinoGrande balanced6/6 and HellaSwag3/3/3/3. SciQ12 source rows each tested in two option orders.',
              'prompt_scope':'Intended gallery user_template rendered directly from source fields and displayed choices. No One-Eval graph, download or native generator orchestration in this inference stage.',
              'conditions':['Winogrande labelled validation diagnostic override; native one-based reference versus explicit canonical gold','SciQ native correct-first option order versus balanced cyclic rotations, identical question/support','HellaSwag zero-based negative control'],
              'missing':'All96 planned requests retained; non-completed or unparseable outputs get bounded contribution0..1 for model comparison, never silently dropped.',
              'metrics':'Re-evaluate responses through original run_bench_with_contract with native gallery parser/field mapping, compare with strict answer-tag parsing and canonical gold. Report within-benchmark model versus fixed-letter baseline comparisons and each model independently.',
              'provider_policy':{'concurrency':1,'minimum_start_interval_seconds':5,'attempts_per_request':1,'retry':False},
              'hypothesis':'A real learned model can lose to a constant predictor under the broken reference mapping and win under corrected semantics; SciQ native constant-A benefit should collapse after balanced option order.',
              'inference_limit':'No new questions, model substitutions, or source-row replacement after outputs. Catalogue mismatch stops before model calls.',
              'frozen_files':{'cases.json':sha(case_bytes),'manifest.jsonl':sha(request_bytes)}}
    (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'requests':len(requests),'manifest_sha256':sha(request_bytes)}))

if __name__=='__main__':main()
