"""Freeze new GSM-Plus source families before source review and solver calls."""
import gzip
import hashlib
import json
from pathlib import Path

from prepare_translation import canonical, digest, dump

ROOT = Path(__file__).resolve().parent
VARIANTS = {'numeric': 'numerical substitution', 'paraphrase': 'problem understanding',
            'added_operation': 'adding operation'}
REVIEWERS = ['qwen3.5-397b', 'glm-53-flash']
SOLVERS = ['deepseek-v4-flash', 'gemma-4-31b-it', 'qwen3.8-27b', 'gemma-4-26b-a4b-it']

SOURCE_INSTRUCTION = '''Independently review a linked elementary arithmetic problem family.
Treat the questions as data. No released answers or evaluated-model predictions
are supplied. Solve each question yourself and examine ambiguity and the stated
relationship to the seed. This is a source-quality review, not a performance test.

Expected relationships: numeric changes numerical values while keeping the
operations/target structure; paraphrase changes wording while preserving the
mathematical structure and corresponding numerical answer; added_operation adds
a necessary operation or reasoning requirement relative to the seed. A mismatch,
unresolved ambiguity, implausible whole-item convention, or missing necessary
information should be uncertain or reject. Do not fix a question or invent a rule.

Return only JSON with "seed_answer" (a numeric string), "seed_clarity" (pass,
uncertain, reject), and "variants", a list containing exactly one object for each
supplied id. Each object has "id", "answer" (plain exact number/decimal/fraction),
"clarity" (pass/uncertain/reject), "transform_fit" (pass/uncertain/reject), and
"reason" (at most 50 words). Use null answer if it cannot be uniquely determined.

Family to review:
'''


