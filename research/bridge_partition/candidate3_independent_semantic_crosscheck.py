#!/usr/bin/env python3
"""Independent certifier agreement on full-original SWDF SPARQL calibration.

Physically source-preserving 4x separate Oxigraph indexed TCP workers. Runs
unchanged SELECT, tests two separately implemented conservative verifiers
on all original calibration queries. 84 previously inspected calibration
queries; DOES NOT reopen earlier holdout or claim new independent novelty.
"""
import collections,json,time,hashlib
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_swdf_semantic_calibration as study
import candidate3_source_identity_worker as workers
from candidate3_sparql_semantic_certifier import certify
from candidate3_sparql_semantic_oracle import certified_verify
OUT=Path("results_candidate3_independent_semantic_crosscheck")
OUT.mkdir(exist_ok=True)

def main():
    tick=time.perf_counter()
    graph,by_pred,sizes,roles,packs,loads,route,cap=core.prepare_source()
    central=Store()
    central.load(input=graph,format=RdfFormat.N_TRIPLES)
    plans,_=core.choose_plans(roles["training"],roles["calibration"],route,loads,sizes,cap)
    frag={p for p in route if len(route[p])>1}
    assert len(roles["calibration"])>=30
    methods={}
    for method in ("no_move","one_swap"):
        ports,procs=workers.start_group(packs)
        try:
            curr=route
            migration={"moved_bytes":0}
            if method!="no_move":
                curr,migration=core.physically_apply(plans[method],by_pred,route,loads,sizes,cap,ports)
            old_cache={}
            rows=[]
            for q in roles["calibration"]:
                try:
                    physical=study.execute_sharded(q["query"],q["pattern"],curr,ports,frag)
                    old=certify(central,physical["index"],q["query"],truth_full_cache=old_cache)
                    new=certified_verify(q["query"],central,
                         __import__("candidate3_sparql_semantic_oracle").from_oxigraph(
                             physical["index"],q["query"],max_rows=30000),
                         max_rows=30000)
                    x={"sha":q["text_hash"],"old":old["status"],"new":new["status"],
                       "old_reason":old.get("reason"),"new_reason":new.get("reason")}
                except Exception as exc:
                    x={"sha":q["text_hash"],"old":"INCONCLUSIVE","new":"BLOCKED",
                         "error":type(exc).__name__+":"+str(exc)[:150]}
                rows.append(x)
            counts=collections.Counter((r["old"],r["new"]) for r in rows)
            methods[method]={"n":len(rows),"status_agreements":{
                "/".join(k):v for k,v in sorted(counts.items())},
                "old_pass":sum(r["old"]=="PASS" for r in rows),
                "new_pass":sum(r["new"]=="PASS" for r in rows),
                "strict_both_pass":sum(r["old"]==r["new"]=="PASS" for r in rows),
                "moved_bytes":migration["moved_bytes"],
                "not_both_pass":[r for r in rows if not(r["old"]==r["new"]=="PASS")][:20]}
            print("INDEPENDENT_SEMANTIC_METHOD",method,json.dumps(
                {k:v for k,v in methods[method].items() if k!="not_both_pass"}),flush=True)
        finally:workers.stop_group(procs)
    result={"schema":"candidate3-independent-source-semantic-cross-check-v1",
      "source_sha":"97575d036db4e55fa89f25231d3afb2c427555bce4a60fc429f902ddf7c45400",
      "calibration_only":True,"n_calibration":len(roles["calibration"]),
      "n_four_independent_tcp_oxigraph_workers":4,
      "semantic_verifiers":["previous-W3C-conservative-pyoxigraph",
            "separate-rdflib-isomorphism-global-bnode-and-unordered-LIMIT"],
      "methods":methods,"seconds":round(time.perf_counter()-tick,3),
      "limitations":[
         "Previously examined SWDF calibration data, not fresh unseen query validation",
         "Same physical coordinator gathers raw RDF fragments and executes original query",
         "Cross-verifier agreement is not formal proof of W3C conformance for all SPARQL 1.1",
         "No matched prior-art runtime economic proof or multi-host result"]}
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("CROSSCHECK_SEMANTIC_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("CROSSCHECK_SEMANTIC_END",flush=True)
if __name__=="__main__":main()
