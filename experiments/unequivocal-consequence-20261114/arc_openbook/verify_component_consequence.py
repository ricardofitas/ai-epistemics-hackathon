"""Actual installed DataFlow generator + original OneEval metric imports.

Bounded component path: original preprocessing is a byte-authenticated archived
input, not re-executed here through DataFlowEvalTool's serving imports.
No AST scaffolds or provider calls in this verification.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from importlib import metadata
import copy,gzip,hashlib,json,os,re,string,sys,tempfile,zipfile

ROOT=Path(__file__).resolve().parent
os.environ['ONE_EVAL_LOG_FILE']=str(ROOT/'one_eval_component.log')
sys.path.insert(0,str(ROOT/'support/oneeval_alias_evidence_20261113'))
from dataflow.operators.core_text import BenchAnswerGenerator
from dataflow.prompts.core_text import FormatStrPrompt
from dataflow.utils.storage import FileStorage
from dataflow.core import LLMServingABC
from one_eval.core.state import BenchInfo
from one_eval.metrics.runner import MetricRunner
import one_eval.metrics.common.general

SOURCE_REV='8aba20ad17ee2c7d2391162ac03ffaebcbb17506'
ARCHIVE_SHA='45b5eb305790ae8f2bf5ceddc46ddabaf230d8654f4260d092443c008a7ffc2b'
CAP=ROOT/'capture'
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
def sha(data):return hashlib.sha256(data).hexdigest()
def canon(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def readrows(path):return [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
def dump(name,value):(OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
assert sha((ROOT/'capture.zip').read_bytes())==ARCHIVE_SHA
archive=zipfile.ZipFile(ROOT/'capture.zip')
entries={v['bench_name']:v for v in json.loads((CAP/'GALLERY.json').read_bytes())['benches']}

class Recorder(LLMServingABC):
    def __init__(self,outputs):self.outputs=outputs;self.prompts=[];self.system=None
    def start_serving(self):pass
    def cleanup(self):pass
    def generate_from_input(self,user_inputs,system_prompt=None):
        assert not self.prompts
        self.prompts=list(user_inputs);self.system=system_prompt
        assert len(self.outputs)==len(self.prompts)
        return list(self.outputs)

def normalize_template(template):
    template=template.replace('{choice}','CHOICE')
    return template if '{{' in template and '}}' in template else re.sub(r'\{([A-Za-z_][A-Za-z0-9_]*)\}',r'{{\1}}',template)

def score(name,entry,records,preds,contract=None):
    with tempfile.TemporaryDirectory(prefix='metric-') as tmp:
        path=Path(tmp)/'records.jsonl'
        path.write_text(''.join(json.dumps(dict(r,generated_ans=p))+'\n' for r,p in zip(records,preds)))
        info=BenchInfo(bench_name=name,meta={'artifact_paths':{'records':str(path)},'pred_key':'generated_ans','ref_key':entry['meta']['key_mapping']['input_label_key']})
        result=MetricRunner(max_workers=1).run_bench_with_contract(info,contract or entry['meta']['evaluation'])
        assert 'error' not in result,result
        return dict(result['primary_metric_result'],details=result['primary_metric_details'])

all_captures=[];reports=[]
for name in ['arc-challenge','openbookqa','mmlu']:
    entry=entries[name];folder=CAP/'capture'/name
    selected=readrows(folder/'SELECTED.jsonl.gz')
    preprocessed=readrows(folder/'NATIVE_PREPROCESSED.jsonl.gz')
    historic_prompts=readrows(folder/'CHECKER_NATIVE.jsonl.gz')
    assert len(selected)==len(preprocessed)==len(historic_prompts)==100
    assert (folder/'NATIVE_PREPROCESSED.jsonl.gz').read_bytes()==archive.read('capture/'+name+'/NATIVE_PREPROCESSED.jsonl.gz')
    labels=[];questions=[];choice_lists=[]
    for item,row in zip(selected,preprocessed):
        source=item['record']
        assert sha(canon(source))==item['source_sha256']
        if name=='mmlu':
            texts=source['choices'];idx=int(source['answer']);q=source['question']
        else:
            raw=source['choices'];texts=raw['text'];idx=list(map(str,raw['label'])).index(str(source['answerKey']))
            q=source['question'] if name=='arc-challenge' else source['question_stem']
            expected=[json.dumps(raw[k],ensure_ascii=False) for k in sorted(raw)]
            assert row['normalized_choices']==expected
        labels.append(string.ascii_uppercase[idx]);questions.append(q);choice_lists.append(texts)
    fixture=['<answer>'+label+'</answer>' for label in labels]
    cohort={}
    for condition in ['original','choices_only','binding_only','choices_and_binding']:
        fixed_choices=condition in ['choices_only','choices_and_binding']
        fixed_binding=condition in ['binding_only','choices_and_binding']
        rows=copy.deepcopy(preprocessed)
        for row,texts in zip(rows,choice_lists):
            if fixed_choices:row['normalized_choices']=texts
        template=normalize_template(entry['meta']['prompt']['user_template'])
        if fixed_binding:template=template.replace('{{question_stem}}','{{question}}')
        sink=Recorder(fixture)
        generator=BenchAnswerGenerator(eval_type='key3_q_choices_a',llm_serving=sink,prompt_template=FormatStrPrompt(template),force_generate=True)
        with tempfile.TemporaryDirectory(prefix='actual-generator-') as temp:
            root=Path(temp);input_path=root/'prepared.jsonl'
            input_path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            storage=FileStorage(str(input_path),cache_path=str(root/'cache')).step()
            columns=generator.run(storage=storage,input_question_key=entry['meta']['key_mapping']['input_question_key'],input_choices_key='normalized_choices',output_key='generated_ans')
            assert columns==['generated_ans']
            saved=Path(storage._get_cache_file_path(1))
            saved_rows=[json.loads(line) for line in saved.read_text().splitlines()]
            assert [r['generated_ans'] for r in saved_rows]==fixture
        if condition=='original':
            assert sink.prompts==[r['prompt'] for r in historic_prompts]
        source_score=score(name,entry,rows,fixture)
        absent=[]
        for i,(prompt,row,label,q,texts) in enumerate(zip(sink.prompts,rows,labels,questions,choice_lists)):
            offered=row['normalized_choices'];legal=label in string.ascii_uppercase[:len(offered)]
            probe=generator._build_prompt(eval_type='key3_q_choices_a',question='QUESTION_NONCE_'+str(i),context=None,choices=offered)
            all_captures.append(dict(benchmark=name,condition=condition,source_index=selected[i]['source_index'],source_sha256=selected[i]['source_sha256'],prompt=prompt,prompt_sha256=sha(prompt.encode()),question_present=q in prompt,question_mutation_changes_prompt=probe!=prompt,displayed_choices=offered,source_choices=texts,source_label=label,fixture_response=fixture[i],source_label_is_offered=legal,source_gold_is_individual_choice=texts[string.ascii_uppercase.index(label)] in offered))
            if not legal:absent.append(i)
        native_details=source_score.get('details') or []
        credited_absent=sum(native_details[i]==1 for i in absent)
        cohort[condition]=dict(question_present=sum(q in prompt for q,prompt in zip(questions,sink.prompts)),choices_preserved=sum(row['normalized_choices']==texts for row,texts in zip(rows,choice_lists)),label_not_offered=len(absent),credited_unoffered_labels=credited_absent,source_letter_fixture_score={k:v for k,v in source_score.items() if k!='details'})
        if condition=='original':
            for letter in ['C','D']:
                constant=score(name,entry,rows,['<answer>'+letter+'</answer>']*len(rows))
                cohort[condition]['constant_'+letter]={k:v for k,v in constant.items() if k!='details'}
    reports.append(dict(benchmark=name,source_rows=100,conditions=cohort))
dump('CAPTURES.json',all_captures)
provenance={}
for cls in [BenchAnswerGenerator,FormatStrPrompt,FileStorage,MetricRunner,BenchInfo]:
    path=Path(sys.modules[cls.__module__].__file__)
    provenance[cls.__name__]=dict(path=str(path),sha256=sha(path.read_bytes()),normal_import=True)
summary=dict(status='PASS',timestamp=datetime.now(timezone.utc).isoformat(),source_revision=SOURCE_REV,original_capture_sha256=ARCHIVE_SHA,models_called=0,judges_called=0,source_questions=300,conditions=1200,results=reports,modules=provenance,versions={n:metadata.version(n) for n in ['open-dataflow','numpy','pandas','langgraph','langchain-core']},scope='Installed unmodified generator, formatter, FileStorage, original metric registry/parser/MetricRunner/BenchInfo normal imports. Original preprocessor inputs authenticated from prior captures; full DataFlowEvalTool and graph/serving orchestration NOT executed. Serving is a deterministic constructed fixture, not a model. Choice accuracy is the gallery generation metric, not official ARC/OpenBook acc_norm. Gallery metadata warns contract_inferred/reference_mapped, smoke_passed=false.')
dump('SUMMARY.json',summary)
print(json.dumps(summary,indent=2))
