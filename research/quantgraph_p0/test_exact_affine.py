import random
import unittest
from fractions import Fraction
from exact_affine import ExactSharedAxis,Tick,Mark,EvidenceIncomplete

class ExactAffineTests(unittest.TestCase):
    def chart(self,offset_a=('19','21'),offset_b=('79','81')):
        return ExactSharedAxis([Tick('100','-2','2'),Tick('0','98','102')],
                  [Mark('A',*offset_a),Mark('B',*offset_b)],'decreasing',True)
    def test_exact_dependency_narrowing(self):
        m=ExactSharedAxis([Tick('100','-2','2'),Tick('0','98','102')],
           [Mark('A','20','20'),Mark('B','80','80')],'decreasing',True)
        self.assertEqual(m.bound({'A':'1','B':'-1'}),(Fraction(288,5),Fraction(312,5)))
    def test_interval_extremes_contain_every_feasible_world(self):
        m=self.chart();lo,hi=m.bound({'A':'1','B':'-1'});rng=random.Random(20261123)
        count=0
        for _ in range(10000):
            top=Fraction(rng.randrange(9800,10201),100)
            bottom=Fraction(rng.randrange(-200,201),100)
            slope=(bottom-top)/100
            if not Fraction(-104,100)<=slope<=Fraction(-96,100):continue
            pA=Fraction(rng.randrange(1900,2101),100)
            pB=Fraction(rng.randrange(7900,8101),100)
            x=slope*(pA-pB)
            self.assertLessEqual(lo,x);self.assertGreaterEqual(hi,x)
            count+=1
        self.assertGreater(count,5000)
    def test_float_rejected(self):
        with self.assertRaises(EvidenceIncomplete):
            ExactSharedAxis([Tick('100',-2.0,2.0),Tick('0','98','102')],
                            [Mark('A','20','20')],'decreasing',True)
    def test_untrusted_source_refused(self):
        with self.assertRaises(EvidenceIncomplete):
            ExactSharedAxis([Tick('100','-2','2'),Tick('0','98','102')],
                            [Mark('A','20','20')],'decreasing',False)
    def test_ambiguous_axis_refused(self):
        with self.assertRaises(EvidenceIncomplete):
            ExactSharedAxis([Tick('100','0','100'),Tick('0','0','100')],
                            [Mark('A','20','20')],'decreasing',True)
    def test_out_of_range_refused(self):
        with self.assertRaises(EvidenceIncomplete):
            ExactSharedAxis([Tick('100','-2','2'),Tick('0','98','102')],
                            [Mark('A','120','121')],'decreasing',True)
    def test_existing_chart_strong_source_exact(self):
        m=ExactSharedAxis([Tick('104','100','100'),Tick('340','0','0')],
           [Mark('blue2018','167','175'),Mark('blue2013','195','203')],
           'decreasing',True)
        lo,hi=m.bound({'blue2018':'1'})
        self.assertLess(lo,Fraction(72));self.assertGreater(hi,Fraction(72))
        self.assertEqual(lo,Fraction(16500,236))
        self.assertEqual(hi,Fraction(17300,236))
    def test_both_slope_orientations(self):
        c=ExactSharedAxis([Tick('0','0','0'),Tick('100','100','100')],
             [Mark('A','20','22'),Mark('B','40','41')],'increasing',True)
        self.assertEqual(c.bound({'A':'1','B':'-1'}),(Fraction(-21),Fraction(-18)))
    def test_no_claim_outside_assumptions(self):
        self.assertFalse(self.chart().evidence_flags()['image_or_RAG_correctness_certified'])
if __name__=='__main__':unittest.main()
