#!/usr/bin/env python3
"""Synthetic semantics and original-source blank-node preservation regressions."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from pyoxigraph import Store,RdfFormat

import candidate3_selective_fetch_transport as selective
from candidate3_sparql_semantic_certifier import certify

P="<http://ex.org/p>"
Q="<http://ex.org/q>"
X="<http://ex.org/x>"
A="<http://ex.org/a>"
B="<http://ex.org/b>"
SOURCE = (
    b'<http://ex.org/a> <http://ex.org/p> <http://ex.org/x> .\n'
    b'<http://ex.org/b> <http://ex.org/p> <http://ex.org/y> .\n'
    b'<http://ex.org/a> <http://ex.org/q> _:joint .\n'
    b'_:joint <http://ex.org/p> "value"@en .\n'
)


class SelectiveFetch(unittest.TestCase):
    def test_anchor_filter_preserves_source_bytes(self):
        q=("SELECT ?s WHERE { ?s <http://ex.org/p> <http://ex.org/x> . "
           "?s <http://ex.org/q> ?o }")
        filters=selective.compile_filters(q)
        self.assertIsNotNone(filters[P])
        self.assertIsNone(filters[Q])
        source_p=b"".join(line for line in SOURCE.splitlines(keepends=True)
            if P.encode() in line)
        selected=selective.filter_fragment(source_p,filters[P])
        self.assertEqual(selected,b'<http://ex.org/a> <http://ex.org/p> <http://ex.org/x> .\n')
        self.assertNotIn(b"<http://ex.org/b>",selected)
        self.assertEqual(filters[Q],None)

    def test_repeated_predicate_wildcard_forces_full_fetch(self):
        q=("SELECT ?s WHERE { ?s <http://ex.org/p> <http://ex.org/x> . "
           "?s <http://ex.org/p> ?another . ?s <http://ex.org/q> ?v }")
        self.assertIsNone(selective.compile_filters(q)[P])

    def test_same_predicate_multiple_anchors_are_unioned(self):
        q=("SELECT ?s WHERE { ?s <http://ex.org/p> <http://ex.org/x> . "
           "?s <http://ex.org/p> <http://ex.org/y> . ?s <http://ex.org/q> ?v }")
        spec=selective.compile_filters(q)[P]
        source_p=b"".join(line for line in SOURCE.splitlines(keepends=True)
            if P.encode() in line)
        filtered=selective.filter_fragment(source_p,spec)
        self.assertIn(b"<http://ex.org/a>",filtered)
        self.assertIn(b"<http://ex.org/b>",filtered)
        self.assertNotIn(b'_:joint <http://ex.org/p>',filtered)

    def test_literal_language_exactness(self):
        q=('SELECT ?s WHERE { ?s <http://ex.org/q> "value"@en . '
           '?s <http://ex.org/p> ?o }')
        raw=(b'<http://ex.org/a> <http://ex.org/q> "value"@en .\n'
             b'<http://ex.org/b> <http://ex.org/q> "value"@fr .\n')
        self.assertEqual(selective.filter_fragment(raw,selective.compile_filters(q)[Q]),
            b'<http://ex.org/a> <http://ex.org/q> "value"@en .\n')

    def test_same_lexical_blank_node_identity(self):
        raw=b'_:node1 <http://ex.org/q> <http://ex.org/a> .\n'
        entries=selective.index_original_lines(raw)
        self.assertEqual(selective.select_original_lines(entries,[{
            "subject":None,"object":["iri","http://ex.org/a"]}]),raw)

    def test_full_answer_semantics_on_real_original_triples(self):
        q=("SELECT ?s WHERE { ?s <http://ex.org/p> <http://ex.org/x> . "
           "?s <http://ex.org/q> ?o }")
        filters=selective.compile_filters(q)
        temp=Store()
        temp.load(input=SOURCE,format=RdfFormat.N_TRIPLES)
        parts=[]
        for p in (P,Q):
            raw=b"".join(line for line in SOURCE.splitlines(keepends=True)
                if p.encode() in line)
            parts.append(selective.filter_fragment(raw,filters[p]))
        alt=Store()
        alt.load(input=b"".join(parts),format=RdfFormat.N_TRIPLES)
        self.assertEqual(certify(temp,alt,q)["status"],"PASS")

    def test_request_assembly_keeps_router_groups(self):
        self.assertEqual(selective.work_requests({0:[P],1:[Q]},
            {P:[{"subject":None,"object":["iri","http://ex.org/x"]}],Q:None}),
            {0:{P:[{"subject":None,"object":["iri","http://ex.org/x"]}]},1:{Q:None}})


if __name__=="__main__":
    unittest.main()
