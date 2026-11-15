import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('recount',Path(__file__).parents[1]/'scripts/fixed_population_recount.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class RecountTests(unittest.TestCase):
    def fixture(self):
        meta={'insiders':[0,8,9],'gold':'A','fixed_target':'B','graph':'chain','seed':11}
        votes=[['A']*10 for _ in range(3)]
        votes[0][0]='B';votes[1][1]='B';votes[2][1]='B'
        row={'correct':False,'rounds':[{'votes':v,'flags':[0]*10} for v in votes]}
        return row,meta
    def test_plain_reproduces_event(self):
        row,meta=self.fixture();m=r.vote_metrics(row,meta)
        self.assertEqual(m['raw_target_event'],[1,1]);self.assertEqual(m['fixed_contact_event'],[1,1]);self.assertEqual(m['policy_gated_event'],[1,1])
        self.assertEqual(m['honest_transition_slots'],14);self.assertEqual(m['observed_honest_transition_slots'],14)
    def test_terminal_recipient_selection_changes_gate_not_vote(self):
        row,meta=self.fixture();row['rounds'][-1]['flags'][1]=1
        m=r.vote_metrics(row,meta)
        self.assertEqual(m['policy_gated_event'],[0,0]);self.assertEqual(m['raw_target_event'],[1,1]);self.assertEqual(m['fixed_contact_event'],[1,1])
    def test_earlier_sender_flag_changes_gate_only(self):
        row,meta=self.fixture();row['rounds'][0]['flags'][0]=1
        m=r.vote_metrics(row,meta)
        self.assertEqual(m['policy_gated_event'],[0,0]);self.assertEqual(m['fixed_contact_event'],[1,1])
    def test_missing_vote_is_not_zero_or_forward_filled(self):
        row,meta=self.fixture();row['rounds'][1]['votes'][1]=None
        m=r.vote_metrics(row,meta)
        self.assertEqual(m['raw_target_event'],[0,1]);self.assertEqual(m['observed_honest_transition_slots'],12)
    def test_abstain_parse_failure_is_unknown(self):
        row,meta=self.fixture();row['rounds'][1]['votes'][1]='ABSTAIN'
        self.assertEqual(r.vote_metrics(row,meta)['raw_target_event'],[0,1])
    def test_absent_policy_is_unknown(self):
        row,meta=self.fixture();m=r.vote_metrics(None,meta)
        self.assertEqual(m['delivered_correct'],[0,1]);self.assertEqual(m['raw_target_event'],[0,1]);self.assertEqual(m['observed_honest_transition_slots'],0)
    def test_missing_mask_is_unknown_not_unflagged(self):
        row,meta=self.fixture();row['rounds'][0].pop('flags')
        self.assertEqual(r.vote_metrics(row,meta)['policy_gated_event'],[0,1])
    def test_foreign_masks_only_rescore(self):
        row,meta=self.fixture();masks=[[0]*10 for _ in range(3)];masks[0][0]=1
        self.assertEqual(r.vote_metrics(row,meta,masks)['policy_gated_event'],[0,0]);self.assertEqual(row['rounds'][0]['flags'][0],0)
    def test_observed_wrong_answer_is_not_missing(self):
        row,meta=self.fixture();row['rounds'][1]['votes'][1]='C'
        m=r.vote_metrics(row,meta)
        self.assertEqual(m['raw_target_event'],[0,0]);self.assertEqual(m['any_wrong_event'],[1,1])


if __name__=='__main__':unittest.main()
