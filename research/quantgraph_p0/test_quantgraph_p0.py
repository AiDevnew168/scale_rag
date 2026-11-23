import unittest,math,random
from quantgraph_p0 import Axis,Tick,Mark,CorrelatedChart,EvidenceError,union_of_branch_bounds
HASH='0'*64

def build(p1=(20,20),p2=(80,80),t1=(-2,2),t2=(98,102),verified=True):
    return CorrelatedChart(Axis(HASH,'chart-1','percent','decreasing','linear',
        (Tick(100,*t1),Tick(0,*t2)),verified),
        (Mark('A',*p1),Mark('B',*p2)))

class P0(unittest.TestCase):
    def test_correlated_calibration_tightens_difference(self):
        x=build()
        coupled=x.bound({'A':1,'B':-1})
        loose=x.independent_baseline({'A':1,'B':-1})
        self.assertAlmostEqual(coupled[0],57.6,places=4)
        self.assertAlmostEqual(coupled[1],62.4,places=4)
        self.assertLess(coupled[1]-coupled[0],loose[1]-loose[0])

    def test_width_ambiguity_refuses_exact_point(self):
        x=build()
        self.assertEqual(x.answer({'A':1,'B':-1},0.1)['decision'],'ABSTAIN_EXACT_VALUE')
        self.assertEqual(x.answer({'A':1,'B':-1},3)['decision'],'BOUNDED_WITHIN_TOLERANCE')

    def test_mark_pixel_uncertainty_widens_interval(self):
        tight=build().bound({'A':1,'B':-1})
        wider=build((19,21),(79,81)).bound({'A':1,'B':-1})
        self.assertLessEqual(wider[0],tight[0]);self.assertGreaterEqual(wider[1],tight[1])

    def test_ambiguous_series_union_must_not_choose_favorable(self):
        x=build()
        u=union_of_branch_bounds([(x,{'A':1,'B':-1}),
                                  (x,{'A':-1,'B':1})])
        self.assertEqual(u['n_plausible_bindings'],2)
        self.assertLess(u['convex_hull'][0],0)
        self.assertGreater(u['convex_hull'][1],0)
        self.assertFalse(u['claims_actual_correct_visual_binding'])

    def test_unchecked_evidence_fails_closed(self):
        with self.assertRaises(EvidenceError):build(verified=False)

    def test_unsupported_log_axis_fails_closed(self):
        with self.assertRaises(EvidenceError):
            CorrelatedChart(Axis(HASH,'c','units','decreasing','log',
                                 (Tick(100,0,0),Tick(0,100,100)),True),
                           [Mark('A',20,20)])

    def test_inconsistent_source_ticks_fails_closed(self):
        with self.assertRaises(EvidenceError):
            CorrelatedChart(Axis(HASH,'c','units','decreasing','linear',
                                 (Tick(100,0,0),Tick(100,100,100)),True),
                           [Mark('A',20,20)])

    def test_no_anchor_tick_extrapolation_guess(self):
        with self.assertRaises(EvidenceError):
            CorrelatedChart(Axis(HASH,'c','units','decreasing','linear',
                                 (Tick(100,0,0),),True),[Mark('A',20,20)])

    def test_invalid_bounds_are_rejected(self):
        with self.assertRaises(EvidenceError):build(p1=(23,19))

    def test_pixel_orientation_is_semantically_required(self):
        with self.assertRaises(EvidenceError):
            CorrelatedChart(Axis(HASH,'c','units','increasing','linear',
                                 (Tick(100,0,0),Tick(0,100,100)),True),[Mark('A',20,20)])

    def test_adversarial_randomized_feasible_worlds_always_inside_bounds(self):
        rng=random.Random(20261123)
        x=build((19,21),(79,81))
        lo,hi=x.bound({'A':1,'B':-1})
        b_lo,b_hi=x.independent_baseline({'A':1,'B':-1})
        self.assertGreater(b_hi-b_lo,hi-lo)
        for _ in range(1000):
            a=-(.96+.08*rng.random())
            top=98+4*rng.random()
            bottom=top+100*a
            if not (-2<=bottom<=2):continue
            pA=19+2*rng.random();pB=79+2*rng.random()
            value=a*(pA-pB)
            self.assertLessEqual(lo-1e-6,value)
            self.assertGreaterEqual(hi+1e-6,value)

    def test_extrapolation_without_revalidated_source_fails(self):
        with self.assertRaises(EvidenceError):build(p1=(-1,0))

    def test_no_generalizes_without_source_proof(self):
        out=build().answer({'A':1,'B':-1},0.1)
        self.assertFalse(out['probabilistic_confidence_claim'])
        self.assertFalse(out['formal_floating_point_certificate'])

    def test_missing_binding_inventory_fails_closed(self):
        with self.assertRaises(EvidenceError):union_of_branch_bounds([])

if __name__=='__main__':unittest.main()
