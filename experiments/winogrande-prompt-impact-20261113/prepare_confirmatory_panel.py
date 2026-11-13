"""Freeze 50 previously unqueried questions and their actual prompt pairs."""
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path

from analyze_prompt_collisions import HERE, WORKSPACE, audit, digest, gzip_rows, normalize_record, recover_native_inputs, render_typed_prompt


def keyed(value):
    return digest('one-eval-prompt-information-20261113-v1|' + value)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def main():
    name = 'winogrande'
    rows = gzip_rows(audit.CAPTURE / 'winogrande__validation.jsonl.gz')
    entries = json.loads((audit.ROOT / 'GALLERY_SELECTED.json').read_text())['benches']
    entry = next(e for e in entries if e['bench_name'] == name)
    native_text = recover_native_inputs(name, rows, entry)
    pilot = json.loads((WORKSPACE / 'default_contract_model_capture_20261113/cases.json').read_text())
    excluded_indices = {c['row_index'] for c in pilot if c['bench'] == name}
    excluded_prompts = {native_text[i] for i in excluded_indices}
    group = defaultdict(list)
    for index, prompt in enumerate(native_text):
        if prompt not in excluded_prompts:
            group[prompt].append(index)

    mixed = [p for p, indices in group.items() if len({rows[i]['answer'] for i in indices}) == 2]
    cases = []

    def add(index, stratum):
        source = rows[index]
        repaired = render_typed_prompt(source, normalize_record(name, source, str(index), permute=False), entry['meta']['key_mapping'], entry['meta']['prompt']['user_template'])
        cases.append(dict(source_row=index, source_sha256=digest(canonical(source)),
                          source_id_hash=digest(source['sentence']), stratum=stratum,
                          gold={'1': 'A', '2': 'B'}[source['answer']],
                          native_prompt=native_text[index], corrected_prompt=repaired,
                          dependency_group=digest(native_text[index])))

    for prompt in sorted(mixed, key=keyed)[:15]:
        for label in ('1', '2'):
            candidates = [i for i in group[prompt] if rows[i]['answer'] == label]
            chosen = min(candidates, key=lambda i: keyed(canonical(rows[i])))
            add(chosen, 'contradictory_pair')
    for label in ('1', '2'):
        candidates = [p for p, indices in group.items() if len(indices) == 1 and rows[indices[0]]['answer'] == label]
        for prompt in sorted(candidates, key=keyed)[:10]:
            add(group[prompt][0], 'singleton_control')
    cases.sort(key=lambda c: keyed(c['source_sha256']))
    assert len(cases) == len({c['source_row'] for c in cases}) == len({c['corrected_prompt'] for c in cases}) == 50
    assert sum(c['gold'] == 'A' for c in cases) == 25
    assert not excluded_indices.intersection(c['source_row'] for c in cases)
    assert not excluded_prompts.intersection(c['native_prompt'] for c in cases)
    assert len({c['dependency_group'] for c in cases}) == 35
    payload = ('\n'.join(canonical(c) for c in cases) + '\n').encode()
    (HERE / 'fresh_panel.jsonl.gz').write_bytes(gzip.compress(payload, mtime=0))
    models = ['gemma-4-31b-it', 'qwen3.8-27b']
    requests = []
    for case in cases:
        for condition in ('native_prompt', 'corrected_prompt'):
            for model in models:
                payload = {'model': model, 'input': case[condition], 'temperature': 0, 'max_output_tokens': 4096, 'stream': True, 'tools': [], 'tool_choice': 'none', 'agentic_memory': False, 'store': False}
                trial_id = keyed('|'.join([case['source_sha256'], condition, model]))
                requests.append(dict(trial_id=trial_id, source_row=case['source_row'], group=case['dependency_group'], condition=condition, request_payload=payload))
    requests.sort(key=lambda r: keyed('order|' + r['trial_id']))
    request_bytes = ('\n'.join(canonical(x) for x in requests) + '\n').encode()
    assert len(requests) == len({r['trial_id'] for r in requests}) == 200
    (HERE / 'planned_requests.jsonl.gz').write_bytes(gzip.compress(request_bytes, mtime=0))
    protocol = dict(status='prepared, not executed', model_inference_calls=0, planned_requests=200, models=models,
                    design='50 WinoGrande labelled validation items. 15 groups contribute two opposite-gold rows with identical native visible input. 20 singleton groups contribute 10 items per label. Exclude all rows sharing a native prompt with the earlier pilot. Sample by salted hash.',
                    inferential_scope='Prespecified diagnostic strata. The sample deliberately enriches collisions. Report each stratum and model separately. It cannot estimate deployment prevalence or corpus-wide accuracy loss.',
                    intervention='The same item and model receive the exact captured native wire and a direct source-bound rendering. Option order, requested output format and generation settings are held fixed. The repaired renderer also removes unresolved template braces. No claim that its effects isolate one individual formatting change.',
                    primary='Within each model and each stratum, paired difference in source-correct accuracy between rendered conditions. Identify rows by source_row, not request position. Report discordant counts, counts scoring zero, and a paired 95% bootstrap interval resampling prompt groups within stratum (10000 draws, seed 20261113).',
                    secondary='Replay identical captured outputs through the shipped and source-correct reference routes. Within a fixed output set, inspect model-versus-constant ordering, scoring coverage, and any change between the two models; report ties. The question-level response and score must remain linked.',
                    missing='Keep every planned call in the denominator. Report known-correct and best/worst bounds for incomplete or unparseable responses, including bounds on paired differences. Group bootstrap intervals are conditional on the observed scoring convention; display sensitivity bounds alongside them.',
                    decision='An independently attributable real evaluation with a materially changed conclusion advances the external-impact claim. This controlled panel can establish consequences and remedy under the frozen protocol. A null or ambiguous result remains in the report.',
                    questions=50, paired_collision_groups=15, singleton_controls=20, pilot_wino_rows_excluded=len(excluded_indices),
                    manifest_uncompressed_sha256=hashlib.sha256(request_bytes).hexdigest(),
                    cases_compressed_sha256=hashlib.sha256((HERE / 'fresh_panel.jsonl.gz').read_bytes()).hexdigest())
    (HERE / 'NEXT_EXPERIMENT.json').write_text(json.dumps(protocol, indent=2) + '\n')
    print(json.dumps({k:protocol[k] for k in ['status','questions','paired_collision_groups','singleton_controls','planned_requests','model_inference_calls','manifest_uncompressed_sha256']}))


if __name__ == '__main__':
    main()
