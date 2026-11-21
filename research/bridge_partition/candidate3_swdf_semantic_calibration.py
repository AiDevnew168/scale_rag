#!/usr/bin/env python3
"""Physically indexed SWDF 4-worker SPARQL semantic verifier calibration.

Test REPAIRED identity-preserving worker (but source SWDF already inspected).
For every calibration SELECT, original text runs unchanged both on central
and on a coordinator graph materialized from TCP worker original RDF source
fragments; a separate truth-only unbounded query is evaluated if original
has unordered LIMIT. No future holdout query *outcomes* needed here.
Never claim publishable independent confirmation from this regression.
"""
import collections,hashlib,json,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_real_sparql_shards as transport
import candidate3_source_identity_worker as workers
from candidate3_sparql_semantic_certifier import certify,characterize

OUT=Path("results_candidate3_swdf_semantic_calibration")
OUT.mkdir(exist_ok=True)

def execute_sharded(raw_query,pattern,route,ports,frag):
    grouping=core.shards_for_query(pattern,route,frag)
    start=time.perf_counter()
    def fetch(item):
        shard,preds=item
        payload=json.dumps({"predicates":sorted(preds)}).encode()
        b,ms=transport.call(ports[shard],"/raw-fragments",payload,
                  {"Content-Type":"application/json"},timeout=50)
        return shard,b
    with ThreadPoolExecutor(max_workers=4) as pool:
        parts=list(pool.map(fetch,sorted(grouping.items())))
    data=b"".join(part for _,part in parts)
    rdf=Store()
    rdf.bulk_load(input=data,format=RdfFormat.N_TRIPLES)
    result={"index":rdf,"wall_ms":(time.perf_counter()-start)*1000,
           "actual_fragment_bytes":len(data),"shard_contacts":len(parts)}
    return result

def main():
    started=time.perf_counter()
    original_graph,by_pred,sizes,roles,packs,loads,route,cap=core.prepare_source()
    plans,_=core.choose_plans(roles["training"],roles["calibration"],route,loads,sizes,cap)
    assert len(roles["calibration"])>=30
    central=Store()
    central.bulk_load(input=original_graph,format=RdfFormat.N_TRIPLES)
    frag={p for p in route if len(route[p])>1}
    cache={}
    output={}
    for method in ("no_move","one_swap","replica_only","swap_replica"):
        ports,processes=workers.start_group(packs)
        try:
            after=route
            moved={"moved_bytes":0,"wall_clock_migration_and_index_update_ms":0}
            if method!="no_move":
                after,moved=core.physically_apply(plans[method],by_pred,route,
                                 loads,sizes,cap,ports)
            audit=[]
            for row in roles["calibration"]:
                sha=row["text_hash"]
                q=row["query"]
                try:
                    result=execute_sharded(q,row["pattern"],after,ports,frag)
                    outcome=certify(central,result["index"],q,truth_full_cache=cache)
                except Exception as exc:
                    outcome={"status":"INCONCLUSIVE","kind":"unknown",
                             "reason":type(exc).__name__+": "+str(exc)[:180]}
                    result={"wall_ms":None,"actual_fragment_bytes":None,
                           "shard_contacts":None}
                audit.append({"sha":sha,"outcome":outcome,
                              "worker_fetch_and_bulk_load_wall_ms":result["wall_ms"],
                              "predicate_payload_bytes":result["actual_fragment_bytes"],
                              "shard_contacts":result["shard_contacts"]})
            statuses=collections.Counter(r["outcome"]["status"] for r in audit)
            reasons=collections.Counter((r["outcome"]["kind"],
                        r["outcome"].get("reason","")) for r in audit)
            output[method]={"policy":plans[method],"physical_migration":moved,
                "n_calibration":len(audit),
                "statuses":dict(statuses),
                "reason_counts":[{"kind":k[0],"reason":k[1],"n":v}
                    for k,v in reasons.most_common()],
                "outcomes":audit,\n                "nonpassing_hash_and_reason":[{"sha":z["sha"],**z["outcome"]} for z in audit\n                                  if z["outcome"]["status"]!="PASS"]}
            print("SEMANTIC_CALIBRATION_ACTION",method,dict(statuses),flush=True)
        finally:workers.stop_group(processes)
    report={"schema":"candidate3-SWDF-calibration-SPARQL-semantic-certifier-v1",
        "source_graph_sha":"97575d036db4e55fa89f25231d3afb2c427555bce4a60fc429f902ddf7c45400",
        "source_queries_sha":"7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3",
        "four_independent_indexed_worker_processes":True,
        "n_full_graph_rdf_triples":len(central),
        "methods":output,
        "truth_unsliced_query_cache_size":len(cache),
        "elapsed_seconds":round(time.perf_counter()-started,2),
        "strict_confirmatory_SOTA_profit_GO":False,
        "limitations":[
          "Calibration only, source previously examined; NOT independent confirmatory performance",
          "Unordered LIMIT checked by unsliced centralized entire result bag and legal subset",
          "Ordered LIMIT with differing but potentially tied results returns INCONCLUSIVE",
          "Blank-node label scope preserved through globally consistent answer-bag bijection",
          "Raw source fragments over TCP preserve blank node identity; this is NOT a production federated SPARQL optimizer",
          "No objective/economic advantage can be claimed if any originally eligible queries remain FAIL or INCONCLUSIVE",
          "Central unsliced result row guard may cause INCONCLUSIVE for very large result bags",
          "No cross-host network, real date-aligned source log, WISE/WASP or DIAERESIS runtime comparison"] }
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    short={k:v for k,v in report.items() if k!="methods"}
    short["methods"]={k:{q:v for q,v in val.items() if q!="outcomes"} for k,val in output.items()}
    print("SEMANTIC_CALIBRATION_GATE_START",flush=True)
    print(json.dumps(short,indent=2),flush=True)
    print("SEMANTIC_CALIBRATION_GATE_END",flush=True)
if __name__=="__main__":main()
