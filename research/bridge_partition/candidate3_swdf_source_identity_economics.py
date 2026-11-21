#!/usr/bin/env python3
"""SWDF four physical Oxigraph stores: source-preserving full SPARQL stress.

Unchanged 102 heldout queries and frozen training+calibration plan from previous
run; HOWEVER 102 heldout has already been inspected in previous experiment.
This is a BUG-FIX engineering A/B, not independent confirmation nor prior art
algorithm claim. Preserves original source NTriples blank-node identity at
fragment boundary instead of CONSTRUCT's potentially reminted labels.
"""
import collections,hashlib,json,math,random,statistics,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pyoxigraph import Store,RdfFormat
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_real_sparql_shards as engine
import candidate3_source_identity_worker as worker

OUT=Path("results_candidate3_swdf_identity_preserving")
OUT.mkdir(exist_ok=True)
SEED=20261121
REPS=2
METHODS=["no_move","one_swap","two_swap_greedy","replica_only","swap_replica"]

def query(q,pattern,locations,ports,frag):
    groups=core.shards_for_query(pattern,locations,frag)
    started=time.perf_counter()
    def one(tup):
        j,ps=tup
        raw,lat=engine.call(ports[j],"/raw-fragments",json.dumps({
           "predicates":sorted(ps)}).encode(),{"Content-Type":"application/json"},timeout=70)
        return j,raw,lat
    with ThreadPoolExecutor(max_workers=4) as executor:
        parts=list(executor.map(one,sorted(groups.items())))
    received=b"".join(x[1] for x in parts)
    indexed=Store()
    indexed.bulk_load(input=received,format=RdfFormat.N_TRIPLES)
    answer=engine.evaluate(indexed,q)
    return {"answer":answer,
      "wall_ms":round((time.perf_counter()-started)*1000,4),
      "network_bytes":len(received),"shard_calls":len(parts)}

def check_fragments(roles,by_pred,loc,ports):
    relevant=sorted(set(p for role in ("calibration",) for r in roles[role] for p in r["pattern"]))
    checks=[]
    for p in relevant:
        original=b"".join(by_pred[p])
        received=b""
        for j in sorted(loc[p]):
            raw,ms=engine.call(ports[j],"/raw-fragments",
                json.dumps({"predicates":[p]}).encode(),
                {"Content-Type":"application/json"},timeout=80)
            received+=raw
        checks.append({
            "predicate_sha256":hashlib.sha256(p.encode()).hexdigest(),
            "exact_original_NTriples_payload":received==original,
            "source_bytes":len(original),"received_bytes":len(received)})
    return {"n_calibration_relevant_predicates":len(checks),
       "n_exact_original_payload":sum(r["exact_original_NTriples_payload"] for r in checks),
       "failed_hashes":[r["predicate_sha256"] for r in checks
           if not r["exact_original_NTriples_payload"]]}

def nontime(ref,q,route,ports,frag):
    return query(q["query"],q["pattern"],route,ports,frag)

def run_stage(rows,truth,oldroute,oldports,newroute,newports,frag,repeat=REPS):
    rng=random.Random(SEED+len(rows))
    errors=[];pairs=[];baseline_failures=0;alt_failures=0
    for r in rows:
        h=r["text_hash"]
        if h not in truth:
            errors.append({"hash":h,"type":"central_unsupported_or_row_cap"})
            continue
        for i in range(repeat):
            try:
                if rng.randrange(2):
                    old=nontime(truth[h],r,oldroute,oldports,frag)
                    new=nontime(truth[h],r,newroute,newports,frag)
                else:
                    new=nontime(truth[h],r,newroute,newports,frag)
                    old=nontime(truth[h],r,oldroute,oldports,frag)
                old_ok=old["answer"]==truth[h]
                new_ok=new["answer"]==truth[h]
                if not old_ok:baseline_failures+=1
                if not new_ok:alt_failures+=1
                if not old_ok or not new_ok:
                    errors.append({"hash":h,"type":"original_FULL_SELECT_exact_multiset_mismatch",
                      "baseline_ok":old_ok,"alternative_ok":new_ok,
                      "query_has_unordered_limit":("LIMIT" in r["query"].upper() and
                         "ORDER BY" not in r["query"].upper())})
                pairs.append({"family":json.dumps(r["family"]),
                    "hash":h,"repeat":i,
                    "exact_original_answers_on_both":old_ok and new_ok,
                    "truth_nonempty":truth[h]["count"]>0,
                    "old_ms":old["wall_ms"],"alt_ms":new["wall_ms"],
                    "saved_ms":old["wall_ms"]-new["wall_ms"],
                    "bytes_saved":old["network_bytes"]-new["network_bytes"],
                    "contacts_saved":old["shard_calls"]-new["shard_calls"]})
            except Exception as exc:
                errors.append({"hash":h,"type":type(exc).__name__,"detail":str(exc)[:160]})
    return pairs,errors,{"n_records":len(pairs),"n_original_response_exact_pairs":
           sum(int(p["exact_original_answers_on_both"]) for p in pairs),
       "baseline_incorrect_pairs":baseline_failures,
       "alternate_incorrect_pairs":alt_failures,
       "number_errors_or_mismatches":len(errors),
       "nonempty_query_pairs":sum(int(p["truth_nonempty"]) for p in pairs),
       "total_network_bytes_saved":sum(p["bytes_saved"] for p in pairs),
       "total_contacts_saved":sum(p["contacts_saved"] for p in pairs),
       "paired_total_saved_ms_before_migration":round(sum(p["saved_ms"] for p in pairs),4),
       "p50_baseline_ms":round(statistics.median([p["old_ms"] for p in pairs]),4) if pairs else None,
       "p50_alt_ms":round(statistics.median([p["alt_ms"] for p in pairs]),4) if pairs else None,
       "errors_sample":errors[:12]}

