import io,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import candidate3_external_largerdfbench2026_query_gate as benchmark


def make_zip(files):
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w") as z:
        for path,body in files.items():
            z.writestr(path,body)
    return mem.getvalue()


class ExternalSourceGate(unittest.TestCase):
    def test_synthetic_public_query_parses_both_engines(self):
        q="SELECT ?s WHERE { ?s <http://ex.org/p> <http://ex.org/o> . ?s <http://ex.org/q> ?x }"
        doc=benchmark.audit_public_queries({"S1.rq":q})
        self.assertEqual(doc["engine_and_constant_BGP_features"]["rdflib_parse_pass"],1)
        self.assertEqual(doc["engine_and_constant_BGP_features"]["oxigraph_syntax_pass"],1)
        self.assertEqual(doc["engine_and_constant_BGP_features"]["plain_BGP_constant_anchor_supported"],1)
        self.assertFalse(doc["RDF_source_graph_evaluated"])
        self.assertFalse(doc["novel_or_journal_method_claim"])

    def test_missing_prefix_mismatch_is_reported(self):
        q="SELECT ?s WHERE { ?s rdf:type ?o . ?s <http://ex.org/p> ?v }"
        doc=benchmark.audit_public_queries({"C1.rq":q})
        self.assertEqual(doc["engine_and_constant_BGP_features"]["oxigraph_syntax_fail"],1)

    def test_non_UTF8_rejected(self):
        with self.assertRaises(ValueError):
            benchmark.inspect_zip(make_zip({"S1.rq":b"\xffSELECT ?s WHERE {}"}))

    def test_traversal_rejected(self):
        with self.assertRaises(ValueError):
            benchmark.inspect_zip(make_zip({"../S1.rq":"SELECT ?s WHERE { ?s ?p ?o }"}))

    def test_no_benchmark_query_rejected(self):
        with self.assertRaises(ValueError):
            benchmark.inspect_zip(make_zip({"README.md":"not a query"}))

    def test_detects_valid_zip_query_safely(self):
        src=make_zip({"S1.rq":"SELECT ?s WHERE { ?s ?p ?o }","notes/readme.txt":"notes"})
        texts=benchmark.inspect_zip(src)
        self.assertEqual(len(texts),1)
        self.assertIn("S1.rq",texts)

    def test_tiny_archive_does_not_match_published_sha(self):
        with self.assertRaises(ValueError):
            benchmark.query_archive_entries(make_zip({"S1.rq":"SELECT ?s WHERE {}"}))


if __name__=="__main__":
    unittest.main()
