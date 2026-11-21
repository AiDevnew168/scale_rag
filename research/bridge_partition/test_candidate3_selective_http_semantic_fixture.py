#!/usr/bin/env python3
"""Physical localhost TCP four-index-worker identity + SPARQL-BGP proof fixture.

This uses only synthetic public RDF, not historic SWDF heldout requests.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent))
from pyoxigraph import RdfFormat,Store
import candidate3_source_identity_worker as worker
import candidate3_real_sparql_shards as transport
import candidate3_swdf_real_full_sparql_economics as router
import candidate3_selective_fetch_transport as selective
from candidate3_sparql_semantic_certifier import certify,solution_rows

P="<http://ex.org/p>"
Q="<http://ex.org/q>"
R="<http://ex.org/r>"
S="<http://ex.org/s>"
PACKS=[
 {P:b'_:shared <http://ex.org/p> <http://ex.org/x> .\n'
        b'_:other <http://ex.org/p> <http://ex.org/y> .\n'},
 {Q:b'_:shared <http://ex.org/q> "match"@en .\n'
        b'_:other <http://ex.org/q> "wrong"@en .\n'},
 {R:b'<http://ex.org/extra> <http://ex.org/r> <http://ex.org/x> .\n'},
 {S:b'<http://ex.org/extra> <http://ex.org/s> "unused" .\n'},
]
ROUTE={P:{0},Q:{1},R:{2},S:{3}}


class FourIndexedWorkersHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ports,cls.workers=worker.start_group(PACKS)
        cls.central=Store()
        cls.central.load(input=b"".join(b"".join(p.values()) for p in PACKS),
                         format=RdfFormat.N_TRIPLES)

    @classmethod
    def tearDownClass(cls):
        worker.stop_group(cls.workers)

    def request(self,query,method):
        filt=selective.compile_filters(query)
        groups=router.shards_for_query(tuple(sorted(filt)),ROUTE,set())
        result=[]
        for shard,requested in sorted(groups.items()):
            if method=="full":
                endpoint="/raw-fragments"
                body=json.dumps({"predicates":requested}).encode()
            else:
                endpoint="/selective-fragments"
                body=json.dumps({"filters":{
                    p:filt[p] for p in requested}}).encode()
            value,_lat=transport.call(self.ports[shard],endpoint,body,
                {"Content-Type":"application/json"},timeout=20)
            result.append(value)
        return b"".join(result)

    def test_http_reduces_original_bytes_preserves_cross_shard_bnode_join(self):
        q=("SELECT ?v WHERE { ?s <http://ex.org/p> <http://ex.org/x> . "
           "?s <http://ex.org/q> ?v }")
        full=self.request(q,"full")
        reduced=self.request(q,"filtered")
        self.assertLess(len(reduced),len(full))
        self.assertIn(b"_:shared",reduced)
        self.assertNotIn(b"_:other <http://ex.org/p>",reduced)
        for blob in (full,reduced):
            local=Store()
            local.load(input=blob,format=RdfFormat.N_TRIPLES)
            self.assertEqual(certify(self.central,local,q)["status"],"PASS")
            variables,rows=solution_rows(local,q)
            self.assertEqual(len(rows),1)

    def test_language_tagged_constant_selective_join(self):
        q=('SELECT ?s WHERE { ?s <http://ex.org/q> "match"@en . '
           '?s <http://ex.org/p> ?v }')
        reduced=self.request(q,"filtered")
        self.assertIn(b'"match"@en',reduced)
        self.assertNotIn(b'"wrong"@en',reduced)
        local=Store()
        local.load(input=reduced,format=RdfFormat.N_TRIPLES)
        self.assertEqual(certify(self.central,local,q)["status"],"PASS")

    def test_unrestricted_repeated_predicate_safe_fallback(self):
        q=("SELECT ?s WHERE { ?s <http://ex.org/p> <http://ex.org/x> . "
           "?s <http://ex.org/p> ?another . ?s <http://ex.org/q> ?v }")
        full=self.request(q,"full")
        reduced=self.request(q,"filtered")
        self.assertEqual(len(full),len(reduced))
        self.assertEqual(full,reduced)


if __name__=="__main__":
    unittest.main()
