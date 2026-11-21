import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import candidate3_trainonly_selective_fetch_feasibility as feasibility


class TrainOnlyStructuralFeasibility(unittest.TestCase):
    def test_fixed_object_with_shared_subject_can_be_selective_anchor(self):
        q=("SELECT ?s WHERE { ?s <http://ex.org/p> <http://ex.org/value> . "
           "?s <http://ex.org/p2> ?other }")
        info=feasibility.describe_eligible_query(q)
        self.assertTrue(info["has_subject_or_object_constant"])
        self.assertTrue(info["has_fixed_pattern_with_shared_variable"])
        self.assertTrue(info["has_constant_object"])
        self.assertEqual(info["patterns"],2)

    def test_no_fixed_subject_object_is_not_selective(self):
        q=("SELECT ?s WHERE { ?s <http://ex.org/p> ?o . "
           "?s <http://ex.org/p2> ?x }")
        info=feasibility.describe_eligible_query(q)
        self.assertTrue(info["has_shared_variable"])
        self.assertTrue(info["has_only_predicate_constants"])
        self.assertFalse(info["has_fixed_pattern_with_shared_variable"])

    def test_fixed_constant_on_disconnected_bgp_is_not_join_anchor(self):
        q=("SELECT ?s WHERE { <http://ex.org/person> <http://ex.org/p> ?x . "
           "?s <http://ex.org/p2> ?o }")
        info=feasibility.describe_eligible_query(q)
        self.assertTrue(info["has_subject_or_object_constant"])
        self.assertFalse(info["has_fixed_pattern_with_shared_variable"])

    def test_multiple_constant_and_join_terms(self):
        q=("SELECT ?s WHERE { <http://ex.org/s> <http://ex.org/p> ?x . "
           "?x <http://ex.org/p2> <http://ex.org/o> }")
        info=feasibility.describe_eligible_query(q)
        self.assertTrue(info["has_fixed_pattern_with_shared_variable"])
        self.assertTrue(info["has_constant_object"])

if __name__=="__main__":
    unittest.main()
