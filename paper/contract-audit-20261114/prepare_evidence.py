import json,hashlib,shutil,csv,zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent/'run0653_inputs'
OUT=Path(__file__).resolve().parent
sources={
'calibration.json':('OneEval_verificador_e_evidencia_externa_20261114','VALIDATION.json'),
'wino.json':('OneEval_verificador_e_evidencia_externa_20261114','panels/oneeval__winogrande__validation.report.json'),
'sciq.json':('OneEval_verificador_e_evidencia_externa_20261114','panels/oneeval__sciq__test.report.json'),
'labbench.json':('OneEval_verificador_e_evidencia_externa_20261114','panels/oneeval__lab-bench-language-agent-biology-benchmark__train.report.json'),
'external.json':('OneEval_verificador_e_evidencia_externa_20261114','RESEARCH_DECISION.json'),
'prospective.json':('OneEval_validacao_prospetiva_4_benchmarks_20261114','RESEARCH_STATUS.json'),
'splits.json':('OneEval_extensao_splits_completos_20261114','SUMMARY.json'),
'split_checks.json':('OneEval_extensao_splits_completos_20261114','INDEPENDENT_CHECKS.json'),
'factorization.json':('OneEval_decomposicao_scores_e_consumo_20261114','FACTORIZATION.json'),
'resources.json':('OneEval_decomposicao_scores_e_consumo_20261114','RESOURCE_RECONCILIATION.json'),
'capture.json':('OneEval_decomposicao_scores_e_consumo_20261114','CAPTURE_VERIFICATION.json'),
'mutations.json':('OneEval_mutacoes_e_verificador_v2_20261114','VERIFIED_ACCOUNTING.json'),
'harness.json':('Epistemics_LMHarness_contratos_de_pedidos_20261114','VERIFICATION.json')}
(OUT/'evidence').mkdir(exist_ok=True)
manifest={}
for target,(folder,name) in sources.items():
 data=(BASE/folder/name).read_bytes();parent_hash=hashlib.sha256(data).hexdigest()
 if target=='capture.json':
  value=json.loads(data);value.pop('checks',None);data=(json.dumps(value,indent=2)+'\n').encode()
 (OUT/'evidence'/target).write_bytes(data)
 manifest[target]=dict(source_archive=folder+'.zip',member=name,sha256=hashlib.sha256(data).hexdigest(),parent_member_sha256=parent_hash)
 if target=='capture.json':manifest[target]['transform']='Omit per-trial checks list; preserve all aggregate fields unchanged.'

with zipfile.ZipFile(BASE/'OneEval_decomposicao_scores_e_consumo_20261114/input/OneEval_ensaio_emparelhado_200_resultados_20261114.zip') as z:
 raw=z.read('oneeval_paired_20261114/RESULTS.json');value=json.loads(raw)
 subset={'unique_source_questions':value['unique_source_questions'],'independent_prompt_groups':value['independent_prompt_groups'],'raw_output_reference_replays':[r for r in value['raw_output_reference_replays'] if r['stratum']=='all_frozen_panel' and r['condition']=='corrected_prompt' and r['predictor']=='always_B']}
 data=(json.dumps(subset,indent=2)+'\n').encode();(OUT/'evidence/paired_constant_controls.json').write_bytes(data)
 manifest['paired_constant_controls.json']=dict(source_archive='OneEval_decomposicao_scores_e_consumo_20261114.zip/input/OneEval_ensaio_emparelhado_200_resultados_20261114.zip',member='oneeval_paired_20261114/RESULTS.json',parent_member_sha256=hashlib.sha256(raw).hexdigest(),transform='Keep source-question/group totals and the2 unchanged all-panel repaired-prompt always-B replay rows.',sha256=hashlib.sha256(data).hexdigest())
if (OUT/'evidence/native_integration.json').exists():
 data=(OUT/'evidence/native_integration.json').read_bytes()
 manifest['native_integration.json']=dict(source_archive='Epistemics_LMHarness_integracao_nativa_20261114.zip',member='SUMMARY.json',sha256=hashlib.sha256(data).hexdigest())
(OUT/'EVIDENCE_SOURCES.json').write_text(json.dumps(manifest,indent=2)+'\n')
claims=[
('C1','2','21 configurations;64119 record appearances;7 failed;14 passed','calibration.json','Known-fault calibration; overlapping records'),
('C2','2','1267 question-dependence failures;628 changed references;300 conflict groups;309 deterministic unavoidable errors','wino.json','Captured validation split and deterministic mapping only'),
('C3','2','400 prospective rows;2 initial adapter false alerts','prospective.json','Post-outcome whitespace adapter review retained'),
('C4','2','27346 additional rows;27746 total captured source rows;ARC1172;OpenBookQA500','splits.json;split_checks.json','Post-discovery extension; source sample counts not prevalence'),
('C5','3','200 requests;194 complete;Qwen+36..48pp;Gemma-10..82pp','capture.json;factorization.json','50 diagnostic questions in35 dependency groups'),
('C6','4','Same repaired outputs reference effects:Gemma42pp,Qwen40pp','factorization.json','Native heuristic parser fixed-output score; posthoc interaction'),
('C7','5','2200 synthetic variants from200 units;800 accepted altered cases in v1','mutations.json','Development diagnostics, not independent generalization'),
('C8','6','200 native rows;801 per-option objects;600 controlled carrier failures; installed task-path200/801/400 fixtures','harness.json;native_integration.json','Reused data; native-method projection and installed local-data task path; models/tokenizers untested'),
('C9','8','External affected run not verified','external.json','Search evidence does not establish absence')
]
with (OUT/'claim_evidence.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['claim_id','section','numerical_or_status_claim','evidence_files','qualification']);w.writerows(claims)
(OUT/'claims.json').write_text(json.dumps([dict(zip(['id','section','claim','evidence','qualification'],c)) for c in claims],indent=2)+'\n')

