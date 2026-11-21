#!/usr/bin/env python3
"""Offline unit tests: synthetic reports only, never original SWDF heldout data."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from candidate3_counterfactual_oracle_gap import interpret, ALTERNATIVES, SCHEMA


def synthetic_report(scores):
    def arm(gain):
        return {"full_query_correctness_gate": True, "economic": {
            "valid": True,
            "projected_unexecuted_original_full_period_net_point_ms": gain,
            "day_cluster_bootstrap_95_projected_net_ms": [gain - 1, gain + 1]}}
    return {"schema": SCHEMA, "selected_real_policy": "no_move",
        "initial_training_source_audit": {
            "observed_exact_eligible_occurrences_by_split": {
                "train": 4707, "construction": 450, "calibration": 544, "test": 1441}},
        "methods": {"no_move": arm(50), **{
            name: arm(scores[i]) for i, name in enumerate(ALTERNATIVES)}}}


class VerdictTests(unittest.TestCase):
    def test_hypothetical_winner_not_claimed_as_real_policy_profit(self):
        r = interpret(synthetic_report([-3, 4, 11, 5]))
        self.assertEqual(r["real_controller_incremental_gain_vs_static_ms"], 0)
        self.assertEqual(r["best_hypothetical_action"], "replica_only")
        self.assertEqual(r["posthoc_oracle_gap_vs_safe_controller_ms"], 11)
        self.assertFalse(r["journal_GO"])

    def test_all_negative_says_no_detected_placement_upside(self):
        r = interpret(synthetic_report([-3, -4, -1, -5]))
        self.assertEqual(r["best_hypothetical_action"], "no_move")
        self.assertEqual(r["best_hypothetical_gain_ms"], 0)

    def test_semantic_failure_blocks_complete_oracle(self):
        data = synthetic_report([1, 2, 3, 4])
        data["methods"]["one_swap"]["full_query_correctness_gate"] = False
        r = interpret(data)
        self.assertEqual(r["diagnostic_oracle"], "BLOCKED_NOT_ALL_ARMS_VALID")
        self.assertFalse(r["comparison_arms_all_valid"])

    def test_invalid_point_or_interval_blocks_oracle(self):
        for invalid in (float("nan"), float("inf"), None):
            with self.subTest(invalid=invalid):
                data = synthetic_report([1, 2, 3, 4])
                data["methods"]["one_swap"]["economic"][
                    "projected_unexecuted_original_full_period_net_point_ms"] = invalid
                self.assertEqual(interpret(data)["diagnostic_oracle"],
                                 "BLOCKED_NOT_ALL_ARMS_VALID")

    def test_missing_arm_rejected(self):
        data = synthetic_report([1, 2, 3, 4])
        del data["methods"]["swap_replica"]
        with self.assertRaisesRegex(ValueError, "Missing or unexpected"):
            interpret(data)

    def test_policy_hindsight_rejected(self):
        data = synthetic_report([1, 2, 3, 4])
        data["selected_real_policy"] = "one_swap"
        with self.assertRaisesRegex(ValueError, "no_move"):
            interpret(data)

    def test_count_drift_rejected(self):
        data = synthetic_report([1, 2, 3, 4])
        data["initial_training_source_audit"][
            "observed_exact_eligible_occurrences_by_split"]["test"] = 1440
        with self.assertRaisesRegex(ValueError, "eligibility"):
            interpret(data)

    def test_invalid_baseline_semantics_blocks(self):
        data = synthetic_report([1, 2, 3, 4])
        data["methods"]["no_move"]["full_query_correctness_gate"] = False
        self.assertEqual(interpret(data)["status"], "INVALID_BASELINE_SEMANTICS")


if __name__ == "__main__":
    unittest.main()
