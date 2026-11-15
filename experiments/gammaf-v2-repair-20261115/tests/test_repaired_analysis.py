import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from analyze_repaired_results import postprocess
from fixed_population_recount import BASE,INLINE


class RepairedAnalysisTests(unittest.TestCase):
    def inputs(self,root):
        w={'task':'CSQA','item':1,'graph':'chain','seed':11,'gold':'A','fixed_target':'B','insiders':[0,8,9]}
        manifest={'manifest_sha256':'fixture','prompt_format':'full-labelled-options-v1','worlds':[w]}
        key='CSQA:1:chain:11'
        row=dict(w,world=key,arm=BASE,initial_insiders=w['insiders'],world_seed=11,correct=True,target='B',
                 rounds=[{'votes':['A']*10,'flags':[0]*10} for _ in range(3)])
        payload={'manifest_sha256':'fixture','mode':'mock','rows':[row],'failures':[]}
        (root/'manifest.json').write_text(json.dumps(manifest));(root/'results.json').write_text(json.dumps(payload))
        return payload
    def test_mock_and_missing_policy_remain_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.inputs(p)
            r=postprocess(p/'manifest.json',p/'results.json',p/'out',100)
            self.assertFalse(r['scientific_model_results'])
            self.assertEqual(r['paired_delivered_outcomes']['missing_one_or_both'],1)
            self.assertEqual(r['by_arm'][INLINE]['delivered_correct']['count_bounds'],[0,1])
    def test_rejects_foreign_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);data=self.inputs(p);data['manifest_sha256']='wrong';(p/'results.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):postprocess(p/'manifest.json',p/'results.json',p/'out',100)
    def test_rejects_changed_initial_roles(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);data=self.inputs(p);data['rows'][0]['initial_insiders']=[1,8,9];(p/'results.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):postprocess(p/'manifest.json',p/'results.json',p/'out',100)


if __name__=='__main__':unittest.main()
