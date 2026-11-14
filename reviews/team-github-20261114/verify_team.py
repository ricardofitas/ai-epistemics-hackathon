"""Read-only verification of AntGalasso branch d4419f1; no model calls."""
from pathlib import Path
import sys, json, dataclasses, hashlib
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'snapshot'))
from gammaf_epistemic import load_debates, score_debate, discrepancy_table, Debate, Round
from gammaf_epistemic.audit_proofs import shadow_summary, shadow_events
from gammaf_epistemic.stats_eval import split_questions

debates=load_debates(with_trajectories=False)
assert len(debates)==11200
assert all(int(score_debate(d).g_del)==d.actual and int(score_debate(d).g_release)==d.published for d in debates)
table=discrepancy_table(debates)
assert table['matches_reference']
tune,held=split_questions(debates)
assert len(tune)==80 and len(held)==320 and not(tune&held)
before=('A','A','A','A','A','B','B','B','A','A')
after=('B','B','B','B','B','B','A','A','A','A')
flags=(0,)*10
adj=tuple(tuple(int(i!=j) for j in range(10)) for i in range(10))
d=Debate(dataset='MMLU',method='BlindGuard',item=1,graph='chain',gold='A',votes=after,flags=flags,executed_rounds=2,published=0,actual=0,all_answer='B',delivered='B',rounds=(Round(0,before,flags),Round(1,after,flags)),adjacency=adj,insiders=(5,6,7),attack_target='B')
c=dataclasses.replace(d,method='no_defense_baseline')
assert shadow_events(d) and shadow_events(c)
mixed=shadow_summary([d,c])
assert mixed['detector_rate_percent']==100 and mixed['control_rate_percent']==100
assert mixed['contamination_rate_percent']==200
assert mixed['contaminated_debates']==2
saved=json.loads((BASE/'snapshot/artifacts/results.json').read_text())
s=saved['shadow']
det_hits=sum(v['contaminated'] for v in s['by_task'].values())
assert det_hits==217
control_hits=s['contaminated_debates']-det_hits
assert control_hits==323
assert abs(100*det_hits/s['detector_debates']-s['detector_rate_percent'])<1e-10
all_rate=100*(det_hits+control_hits)/(s['detector_debates']+s['control_debates'])
report={'branch':'feat/gammaf-epistemic-audit','commit':'d4419f160252adee3d639df9ea23cd1600277c32','new_model_calls':0,'terminal_data_sha256':hashlib.sha256((BASE/'snapshot/swarmlab-gammaf/gammaf_handoff/gamma_debates.jsonl.gz').read_bytes()).hexdigest(),'terminal_only_replay':{'debates':len(debates),'all_11200_saved_labels_match':True,'discrepancy':table['totals'],'control_disagreements':table['controls']['disagreements'],'tune_questions':len(tune),'held_questions':len(held),'question_split_disjoint':True},'reproduced_bug':{'kind':'mixed_population_shadow_summary','minimal_witness':{'detector_debates':mixed['detector_debates'],'control_debates':mixed['control_debates'],'detector_rate_percent':mixed['detector_rate_percent'],'control_rate_percent':mixed['control_rate_percent'],'contamination_rate_percent':mixed['contamination_rate_percent'],'mean_events_per_contaminated_debate':mixed['mean_events_per_contaminated_debate']},'saved_artifact':{'detector_hits':det_hits,'detector_denominator':s['detector_debates'],'detector_rate_percent':s['detector_rate_percent'],'control_hits':control_hits,'control_denominator':s['control_debates'],'control_rate_percent':s['control_rate_percent'],'contaminated_debates_combined':s['contaminated_debates'],'published_mixed_denominator_rate_percent':s['contamination_rate_percent'],'correct_combined_population_rate_percent':all_rate,'detector_events':s['events'],'correct_detector_events_per_detector_hit':s['events']/det_hits,'published_events_over_combined_hits':s['mean_events_per_contaminated_debate']}},'limitations':['Terminal labels replayed from committed compact projection, not independent public-source authentication.','28 upstream raw trajectory files are absent from Git tree. New full-trajectory detector and shadow rates not independently rerun. Handoff documents a source-download setup for old replay.','Shadow events are observational temporal adjacency/vote-change patterns; no counterfactual model intervention proves transmission.','EpistemicGuard is offline reaggregation of trajectories generated under other detectors; no live superiority claim verified.']}
(BASE/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
