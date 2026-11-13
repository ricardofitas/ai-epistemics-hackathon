#!/usr/bin/env python3
"""Separate source-quality-motivated 30-family cohort; no solver outputs.

The original 32-family gate is recorded as failed. This script never promotes
an uncertain/rejected first source judgment or edits a source question/gold.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'consequence_math_sources_20261113'
PLAN32_SHA = '99e811f788c9815d72f1e908d8db9cd7a515e2370eb51f2a412512f3bd108dfc'
VARIANTS = ('numeric', 'paraphrase', 'p1', 'p2')
EXPECTED = ('R002 R004 R005 R008 R009 R010 R012 R013 R015 R016 R017 R019 R020 R021 R023 '
            'R024 R025 R026 R027 R028 R029 R030 R034 R038 R039 R041 R043 R044 R047 R049').split()
REVIEWS = ('source_review_a.jsonl', 'reserve_source_review_a.jsonl',
           'source_review_b.jsonl', 'reserve_source_review_b.jsonl')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def scalar(v):
    require(isinstance(v, (str, int, float)) and not isinstance(v, bool), 'Non-numeric computed answer')
    text = str(v).strip()
    if ',' in text:
        import re
        require(re.fullmatch(r'[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?', text), 'Bad thousands separator')
        text = text.replace(',', '')
    return Fraction(text)

def load_stream(source, names, expected):
    records, refs = {}, {}
    for name in names:
        path = source / name
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            ids = [row[k] for k in ('review_id', 'response_id') if k in row]
            require(ids and len(set(ids)) == 1, 'Missing/conflicting review ID')
            rid = ids[0]
            require(rid in expected and rid not in records, 'Unknown/duplicate source review: ' + rid)
            require(row.get('source_family_id') == expected[rid], 'Source-family mismatch: ' + rid)
            records[rid] = row
            refs[rid] = {'path': 'source_reviews/' + name, 'sha256': sha(path)}
    require(set(records) == set(expected), 'Each first-review stream must cover all50 families')
    return records, refs

def assess(row, family):
    reasons = []
    if row.get('family_disposition') != 'pass':
        reasons.append('family_disposition_not_pass:' + str(row.get('family_disposition')))
    checks = row.get('variant_checks')
    if not isinstance(checks, dict) or set(checks) != set(VARIANTS):
        reasons.append('missing_or_unexpected_four_variant_checks'); checks = {}
    gold = {v['variant']: v['gold_answer'] for v in family['variants']}
    for name in VARIANTS:
        c = checks.get(name, {})
        if c.get('gold_status') != 'pass':
            reasons.append(name + ':gold_status_not_pass')
        try:
            if scalar(c.get('computed_answer')) != scalar(gold[name]):
                reasons.append(name + ':computed_answer_disagrees_with_unchanged_source_gold')
        except (ValueError, ZeroDivisionError, TypeError, OverflowError):
            reasons.append(name + ':invalid_or_missing_computed_answer')
        if name in ('numeric', 'paraphrase') and c.get('target_structure_status') not in ('pass', 'same', 'preserved'):
            reasons.append(name + ':target_structure_not_preserved')
        if not any(c.get(k) for k in ('arithmetic_evidence', 'evidence', 'derivation', 'equation', 'rationale')):
            reasons.append(name + ':missing_independent_arithmetic_evidence')
    return {'accepted': not reasons, 'reasons': reasons}

def prepare(source, out):
    require(sha(source / 'selection_plan.json') == PLAN32_SHA, 'Original32 source plan changed')
    oldplan = read(source / 'selection_plan.json')
    for name, digest in oldplan['input_sha256'].items():
        require(sha(source / name) == digest, 'Original source preparation changed: ' + name)
    for item in read(source / 'source_manifest.json'):
        name = item['name'] + ('.md' if item['name'].endswith('readme') else '.jsonl')
        require(sha(source / name) == item['sha256'], 'Raw source changed: ' + name)
    ranked = read(source / 'ranked_candidate_families.json')['families']
    require(len(ranked) == 50 and [f['candidate_rank'] for f in ranked] == list(range(1,51)), 'Bad50-family priority')
    require(ranked == sorted(ranked, key=lambda f:(hashlib.sha256(f"2026111391|{f['source_family_id']}".encode()).hexdigest(),f['source_family_id'])), 'Priority order changed')
    expected = {f"R{f['candidate_rank']:03d}":f['source_family_id'] for f in ranked}
    a, ar = load_stream(source, REVIEWS[:2], expected)
    b, br = load_stream(source, REVIEWS[2:], expected)
    rows, accepted = [], []
    for family in ranked:
        rid = f"R{family['candidate_rank']:03d}"
        aa, bb = assess(a[rid], family), assess(b[rid], family)
        eligible = aa['accepted'] and bb['accepted']
        rows.append({'review_id':rid,'source_family_id':family['source_family_id'],
            'candidate_rank':family['candidate_rank'],'source_eligible':eligible,
            'raw_first_review_a':a[rid],'raw_first_review_b':b[rid],
            'review_a_assessment':aa,'review_b_assessment':bb,
            'review_file_a':ar[rid],'review_file_b':br[rid]})
        if eligible:
            accepted.append((rid,family))
    require([rid for rid,_ in accepted] == EXPECTED, 'Both-pass pool differs from predeclared30 IDs; stop')
    require(len(accepted) == 30 < 32, 'Original32 gate status changed; stop')
    review_hashes = {name:sha(source/name) for name in REVIEWS}
    gate = {'status':'failed_insufficient_source_valid_families','cohort':'original32family_consequence_plan',
        'required_families':32,'strict_both_first_pass_families':30,
        'candidate_families_reviewed':50,'excluded_or_uncertain_families':20,
        'accepted_review_ids':EXPECTED,'no_solver_outputs_generated_or_inspected':True,
        'no_relaxation_or_coordinator_override':True,'original_selection_plan_sha256':PLAN32_SHA,
        'first_review_sha256':review_hashes,
        'consequence':'Original32-family study is stopped before solver inference. A separate30-family cohort must be frozen as a new source-quality-motivated study.'}
    gate_path = source / 'GATE32_FAILED.json'
    if gate_path.exists():
        prior = read(gate_path)
        require(prior.get('strict_both_first_pass_families',prior.get('eligible_family_count')) == 30,
                'Existing original32 gate disagrees')
    else:
        write(gate_path,gate)
    out.mkdir(parents=True,exist_ok=True)
    for name in ('selected_data.json','source_disposition.json','selection_plan30.json'):
        require(not(out/name).exists(),'Refusing to overwrite30-family source output: '+name)
    for name in REVIEWS:
        target=out/'source_reviews'/name;target.parent.mkdir(parents=True,exist_ok=True)
        require(not target.exists(),'Review copy already exists: '+str(target));shutil.copyfile(source/name,target)
        require(sha(target)==review_hashes[name],'First-review byte mismatch')
    for name in ('ranked_candidate_families.json','selection_plan.json','source_manifest.json','GATE32_FAILED.json'):
        target=out/'source_inputs'/name;target.parent.mkdir(parents=True,exist_ok=True)
        require(not target.exists(),'Source input copy exists');shutil.copyfile(source/name,target)
    plan={'cohort_id':'consequence-math30-20261113','status':'new_source_only_cohort_before_solver_inference',
        'motivation':'The original exact32-family gate failed with only30 families passing both independent first source reviews. Preserve that failure; accept all30 strict passes in a separate cohort without overriding uncertainty.',
        'original32_gate_sha256':sha(gate_path),'original_selection_plan_sha256':PLAN32_SHA,
        'source_family_order_seed':2026111391,
        'order':'Retain original SHA256 priority order; use all30 strict both-pass families, no further subset selection.',
        'accepted_review_ids':EXPECTED,'family_count':30,'variants_per_family':4,
        'selection_slots':list(range(1,16)),'confirmation_slots':list(range(16,31)),
        'source_gate':'Both unmodified first family_disposition pass; all four gold_status pass; both independently computed numeric answers equal unchanged source gold; numeric/paraphrase structure pass/same/preserved; independent arithmetic evidence. No coordinator overrides, no question/gold edits.',
        'replacement':'None. All30 eligible families are included. Any later source invalidity stops this cohort for a separate amendment.',
        'batching':'Five common blocks of three distinct families per role, same blocks across four variants and two solvers; selection and confirmation never share a request.',
        'planned_main_requests':80,'planned_format_requests':2,'planned_total_requests':82,
        'target_scope':'Numerical substitution and harmless paraphrase are distinct target examples; their conjunction is not a composition test in the same problem.',
        'no_solver_outputs_generated_or_inspected':True,'human_source_validation':'pending; two independent agent first reviews',
        'source_review_sha256':review_hashes,
        'source_manifest_sha256':sha(source/'source_manifest.json'),
        'ranked_candidate_families_sha256':sha(source/'ranked_candidate_families.json')}
    write(out/'selection_plan30.json',plan)
    finalslots={f['source_family_id']:i for i,(_,f) in enumerate(accepted,1)}
    for row in rows:
        row['final_selected_slot']=finalslots.get(row['source_family_id'])
    disposition={'status':'all30_strict_source_passes_selected','cohort_id':plan['cohort_id'],
        'created_utc':datetime.now(timezone.utc).isoformat(),'no_solver_outputs_generated_or_inspected':True,
        'selection_plan_sha256':sha(out/'selection_plan30.json'),'source_gate32_failed_sha256':sha(gate_path),
        'prepare_source30_sha256':sha(Path(__file__)),'candidate_families':50,'accepted_families':30,
        'excluded_or_uncertain_families':20,'coordinator_overrides':0,'question_or_gold_edits':0,
        'first_review_sha256':review_hashes,'families':rows}
    write(out/'source_disposition.json',disposition)
    lookup={r['source_family_id']:r for r in rows}
    families=[]
    for slot,(rid,family) in enumerate(accepted,1):
        entry={k:v for k,v in family.items() if k not in ('initial_status','source_validation_status')}
        entry.update({'status':'accepted','source_validation_status':'accepted','selection_slot':slot,
            'analysis_role':'selection' if slot<=15 else 'confirmation',
            'batch_block':((slot-1)%15)//3+1,'source_review_id':rid,
            'source_review_references':{'a':lookup[family['source_family_id']]['review_file_a'],
                                       'b':lookup[family['source_family_id']]['review_file_b']}})
        families.append(entry)
    data={'status':'accepted_source_reviewed','cohort_id':plan['cohort_id'],'family_count':30,
        'variants_per_family':4,'selection_plan_sha256':sha(out/'selection_plan30.json'),
        'source_disposition_sha256':sha(out/'source_disposition.json'),'source_review_gate':'strict_both_first_pass_no_overrides',
        'no_solver_outputs_generated_or_inspected':True,'families':families,
        'scope':plan['target_scope'],'human_source_validation':plan['human_source_validation']}
    write(out/'selected_data.json',data)
    print(json.dumps({'status':data['status'],'cohort_id':plan['cohort_id'],'families':30,
        'selection':15,'confirmation':15,'main_requests':80,'format_requests':2,
        'selected_data_sha256':sha(out/'selected_data.json'),
        'source_disposition_sha256':sha(out/'source_disposition.json'),
        'selection_plan30_sha256':sha(out/'selection_plan30.json'),
        'original32_gate_sha256':sha(gate_path)}))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-dir',type=Path,default=SOURCE)
    ap.add_argument('--output-dir',type=Path,default=HERE)
    args=ap.parse_args();prepare(args.source_dir.resolve(),args.output_dir.resolve())

if __name__=='__main__':
    main()
