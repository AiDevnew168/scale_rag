"""Adversarial mathematical smoke checks. NOT an actual multimodal QA benchmark."""
from fractions import Fraction
import unittest
try:
    from .evidence_bounds import AxisLinear,Interval,LinearExpression,InsufficientEvidence,compare_gt,naive_independent_subtraction
except ImportError:
    from evidence_bounds import AxisLinear,Interval,LinearExpression,InsufficientEvidence,compare_gt,naive_independent_subtraction

class EvidenceContract(unittest.TestCase):
    def setUp(self):
        self.axis=AxisLinear.of("chart-A",100,0,0,100,calibration_verified=True)
        self.a=self.axis.read(Interval.of(39,41),mark_verified=True,observation_id="a")
        self.b=self.axis.read(Interval.of(49,51),mark_verified=True,observation_id="b")
        self.ev={self.a.key:self.a,self.b.key:self.b}
        self.x=LinearExpression.variable(self.a.key)
        self.y=LinearExpression.variable(self.b.key)
    def test_axis_inversion(self):
        self.assertEqual(self.a.values,Interval.of(59,61))
        self.assertEqual(self.b.values,Interval.of(49,51))
    def test_true_value_in_bounds(self):
        self.assertTrue(self.a.values.contains(60))
    def test_proven_comparison(self):
        self.assertEqual(compare_gt(self.x,self.y,self.ev).status,"PROVEN_TRUE")
        self.assertEqual(compare_gt(self.x,self.y,self.ev).margin,Interval.of(8,12))
    def test_reversed_comparison(self):
        self.assertEqual(compare_gt(self.y,self.x,self.ev).status,"PROVEN_FALSE")
    def test_shared_dependency(self):
        self.assertEqual(self.x.minus(self.x).evaluate(self.ev),Interval.of(0,0))
        self.assertEqual(naive_independent_subtraction(self.a.values,self.a.values),Interval.of(-2,2))
    def test_ambiguous_threshold_abstention(self):
        self.assertEqual(compare_gt(self.x,LinearExpression({},Fraction(60)),self.ev).status,"ABSTAIN")
    def test_missing_evidence(self):
        with self.assertRaises(InsufficientEvidence):self.x.evaluate({})
    def test_unverified_mark(self):
        with self.assertRaises(InsufficientEvidence):
            self.axis.read(Interval.of(39,41),mark_verified=False,observation_id="m")
    def test_unverified_axis(self):
        a=AxisLinear.of("chart-A",0,0,100,100,calibration_verified=False)
        with self.assertRaises(InsufficientEvidence):
            a.read(Interval.of(0,1),mark_verified=True,observation_id="m")
    def test_denominator_includes_zero(self):
        with self.assertRaises(InsufficientEvidence):
            Interval.of(1,2).div(Interval.of(-1,1))
    def test_binary_float_banned(self):
        with self.assertRaises(TypeError):Interval.of(0.1,0.2)
    def test_ratio(self):
        self.assertEqual(Interval.of(6,8).div(Interval.of(2,4)),Interval.of("1.5",4))
    def test_degenerate_axis(self):
        with self.assertRaises(InsufficientEvidence):
            AxisLinear.of("chart-A",0,0,0,100,calibration_verified=True)
    def test_pixel_location_sweep(self):
        for lo in range(20,80,5):
            for width in (1,2,3):
                obs=self.axis.read(Interval.of(lo,lo+width),mark_verified=True,observation_id="s")
                for step in range(11):
                    pixel=Fraction(lo)+Fraction(width*step,10)
                    self.assertTrue(obs.values.contains(100-pixel))
    def test_same_source_algebra(self):
        self.assertEqual(self.x.plus(self.y).minus(self.x).evaluate(self.ev),self.b.values)

if __name__=="__main__":
    unittest.main()
