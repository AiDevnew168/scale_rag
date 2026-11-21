#!/usr/bin/env python3
"""Adversarial SPARQL SELECT validity tests, including hard negative cases."""
import unittest
from candidate3_sparql_semantic_oracle import (
    Answers,iri,blank,literal,equal_bag,subbag,verify,query_contract,
    graph_of_answers
)

QFULL="SELECT ?x ?y WHERE { ?x <urn:p> ?y . ?x <urn:q> ?z }"
QLIMIT=QFULL+" LIMIT 1"
QDIS=QFULL.replace("SELECT","SELECT DISTINCT",1)+" LIMIT 1"

def A(*rows,variables=("x","y")):
    return Answers(tuple(variables),tuple(rows))

class SolutionSemantics(unittest.TestCase):
    def test_unordered_complete_bag_order_irrelevant(self):
        a=A((iri("urn:1"),literal("1")), (iri("urn:2"),literal("2")))
        b=A((iri("urn:2"),literal("2")), (iri("urn:1"),literal("1")))
        self.assertTrue(equal_bag(a,b))
        self.assertEqual(verify(QFULL,a,b)["status"],"PASS")

    def test_duplicate_solution_multiplicity_is_not_discarded(self):
        one=A((iri("urn:1"),literal("x")),)
        two=A((iri("urn:1"),literal("x")), (iri("urn:1"),literal("x")))
        self.assertFalse(equal_bag(one,two))
        self.assertFalse(subbag(two,one))
        self.assertTrue(subbag(one,two))

    def test_rdf_literal_language_and_lexical_datatype_identity(self):
        self.assertFalse(equal_bag(A((iri("u"),literal("cat","en")),),
                                   A((iri("u"),literal("cat","fr")),)))
        self.assertFalse(equal_bag(A((iri("u"),literal("01",datatype="http://www.w3.org/2001/XMLSchema#integer")),),
                                   A((iri("u"),literal("1",datatype="http://www.w3.org/2001/XMLSchema#integer")),)))

    def test_blank_node_global_rename_and_shared_identity(self):
        central=A((blank("X"),iri("urn:a")),(blank("X"),iri("urn:b")))
        changed=A((blank("Y"),iri("urn:b")),(blank("Y"),iri("urn:a")))
        broken=A((blank("Y"),iri("urn:b")),(blank("Z"),iri("urn:a")))
        self.assertTrue(equal_bag(central,changed))
        self.assertFalse(equal_bag(central,broken))

    def test_blank_node_bijection_injectivity(self):
        distinct=A((blank("A"),iri("urn:a")),(blank("B"),iri("urn:a")))
        collapsed=A((blank("Z"),iri("urn:a")),(blank("Z"),iri("urn:a")))
        self.assertFalse(equal_bag(distinct,collapsed))

    def test_blank_node_same_row_repeated_variable(self):
        ref=A((blank("x"),blank("x")))
        valid=A((blank("y"),blank("y")))
        bad=A((blank("y"),blank("z")))
        self.assertTrue(equal_bag(ref,valid))
        self.assertFalse(equal_bag(ref,bad))

    def test_unbound_solution_variable_preserved(self):
        self.assertFalse(equal_bag(A((iri("x"),None)),A((iri("x"),literal("")),)))

    def test_full_result_no_limit_uses_global_identity(self):
        ref=A((blank("C"),literal("a")), (blank("C"),literal("b")))
        val=A((blank("Y"),literal("b")), (blank("Y"),literal("a")))
        self.assertEqual(verify(QFULL,ref,val)["status"],"PASS")

    def test_unordered_limit_different_but_legitimate_first_row(self):
        allrows=A((iri("urn:a"),literal("a")),(iri("urn:b"),literal("b")))
        ref=A((iri("urn:a"),literal("a")))
        candidate=A((iri("urn:b"),literal("b")))
        self.assertEqual(verify(QLIMIT,ref,candidate,allrows)["status"],"PASS")
        self.assertFalse(equal_bag(ref,candidate))

    def test_unordered_limit_rejects_out_of_universe(self):
        allrows=A((iri("urn:a"),literal("a")),(iri("urn:b"),literal("b")))
        ref=A((iri("urn:a"),literal("a")))
        invalid=A((iri("urn:c"),literal("c")))
        self.assertEqual(verify(QLIMIT,ref,invalid,allrows)["status"],"FAIL")

    def test_unordered_limit_rejects_duplicate_if_full_only_one_occurrence(self):
        q=QFULL+" LIMIT 2"
        full=A((iri("urn:a"),literal("a")),(iri("urn:b"),literal("b")))
        candidate=A((iri("urn:a"),literal("a")),(iri("urn:a"),literal("a")))
        self.assertEqual(verify(q,full,candidate,full)["status"],"FAIL")

    def test_blank_node_limit_any_coherent_subset(self):
        allrows=A((blank("z"),literal("a")), (blank("z"),literal("b")))
        good=A((blank("X"),literal("b")))
        bad=A((blank("X"),literal("other")))
        self.assertEqual(verify(QLIMIT,good,good,allrows)["status"],"PASS")
        self.assertEqual(verify(QLIMIT,good,bad,allrows)["status"],"FAIL")

    def test_limit_invalid_shared_blank_mapping_over_multiple_rows(self):
        full=A((blank("a"),literal("a")), (blank("b"),literal("b")), (blank("c"),literal("c")))
        central=A((blank("x"),literal("a")),(blank("y"),literal("b")))
        proposed=A((blank("x"),literal("a")),(blank("x"),literal("b")))
        q=QFULL+" LIMIT 2"
        self.assertEqual(verify(q,central,proposed,full)["status"],"FAIL")

    def test_unsupported_offset_is_explicitly_blocked(self):
        q=QFULL+" LIMIT 2 OFFSET 1"
        val=A((iri("x"),literal("v")))
        self.assertEqual(verify(q,val,val)["status"],"BLOCKED")

    def test_unsupported_ordered_slice_is_explicitly_blocked(self):
        q=QFULL+" ORDER BY ?x LIMIT 1"
        val=A((iri("x"),literal("v")))
        self.assertEqual(verify(q,val,val)["status"],"BLOCKED")

    def test_missing_unlimited_reference_is_not_silent_pass(self):
        val=A((iri("x"),literal("v")))
        self.assertEqual(verify(QLIMIT,val,val)["status"],"BLOCKED")

    def test_limit_correct_cardinality(self):
        full=A((iri("x"),literal("v")))
        invalid=A()
        self.assertEqual(verify(QFULL+" LIMIT 5",full,invalid,full)["status"],"FAIL")

    def test_nested_subqueries_rejected(self):
        q="SELECT ?s WHERE { { SELECT ?s WHERE { ?s <urn:p> ?o } LIMIT 2 } } LIMIT 1"
        val=Answers(("s",),((iri("s"),),))
        self.assertEqual(verify(q,val,val)["status"],"BLOCKED")

    def test_distinct_limit_is_subset_of_unsliced_distinct(self):
        full=A((iri("1"),literal("a")),(iri("2"),literal("b")))
        central=A((iri("1"),literal("a")))
        candidate=A((iri("2"),literal("b")))
        self.assertEqual(verify(QDIS,central,candidate,full)["status"],"PASS")

if __name__=="__main__":
    unittest.main(verbosity=2)
