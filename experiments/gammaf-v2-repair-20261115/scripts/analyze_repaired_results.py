#!/usr/bin/env python3
"""Postprocess the frozen repaired-prompt manifest and partial or final rows.

Every planned world remains in the denominator, even when a run is incomplete.
No API calls. Mock results are explicitly identified as harness validation.
"""
import argparse
import hashlib
import json
from pathlib import Path

from fixed_population_recount import ARMS, BASE, INLINE, analyze, load_population


def postprocess(manifest_path, results_path, out, draws=20000):
    manifest=json.loads(Path(manifest_path).read_text())
    payload=json.loads(Path(results_path).read_text())
    expected=manifest['manifest_sha256']
    if payload.get('manifest_sha256') != expected:
        raise ValueError('results do not belong to the frozen manifest')
    if manifest.get('prompt_format') != 'full-labelled-options-v1':
        raise ValueError('not a repaired full-labelled-options manifest')
    population=load_population(manifest_path)
    rows=payload['rows']
    for row in rows:
        if row['world'] not in population or row['arm'] not in ARMS:
            raise ValueError('unexpected world or arm')
        meta=population[row['world']]
        if sorted(row['initial_insiders']) != sorted(meta['insiders']) or row['world_seed'] != meta['seed']:
            raise ValueError('seed or initially malicious identities differ from the manifest')
    result, table=analyze(rows,population,draws=draws)
    result['scope']='Repaired full-labelled-options paired replication on a fixed previously used panel.'
    result['mode']=payload.get('mode')
    result['scientific_model_results']=payload.get('mode')=='adaption'
    if payload.get('mode') != 'adaption':
        result['scope']='MOCK HARNESS VALIDATION ONLY; not scientific model results.'
    result['manifest_sha256']=expected
    result['results_sha256']=hashlib.sha256(Path(results_path).read_bytes()).hexdigest()
    result['failures']=payload.get('failures',[])
    result['physical_attempts']=payload.get('physical_attempts')
    result['budget']=payload.get('budget')
    paired_counts={'gain':0,'loss':0,'both_correct':0,'both_incorrect':0,'missing_one_or_both':0}
    round1_mismatch=[]
    for world in population:
        base,inline=table.get((world,BASE)),table.get((world,INLINE))
        if base is None or inline is None:
            paired_counts['missing_one_or_both']+=1
            continue
        a,b=base.get('correct'),inline.get('correct')
        if a is None or b is None:paired_counts['missing_one_or_both']+=1
        elif a and b:paired_counts['both_correct']+=1
        elif not a and b:paired_counts['gain']+=1
        elif a and not b:paired_counts['loss']+=1
        else:paired_counts['both_incorrect']+=1
        ar=base.get('rounds',[]);br=inline.get('rounds',[])
        if ar and br and ar[0].get('votes')!=br[0].get('votes'):round1_mismatch.append(world)
    result['paired_delivered_outcomes']=paired_counts
    result['round1_mismatch_worlds']=round1_mismatch
    target=Path(out);target.mkdir(parents=True,exist_ok=True)
    (target/'repaired_fixed_population_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    compact={k:result[k] for k in ('scope','mode','scientific_model_results','manifest_sha256','by_arm','paired','paired_delivered_outcomes','round1_mismatch_worlds','physical_attempts')}
    (target/'repaired_analysis_summary.json').write_text(json.dumps(compact,indent=2)+'\n')
    print(json.dumps(compact,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True);p.add_argument('--results',required=True);p.add_argument('--out',required=True)
    p.add_argument('--draws',type=int,default=20000)
    a=p.parse_args();postprocess(a.manifest,a.results,a.out,a.draws)
