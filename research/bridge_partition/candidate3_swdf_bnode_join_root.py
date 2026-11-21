#!/usr/bin/env python3
"""Calibration-only forensic: exactly why 2-predicate 3-BGP SWDF joins vanish.

Inspect central and source-predicate-extracted subgraph with original blank
node IDs; test connectivity at each BGP stage without changing source queries.
Never claim that eliminating a subset of failed queries proves correctness.
"""
import hashlib,json,collections
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_swdf_real_full_sparql_economics as core
from candidate3_sparql_semantic_certifier import solution_rows
OUT=Path("results_candidate3_SWDF_blanknode_join_root");OUT.mkdir(exist_ok=True)
SHA="38e0d2ce07a5c87e75a6070993f35e4b12bb2675d510853f713f60ca1022b4bc"
RDFTYPE="<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
DTSTART="<http://www.w3.org/2002/12/cal/ical#dtstart>"
CLASS="<http://data.semanticweb.org/ns/swc/ontology#ConferenceEvent>"
def run():
    graph,pred,size,roles,_,_,_,_=core.prepare_source()
    full=Store();full.bulk_load(input=graph,format=RdfFormat.N_TRIPLES)
    fragment=Store()
    raw=b"".join(pred[RDFTYPE])+b"".join(pred[DTSTART])
    fragment.bulk_load(input=raw,format=RdfFormat.N_TRIPLES)
    serial=Store();serial.load(input=raw,format=RdfFormat.N_TRIPLES)
    q1=f"SELECT ?obj WHERE {{ ?obj {RDFTYPE} {CLASS} }} LIMIT 20"
    q2=f"SELECT ?obj ?targetObj WHERE {{ ?obj {RDFTYPE} {CLASS} . ?obj {DTSTART} ?targetObj }} LIMIT 20"
    q3=f"SELECT ?obj ?targetObj ?typ WHERE {{ ?obj {RDFTYPE} {CLASS} . ?obj {DTSTART} ?targetObj . ?targetObj {RDFTYPE} ?typ }} LIMIT 20"
    qdate=f"SELECT ?obj ?date WHERE {{ ?obj {DTSTART} ?date }} LIMIT 20"
    queries={"types_only":q1,"class_to_dtstart":q2,
        "class_dtstart_target_type":q3,"date_only":qdate}
    comparison={}
    for name,q in queries.items():
        item={}
        for gname,g in (("full",full),("fragment_bulk_load",fragment),("fragment_serial_load",serial)):
            names,rows=solution_rows(g,q)
            item[gname]={"rows":len(rows),"first5":rows[:5]}
        comparison[name]=item
    result={"schema":"candidate3-SWDF-blanknode-3pattern-join-failure-root-v1",
      "source_exact_SHA":"97575d036db4e55fa89f25231d3afb2c427555bce4a60fc429f902ddf7c45400",
      "full_graph_triples":len(full),"fragment_graph_triples":len(fragment),"serial_load_triples":len(serial),
      "original_2predicate_NTriples_bytes":len(raw),
      "full_queries_were_not_heldout":True,
      "comparisons":comparison,
      "note":"If 2-pattern matches but 3-pattern does not, the targetObj/rdf:type join is broken; inspect RDF blank-node parser scope."}
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("SWDF_BNODE_JOIN_ROOT_START");print(json.dumps(result,indent=2))
    print("SWDF_BNODE_JOIN_ROOT_END")
if __name__=="__main__":run()
