#!/usr/bin/env python3
"""Focused calibration-only forensic audit of four valid-but-empty shard queries.

No heldout query labels read. Prints original public FEASIBLE source query
for precisely four already known SHA256 calibration failures, with every
actual RDF fragment byte count and query algebra triple structures.
"""
import hashlib,json,collections
from pathlib import Path
from pyoxigraph import Store,RdfFormat
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_real_sparql_shards as net
import candidate3_source_identity_worker as workers
from candidate3_sparql_semantic_certifier import characterize,solution_rows

HASHES={
 "33e783e4abeee06f53cde08782d8fe9f93b8a12f6dbe2501e397f0fbb1214bab",
 "38e0d2ce07a5c87e75a6070993f35e4b12bb2675d510853f713f60ca1022b4bc",
 "489709172858844dc73cbe4a54d0e0da0686063f19ac2018802f023537949efb",
 "72b094d60adfda9c6d4ae6e574635290a9b8d991ec7a510926872b745ef07d51"
}
OUT=Path("results_candidate3_SWDF_semantic_forensics")
OUT.mkdir(exist_ok=True)

def main():
    graph,pred,size,roles,packs,loads,route,cap=core.prepare_source()
    original=Store();original.bulk_load(input=graph,format=RdfFormat.N_TRIPLES)
    target=[r for r in roles["calibration"] if r["text_hash"] in HASHES]
    assert len(target)==4
    results=[]
    for r in target:
        groups=core.shards_for_query(r["pattern"],route,range(4),set())
        # Physically retrieved bytes are byte-exact source fragments; no worker
        # process needed to isolate root cause of original data completeness.
        collected=[]
        for shard,ps in sorted(groups.items()):
            for p in ps:
                assert shard in route[p]
                collected.append(b"".join(pred[p]))
        reconstructed=b"".join(collected)
        sub=Store();sub.bulk_load(input=reconstructed,format=RdfFormat.N_TRIPLES)
        raw=r["query"];meta=characterize(raw)
        original_rows=solution_rows(original,raw,maximum=30000)[1]
        subset_rows=solution_rows(sub,raw,maximum=30000)[1]
        triple_nodes=[]
        def scan(x):
            if isinstance(x,CompValue):
                if x.name=="BGP":
                    for s,p,o in x["triples"]:
                        triple_nodes.append([str(s),str(p),str(o)])
                for key,val in x.items():
                    if key not in ("triples","_vars"):scan(val)
            elif isinstance(x,(tuple,list)):
                for val in x:scan(val)
        scan(prepareQuery(raw).algebra)
        result={"hash":r["text_hash"],"original_query":raw,
         "normalized_predicates":r["pattern"],
         "algebra_BGP_triples":triple_nodes,
         "query_original_count":len(original_rows),
         "query_filtered_input_count":len(subset_rows),
         "selected_source_predicate_payload_bytes":len(reconstructed),
         "n_source_predicates":len(r["pattern"]),
         "filtered_graph_triples":len(sub),
         "slice_kind":meta.kind,
         "raw_first_central":original_rows[:3],
         "raw_first_subset":subset_rows[:3]}
        results.append(result)
    report={"schema":"candidate3-4-SWDF-calibration-query-mismatch-forensics-v1",
      "n":len(results),"all_queries_from_calibration_only":True,
      "source_sha":"7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3",
      "causes":results}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("SWDF_CALIB_FORENSICS_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("SWDF_CALIB_FORENSICS_END",flush=True)
if __name__=="__main__":main()