def main():
    started=time.perf_counter()
    graph,by_pred,size,roles,packs,loads,route,cap=core.prepare_source()
    plans,decisions=core.choose_plans(roles["training"],roles["calibration"],
                                     route,loads,size,cap)
    assert set(plans)==set(METHODS)
    central=Store()
    central.bulk_load(input=graph,format=RdfFormat.N_TRIPLES)
    frag={p for p in route if len(route[p])>1}
    truth={};central_error=[]
    for key in ("calibration","holdout"):
        for r in roles[key]:
            try:truth[r["text_hash"]]=engine.evaluate(central,r["query"])
            except Exception as e:
                central_error.append({"hash":r["text_hash"],"type":type(e).__name__,
                     "error":str(e)[:120]})
    oldports,oldworkers=worker.start_group(packs)
    rows={}
    try:
        frozen=check_fragments(roles,by_pred,route,oldports)
        for action in METHODS:
            if action=="no_move":
                newports=oldports;newworkers=[]
                location=route
                mig={"moved_bytes":0,"wall_clock_migration_and_index_update_ms":0}
            else:
                newports,newworkers=worker.start_group(packs)
                location,mig=core.physically_apply(plans[action],by_pred,
                                                  route,loads,size,cap,newports)
            try:
                fidelity=check_fragments(roles,by_pred,location,newports)
                assert fidelity["n_exact_original_payload"]==fidelity["n_calibration_relevant_predicates"],fidelity
                # Diagnostic stage before re-testing already-opened holdout.
                calib_pairs,calib_errors,calib=run_stage(roles["calibration"],truth,
                         route,oldports,location,newports,frag,repeat=1)
                test_pairs,test_errors,test=run_stage(roles["holdout"],truth,
                         route,oldports,location,newports,frag,repeat=REPS)
                exact=(test["number_errors_or_mismatches"]==0 and
                     test["n_records"]==len(roles["holdout"])*REPS)
                rows[action]={"plan":plans[action],"migration":mig,
                  "calibration_fragment_identity":fidelity,
                  "calibration":calib,"heldout_exploratory":test,
                  "full_original_query_correctness_gate":exact,
                  "net_economic_acceptance_gate":"NOT_EVALUABLE_FULL_EXACTNESS_FAILED"
                     if not exact else "PENDING_INDEPENDENT_FRESH_CONFIRMATION",
                  "net_point_if_complete_only":(
                      round(test["paired_total_saved_ms_before_migration"]-
                         mig["wall_clock_migration_and_index_update_ms"],4) if exact else None)}
                print("RAW_SOURCE_ACTION",action,json.dumps({
                      "fidelity":fidelity["n_exact_original_payload"],
                      "test":{k:v for k,v in test.items() if k!="errors_sample"},
                      "gate":rows[action]["net_economic_acceptance_gate"]}),flush=True)
            finally:
                if newworkers:worker.stop_group(newworkers)
    finally:worker.stop_group(oldworkers)
    result={"schema":"candidate3-SWDF-source-identity-preserving-physical-SPARQL-A-B-v1",
       "sha_graph_uncompressed":"97575d036db4e55fa89f25231d3afb2c427555bce4a60fc429f902ddf7c45400",
       "sha_query_file":"7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3",
       "n_full_central_rdf_triples":len(central),
       "initial_four_shard_bytes":loads,
       "byte_ceiling":cap,
       "n_heldout_texts":len(roles["holdout"]),
       "n_heldout_predicate_families":len({r["family"] for r in roles["holdout"]}),
       "n_calibration_predicates":frozen["n_calibration_relevant_predicates"],
       "source_raw_calibration_predicates_match_baseline":frozen,
       "central_query_failures":central_error,
       "plans_selected_before_test":decisions,
       "actions":rows,
       "elapsed_seconds":round(time.perf_counter()-started,2),
       "limitations":[
         "Original SWDF future heldout was ALREADY inspected in earlier 2026-11-21 experiment; this is an engineering repair/regression, not an independent confirmatory success.",
         "The output of original SELECT LIMIT without ORDER BY is SPARQL-unordered and may differ legally across stores; exact query multiset still enforced in the acceptance gate and failures are NOT silently excluded.",
         "Workers now serve ORIGINAL RDF NTriples predicate payloads, retaining blank node lexical source identity; underlying Oxigraph physical index still stores and mutates the data.",
         "The coordinator performs entire original unmodified SPARQL query; workers serve raw indexed fragments, not native per-shard distributed joins.",
         "Complete source dataset but graph snapshot version matching to recorded SWDF query logs is not verified.",
         "Same-machine four-TCP-worker benchmark; no cross-host Ethernet, power or real USD cost.",
         "No faithful runnable WISE/WASP/AdPart system comparison, and no novel algorithm publication claim."]}
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    summary={k:v for k,v in result.items() if k!="actions"}
    summary["actions"]={a:{k:v for k,v in item.items()
       if k not in ("calibration", "heldout_exploratory")}|
       {"calibration":{k:v for k,v in item["calibration"].items() if k!="errors_sample"},
        "heldout":{k:v for k,v in item["heldout_exploratory"].items() if k!="errors_sample"}}
       for a,item in rows.items()}
    print("RAW_IDENTITY_SWDF_E2E_START",flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    print("RAW_IDENTITY_SWDF_E2E_END",flush=True)
if __name__=="__main__":main()
