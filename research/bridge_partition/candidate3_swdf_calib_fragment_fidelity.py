#!/usr/bin/env python3
"""Calibration-only physical predicate-fragment identity audit.

Checks *actual returned RDF triples* against source for every predicate in
calibration query families. Does not inspect heldout. Determines whether
unmodified LIMIT result divergence can coexist with identical input graphs.
This is NOT a repaired independent future economic study.
"""
import collections,hashlib,json,time
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_real_sparql_shards as net
import candidate3_paired_full_sparql as paired

OUT=Path("results_candidate3_swdf_calibration_fragment_fidelity")
OUT.mkdir(exist_ok=True)

def count_terms(data,pred):
    store=Store()
    store.bulk_load(input=data,format=RdfFormat.N_TRIPLES)
    query=f"SELECT ?s ?o WHERE {{ ?s {pred} ?o }}"
    bag=collections.Counter()
    for binding in store.query(query):
        bag[(str(binding["s"]),str(binding["o"]))]+=1
    serial=json.dumps(sorted((list(k),v) for k,v in bag.items()),
         separators=(",",":"),ensure_ascii=False)
    return {"n_triples":len(store),"n_query_results":sum(bag.values()),
      "lexical_term_bag_sha256":hashlib.sha256(serial.encode()).hexdigest(),
      "mentions_bnode":any(("_:" in str(k)) for k in bag)}
def run():
    graph,by_pred,sizes,roles,packs,loads,route,cap=core.prepare_source()
    predicates=sorted({p for x in roles["calibration"] for p in x["pattern"]})
    assert len(predicates)>=10
    plans,_=core.choose_plans(roles["training"],roles["calibration"],route,loads,sizes,cap)
    results={}
    for policy in ("no_move","one_swap","replica_only","swap_replica"):
        ports,workers=paired.start_group(packs)
        try:
            chosen=route
            migration={"moved_bytes":0}
            if policy!="no_move":
                chosen,migration=core.physically_apply(
                    plans[policy],by_pred,route,loads,sizes,cap,ports)
            checks=[]
            for pred in predicates:
                raw=b"".join(by_pred[pred])
                expected=count_terms(raw,pred)
                distributed=[]
                for portid in sorted(chosen[pred]):
                    payload=json.dumps({"predicates":[pred]}).encode()
                    returned,ms=net.call(ports[portid],"/construct",payload,
                                  {"Content-Type":"application/json"},timeout=90)
                    distributed.append(returned)
                actual=count_terms(b"".join(distributed),pred)
                exact=(expected["n_triples"]==actual["n_triples"] and
                       expected["lexical_term_bag_sha256"]==actual["lexical_term_bag_sha256"])
                checks.append({"predicate_sha256":hashlib.sha256(pred.encode()).hexdigest(),
                   "expected":expected,"distributed":actual,
                   "exact_lexical_graph_fragment_match":exact})
            results[policy]={"n_predicates":len(predicates),
                "n_exact_lexical_fragment_matches":sum(
                    x["exact_lexical_graph_fragment_match"] for x in checks),
                "n_blank_node_predicate_fragments":sum(
                    x["expected"]["mentions_bnode"] for x in checks),
                "migration":migration,
                "failures":[x for x in checks if not x["exact_lexical_graph_fragment_match"]][:15],
                "all_matches":all(x["exact_lexical_graph_fragment_match"] for x in checks)}
        finally:paired.shutdown(workers)
    verdict={"schema":"candidate3-swdf-four-physical-fragment-identity-calibration-v1",
       "source_rdf_sha":"97575d036db4e55fa89f25231d3afb2c427555bce4a60fc429f902ddf7c45400",
       "source_queries_sha":"7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3",
       "strict_only_calibration_predicates":len(predicates),
       "policies":results,
       "limitations":[
         "Original historical SWDF test queries have already been opened by prior exploratory runs; this test never queries their answers.",
         "Lexical RDF-term comparison over SELECT ?s ?o of local extracted fragments, not an isomorphism proof for arbitrarily re-labeled blank nodes.",
         "Physical multi-process indexes and HTTP, all on same localhost runner.",
         "Unordered SELECT LIMIT outputs can differ even on identical RDF datasets; this test isolates fragments and cannot substitute exact query-output equality.",
         "No production net-economic, P95 SLA or WISE/WASP superiority is claimed."]}
    OUT.joinpath("report.json").write_text(json.dumps(verdict,indent=2))
    summary={k:v for k,v in verdict.items() if k!="policies"}
    summary["policies"]={k:{kk:vv for kk,vv in v.items() if kk!="failures"}|
        {"failed_predicate_hashes":[x["predicate_sha256"] for x in v["failures"]]}
         for k,v in results.items()}
    print("CALIB_FRAGMENT_FIDELITY_START",flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    print("CALIB_FRAGMENT_FIDELITY_END",flush=True)

if __name__=="__main__":run()
