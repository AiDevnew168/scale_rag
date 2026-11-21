import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import candidate3_trainonly_selective_fetch_cluster_sensitivity as audit

def report(gain=5.0,byte_frac=0.8):
    hs=[f"{i:064x}" for i in range(24)]
    rows=[]
    for h in hs:
        for i in (0,1):
            rows.append({"text_sha256":h,"repetition":i,
              "full_ms":20.0,"pushdown_ms":20.0-gain,
              "full_rdf_bytes":1000,
              "pushdown_rdf_bytes":int(1000*(1-byte_frac)),
              "saved_ms":gain})
    return {"schema":"candidate3-trainonly-source-physical-constant-pushdown-v1",
      "frozen_selection":{"n_query_texts":24,"paired_repeats":2,
       "training_original_UTC_days":88,"no_2014_heldout_reuse":True,
       "candidate_selection":{"calibration_or_test_original_query_texts_examined":False,
          "chosen_text_hashes":hs}},
      "n_expected_pairs":48,"n_semantically_legal_pairs":48,
      "all_original_queries_correct":True,"errors":[],
      "deidentified_original_training_paired_rows":rows}

class QueryClusterAudit(unittest.TestCase):
    def test_all_fast_passes_additional_training_sensitivity(self):
        x=audit.assess(report())
        self.assertEqual(x["n_query_clusters"],24)
        self.assertTrue(x["positive_lower_gain_under_cluster_sensitivity"])
        self.assertTrue(x["research_development_gate_not_publication"])
        self.assertEqual(x["observed_mean_query_saved_ms"],5.0)
        self.assertFalse(x["journals_SOTA_GO"])

    def test_more_bytes_saved_but_slower_does_not_pass(self):
        x=audit.assess(report(gain=-4))
        self.assertFalse(x["positive_lower_gain_under_cluster_sensitivity"])
        self.assertFalse(x["research_development_gate_not_publication"])
        self.assertEqual(x["n_query_clusters_with_negative_mean_latency"],24)

    def test_wrong_semantics_blocks_before_clustering(self):
        r=report()
        r["all_original_queries_correct"]=False
        self.assertEqual(audit.assess(r)["status"],"BLOCKED_INVALID_FROZEN_PAIRS")

    def test_bad_pair_values_refused_by_primary(self):
        r=report()
        r["deidentified_original_training_paired_rows"][0]["saved_ms"]=1e9
        self.assertEqual(audit.assess(r)["status"],"BLOCKED_INVALID_FROZEN_PAIRS")

    def test_all_equal_gain_bootstrap_is_exact_point(self):
        x=audit.assess(report(gain=1.5))
        self.assertEqual(x["query_cluster_bootstrap95_latency_ms_DESCRIPTIVE"],[1.5,1.5])

    def test_seeded_reproducibility(self):
        x=audit.assess(report(gain=2.3))
        y=audit.assess(report(gain=2.3))
        self.assertEqual(x,y)

    def test_beyond_positive_byte_threshold_but_no_speed_gain(self):
        x=audit.assess(report(gain=0,byte_frac=0.95))
        self.assertFalse(x["research_development_gate_not_publication"])

if __name__=="__main__":
    unittest.main()
