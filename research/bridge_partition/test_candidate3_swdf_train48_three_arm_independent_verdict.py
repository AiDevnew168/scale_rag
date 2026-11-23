"""No-source adversarial checks for independent 48x3 strong baseline audit."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import candidate3_swdf_train48_three_arm_independent_verdict as v


def fixture():
    rows=[]
    for i in range(48):
        h=f"{i:064x}"
        family=f"{i%8:064x}"
        cohort="ranks_1_24" if i<24 else "ranks_25_48"
        initial=list(v.ARMS)
        for rep in range(3):
            rows.append({
                "text_sha256":h,"cohort":cohort,
                "family_sha256":family,"repeat":rep,
                "method_order":initial[rep:]+initial[:rep],
                "elapsed_ms":{"central_indexed":1.5,"full_fragment_ship":150.0,
                              "constant_pushdown":90.0},
                "rdf_payload_bytes":{"central_indexed":0,
                    "full_fragment_ship":1000000,"constant_pushdown":400000},
                "solution_counts":{"central_indexed":3,
                    "full_fragment_ship":3,"constant_pushdown":3},
                "status":{"full_fragment_ship":"PASS",
                          "constant_pushdown":"PASS"}})
    return {"schema":v.SCHEMA,
            "frozen":{"cohort_one_hash":v.EXPECTED_FIRST,
                      "cohort_two_hash":v.EXPECTED_SECOND,
                      "original_future_holdout_reused":False,
                      "original_SOURCE_query_never_rewritten":True,
                      "n_unique_original_training_texts":48,
                      "repetitions_per_text":3},
            "expected_matched_3arm_query_blocks":144,
            "completed_matched_3arm_blocks":144,
            "errors":[],
            "original_complete_SELECT_semantic_all_pass":True,
            "deidentified_all_method_query_timings":rows}


class Adversarial(unittest.TestCase):
    def test_complete_three_arm_report_is_scoped_no_go_not_journal_go(self):
        result=v.check(fixture())
        self.assertEqual(result["status"],"VALID_ENGINEERING_EVIDENCE")
        self.assertEqual(result["n_query_text_clusters_central_outperforms_selective"],48)
        self.assertEqual(result["single_host_304k_RDF_temp_store_coordinator_competitiveness"],"NO_GO")
        self.assertEqual(result["source_original_RDF_response_body_bytes_saved_full_to_selective"],144*600000)
        self.assertFalse(result["journal_GO"])

    def test_missing_original_query_block_rejected(self):
        report=fixture();report["deidentified_all_method_query_timings"].pop()
        self.assertEqual(v.check(report)["status"],"INVALID_EVIDENCE")

    def test_wrong_source_sample_fingerprint_rejected(self):
        report=fixture();report["frozen"]["cohort_one_hash"]="wrong"
        self.assertEqual(v.check(report)["status"],"INVALID_EVIDENCE")

    def test_incomplete_frozen_original_semantic_certification_rejected(self):
        report=fixture()
        report["deidentified_all_method_query_timings"][0]["status"]["constant_pushdown"]="FAIL"
        self.assertEqual(v.check(report)["status"],"INVALID_EVIDENCE")

    def test_duplicate_repetition_rejected(self):
        report=fixture()
        report["deidentified_all_method_query_timings"][0]["repeat"]=1
        self.assertEqual(v.check(report)["status"],"INVALID_EVIDENCE")

    def test_unbalanced_method_order_rejected(self):
        report=fixture()
        report["deidentified_all_method_query_timings"][0]["method_order"]=[
            "central_indexed","constant_pushdown","full_fragment_ship"]
        self.assertEqual(v.check(report)["status"],"INVALID_EVIDENCE")

    def test_more_selective_bytes_rejected(self):
        report=fixture()
        report["deidentified_all_method_query_timings"][0]["rdf_payload_bytes"]["constant_pushdown"]=2000000
        self.assertEqual(v.check(report)["status"],"INVALID_EVIDENCE")

    def test_negative_or_nonfinite_wall_time_rejected(self):
        for value in (-3.0,float("nan"),float("inf")):
            with self.subTest(value=value):
                report=fixture()
                report["deidentified_all_method_query_timings"][0]["elapsed_ms"]["central_indexed"]=value
                self.assertEqual(v.check(report)["status"],"INVALID_EVIDENCE")

    def test_wrong_source_family_per_repetition_rejected(self):
        report=fixture()
        report["deidentified_all_method_query_timings"][0]["family_sha256"]="f"*64
        self.assertEqual(v.check(report)["status"],"INVALID_EVIDENCE")

    def test_valid_selective_advantage_still_not_paper_proof(self):
        report=fixture()
        for row in report["deidentified_all_method_query_timings"]:
            row["elapsed_ms"]["central_indexed"]=200
        result=v.check(report)
        self.assertEqual(result["status"],"VALID_ENGINEERING_EVIDENCE")
        self.assertEqual(result["single_host_304k_RDF_temp_store_coordinator_competitiveness"],
                         "UNRESOLVED_STRONG_BASELINE")
        self.assertFalse(result["journal_GO"])


if __name__=="__main__":
    unittest.main()
