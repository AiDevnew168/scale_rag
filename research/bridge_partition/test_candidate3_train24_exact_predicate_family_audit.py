import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import candidate3_train24_exact_predicate_family_audit as diversity

P="<http://ex.org/p>";Q="<http://ex.org/q>";R="<http://ex.org/r>"
class ExactSourcePredicateFamilies(unittest.TestCase):
    def test_same_exact_predicate_set_clusters_texts_independent_of_order(self):
        rows=[{"hash":"a","pattern":(P,Q)},{"hash":"b","pattern":(Q,P)},
              {"hash":"c","pattern":(P,R)}]
        res=diversity.summarize(rows,{P:10,Q:15,R:20})
        self.assertEqual(res["n_exact_predicate_set_families"],2)
        self.assertEqual(res["query_texts_per_family_descending"],[2,1])
        self.assertEqual(res["exact_source_full_bytes_two_repeats"],2*(25+25+30))
        self.assertFalse(res["journals_SOTA_GO"])
    def test_equal_total_byte_sizes_do_not_fake_same_predicate_family(self):
        rows=[{"hash":"a","pattern":(P,)},{"hash":"b","pattern":(Q,)}]
        res=diversity.summarize(rows,{P:10,Q:10})
        self.assertEqual(res["n_exact_predicate_set_families"],2)
        self.assertEqual(res["n_unique_full_response_byte_values"],1)
    def test_absent_original_predicate_fails_closed(self):
        with self.assertRaises(RuntimeError):
            diversity.summarize([{"hash":"a","pattern":(P,Q)}],{P:10})

if __name__=="__main__":unittest.main()
