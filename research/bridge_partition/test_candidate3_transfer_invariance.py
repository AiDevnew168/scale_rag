import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import candidate3_transfer_invariance as invariant
from candidate3_swdf_real_full_sparql_economics import shards_for_query


class TransferInvariantTests(unittest.TestCase):
    def setUp(self):
        # A is originally split, B and C are wholly owned fragments.
        self.source={"A":(b"a"*80,b"b"*20),"B":(b"c"*60,),"C":(b"d"*90,)}
        self.before={"A":{0,1},"B":{2},"C":{3}}
        self.before_frags={"A":{0:b"a"*80,1:b"b"*20},
                           "B":{2:b"c"*60},"C":{3:b"d"*90}}
        self.after={"A":{0,1},"B":{1},"C":{1,3}}
        self.after_frags={"A":{0:b"a"*80,1:b"b"*20},
                          "B":{1:b"c"*60},"C":{1:b"d"*90,3:b"d"*90}}

    def test_replica_and_move_save_rpc_but_never_source_bytes(self):
        result=invariant.compare(("A","B","C"),self.before,self.after,
                                 self.before_frags,self.after_frags,self.source,
                                 shards_for_query,{"A"})
        self.assertEqual(result["before"]["rdf_response_bytes"],250)
        self.assertEqual(result["after"]["rdf_response_bytes"],250)
        self.assertEqual(result["shard_contacts_saved"],2)
        self.assertEqual(result["rdf_bytes_saved"],0)

    def test_reject_duplicate_replicated_fragment_in_fetch(self):
        groups={0:["A"],1:["A","B"],2:["B"],3:["C"]}
        with self.assertRaises(ValueError):
            invariant.verify_one_query(("A","B","C"),self.before,
                                        self.before_frags,self.source,groups)

    def test_reject_missing_fragment(self):
        with self.assertRaises(ValueError):
            invariant.verify_one_query(("A","B","C"),self.before,
                                        self.before_frags,self.source,{0:["A"],2:["B"],3:["C"]})

    def test_query_without_replica_invariance(self):
        relocated={"A":{0,1},"B":{1},"C":{2}}
        relocated_fragments={"A":dict(self.before_frags["A"]),
                              "B":{1:b"c"*60},"C":{2:b"d"*90}}
        result=invariant.compare(("A","B","C"),self.before,relocated,
                                 self.before_frags,relocated_fragments,
                                 self.source,shards_for_query,{"A"})
        self.assertEqual(result["rdf_bytes_saved"],0)
        self.assertEqual(result["shard_contacts_saved"],1)

    def test_workflow_success_with_one_failure_is_inference_fail(self):
        methods={k:{"full_query_correctness_gate":False,
                     "original_temporal_test":{
                         "n_requested":1258,"n_semantically_correct_paired":1256,
                         "observed_RDF_payload_bytes_saved_correct_queries":0,
                         "observed_contacts_saved_correct_queries":99},
                     "economic":{"valid":False}}
                 for k in ("no_move","one_swap","two_swap_greedy",
                           "replica_only","swap_replica")}
        doc={"schema":"candidate3-original-authentic-176day-four-process-semantic-economic-v1",
             "selected_real_policy":"no_move","methods":methods}
        result=invariant.classify_physical_report(doc)
        self.assertEqual(result["status"],"INVALID_FOR_ECONOMIC_INFERENCE")
        self.assertEqual(result["actual_incremental_gain_vs_static_ms"],0.0)
        self.assertFalse(result["claim_positive_net"])

    def test_missing_arm_fails_closed(self):
        doc={"schema":"candidate3-original-authentic-176day-four-process-semantic-economic-v1",
             "selected_real_policy":"no_move","methods":{}}
        self.assertEqual(invariant.classify_physical_report(doc)["status"],
                         "INVALID_FOR_ECONOMIC_INFERENCE")

    def test_unknown_schema_fails_closed(self):
        self.assertEqual(invariant.classify_physical_report({})["status"],
                         "UNKNOWN_REPORT_SCHEMA")


if __name__=="__main__":unittest.main()
