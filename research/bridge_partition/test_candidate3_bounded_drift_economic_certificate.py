#!/usr/bin/env python3
"""Fail-closed adversarial tests of the conditional future-net certificate."""
import math,unittest
from candidate3_bounded_drift_economic_certificate import (
    compute_bound,adversarial_impossibility_example,locality_witness_l1_difference)

def args():
    return dict(samples_by_action={"swap":[40.0]*64,
                                  "replica":[35.0]*64},
       training_fixed_actions=["swap","replica"],
       reward_abs_bound_ms=50.0,
       tail_delta=0.05,
       future_request_horizon=100,
       future_l1_drift_bound=0.1,
       l1_bound_is_externally_justified=True,
       migration_upper_ms_by_action={"swap":100.0,"replica":20.0},
       migration_upper_is_certified=True,
       calibration_is_independent_blocks=True,
       same_query_population_contract=True,
       full_sparql_correctness_gate=True)
class CertificateTests(unittest.TestCase):
    def test_conditional_positive_net_requires_all_premises(self):
        r=compute_bound(**args())
        self.assertEqual(r["selected"],"swap")
        self.assertTrue(r["full_expected_profit_certificate"])
        self.assertFalse(r["is_distribution_free_under_arbitrary_future_shift"])
        self.assertGreater(r["actions"]["swap"]["LCB_expected_net_ms_for_frozen_horizon"],0)
    def test_unknown_future_shift_refuses_even_positive_history(self):
        a=args()
        a["future_l1_drift_bound"]=None
        a["l1_bound_is_externally_justified"]=False
        r=compute_bound(**a)
        self.assertEqual(r["selected"],"no_move")
        self.assertEqual(r["status"],"ABSTAIN_UNCERTIFIED")
        self.assertIn("future_drift_not_verified",r["reasons"])
    def test_huge_shift_abstains(self):
        a=args();a["future_l1_drift_bound"]=2
        r=compute_bound(**a)
        self.assertEqual(r["status"],"ABSTAIN_NONPOSITIVE_NET_LOWER_BOUND")
    def test_single_measured_cutover_not_certified_cost(self):
        a=args();a["migration_upper_is_certified"]=False
        r=compute_bound(**a)
        self.assertEqual(r["selected"],"no_move")
        self.assertIn("full_migration_cost_upper_not_certified",r["reasons"])
    def test_semantically_incorrect_responses_veto_any_profit(self):
        a=args();a["full_sparql_correctness_gate"]=False
        r=compute_bound(**a)
        self.assertFalse(r["full_expected_profit_certificate"])
    def test_no_false_independence_of_query_repeats(self):
        a=args();a["calibration_is_independent_blocks"]=False
        r=compute_bound(**a)
        self.assertIn("independent_block_assumption_unmet",r["reasons"])
    def test_nonfinite_or_out_of_range_reward_forbidden(self):
        for v in (51.0,-51.0,float("nan")):
            a=args();a["samples_by_action"]["swap"][0]=v
            r=compute_bound(**a)
            self.assertEqual(r["selected"],"no_move")
            self.assertIn("unbounded_or_nonfinite_calibration_reward_swap",r["reasons"])
    def test_short_observation_abstains(self):
        a=args()
        a["samples_by_action"]={"swap":[40.0],"replica":[35.0]}
        r=compute_bound(**a)
        self.assertIn("unequal_or_insufficient_independent_days",r["reasons"])
    def test_simultaneous_union_bound_increases_with_more_actions(self):
        a=args()
        baseline=compute_bound(**a)
        a["training_fixed_actions"].append("extra")
        a["samples_by_action"]["extra"]=[10.0]*64
        a["migration_upper_ms_by_action"]["extra"]=1.0
        enlarged=compute_bound(**a)
        self.assertGreater(enlarged["actions"]["swap"]["simultaneous_Hoeffding_penalty_ms"],
                           baseline["actions"]["swap"]["simultaneous_Hoeffding_penalty_ms"])
    def test_incomplete_snapshot_or_future_population_refusal(self):
        a=args();a["same_query_population_contract"]=False
        r=compute_bound(**a);self.assertEqual(r["selected"],"no_move")
    def test_empty_or_unfrozen_action_library_rejected(self):
        a=args();a["training_fixed_actions"]=[]
        r=compute_bound(**a);self.assertEqual(r["status"],"ABSTAIN_UNCERTIFIED")
    def test_witness_touches_not_wallclock(self):
        old={"seen_A":3,"never_A":4}
        new={"seen_A":1,"never_A":1}
        self.assertEqual(locality_witness_l1_difference(old,new,{"seen_A"}),2)
        self.assertEqual(locality_witness_l1_difference(old,new,{"never_A"}),3)
    def test_impossible_to_guarantee_unbounded_future_drift(self):
        x=adversarial_impossibility_example()
        self.assertTrue(x["same_observed_history"])
        self.assertGreater(x["future_world_net_savings_ms"]["continuation_good"],0)
        self.assertLess(x["future_world_net_savings_ms"]["continuation_bad"],0)
if __name__=="__main__":unittest.main(verbosity=2)
