#!/usr/bin/env python3
"""Prepare the post-discovery 36-call source-compatibility repair experiment."""
from collections import Counter
from copy import deepcopy
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import shutil

ROOT = Path(__file__).resolve().parent
IMPACT = ROOT.parent
WORK = IMPACT.parent
OLD = IMPACT / 'advice'
CASE = 'PAPER-GSM-VARIANT-ROBUSTNESS'
MODELS = ['gemma-4-31b-it', 'glm-5.2', 'qwen3.8-27b', 'deepseek-v4-flash']
ARMS = ['baseline', 'generic_verification', 'primary_source_facts']
SEED = 2026111349
PREFIX = '\n\nAdditional context for this answer:\n'
APPEND_PREFIX = '\n\nAdditional context note:\n'
PATCH = '''In the primary GSM-Symbolic paper, Section 4.3 constructs GSM-P1 and GSM-P2 by adding one and two clauses to GSM-Symbolic questions, respectively, to vary question difficulty. The authors note that a clause change need not correspond to exactly one reasoning step. Separately, Sections 4.1–4.2 describe instantiating the same symbolic template with different proper names and numerical values while the overall reasoning needed for that template stays the same. The documented Section 4.2 factors are changes to names, values, or both; an independent free-form sentence-paraphrasing condition is not described in that comparison. Clause-added template conditions and within-template name/value instantiations are different construction settings. These descriptions specify what was varied, without prescribing which public resource or validated adaptation to choose.'''
CONTROL = '''When using available resource descriptions, check which comparison each evaluation condition actually supports. State the relation between the inputs being changed, the task a system must perform, the annotation for each resulting example, and the conclusion attached to a score. Keep controlled changes separate from additional changes when their interpretation differs. A familiar resource name or an extra variant name does not by itself establish compatibility with every requested claim. If an evaluation covers only part of the question, a bounded result, an appropriate alternative, or a concrete validated extension can remain useful. Keep the final recommendation practical and make any necessary assumptions explicit. These checks concern resource–claim compatibility and do not require a particular public benchmark, scoring method, or predetermined answer.'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    if any((ROOT / f).exists() for f in ['api_artifacts', 'responses.jsonl', 'stream_journals']):
        raise ValueError('Refusing to rebuild after any collection begins')
    old_protocol = json.loads((OLD / 'protocol.json').read_text())
    assert old_protocol['models'] == MODELS
    common = old_protocol['common_instruction']
    old_case = next(c for c in json.loads((OLD / 'casepack.json').read_text())['cases'] if c['id'] == CASE)
    c = deepcopy(old_case)
    c['study_role'] = 'post_discovery_source_compatibility_followup'
    c['sampling_status'] = 'Prospective source-repair block, no requests executed by preparer'
    assert all(c.get(k) == old_case.get(k) for k in ['natural_prompt', 'model_facing_prompt', 'critical_criteria', 'critical_requirements'])
    original_card = json.loads((OLD / 'sourcecards.json').read_text())['primary_source_facts'][CASE]['text']
    assert (OLD / 'sourcecard_math.txt').read_text() == original_card + '\n'
    assert sha(OLD / 'sourcecard_math.txt') == '656a080db5ecf13c90c65dba39b0abdf566fcd10d70ce99421699168a8c5c297'
    assert hashlib.sha256(original_card.encode()).hexdigest() == 'b1a9ab7e00deef5792fe1552dedce525c108aa4a3258420c90409e59f711f9b4'
    old_source_rows = [json.loads(s) for s in (OLD / 'manifest.jsonl').read_text().splitlines()
                       if json.loads(s)['case_id'] == CASE and json.loads(s)['arm'] == 'primary_source_facts']
    assert len(old_source_rows) == 12 and all(j['request_payload']['input'] == c['natural_prompt'] + PREFIX + original_card for j in old_source_rows)
    assert all(j['request_payload']['instructions'] == common for j in old_source_rows)
    shutil.copyfile(OLD / 'sourcecard_math.txt', ROOT / 'original_sourcecard.txt')
    shutil.copyfile(OLD / 'rubric.json', ROOT / 'rubric.json')
    shutil.copyfile(OLD / 'mechanism_definitions.json', ROOT / 'mechanism_definitions.json')
    assert sha(ROOT / 'rubric.json') == sha(OLD / 'rubric.json')
    (ROOT / 'source_patch.txt').write_text(PATCH + '\n')
    (ROOT / 'generic_compatibility.txt').write_text(CONTROL + '\n')
    save('casepack.json', {'cases': [c], 'source_casepack_sha256': sha(OLD / 'casepack.json'),
                          'criteria_and_question_unchanged': True,
                          'operational_metadata_changes_only': ['study_role', 'sampling_status']})
    save('review_casepack.json', {'cases': [c], 'visibility': 'Original question/criteria only; no explicit condition/model/repetition or treatment text. Reviewers receive the same full primary-source warrants across all conditions; response wording can reveal context naturally.'})
    contexts = {ARMS[0]: original_card, ARMS[1]: original_card + APPEND_PREFIX + CONTROL,
                ARMS[2]: original_card + APPEND_PREFIX + PATCH}
    save('contexts.json', {'original_sourcecard': original_card, 'source_patch': PATCH,
                          'generic_compatibility': CONTROL, 'full_contexts': contexts,
                          'model_facing': 'Only original question + common context prefix + assigned full context, with original common instruction'})
    jobs = []
    for model in MODELS:
        for arm in ARMS:
            for rep in range(1, 4):
                payload = {'model': model, 'input': c['natural_prompt'] + PREFIX + contexts[arm],
                           'instructions': common, 'max_output_tokens': 8192, 'temperature': 0.7,
                           'tools': [], 'tool_choice': 'none', 'agentic_memory': False, 'store': False, 'stream': True}
                jobs.append({'case_id': CASE, 'stage': 'source_compatibility_repair', 'arm': arm,
                             'repetition': rep, 'requested_model': model, 'original_question': c['natural_prompt'],
                             'context_sha256': hashlib.sha256(contexts[arm].encode()).hexdigest(),
                             'request_payload': payload})
    random.Random(SEED).shuffle(jobs)
    for i, job in enumerate(jobs, 1):
        job.update(trial_id=f'SR-{i:02d}', execution_order=i)
    assert len(jobs) == 36 and all(n == 3 for n in Counter((j['requested_model'],j['arm']) for j in jobs).values())
    (ROOT / 'manifest.jsonl').write_text(''.join(json.dumps(j,ensure_ascii=False) + '\n' for j in jobs))
    lengths = {name: {'words': len(text.split()), 'characters': len(text)}
               for name,text in {'original_sourcecard': original_card, 'patch_paragraph': PATCH,
                                 'generic_paragraph': CONTROL, **{'full_' + k:v for k,v in contexts.items()}}.items()}
    checks = {'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'calls_made': 0,
              'original_sourcecard_file_sha256': sha(ROOT / 'original_sourcecard.txt'),
              'original_sourcecard_model_text_sha256': hashlib.sha256(original_card.encode()).hexdigest(),
              'question_and_critical_criteria_unchanged': True,
              'question_sha256': hashlib.sha256(c['natural_prompt'].encode()).hexdigest(),
              'critical_criteria_sha256': hashlib.sha256(canonical(c['critical_criteria'])).hexdigest(),
              'original_source_payload_input_equal': True,
              'original_rubric_bytes_equal': True, 'same_five_mechanism_ids': True,
              'lengths': lengths,
              'preparation_scope': 'Structural preparation checks only; not independent source/fidelity review. No original advice files modified.'}
    save('PREPARATION_CHECKS.json', checks)
    files = ['casepack.json','review_casepack.json','rubric.json','mechanism_definitions.json','contexts.json',
             'original_sourcecard.txt','source_patch.txt','generic_compatibility.txt','manifest.jsonl',
             'source_inventory.json','source_verification.json','PREPARATION_CHECKS.json']
    assert all((ROOT / f).exists() for f in files)
    protocol = {'id': 'post-discovery-math-source-repair-20261113',
                'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'status': 'prepared_not_executed',
                'selection': 'Math case and original source-card condition selected after observing unexpected errors in the first three-arm block. This is a new exploratory post-discovery follow-up; no historical pooling or confirmatory general source/RAG-harm inference.',
                'historical_observation': {'summary_sha256': sha(OLD / 'analysis_summary.json'),
                    'source_card_math': '9 yes/9 complete plus 3 incomplete among 12 planned',
                    'generic_math': '2 yes/8 complete plus 4 incomplete among 12 planned',
                    'baseline_math': '5 yes/10 complete (including 3 uncertain) plus 2 incomplete among 12 planned',
                    'scope': 'Reported historical cell counts justify selection only; not included in any new arm denominator.'},
                'research_question': 'Does adding an omitted but verified source-construction fact improve compatibility of scientific advice relative to the unchanged source card and a roughly length-matched generic compatibility reminder?',
                'allocation': {'cases': 1,'configurations': 4,'conditions': 3,'fresh_contexts_per_cell': 3,'client_attempts':36},
                'models': MODELS, 'arms': ARMS, 'cases': [CASE], 'arm_meanings': {'baseline':'unchanged original source card, NOT a no-source arm','generic_verification':'same original card plus length-matched generic compatibility paragraph','primary_source_facts':'same original card plus decisive verified construction-fact patch'},
                'common_instruction': common,
                'controls': {'stream':True,'temperature':0.7,'max_output_tokens':8192,'tools':[],
                             'tool_choice':'none','agentic_memory':False,'store':False,'history':'none',
                             'concurrency':2,'socket_timeout_seconds':120},
                'socket_timeout_scope': 'Per blocking socket operation, not a hard total duration',
                'randomization': {'seed': SEED, 'generator': 'Python Random.shuffle over configuration order, condition order, ascending repetition'},
                'stopping': 'All 36 frozen requests once; no retries, replacements, outcome-based model/item/condition additions or early success stopping. Preserve every incomplete/error/empty/null/uncertain result.',
                'maximum_requested_output_tokens':294912,
                'cost_scope': 'Output cap plus additional input tokens. Preserve provider usage.cost where available; no account debit/balance or USD claim.',
                'model_facing_policy': 'Original unchanged question, exact original source card and assigned appended paragraph only, plus exact previous common answer instruction. No evaluator labels/criteria, adverse historical quote, preferred benchmark, or process-identification answer key is transmitted.',
                'original_card_file_sha256': sha(ROOT / 'original_sourcecard.txt'),
                'original_card_model_text_sha256': hashlib.sha256(original_card.encode()).hexdigest(),
                'primary_outcome': old_protocol['primary_outcome'],
                'mechanism_outcomes': old_protocol['mechanism_outcomes'],
                'named_mechanisms': old_protocol['named_mechanisms'],
                'mechanism_ids': ['wrong_coreference_to_contradiction','svamp_mixed_score_sufficient_for_harmless_perturbation',
                    'finite_behavior_identifies_internal_reasoning','paraphrase_score_sufficient_for_directional_entailment','other_material'],
                'mechanism_scope': 'Same five IDs as the previous block. The P1/P2 construction mismatch, if material under existing criteria, is other_material, not a newly imposed criterion or target-mechanism relabel. Mere mention/use of P1/P2 is not failure: within-template evaluation, justified adaptation and bounded partial evidence remain valid.',
                'secondary_utility': old_protocol['secondary_utility'],
                'primary_estimand': 'Primary labels, same-five mechanism flags and useful-plan labels per configuration/condition among all 3 planned new attempts, with complete/scorable denominators and uncertainty/missingness shown. No pooled population prevalence, model ranking or historical-arm denominator.',
                'contrasts': ['decisive_fact_patch minus unchanged_sourcecard','generic_compatibility minus unchanged_sourcecard','decisive_fact_patch minus generic_compatibility'],
                'missingness': 'Report complete-case counts plus lower/upper bounds among all planned attempts, retaining uncertain/unscorable outcomes. Incompletes are never semantic failures or source-patch successes.',
                'interpretation': 'Selected-case context repair/evidence package. The contrast does not establish general source harm, universal RAG behavior, pure browsing effect, uniquely identified cause of prior errors or task-performance ranking consequences.',
                'lengths': lengths,
                'review': 'Two fresh first agent judgments receive original-question-only anonymous answers and unchanged case/rubric plus shared primary warrants, with explicit model/condition/repetition/full context hidden. Preserve first files/hashes before unblinding; factual and scope disagreements handled transparently. Natural wording may reveal source context, and shared-model agent error remains. Human review pending.',
                'capture_quality': old_protocol['capture_quality'],
                'human_review': 'pending',
                'hashes': {f:sha(ROOT / f) for f in files},
                'prior_advice_protocol_sha256':sha(OLD / 'protocol.json'),
                'prior_advice_freeze_commit':'6566b5cc3c3879e032f2acc92875f9ace25e00e5',
                'original_rubric_sha256':sha(OLD / 'rubric.json'),
                'runner_sha256':sha(WORK / 'paper_research_20261113/run_adaption_stream_pilot.py'),
                'prepare_sha256':sha(Path(__file__))}
    save('protocol.json',protocol)
    print(json.dumps({'requests':36,'manifest_sha256':sha(ROOT / 'manifest.jsonl'),
                      'protocol_sha256':sha(ROOT / 'protocol.json'),'lengths':lengths,'calls_made':0}))


if __name__ == '__main__':
    main()
