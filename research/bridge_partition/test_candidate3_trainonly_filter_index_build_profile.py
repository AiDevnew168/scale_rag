import sys,unittest,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import candidate3_trainonly_filter_index_build_profile as profile

P="<http://ex.org/p>";Q="<http://ex.org/q>"
class IndexCostGate(unittest.TestCase):
    def test_profile_retains_source_fragments_and_counts_real_parse(self):
        fragments={(0,P):b'<http://ex.org/a> <http://ex.org/p> <http://ex.org/b> .\n',
                   (1,Q):b'_:b <http://ex.org/q> "x"@en .\n'}
        doc=profile.profile(fragments,"source","frozen")
        self.assertEqual(doc["status"],"COMPLETE_ENGINEERING_PROFILE")
        self.assertEqual(doc["n_original_worker_predicate_fragments_requested"],2)
        self.assertEqual(doc["original_parsed_triples_count"],2)
        self.assertTrue(doc["cold_index_build_wall_total_ms"]>=0)
        self.assertFalse(doc["journal_GO"])

    def test_routed_fragments_only_filtered_predicates(self):
        row={"pattern":(P,Q),"filters":{P:[{"subject":None,
             "object":["iri","http://ex.org/a"]}],Q:None}}
        fragments=profile.target_fragments([row],{P:{0},Q:{1}},set(),
            [{P:b'<http://ex.org/s> <http://ex.org/p> <http://ex.org/a> .\n'},
             {Q:b'<http://ex.org/s> <http://ex.org/q> <http://ex.org/a> .\n'}])
        self.assertEqual(set(fragments),{(0,P)})

    def test_missing_worker_fragment_fails_closed(self):
        row={"pattern":(P,Q),"filters":{P:[{"subject":None,
             "object":["iri","http://ex.org/a"]}],Q:None}}
        with self.assertRaises(RuntimeError):
            profile.target_fragments([row],{P:{0},Q:{1}},set(),
                [{}, {Q:b'none'}])

if __name__=="__main__":
    unittest.main()
