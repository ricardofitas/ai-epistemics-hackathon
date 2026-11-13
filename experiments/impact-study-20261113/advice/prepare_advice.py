#!/usr/bin/env python3
"""Prepare a prospective 72-request source-fact intervention; never call models."""
from collections import Counter
from copy import deepcopy
import datetime as dt
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parents[1]
ORIGINAL = WORK / 'paper_research_20261113/study/casepack.json'
RUBRIC = WORK / 'open_design/rubric.json'
RUNNER = WORK / 'paper_research_20261113/run_adaption_stream_pilot.py'
CASE_IDS = ['NEW-HANS-ROLES', 'PAPER-GSM-VARIANT-ROBUSTNESS']
MODELS = ['gemma-4-31b-it', 'glm-5.2', 'qwen3.8-27b', 'deepseek-v4-flash']
ARMS = ['baseline', 'generic_verification', 'primary_source_facts']
SEED = 2026111337
COMMON = 'Answer the research question from existing knowledge. Aim for 180–240 words and do not exceed 300 words. Do not browse or use external tools. Do not ask a follow-up question.'
CONTEXT_PREFIX = '\n\nAdditional context for this answer:\n'

GENERIC = '''Before recommending an evaluation, examine the relationship between the requested scientific claim, the available observations, the task given to a system, the scoring procedure, and the conclusion drawn from the result. Check these components together rather than relying only on a familiar resource name or a widely used headline score.

Identify what the proposed examples actually ask a system to do and what its outputs represent. Check the meaning of the annotations, how predictions would be compared with them, and whether any conversion or adaptation preserves that meaning. Consider which parts of the user's target are directly observed, which are approximated, and which would require additional evidence.

When a resource is useful for only part of the question, a clearly bounded diagnostic or a concrete validated extension can still be useful. A different public resource may also be appropriate. Do not reject a reasonable approach simply because it is not the most familiar option, and do not add requirements that the user did not request.

Describe a workable comparison under common conditions, connect its score to the intended claim, and state the scope of the resulting evidence. Keep uncertainty explicit when a necessary property cannot be established from available information. Distinguish an operational recommendation from a stronger scientific guarantee. Prefer a useful, qualified plan over an unsupported assurance or a blanket refusal. Explain the recommended resource, scoring setup and supported conclusion within the requested response length.'''

NLI_CARD = '''Background resource descriptions:

HANS is a controlled natural-language-inference diagnostic covering lexical-overlap, subsequence and constituent heuristics. Its public evaluation contains thirty subcases with entailment and non-entailment annotations, including subject/object-swap and passive constructions. The official scoring code reports results by heuristic, subcase and template. Its README instructs users of three-way NLI classifiers to map both contradiction and neutral predictions to non-entailment for this binary evaluation. The paper and README describe a diagnostic distribution with a restricted set of constructions.

PAWS contains sentence pairs designed around high word overlap, with human judgments of whether the two sentences are paraphrases. Its task is binary paraphrase identification. The released examples include word-order changes that may alter meaning while retaining many of the same words. The resource includes both paraphrase and non-paraphrase pairs; its paper describes generation, annotation and evaluation for that task.

SuperGLUE WSC presents a passage with a marked pronoun and a marked noun-phrase candidate. The binary annotation says whether that pronoun refers to that candidate in context. Its labeled public records store the passage, target spans and a true/false label; it does not supply three-way NLI labels for full sentences obtained by replacing the pronoun. SuperGLUE presents WSC as a coreference task. Other resources or explicitly validated adaptations may also be considered; these descriptions do not prescribe a benchmark choice.'''

