"""Invoke the unmodified public metrics-stage CLI function on real-row fixtures."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import pandas as pd
import audit_contracts as audit

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value

def main():
    audit.load_components()
    common=module('_common',audit.ROOT/'upstream/_common.py')
    native_cli=module('native_public_metric_cli',audit.REPRO/'one-eval-skill/scripts/run_metrics.py')
    captured_gallery=gzip.decompress((audit.CAPTURE/'one_eval__utils__bench_table__bench_gallery.json.gz').read_bytes())
    lookup={x['bench_name']:x for x in json.loads(captured_gallery)['benches']}
    observations=[]
    with tempfile.TemporaryDirectory() as temporary:
        temp=Path(temporary)
        gallery_path=temp/'gallery.json';gallery_path.write_bytes(captured_gallery)
        common.BENCH_GALLERY_JSON=gallery_path
        common.CUSTOM_METRICS_DIR=temp/'no_custom_metrics'
        for bench,split,predictor in [('winogrande','validation','semantic_oracle_letter'),
                                      ('winogrande','validation','constant_B'),
                                      ('winogrande','test','constant_B'),
                                      ('sciq','test','constant_A'),
                                      ('lab-bench-language-agent-biology-benchmark','train','constant_A')]:
            raw=gzip.decompress((audit.CAPTURE/(bench+'__'+split+'.jsonl.gz')).read_bytes())
            source=[json.loads(x) for x in raw.splitlines()]
            path=temp/'native_rows.jsonl';path.write_bytes(raw)
            frame,mapping=audit.load_preprocessor()._preprocess_dataframe(pd.read_json(path,lines=True),bench,copy.deepcopy(lookup[bench]['meta']['key_mapping']),eval_type='key3_q_choices_a')
            records=frame.to_dict('records')
            for i,row in enumerate(records):
                answer=chr(65+int(source[i]['answer'])-1) if predictor=='semantic_oracle_letter' else predictor[-1]
                row['generated_ans']='<answer>'+answer+'</answer>'
            path.write_text(''.join(audit.compact(x)+'\n' for x in records))
            result_path=temp/'eval_results.json'
            result_path.write_text(json.dumps({'model':'constructed_diagnostic_control','results':[{'bench_name':bench,'bench_dataflow_eval_type':'key3_q_choices_a','ok':True,'detail_path':str(path),'key_mapping':mapping}]}))
            result=native_cli.run_metrics(str(result_path))
            primary=result['metric_results'][0]['primary_metric_result']
            assert Path(result['metric_results'][0]['primary_detail_path']).exists()
            observations.append({'bench':bench,'split':split,'predictor':predictor,
                                 'source':'Original public run_metrics.run_metrics; actual gallery file; constructed real-row fixture marked ok for metrics-stage replay.',
                                 'primary_metric_result':primary,'step3_file_written':True})
    report={'orchestration_scope':'Actual public metrics stage, excluding dataset acquisition/generation/evaluator. Gallery path and absent custom-metric directory are the only common-module configuration overrides.',
            'predictions_are_constructed_controls':True,'observations':observations}
    (audit.ROOT/'results/PUBLIC_METRIC_CLI_CONFIRMATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([{k:x[k] for k in ['bench','split','predictor','primary_metric_result']} for x in observations],indent=2))

if __name__=='__main__':main()
