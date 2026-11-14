"""Regression coverage for population consistency in shadow summaries."""
from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gammaf_epistemic import Debate, Round
from gammaf_epistemic import audit_proofs as audit


def exposure(method='BlindGuard', item=1):
    before=('A','A','A','A','A','B','B','B','A','A')
    after=('B','B','B','B','B','B','A','A','A','A')
    flags=(0,)*10
    adjacency=tuple(tuple(int(i != j) for j in range(10)) for i in range(10))
    return Debate(dataset='MMLU', method=method, item=item, graph='chain', gold='A',
        votes=after, flags=flags, executed_rounds=2, published=0, actual=0,
        all_answer='B', delivered='B', rounds=(Round(0,before,flags), Round(1,after,flags)),
        adjacency=adjacency, insiders=(5,6,7), attack_target='B')


def test_mixed_populations_do_not_produce_200_percent():
    detector=exposure()
    control=replace(detector, method='no_defense_baseline')
    s=audit.shadow_summary([detector,control])
    n=len(audit.shadow_events(detector))
    assert n > 0
    assert s['detector_contaminated_debates']==1
    assert s['control_contaminated_debates']==1
    assert s['contaminated_debates']==2
    assert s['detector_rate_percent']==100
    assert s['control_rate_percent']==100
    assert s['contamination_rate_percent']==100
    assert s['total_events']==2*n
    assert s['mean_events_per_contaminated_debate']==n
    assert s['detector_mean_events_per_contaminated_debate']==n
    assert s['control_mean_events_per_contaminated_debate']==n


@pytest.mark.parametrize('method',['BlindGuard','no_defense_baseline'])
def test_single_population_uses_its_own_denominator(method):
    d=exposure(method)
    s=audit.shadow_summary([d])
    assert s['contamination_rate_percent']==100
    assert s['mean_events_per_contaminated_debate']==len(audit.shadow_events(d))
    assert s['detector_contaminated_debates']+s['control_contaminated_debates']==1


def test_empty_population_returns_zero_rates():
    s=audit.shadow_summary([])
    for k in ('contamination_rate_percent','detector_rate_percent','control_rate_percent',
              'mean_events_per_contaminated_debate','detector_mean_events_per_contaminated_debate',
              'control_mean_events_per_contaminated_debate'):
        assert s[k]==0


def test_saved_population_totals_have_consistent_rates(monkeypatch):
    # Test aggregation with the saved study's populations; this does not claim
    # to regenerate event classifications without the public raw trajectories.
    detector_count, control_count=5518,1341
    d=exposure()
    debates=[replace(d,item=i) for i in range(detector_count)]
    debates += [replace(d,item=i,method='no_defense_baseline') for i in range(control_count)]
    def fixed_events(debate,**kwargs):
        i=debate.item
        if debate.is_control:
            count=4+int(i<41) if i<323 else 0
        else:
            count=2+int(i<125) if i<217 else 0
        return [audit.ShadowEvent(debate.key, 0, 5, 1)]*count
    monkeypatch.setattr(audit,'shadow_events',fixed_events)
    monkeypatch.setattr(audit,'score_debate',lambda _:SimpleNamespace(g_del=False))
    s=audit.shadow_summary(debates)
    assert s['detector_contaminated_debates']==217
    assert s['control_contaminated_debates']==323
    assert s['events']==559
    assert s['control_events']==1333
    assert s['total_events']==1892
    assert s['detector_rate_percent']==pytest.approx(3.932584269662921)
    assert s['control_rate_percent']==pytest.approx(24.086502609992543)
    assert s['contamination_rate_percent']==pytest.approx(7.872867764980318)
    assert s['mean_events_per_contaminated_debate']==pytest.approx(1892/540)
    assert s['detector_mean_events_per_contaminated_debate']==pytest.approx(559/217)
    assert s['control_mean_events_per_contaminated_debate']==pytest.approx(1333/323)
