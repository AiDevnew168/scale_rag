import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent))
import candidate3_trainonly_selective_fetch_verdict as verdict


def fixture(full_ms=20, push_ms=15, full_bytes=1000, push_bytes=200):
    hashes=[f"{i:064x}" for i in range(24)]
    rows=[]
    for h in hashes:
        for repetition in (0,1):
            rows.append({"text_sha256":h,"repetition":repetition,
                         "full_ms":full_ms,"pushdown_ms":push_ms,
                         "full_rdf_bytes":full_bytes,
                         "pushdown_rdf_bytes":push_bytes,
                         "saved_ms":full_ms-push_ms})
    return {
      "schema":verdict.EXPECTED_SCHEMA,
      "frozen_selection":{"n_query_texts":24,"paired_repeats":2,
         "training_original_UTC_days":88,"no_2014_heldout_reuse":True,
         "candidate_selection":{"calibration_or_test_original_query_texts_examined":False,
                                "chosen_text_hashes":hashes}},
      "n_expected_pairs":48,"n_semantically_legal_pairs":48,
      "all_original_queries_correct":True,"errors":[],
      "deidentified_original_training_paired_rows":rows}


class SelectiveVerdictTests(unittest.TestCase):
    def test_positive_only_as_training_exploratory(self):
        res=verdict.interpret(fixture())
        self.assertEqual(res["status"],"EXPLORATORY_TRAIN_ONLY_MEASURED")
        self.assertTrue(res["pass_predeclared_25pct_training_byte_reduction"])
        self.assertTrue(res["pass_training_positive_latency_and_1pct_p95_guard"])
        self.assertTrue(res["engineering_followup_if_both"])
        self.assertFalse(res["journal_GO"])

    def test_more_bytes_but_worse_latency_is_no_go(self):
        res=verdict.interpret(fixture(full_ms=20,push_ms=45))
        self.assertTrue(res["pass_predeclared_25pct_training_byte_reduction"])
        self.assertFalse(res["pass_training_positive_latency_and_1pct_p95_guard"])
        self.assertFalse(res["engineering_followup_if_both"])

    def test_zero_selectivity_fails_byte_gate(self):
        res=verdict.interpret(fixture(full_bytes=1000,push_bytes=975))
        self.assertFalse(res["pass_predeclared_25pct_training_byte_reduction"])

    def test_mismatched_semantics_is_invalid(self):
        v=fixture();v["all_original_queries_correct"]=False
        self.assertEqual(verdict.interpret(v)["status"],"INVALID_OR_INCOMPLETE_SPARQL")

    def test_one_failed_query_is_invalid(self):
        v=fixture();v["errors"]=[{"error_kind":"RuntimeError"}]
        self.assertEqual(verdict.interpret(v)["status"],"INVALID_OR_INCOMPLETE_SPARQL")

    def test_missing_repetition_is_invalid(self):
        v=fixture();v["deidentified_original_training_paired_rows"].pop()
        self.assertEqual(verdict.interpret(v)["status"],"INVALID_OR_INCOMPLETE_SPARQL")

    def test_duplicated_repetition_is_invalid(self):
        v=fixture();v["deidentified_original_training_paired_rows"][1]["repetition"]=0
        self.assertEqual(verdict.interpret(v)["status"],"DUPLICATED_PAIR")

    def test_moved_selection_hash_refused(self):
        v=fixture();v["frozen_selection"]["candidate_selection"]["chosen_text_hashes"][0]="f"*64
        self.assertEqual(verdict.interpret(v)["status"],"SAMPLE_CHANGED_AFTER_FREEZE")

    def test_future_query_peek_refused(self):
        v=fixture();v["frozen_selection"]["candidate_selection"]["calibration_or_test_original_query_texts_examined"]=True
        self.assertEqual(verdict.interpret(v)["status"],"INVALID_FROZEN_SELECTION")

    def test_negative_runtime_refused(self):
        v=fixture();v["deidentified_original_training_paired_rows"][0]["full_ms"]=-1
        self.assertEqual(verdict.interpret(v)["status"],"INVALID_PHYSICAL_MEASUREMENT")

    def test_nonfinite_refused(self):
        v=fixture();v["deidentified_original_training_paired_rows"][0]["saved_ms"]=float("nan")
        self.assertEqual(verdict.interpret(v)["status"],"NONFINITE_PAIR")

    def test_unmatched_paired_wall_refused(self):
        v=fixture();v["deidentified_original_training_paired_rows"][0]["saved_ms"]=999
        self.assertEqual(verdict.interpret(v)["status"],"UNMATCHED_WALL_TIME_PAIR")


if __name__=="__main__":
    unittest.main()