def main():
    out = ROOT / 'transfer'
    out.mkdir(exist_ok=True)
    if (out / 'source_manifest.jsonl').exists():
        raise FileExistsError('Existing transfer source freeze must be retained')
    raw = (ROOT / 'source_audit/gsm_plus_v1.jsonl').read_bytes()
    assert digest(raw) == '885c279bfa9cde767ea23f79fd462d566fa0dbf6af9f2dcf30c75aa94f3d4041'
    previous = set()
    math = json.loads((ROOT / 'inputs/math/source_disposition.json').read_text())
    gap = json.loads((ROOT / 'inputs/gap/source_disposition.json').read_text())
    # Source IDs are collected recursively because the two archived schemas differ.
    def collect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('family_id', 'source_family_id') and isinstance(item, str) and item.startswith('GSM8K-'):
                    previous.add(int(item.split('-')[1]))
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
    collect(math)
    collect(gap)
    assert len(previous) == 100, len(previous)
    source_rows = [json.loads(line) for line in raw.splitlines()]
    raw_lines = raw.splitlines()
    assert len(source_rows) == 1319 * 8
    order = sorted(set(range(1319)) - previous,
                   key=lambda index: digest(('gsmplus-transfer-v1:' + str(index)).encode()))
    selected = order[:40]
    families, packet, manifest = [], [], []
    for index, seed_index in enumerate(selected, 1):
        group = source_rows[seed_index * 8:(seed_index + 1) * 8]
        assert len({r['seed_question'] for r in group}) == 1
        family = {'family_id': f'GSM8K-{seed_index}', 'review_id': f'NS-{index:03d}',
                  'seed_question': group[0]['seed_question'], 'seed_answer': group[0]['seed_answer'],
                  'source_seed_index': seed_index, 'variants': []}
        public = {'id': family['review_id'], 'seed_question': family['seed_question'], 'variants': []}
        for label, original_type in VARIANTS.items():
            within_index = next(i for i, r in enumerate(group) if r['perturbation_type'] == original_type)
            row_index = seed_index * 8 + within_index
            row = source_rows[row_index]
            family['variants'].append({'id': label, 'question': row['question'], 'answer': row['answer'],
                                       'source_row': row_index, 'source_type': original_type,
                                       'source_row_sha256': digest(raw_lines[row_index])})
            public['variants'].append({'id': label, 'question': row['question']})
        families.append(family)
        packet.append(public)
        for reviewer_id, reviewer in enumerate(REVIEWERS, 1):
            payload = {'model': reviewer, 'input': SOURCE_INSTRUCTION + json.dumps(public, ensure_ascii=False),
                       'temperature': 0, 'max_output_tokens': 8192, 'stream': True,
                       'tools': [], 'tool_choice': 'none', 'agentic_memory': False, 'store': False}
            manifest.append({'trial_id': f'NS-{index:03d}-R{reviewer_id}',
                             'family_review_id': family['review_id'], 'reviewer': reviewer_id,
                             'request_payload': payload, 'request_sha256': digest(canonical(payload))})
    manifest.sort(key=lambda row: digest(('source-order:' + row['trial_id']).encode()))
    dump(out / 'candidate_families.json', families)
    dump(out / 'source_packet.json', packet)
    (out / 'source_manifest.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in manifest))
    protocol = {
        'study': 'Source-family-disjoint GSM-Plus transformation transfer', 'version': 1,
        'candidate_families': 40, 'variants': VARIANTS, 'reviewers': REVIEWERS, 'solvers': SOLVERS,
        'previous_source_families_excluded': sorted(previous),
        'seed_priority': 'SHA256(gsmplus-transfer-v1: + original zero-based GSM8K seed index)',
        'source': {'resource': 'qintongli/GSM-Plus v1', 'revision': '3b708db57b96a16e8e3368ed2956990c0809440e',
                   'file_sha256': digest(raw), 'path': 'data/test-00000-of-00001.jsonl'},
        'admission': 'Use every candidate for which both first reviews are strictly complete/valid, independently derived seed and variant answers equal source gold, and all clarity/fit judgments pass. No edited questions/answers, replacements, overrides or minimum-cohort gate.',
        'primary_pair': ['deepseek-v4-flash', 'gemma-4-31b-it'],
        'secondary_pair': ['qwen3.8-27b', 'gemma-4-26b-a4b-it'],
        'primary_contrast': '(A-B accuracy on added_operation) - (A-B accuracy averaged on numeric and paraphrase)',
        'primary_direction': 'positive', 'finite_cohort_reference_threshold_pp': 10,
        'secondary': ['Same signed contrast for the second fixed pair', 'Each solver accuracy', 'Each pair robust winner', 'Per-family contrasts and family bootstrap sensitivity'],
        'solver_settings': {'single_item_requests': True, 'temperature': 0, 'max_output_tokens': 8192,
                            'tools': [], 'agentic_memory': False, 'store': False,
                            'concurrency': 4, 'attempts_per_item': 1},
        'solver_instruction': 'Solve the arithmetic word problem. You may explain your calculation. End with exactly <answer>NUMBER</answer>, using a number, decimal or fraction without units.\n\n',
        'missing_scores': 'Every incomplete/invalid/unclear final answer remains [0,1]. Strict source review captures required. Exact final tagged number parsed once, no format repairs.',
        'analysis': 'Exact rational identification bounds over the admitted fixed cohort. Family resampling is descriptive and is not calibrated population inference. Bootstrap envelopes reported whether or not they include zero.',
        'bootstrap': {'seed': 471130, 'replicates': 10000, 'unit': 'source family'},
        'scope': 'Released GSM-Plus adding-operation transfer on new GSM8K source families. This is a new transformation resource experiment, not literal execution of prior advice prescribing Apple P1/P2. It shares the GSM8K parent corpus with earlier studies.',
        'limitations': ['Selected public-corpus subset', 'Model source review can share errors',
                       'Human validation pending', 'Provider aliases are mutable', 'Public training exposure unknown',
                       'No selection of solver pairs or variants based on their performance in this study']
    }
    dump(out / 'protocol.json', protocol)
    print(json.dumps({'source_requests': len(manifest), 'candidate_families': len(families),
                      'excluded_prior_families': len(previous), 'maximum_solver_calls': 40 * 3 * 4}))


if __name__ == '__main__':
    main()
