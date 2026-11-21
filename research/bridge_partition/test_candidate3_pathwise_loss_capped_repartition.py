#!/usr/bin/env python3
"""Prove by adversarial paths that loss-capped migration cannot overspend L."""
import random,unittest
from candidate3_pathwise_loss_capped_repartition import LossCappedTrial,UncertifiableTrial
def trial(**kw):
    x=dict(total_loss_budget_ms=100,
       hard_max_single_request_regret_ms=10,
       certified_max_revert_ms=20,
       actually_paid_migration_ms=30,
       full_shadow_pairing_available=True,
       semantic_correctness_verified=True,
       physically_enforced_regret_ceiling=True,
       revert_upper_is_certified=True)
    x.update(kw)
    return LossCappedTrial(**x)
def step(t,reward):
    # Actual migrated query longer if reward negative.
    return t.observe_real_paired_query(
      static_full_ms=100,migrated_full_ms=100-reward,
      additional_shadow_metering_ms=0)
class AdversarialLossTrials(unittest.TestCase):
    def test_max_regret_adversarial_sequence_reverts_at_hard_limit(self):
        t=trial()
        while True:
            result=step(t,-10)
            if result["must_revert_now_before_next_request"]:break
        out=t.revert(20)
        self.assertTrue(out["loss_budget_respected"])
        self.assertGreaterEqual(t.net_ms,-100)
    def test_many_arbitrary_sequences_never_cross_bound(self):
        for seed in range(75):
            t=trial()
            rng=random.Random(seed)
            for _ in range(250):
                reward=rng.uniform(-10,25)
                res=step(t,reward)
                if res["must_revert_now_before_next_request"]:
                    break
            out=t.revert(rng.uniform(0,20))
            self.assertTrue(out["loss_budget_respected"])
    def test_favorable_history_can_accumulate_real_profit(self):
        t=trial()
        for _ in range(40):step(t,+5)
        out=t.revert(20)
        self.assertGreater(out["final_realized_net_relative_no_move_ms"],0)
    def test_sudden_switch_to_all_bad_requests_still_bounded(self):
        t=trial()
        for _ in range(10):step(t,+2)
        for _ in range(200):
            if step(t,-10)["must_revert_now_before_next_request"]:
                break
        out=t.revert(20)
        self.assertGreaterEqual(out["final_realized_net_relative_no_move_ms"],-100)
    def test_initial_migration_alone_can_exceed_risk_budget(self):
        with self.assertRaises(UncertifiableTrial):trial(actually_paid_migration_ms=71)
    def test_unmetered_shadow_is_not_safe(self):
        with self.assertRaises(UncertifiableTrial):trial(full_shadow_pairing_available=False)
    def test_missing_full_sparql_correctness_fails_closed(self):
        with self.assertRaises(UncertifiableTrial):trial(semantic_correctness_verified=False)
    def test_unbounded_latency_would_void_distribution_free_claim(self):
        with self.assertRaises(UncertifiableTrial):trial(physically_enforced_regret_ceiling=False)
    def test_revert_cost_not_certified_blocks_entry(self):
        with self.assertRaises(UncertifiableTrial):trial(revert_upper_is_certified=False)
    def test_incorrect_time_outlier_breaks_assumptions(self):
        t=trial()
        with self.assertRaises(UncertifiableTrial):
            step(t,-11)
    def test_metering_overhead_must_be_subtracted(self):
        t=trial()
        x=t.observe_real_paired_query(static_full_ms=100,migrated_full_ms=98,
               additional_shadow_metering_ms=5)
        self.assertAlmostEqual(x["net_before_revert_ms"],-33)
    def test_revert_above_upper_is_not_certified(self):
        t=trial()
        with self.assertRaises(UncertifiableTrial):t.revert(21)
    def test_reverting_twice_is_forbidden(self):
        t=trial();t.revert(1)
        with self.assertRaises(UncertifiableTrial):t.revert(1)
    def test_queries_not_allowed_after_revert(self):
        t=trial();t.revert(0)
        with self.assertRaises(UncertifiableTrial):step(t,3)
    def test_huge_shadow_cost_breaks_request_loss_ceiling(self):
        t=trial()
        with self.assertRaises(UncertifiableTrial):
            t.observe_real_paired_query(static_full_ms=100,migrated_full_ms=95,
                          additional_shadow_metering_ms=17)
if __name__=="__main__":unittest.main(verbosity=2)