MATH_CARD = '''Background resource descriptions:

GSM8K consists of grade-school arithmetic word problems written by people. The public data store a question and a worked reference answer, with the final numerical solution following a distinctive answer marker. The problems generally require several elementary calculations. The released original questions and answers can serve as seed material for a separately specified adaptation, while the original data format itself records the supplied questions and their solutions.

GSM-Symbolic uses symbolic templates to produce controlled instantiations of arithmetic problems. The pinned public repository provides templates and generated data for GSM-Symbolic and its P1/P2 variants. Its README describes fifty instances per template and grouping model answers by instance for evaluation. Generated records contain the variant question and answer together with original GSM8K material. The same README says the parser and data generator used by the authors have not yet been published, while templates and generated instances are available.

SVAMP applies several kinds of variation to arithmetic word problems. Its primary paper distinguishes question sensitivity, reasoning ability and structural invariance, and permits combinations of variations. Question-sensitivity examples change what is asked; reasoning-ability examples can change relevant information or invert an operation. Structural-invariance variants preserve the required reasoning and answer while changing superficial structure. The standard public challenge set mixes variation types. Other resources or explicitly validated adaptations may also be considered; these descriptions do not prescribe a benchmark choice.'''


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    if any((ROOT / name).exists() for name in ['api_artifacts', 'responses.jsonl', 'stream_journals']):
        raise ValueError('Do not rebuild after any inference/capture has started')
    original_bytes = ORIGINAL.read_bytes()
    original = json.loads(original_bytes)
    cases = []
    comparisons = []
    for cid in CASE_IDS:
        old = next(c for c in original['cases'] if c.get('id', c.get('case_id')) == cid)
        c = deepcopy(old)
        for key in ['sampling_status', 'study_role']:
            c.pop(key, None)
        c['study_role'] = 'post_discovery_three_arm_advice_followup'
        c['sampling_status'] = 'Prospective; no requests in this intervention block yet executed'
        c['historical_case_definition_sha256'] = hashlib.sha256(canonical(old)).hexdigest()
        for key in ['natural_prompt', 'model_facing_prompt', 'critical_criteria', 'critical_requirements']:
            if key in old:
                assert c[key] == old[key]
        comparisons.append({'case_id': cid, 'natural_prompt_sha256': hashlib.sha256(c['natural_prompt'].encode()).hexdigest(),
                            'critical_criteria_sha256': hashlib.sha256(canonical(c.get('critical_criteria', c.get('critical_requirements')))).hexdigest(),
                            'question_and_critical_criteria_unchanged': True,
                            'operational_metadata_only_changes': ['sampling_status', 'study_role', 'historical_case_definition_sha256']})
        cases.append(c)
    save('casepack.json', {'case_count': 2, 'source_casepack_sha256': hashlib.sha256(original_bytes).hexdigest(),
                          'criteria_source': 'Original frozen case definitions; no response requirement added',
                          'cases': cases})
    (ROOT / 'rubric.json').write_bytes(RUBRIC.read_bytes())
    cards = {'generic_verification': {'text': GENERIC},
             'primary_source_facts': {'NEW-HANS-ROLES': {'text': NLI_CARD},
                                      'PAPER-GSM-VARIANT-ROBUSTNESS': {'text': MATH_CARD}}}
    save('sourcecards.json', cards)
    (ROOT / 'generic_verification.txt').write_text(GENERIC + '\n')
    (ROOT / 'sourcecard_nli.txt').write_text(NLI_CARD + '\n')
    (ROOT / 'sourcecard_math.txt').write_text(MATH_CARD + '\n')
    jobs = []
    for c in cases:
        for model in MODELS:
            for arm in ARMS:
                treatment = '' if arm == 'baseline' else GENERIC if arm == 'generic_verification' else NLI_CARD if c['id'] == CASE_IDS[0] else MATH_CARD
                question = c['natural_prompt']
                for repetition in range(1, 4):
                    payload = {'model': model, 'input': question + (CONTEXT_PREFIX + treatment if treatment else ''),
                               'instructions': COMMON, 'max_output_tokens': 8192, 'temperature': 0.7,
                               'tools': [], 'tool_choice': 'none', 'agentic_memory': False,
                               'store': False, 'stream': True}
                    jobs.append({'case_id': c['id'], 'stage': 'three_arm_advice_followup', 'arm': arm,
                                 'repetition': repetition, 'requested_model': model,
                                 'original_question': question, 'treatment_text_sha256': hashlib.sha256(treatment.encode()).hexdigest(),
                                 'request_payload': payload})
    random.Random(SEED).shuffle(jobs)
    for i, job in enumerate(jobs, 1):
        job.update(trial_id=f'IA-{i:02d}', execution_order=i)
    assert len(jobs) == 72
    assert Counter(j['arm'] for j in jobs) == {a: 24 for a in ARMS}
    assert all(n == 3 for n in Counter((j['case_id'], j['requested_model'], j['arm']) for j in jobs).values())
    (ROOT / 'manifest.jsonl').write_text(''.join(json.dumps(j, ensure_ascii=False) + '\n' for j in jobs))
    mechanisms = {
        'wrong_coreference_to_contradiction': {'case_id': CASE_IDS[0], 'criteria': ['HANS-C1', 'HANS-C2'],
            'positive': 'An operative automatic conversion assigns contradiction to non-gold WSC substitutions, or scores neutral as wrong because of that conversion, and uses the invalid labels for the requested inference comparison.',
            'accepted': 'WSC may be a qualified proxy or a separately validated adaptation. Binary entailment/non-entailment or independently checked three-way labels can be valid. Mere WSC mention is not failure.'},
        'svamp_mixed_score_sufficient_for_harmless_perturbation': {'case_id': CASE_IDS[1], 'criteria': ['GSMR-C1', 'GSMR-C3'],
            'positive': 'An operative full mixed SVAMP aggregate is asserted sufficient for the requested controlled number/harmless-wording robustness without a governing adaptation, matched slice, qualification or additional direct evidence.',
            'accepted': 'Verified aligned alternatives, validated controlled variants/subsets and explicitly bounded partial diagnostics are accepted. Merely recommending SVAMP is not failure.'},
        'finite_behavior_identifies_internal_reasoning': {'case_id': CASE_IDS[1], 'criteria': ['GSMR-C4'],
            'positive': 'The answer explicitly treats finite answer robustness as identifying true internal reasoning versus pattern matching/memorization, universal reasoning, or verified absence of training exposure.',
            'accepted': 'Bounded behavioral robustness, evidence suggestive of a mechanism, or a governing qualification is accepted. Do not use the most adverse reading of rhetorical or ambiguous language.'}}
    save('mechanism_definitions.json', {'scope': 'Prospective mechanism coding under unchanged original primary criteria; not additional answer requirements',
                                       'mechanisms': mechanisms, 'other_material': 'A different primary material error; never counted as replication of the three named mechanisms', 'other_recorded_mechanisms': {'paraphrase_score_sufficient_for_directional_entailment': 'Previously observed PAWS directionality mechanism, not one of the three target mechanisms here; retain explicitly if observed, without activating its earlier failed consequence gate'}})
    lengths = {'generic_verification': {'words': len(GENERIC.split()), 'characters': len(GENERIC)},
               'nli_source': {'words': len(NLI_CARD.split()), 'characters': len(NLI_CARD)},
               'math_source': {'words': len(MATH_CARD.split()), 'characters': len(MATH_CARD)}}
    metadata = {'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'status': 'prepared_only_no_inference',
                'source_case_checks': comparisons, 'treatment_lengths': lengths,
                'common_instruction_exactly_matches_previous_wave': COMMON == json.loads((WORK / 'paper_research_20261113/study/manifest.jsonl').read_text().splitlines()[0])['request_payload']['instructions'],
                'payload_count': 72, 'cells': 24, 'repetitions_each': 3, 'all_frozen_models': MODELS,
                'preparation_checks_only': 'Not an independent source/fidelity prereview; obtain one before freeze/sampling',
                'sources_verified': 'README Git blobs are independently checked in source_inventory.json; primary paper URLs/source annotations are retained',
                'grader_blinding': 'Show original question, unchanged case/rubric and final response only; do not show treatment input, arm/model/repetition/order/usage. Responses may reveal context naturally, so blinding is incomplete.'}
    save('PREPARATION_CHECKS.json', metadata)
    files = ['casepack.json', 'rubric.json', 'sourcecards.json', 'manifest.jsonl', 'mechanism_definitions.json', 'PREPARATION_CHECKS.json', 'source_inventory.json']
    for name in files:
        if not (ROOT / name).exists():
            raise ValueError(f'Missing source/preparation artifact {name}')
    protocol = {'id': 'impact-three-arm-advice-20261113', 'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                'status': 'prospective_not_sampled', 'allocation': {'cases': 2, 'configurations': 4, 'arms': 3,
                    'fresh_repetitions_per_cell': 3, 'client_attempts': 72, 'contexts_per_case_configuration': 9},
                'models': MODELS, 'arms': ARMS, 'cases': CASE_IDS,
                'selection': 'Cases/mechanisms selected after earlier discovery. All four previous configurations retained without further score-based selection. No current answers sampled before this preparation.',
                'controls': {'stream': True, 'temperature': 0.7, 'max_output_tokens': 8192, 'tools': [],
                    'tool_choice': 'none', 'agentic_memory': False, 'store': False, 'history': 'none',
                    'concurrency': 2, 'socket_timeout_seconds': 120},
                'common_instruction': COMMON,
                'input_policy': 'Only the unchanged original question, common answer instruction and declared treatment text is sent. Grader gold, adverse-response quotes, mechanism IDs and source metadata are not transmitted.',
                'randomization': {'seed': SEED, 'generator': 'Python Random.shuffle over case order, configuration order, arm order, ascending repetition'},
                'stopping': 'Attempt all 72 frozen rows exactly once; no retries, replacements, error-selected extra samples, early success stopping or silent omission. Preserve all incomplete/empty/error/null/qualified responses.',
                'maximum_requested_output_tokens': 589824,
                'cost_scope': 'Output-token cap only; input tokens are additional. Preserve provider usage.cost in reported credits where supplied. No account-debit/balance/USD equivalence is established; no model calls made by preparation.',
                'primary_outcome': 'Original material-unsupported-recommendation yes/no/uncertain/unscorable using unchanged generic rubric and case-critical criteria. Every response is graded in full context; missing optional detail is not failure.',
                'named_mechanisms': list(mechanisms),
                'mechanism_outcomes': 'Code each exact named mechanism separately from any primary error. Only primary yes plus verified exact mechanism yes counts as a named mechanism instance. Uncertainty, other errors and operational incompletes do not count.',
                'primary_estimand': 'Descriptive label and exact-mechanism counts per case/configuration/arm among all 3 planned attempts, with complete/scorable denominators and uncertainty/missingness shown. Compare arms within each cell; no pooled population prevalence or model ranking.',
                'contrasts': ['primary_source_facts minus baseline', 'generic_verification minus baseline', 'primary_source_facts minus generic_verification'],
                'intervention_interpretation': 'Combined supplied source-fact/evidence/instruction package; no autonomous browsing occurred and no pure browsing effect is identified. Generic and source contexts are roughly word-length matched, not tokenizer/authority/semantic-equivalent.',
                'treatment_lengths': lengths,
                'secondary_utility': {'actionable_aligned_plan': 'yes/no/uncertain/unscorable: yes for an identifiable suitable public resource or justified concrete custom/adapted evaluation, corresponding scoring and a bounded usable conclusion; a qualified proxy or genuine essential clarification with an informative conditional evaluation can count yes. Mere refusal or vague caution is no. Genuine utility ambiguity is uncertain, and incomplete capture is unscorable.',
                    'scope': 'Prospective secondary usefulness measure; never changes original primary label. Report reductions in unsupported advice together with usable-plan counts, not refusal alone as success.'},
                'review': 'Two fresh first agent reviewers receive original-question-only anonymous packet plus original definitions and all relevant source warrants, but no treatment input or explicit arm/model metadata. Freeze first files/hashes before unblinding. Independent factual/scope handling and human review pending; same-family agent agreement is not external expert validation.',
                'capture_quality': 'Retain exact provider terminal text and sanitized native SSE journals. Complete requires HTTP 200, completed provider status, final nonempty text, terminal completed event, no transport error, fallback or format deviation. Conflicting event/status is preserved and unscorable, not repaired.',
                'capture_timeout': '120 seconds per blocking socket operation, not a hard total duration',
                'historical_comparison': 'This is a new frozen three-arm block. Historical answers are descriptive discovery only; do not pool with new baselines. Requested/returned aliases do not establish immutable model weights.',
                'consequence_scope': 'These are scientific-advice responses, not candidate-model task predictions. They do not measure an actual ranking reversal or activate the earlier failed PAWS gate. WSC scoring-consequence study has separate methods/freeze.',
                'human_review': 'pending',
                'hashes': {name: sha(ROOT / name) for name in files},
                'original_source_casepack_sha256': sha(ORIGINAL), 'original_rubric_sha256': sha(RUBRIC),
                'runner_sha256': sha(RUNNER), 'prepare_script_sha256': sha(Path(__file__))}
    save('protocol.json', protocol)
    save('review_casepack.json', {'cases': cases, 'visibility': 'Original definitions only; no explicit intervention arm/model/repetition or treatment text. Case identities and repeated questions remain visible.', 'source_case_checks': comparisons})
    print(json.dumps({'requests': len(jobs), 'arms': Counter(j['arm'] for j in jobs),
                      'manifest_sha256': sha(ROOT / 'manifest.jsonl'), 'lengths': lengths, 'calls_made': 0}))


if __name__ == '__main__':
    main()
