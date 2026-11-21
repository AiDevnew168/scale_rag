"""No-source synthetic contract tests: original text is never changed by diagnose."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candidate3_swdf_original_prefix_forensics as forensic


class PrefixForensicsTests(unittest.TestCase):
    def test_rdflib_default_rdf_prefix_missing_without_explicit_declaration(self):
        q = "SELECT ?s WHERE { ?s rdf:type ?o . ?s <http://example.org/p> ?x }"
        defaults = forensic.candidate_undeclared_defaults(q)
        self.assertIn("rdf", defaults)
        self.assertEqual(defaults["rdf"],
                         "http://www.w3.org/1999/02/22-rdf-syntax-ns#")

    def test_explicit_prefix_is_not_guessed(self):
        q = ("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> "
             "SELECT ?s WHERE { ?s rdf:type ?o . ?s <http://example.org/p> ?x }")
        self.assertNotIn("rdf", forensic.candidate_undeclared_defaults(q))

    def test_iri_and_literal_are_not_mistaken_as_prefix_reference(self):
        q = ('SELECT * WHERE { ?s <http://example.org/rdf:type> "rdf:type" . '
             '?s <http://example.org/p> ?x }')
        self.assertEqual(forensic.candidate_undeclared_defaults(q), {})

    def test_only_known_rdflib_prefix_map_can_be_trialed(self):
        q = "SELECT * WHERE { ?s inventedPrefix:value ?o }"
        self.assertEqual(forensic.candidate_undeclared_defaults(q), {})

    def test_do_not_accept_unpinned_source_query(self):
        with self.assertRaises(ValueError):
            forensic.diagnose("SELECT * WHERE { ?s ?p ?o }")

    def test_synthetic_rdflib_accepts_implicit_prefix(self):
        from rdflib.plugins.sparql.processor import prepareQuery
        q = "SELECT ?s WHERE { ?s rdf:type ?o . ?s <http://example.org/p> ?x }"
        self.assertIsNotNone(prepareQuery(q))

    def test_sanitized_empty_store_parse_response(self):
        obj = forensic.engine_syntax("SELECT ?s WHERE { ?s ?p ?o }")
        self.assertTrue(obj["accepted"])
        self.assertFalse(obj["missing_prefix_error"])
        self.assertNotIn("query", obj)


if __name__ == "__main__":
    unittest.main()
