#!/usr/bin/env python3
"""Adversarial regressions, not merely happy-path SPARQL validity."""
import unittest
from candidate3_sparql_semantic_validity import validate,plan,normalize_term
I=lambda x:("iri",x)
B=lambda x:("blank",x)
L=lambda v,lang=None,dt="http://www.w3.org/2001/XMLSchema#string":("literal",v,lang,dt)
class Validity(unittest.TestCase):
    def check(self,ref,ans,expected,**kw):
        r=validate(["x"],[(v,) for v in ref],["x"],[(v,) for v in ans],**kw)
        self.assertEqual(r["pass"],expected,r)
        return r
    def test_limit_membership_vs_exact_choice(self):
        self.check([I("a"),I("b"),I("c")],[I("c")],True,limit=1)
        self.check([I("a"),I("b"),I("c")],[I("outside")],False,limit=1)
        self.check([I("a"),I("b"),I("c")],[I("a"),I("c")],False,limit=1)
    def test_duplicate_bag(self):
        self.check([I("a"),I("a"),I("b")],[I("a"),I("a")],True,limit=2)
        self.check([I("a"),I("b"),I("b")],[I("a"),I("a")],False,limit=2)
        self.check([I("a"),I("a")],[I("a")],False)
    def test_offset_size_and_full_membership(self):
        self.check([I("a"),I("b"),I("c")],[I("b"),I("a")],True,offset=1)
        self.check([I("a"),I("b"),I("c")],[I("b")],True,offset=1,limit=1)
        self.check([I("a"),I("b"),I("c")],[I("b"),I("a")],False,offset=2)
        self.check([I("a")],[],True,offset=10,limit=2)
        self.check([I("a")],[],True,limit=0)
    def test_literal_semantics_strict(self):
        self.check([L("Hello","en")],[L("Hello","fr")],False)
        self.check([L("1",None,"http://www.w3.org/2001/XMLSchema#integer")],
                   [L("1",None,"http://www.w3.org/2001/XMLSchema#string")],False)
        self.check([I("http://example.org/a")],[L("http://example.org/a")],False)
    def test_global_blank_node_valid_mapping(self):
        ref=[(B("u"),I("a")),(B("u"),I("b")),(B("v"),I("c"))]
        ans=[(B("x"),I("b")),(B("y"),I("c")),(B("x"),I("a"))]
        self.assertTrue(validate(["x","y"],ref,["x","y"],ans)["pass"])
    def test_blank_aliasing_false_positive(self):
        ref=[(B("u"),I("a")),(B("v"),I("b"))]
        ans=[(B("x"),I("a")),(B("x"),I("b"))]
        self.assertFalse(validate(["x","y"],ref,["x","y"],ans)["pass"])
    def test_injective_blank_node_map(self):
        ref=[(B("u"),I("a")),(B("u"),I("b"))]
        ans=[(B("x"),I("a")),(B("y"),I("b"))]
        self.assertFalse(validate(["x","y"],ref,["x","y"],ans)["pass"])
    def test_subbag_blank_maps_to_any_ref_bnode(self):
        ref=[(B("u"),I("a")),(B("u"),I("b")),(B("v"),I("c"))]
        ans=[(B("z"),I("c"))]
        self.assertTrue(validate(["x","y"],ref,["x","y"],ans,limit=1)["pass"])
    def test_variable_column_reorder(self):
        ref=[(I("subject"),I("object"))]
        ans=[(I("object"),I("subject"))]
        self.assertTrue(validate(["s","o"],ref,["o","s"],ans)["pass"])
        self.assertFalse(validate(["s","o"],ref,["s","other"],ans)["pass"])
    def test_bnode_unbound(self):
        self.check([B("u")],[("unbound",)],False)
        self.check([B("u")],[B("x")],True)
    def test_ordered_fail_closed_and_sequence(self):
        self.assertFalse(validate(["x"],[(I("a"),),(I("b"),)],["x"],
            [(I("b"),),(I("a"),)],ordered=True)["pass"])
        self.assertFalse(validate(["x"],[(I("a"),),(I("b"),)],["x"],
            [(I("b"),),(I("a"),)],ordered=True,unambiguous_order=True)["pass"])
        self.assertTrue(validate(["x"],[(I("a"),),(I("b"),)],["x"],
            [(I("a"),),(I("b"),)],ordered=True,unambiguous_order=True)["pass"])
    def test_tail_modifier_and_nested_reject(self):
        q="SELECT ?x WHERE {?x <http://example.org/p> ?y} LIMIT 2 OFFSET 1"
        x=plan(q)
        self.assertEqual((x["limit"],x["offset"],x["ordered"]),(2,1,False))
        self.assertNotIn("LIMIT",x["reference_query"])
        self.assertNotIn("OFFSET",x["reference_query"])
        self.assertEqual(plan("SELECT ?x WHERE {?x ?p ?y} ORDER BY ?x LIMIT 1")["status"],
                         "ORDERED_SLICE_STRICT_ONLY")
        with self.assertRaises(ValueError):
            plan("SELECT ?x WHERE { {SELECT ?x WHERE {?x ?p ?o} LIMIT 1} } LIMIT 2")
    def test_result_cap_blocks(self):
        r=validate(["x"],[(I("z"),)]*20001,["x"],[(I("z"),)],limit=1)
        self.assertFalse(r["pass"])
    def test_actual_oxigraph_rdf_term_adapter(self):
        from pyoxigraph import Store,RdfFormat
        db=Store()
        db.bulk_load(input=b'<http://a> <http://p> "hola"@es .\n',format=RdfFormat.N_TRIPLES)
        from candidate3_sparql_semantic_validity import result_bag
        vs,rs=result_bag(db,'SELECT ?o WHERE { <http://a> <http://p> ?o }')
        self.assertEqual(vs,("o",))
        self.assertEqual(rs[0][0][0],"literal")
        self.assertEqual(rs[0][0][1],"hola")
        self.assertEqual(rs[0][0][2],"es")
    def test_oxigraph_unordered_limit_valid(self):
        from pyoxigraph import Store,RdfFormat
        from candidate3_sparql_semantic_validity import result_bag
        db=Store()
        db.bulk_load(input=b'<http://a> <http://p> <http://u> .\n<http://b> <http://p> <http://v> .\n',
                  format=RdfFormat.N_TRIPLES)
        q="SELECT ?s WHERE {?s <http://p> ?o} LIMIT 1"
        p=plan(q)
        refv,full=result_bag(db,p["reference_query"])
        ansv,ans=result_bag(db,q)
        self.assertTrue(validate(refv,full,ansv,ans,limit=p["limit"],offset=p["offset"])["pass"])
if __name__=="__main__":unittest.main(verbosity=2)
