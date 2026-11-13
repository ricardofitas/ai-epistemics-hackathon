import itertools
from fractions import Fraction
import unittest

from gap_bounds import family_gap_bounds, mean_family_bounds, signed_coefficients

SPEC = dict(model_a='a', model_b='b', comparison_weights={'c1':'1/2','c2':'1/2'}, target_weights={'t1':'1/2','t2':'1/2'})
KEYS = list(itertools.product(('a','b'), ('c1','c2','t1','t2')))

class GapBoundsTest(unittest.TestCase):
    def test_complete_signed_interaction(self):
        pred = {key:(0,0) for key in KEYS}
        pred['b','c1']=(1,1); pred['b','c2']=(1,1)
        self.assertEqual(family_gap_bounds(pred, **SPEC), (1,1))
        inverse = {key:((1-lo),(1-hi)) for key,(lo,hi) in pred.items()}
        self.assertEqual(family_gap_bounds(inverse, **SPEC), (-1,-1))

    def test_sharp_unknown_bounds_against_every_assignment(self):
        pred = {key:(0,1) for key in KEYS}
        pred['b','c1']=(1,1); pred['a','t2']=(0,0)
        actual=[]
        unknown=[k for k,v in pred.items() if v==(0,1)]
        for assignment in itertools.product((0,1), repeat=len(unknown)):
            exact = dict(pred)
            exact.update({key:(value,value) for key,value in zip(unknown,assignment)})
            actual.append(family_gap_bounds(exact, **SPEC)[0])
        self.assertEqual(family_gap_bounds(pred, **SPEC), (min(actual),max(actual)))

    def test_shared_unknown_outcomes_cancel_before_bounding(self):
        spec=dict(model_a='a',model_b='b',comparison_weights={'same':1},target_weights={'same':1})
        self.assertEqual(signed_coefficients(**spec),{})
        self.assertEqual(family_gap_bounds({('a','same'):(0,1),('b','same'):(0,1)},**spec),(0,0))

    def test_equal_family_weighting_with_rational_results(self):
        self.assertEqual(mean_family_bounds([(0,1),(1,1),(0,0)]),(Fraction(1,3),Fraction(2,3)))

    def test_reject_missing_prediction_and_bad_weights(self):
        with self.assertRaises(ValueError): family_gap_bounds({},**SPEC)
        for weights in ({'x':'1/3'},{'x':-1,'y':2},{'x':0.5,'y':0.5},{}):
            with self.assertRaises(ValueError):
                signed_coefficients('a','b',weights,{'x':1})
        with self.assertRaises(ValueError): mean_family_bounds([])

if __name__=='__main__': unittest.main()
