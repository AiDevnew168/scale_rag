"""Synthetic invariants for original TRAIN-only 3-arm matched baseline.
These tests never fetch SWDF logs/graph or inspect historic heldout outcomes.
"""
import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import candidate3_swdf_train48_three_arm_same_run as experiment


class ThreeArmMatchedDesign(unittest.TestCase):
    def test_each_query_replication_rotates_arms_across_all_positions(self):
        for seed in (20261123,20261124,42,2026):
            orders=experiment.balanced_orders(seed)
            self.assertEqual(len(orders),3)
            self.assertEqual({tuple(v) for v in orders},set(map(tuple,orders)))
            for row in orders:
                self.assertEqual(set(row),set(experiment.METHODS))
            for index in range(3):
                self.assertEqual(
                    set(x[index] for x in orders),set(experiment.METHODS))

    def test_query_fingerprint_is_order_sensitive_and_stable(self):
        rows=[{"hash":"a"*64},{"hash":"b"*64}]
        x=hashlib.sha256(("a"*64+"|"+"b"*64).encode()).hexdigest()
        self.assertEqual(experiment.fingerprint(rows),x)
        self.assertNotEqual(x,experiment.fingerprint(rows[::-1]))

    @staticmethod
    def synthetic():
        rows=[]
        for i in range(48):
            h=f"{i:064x}"
            for rep in range(3):
                rows.append({
                    "text_sha256":h,
                    "family_sha256":f"{i%8:064x}",
                    "repeat":rep,
                    "elapsed_ms":{"central_indexed":2.0,
                        "full_fragment_ship":100.0,
                        "constant_pushdown":50.0},
                    "rdf_payload_bytes":{"central_indexed":0,
                        "full_fragment_ship":1000,
                        "constant_pushdown":200},
                    "solution_counts":{"central_indexed":1,
                        "full_fragment_ship":1,
                        "constant_pushdown":1}})
        return rows

    def test_three_arm_difference_and_bytes_are_not_conflated(self):
        metrics=experiment.aggregate(self.synthetic())
        self.assertEqual(metrics["constant_pushdown"]["mean_ms"],50)
        self.assertEqual(metrics["full_fragment_ship"]["mean_ms"],100)
        self.assertEqual(
            metrics["constant_pushdown"]["mean_penalty_relative_to_direct_indexed_central_ms"],48)
        self.assertEqual(metrics["mean_full_to_selective_saved_ms"],50)
        self.assertEqual(metrics["constant_pushdown"]["RDF_tcp_response_payload_bytes"],48*3*200)
        self.assertEqual(metrics["constant_pushdown"]["n_blocks_slower_than_direct_central"],144)

    def test_missing_repetition_fails_closed(self):
        with self.assertRaises(ValueError):
            experiment.aggregate(self.synthetic()[:-1])

    def test_cluster_function_accounts_for_predicate_families(self):
        r=experiment.cluster_sensitivity(self.synthetic())
        self.assertEqual(r["n_unique_text_clusters"],48)
        self.assertEqual(r["n_distinct_predicate_families"],8)
        self.assertEqual(r["family_text_counts_descending"],[6]*8)
        self.assertEqual(r["n_texts_where_central_beats_selective"],48)
        self.assertEqual(r["n_predicate_families_where_central_beats_selective_mean"],8)
        self.assertFalse("original_query_text" in str(r))

    def test_missing_text_cluster_is_invalid(self):
        r=self.synthetic()
        del r[0:3]
        with self.assertRaises(ValueError):
            experiment.cluster_sensitivity(r)

if __name__=="__main__":
    unittest.main()
