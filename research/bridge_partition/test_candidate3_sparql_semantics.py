#!/usr/bin/env python3
"""Deterministic adversarial SPARQL semantics regressions (not real benchmark)."""
import unittest
from dataclasses import dataclass
from pyoxigraph import BlankNode,Literal,NamedNode
from candidate3_sparql_semantic_certifier import (
 certify,characterize,is_subset_with_global_bnode_bijection,term_key
)
P="<http://example.org/p>"
Q=f"SELECT ?x WHERE {{ ?x {P} ?z }} LIMIT 1"
QS=f"SELECT ?x WHERE {{ ?x {P} ?z }}"
QORDER=f"SELECT ?x WHERE {{ ?x {P} ?z }} ORDER BY ?x LIMIT 1"
QOFF=f"SELECT ?x WHERE {{ ?x {P} ?z }} OFFSET 1 LIMIT 1"
QFULL=f"SELECT ?x WHERE {{ ?x {P} ?z }}"
class Result:
    def __init__(self,rows):
        self.variables=[type("V",(),{"value":"x"})()]
        self._rows=[{"x":row} for row in rows]
    def __iter__(self):return iter(self._rows)
class FakeStore:
    def __init__(self,items):self.data=items
    def query(self,q):return Result(self.data[q])
a=NamedNode("http://example.org/a")
b=NamedNode("http://example.org/b")
c=NamedNode("http://example.org/c")
class Semantics(unittest.TestCase):
    def test_true_unordered_limit_selection_differs_and_passes(self):
        central=FakeStore({Q:[a],QS:[a,b]})
        remote=FakeStore({Q:[b]})
        x=certify(central,remote,Q)
        self.assertEqual(x["status"],"PASS")
        self.assertEqual(x["unsliced_truth_rows"],2)
    def test_illegal_unordered_limit_fabricated_member_fails(self):
        central=FakeStore({Q:[a],QS:[a,b]})
        remote=FakeStore({Q:[c]})
        self.assertEqual(certify(central,remote,Q)["status"],"FAIL")
    def test_unordered_limit_cannot_hide_wrong_cardinality(self):
        central=FakeStore({Q:[a],QS:[a,b]})
        remote=FakeStore({Q:[b,a]})
        self.assertEqual(certify(central,remote,Q)["status"],"FAIL")
    def test_offset_uses_effective_row_count(self):
        central=FakeStore({QOFF:[a],QFULL:[a,b]})
        remote=FakeStore({QOFF:[b]})
        self.assertEqual(certify(central,remote,QOFF)["status"],"PASS")
    def test_ordered_limit_disagreement_conservative_inconclusive(self):
        central=FakeStore({QORDER:[a]})
        remote=FakeStore({QORDER:[b]})
        self.assertEqual(certify(central,remote,QORDER)["status"],"INCONCLUSIVE")
    def test_losing_blanknode_coreference_rejected(self):
        aa=("bnode","a");bb=("bnode","b");cc=("bnode","c")
        left=[(aa,aa),(bb,aa)]
        right=[(cc,cc),(cc,bb)]
        self.assertFalse(is_subset_with_global_bnode_bijection(left,right))
    def test_consistent_blanknode_bag_alpha_equivalence(self):
        lhs=[(("bnode","same"),("iri","urn:a")),
             (("bnode","same"),("iri","urn:b"))]
        rhs=[(("bnode","different"),("iri","urn:b")),
             (("bnode","different"),("iri","urn:a"))]
        self.assertTrue(is_subset_with_global_bnode_bijection(lhs,rhs))
        self.assertTrue(is_subset_with_global_bnode_bijection(rhs,lhs))
    def test_result_blanknode_scoped_labels_pass(self):
        lhs=FakeStore({QFULL:[BlankNode("left"),BlankNode("left")]})
        rhs=FakeStore({QFULL:[BlankNode("right"),BlankNode("right")]})
        self.assertEqual(certify(lhs,rhs,QFULL)["status"],"PASS")
    def test_different_blanknode_identity_fails(self):
        lhs=FakeStore({QFULL:[BlankNode("left"),BlankNode("left")]})
        rhs=FakeStore({QFULL:[BlankNode("x"),BlankNode("y")]})
        self.assertEqual(certify(lhs,rhs,QFULL)["status"],"FAIL")
    def test_repeated_rows_multiset_not_set(self):
        lhs=FakeStore({QFULL:[a,a,b]})
        rhs=FakeStore({QFULL:[a,b,b]})
        self.assertEqual(certify(lhs,rhs,QFULL)["status"],"FAIL")
    def test_term_language_and_datatype_maintained(self):
        self.assertNotEqual(term_key(Literal("bonjour",language="fr")),
                            term_key(Literal("bonjour",language="en")))
        self.assertNotEqual(term_key(Literal("01")),
                            term_key(Literal("01",datatype=NamedNode("http://www.w3.org/2001/XMLSchema#integer"))))
    def test_reduced_is_inconclusive(self):
        q=f"SELECT REDUCED ?x WHERE {{ ?x {P} ?z }} LIMIT 1"
        self.assertEqual(characterize(q).kind,"inconclusive")

if __name__=="__main__":unittest.main(verbosity=2)
