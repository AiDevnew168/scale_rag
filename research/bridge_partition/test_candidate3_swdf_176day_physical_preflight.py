#!/usr/bin/env python3
"""Fast, offline preflight for the frozen original SWDF physical replay.

Tests do not download 2014 logs, select candidate actions, or inspect heldout
SPARQL answers. Run BEFORE the long physical benchmark.
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import candidate3_swdf_176day_physical_economic as physical
import candidate3_feasible_raw_swdf_strict_temporal as source_audit


class TestFrozenSourceEligibilityParity(unittest.TestCase):
    def test_select_word_boundary_literal_is_not_double_escaped(self):
        self.assertEqual(physical.SELECT_TOKEN.pattern, r"\bSELECT\b")

    def test_valid_original_select_passes_lexical_gate(self):
        q = ("SELECT ?s WHERE { ?s <http://example.org/p1> ?o . "
             "?s <http://example.org/p2> ?x }")
        self.assertIsNotNone(physical.SELECT_TOKEN.search(q))
        preds, error = source_audit.select_predicates(q)
        self.assertIsNone(error)
        self.assertEqual(preds, ("http://example.org/p1", "http://example.org/p2"))

    def test_case_insensitive_keyword(self):
        self.assertIsNotNone(physical.SELECT_TOKEN.search("select ?s WHERE {?s ?p ?o}"))
        self.assertIsNotNone(physical.SELECT_TOKEN.search("SeLeCt ?s WHERE {?s ?p ?o}"))

    def test_reject_substring_and_non_select(self):
        for q in ("PSELECT ?s WHERE {}", "SELECTED ?s WHERE {}", "ASK {?s ?p ?o}",
                  "CONSTRUCT {?s ?p ?o} WHERE {?s ?p ?o}"):
            with self.subTest(q=q):
                self.assertIsNone(physical.SELECT_TOKEN.search(q))

    def test_previous_double_escape_was_false_negative(self):
        q = "SELECT ?s WHERE { ?s ?p ?o }"
        self.assertIsNone(re.search(r"\\bSELECT\\b", q, re.I))
        self.assertIsNotNone(physical.SELECT_TOKEN.search(q))


    def test_fail_closed_on_target_engine_missing_prefix_after_freeze(self):
        import hashlib
        supported = "SELECT ?s WHERE { ?s <http://example.org/p> ?o }"
        engine_incompatible = "SELECT ?s WHERE { ?s rdf:type ?o }"
        def row(q, day):
            return {"query": q, "day": day,
                    "text_hash": hashlib.sha256(q.encode()).hexdigest()}
        sampled = {
            "train": [row(supported,"2014-05-15")],
            "construction": [],
            "calibration": [],
            "test": [row(engine_incompatible,"2014-09-26"),
                     row(engine_incompatible,"2014-09-26")],
        }
        result=physical.target_engine_syntax_gate(sampled)
        self.assertFalse(result["all_original_query_texts_engine_executable"])
        self.assertEqual(result["unique_query_texts_probed"],2)
        self.assertEqual(result["engine_incompatible_unique_texts"],1)
        self.assertEqual(result["engine_incompatible_sample_occurrences_by_split"],
                         {"test":2})
        self.assertFalse(result["journal_confirmatory_status_restored"])
        self.assertTrue(all("query" not in str(x) or "query_sha256" in x
                            for x in result["bounded_anonymous_examples"]))
        self.assertNotIn(engine_incompatible,str(result))

    def test_empty_store_accepts_explicit_rdf_prefix(self):
        import hashlib
        q = ("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> "
             "SELECT ?s WHERE { ?s rdf:type ?o }")
        sampled = {"train":[],"construction":[],"calibration":[],
                   "test":[{"query":q,"day":"2014-09-26",
                            "text_hash":hashlib.sha256(q.encode()).hexdigest()}]}
        result=physical.target_engine_syntax_gate(sampled)
        self.assertTrue(result["all_original_query_texts_engine_executable"])


if __name__ == "__main__":
    unittest.main()
