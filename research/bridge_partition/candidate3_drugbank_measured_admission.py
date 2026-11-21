#!/usr/bin/env python3
"""Frozen independent full DrugBank real-RDF candidate admission.

Source real complete RDF, benchmark synthetic source-generated queries, NOT
actual dated SPARQL logs. This exact decision procedure was PRECOMMITTED to
CANDIDATE3_FROZEN_NEW_DRUGBANK_ECONOMIC_ABSTENTION_PROTOCOL.md before the
original 150MB DrugBank.nt data / any test answers were observed.
"""
import collections,hashlib,json,math,random,statistics,time
from pathlib import Path
from remotezip import RemoteZip
from pyoxigraph import Store,RdfFormat
import candidate3_nyt_real_graph_preflight as nytsrc
import candidate3_nyt_full_real_e2e as nytrun
import candidate3_ptcr_watdiv_byte_stress as swap
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_real_sparql_shards as engine
import candidate3_source_identity_worker as workers
from candidate3_sparql_semantic_certifier import certify

URL="https://zenodo.org/api/records/22140177/files/rdf_datasets.zip/content"
GRAPH="DrugBank.nt"
BYTES=150431510
BUDGET=25000000
SEED=20261121
BOOT=3000
REPS_CALIB=2
REPS_TEST=3
OUT=Path("results_candidate3_drugbank_frozen_economic_admission")
OUT.mkdir(exist_ok=True)

def load_and_split():
    with RemoteZip(URL,timeout=130) as source:
        m=source.getinfo(GRAPH)
        assert m.file_size==BYTES,(m.file_size,BYTES)
        raw=source.read(GRAPH)
    assert len(raw)==BYTES
    hash_src=hashlib.sha256(raw).hexdigest()
    subject,pred_counts,groups,triples=nytsrc.families(raw)
    assert len(groups)>=125,(len(groups),triples)
    selected=groups[:125]
    role={"training":[],"calibration":[],"test":[]}
    for pat,support in selected:
        key="candidate3-DrugBank-risk-gate-v1:"+str(SEED)+":"+json.dumps(pat)
        fold=int(hashlib.sha256(key.encode()).hexdigest(),16)%5
        name="training" if fold<=2 else ("calibration" if fold==3 else "test")
        query="SELECT DISTINCT ?s WHERE { "+" . ".join(
            "?s "+p+" ?o"+str(i) for i,p in enumerate(pat))+" . } LIMIT 3"
        role[name].append({"pattern":pat,"query":query,"support":support,
            "hash":hashlib.sha256(query.encode()).hexdigest()})
    assert len(role["test"])>=20 and len(role["calibration"])>=15 and len(role["training"])>=50,        {k:len(v) for k,v in role.items()}
    assert not({x["pattern"] for x in role["test"]}&
        {x["pattern"] for x in role["training"]+role["calibration"]})
    by_pred=collections.defaultdict(list);sizes=collections.Counter()
    for line in raw.splitlines(keepends=True):
        if not line.strip():continue
        arr=line.split(None,2)
        assert len(arr)==3 and arr[1].startswith(b"<")
        p=arr[1].decode("utf8")
        sizes[p]+=len(line)
        by_pred[p].append(line)
    assert sum(sizes.values())==len(raw)
    cap=math.ceil(len(raw)*1.10/4)
    packs,loads,route=engine.payloads_by_shard(by_pred,sizes,cap)
    assert max(loads)<=cap
    return raw,hash_src,triples,role,by_pred,sizes,cap,packs,loads,route

def pairs_evaluate(queries,original,original_ports,moved,moved_ports,fragmented,
        truth,repeat=REPS_CALIB):
    rng=random.Random(SEED+repeat)
    rows=[];bad=[];cache={}
    for q in queries:
        for rep in range(repeat):
            try:
                if rng.randrange(2):
                    base=nytrun.run_query(original_ports,original,q,fragmented)
                    alt=nytrun.run_query(moved_ports,moved,q,fragmented)
                else:
                    alt=nytrun.run_query(moved_ports,moved,q,fragmented)
                    base=nytrun.run_query(original_ports,original,q,fragmented)
                fullb=certify(truth,base["store"],q["query"],cache)
                fulla=certify(truth,alt["store"],q["query"],cache)
                if fullb["status"]!="PASS" or fulla["status"]!="PASS":
                    bad.append({"hash":q["hash"],"repeat":rep,
                      "base":fullb,"candidate":fulla})
                rows.append({"family":json.dumps(q["pattern"]),"repeat":rep,
                   "saving_ms":base["wall_ms"]-alt["wall_ms"],
                   "old_ms":base["wall_ms"],"new_ms":alt["wall_ms"],
                   "contacts_saved":base["shards"]-alt["shards"],
                   "bytes_saved":base["tcp_payload_bytes"]-alt["tcp_payload_bytes"]})
            except Exception as exc:
                bad.append({"hash":q["hash"],"repeat":rep,
                    "error":type(exc).__name__+":"+str(exc)[:150]})
    return rows,bad

def quantile95(rows,key):
    nums=sorted(x[key] for x in rows)
    return nums[min(len(nums)-1,math.ceil(.95*len(nums))-1)] if nums else None

def mean_lcb(rows,expected_future_families,replicate,fixed_cost):
    groups=collections.defaultdict(list)
    for x in rows:groups[x["family"]].append(x["saving_ms"])
    vals=[statistics.mean(k) for k in groups.values()]
    if len(vals)<15:return None
    rng=random.Random(SEED)
    n=len(vals)
    dist=sorted(statistics.mean([vals[rng.randrange(n)] for _ in range(n)])
       *expected_future_families*replicate-fixed_cost for __ in range(BOOT))
    return {"n_calibration_families":n,
        "net_predicted_ms_at_test_horizon":round(statistics.mean(vals)*expected_future_families*replicate-fixed_cost,4),
        "bootstrap_lower95_net_ms":round(dist[74],4),
        "bootstrap_upper95_net_ms":round(dist[2924],4)}

def main():
    start=time.perf_counter()
    raw,sha,lines,roles,by_pred,sizes,cap,packs,loads,route=load_and_split()
    chosen,train=swap.select_first_under_same_budget(route,sizes,loads,cap,
        [{"pattern":x["pattern"]} for x in roles["training"]])
    assert train["selected_move_bytes"]<=BUDGET
    frag={p for p,sh in route.items() if len(sh)>1}
    central=Store()
    central.load(input=raw,format=RdfFormat.N_TRIPLES)
    original_port,original_worker=workers.start_group(packs)
    changed_port,changed_worker=workers.start_group(packs)
    try:
        action={"swaps":[chosen] if chosen else [],
              "replicate":None,"planned_bytes":train["selected_move_bytes"]}
        after,migration=core.physically_apply(action,by_pred,route,loads,
            sizes,cap,changed_port)
        calib,error_calib=pairs_evaluate(roles["calibration"],route,original_port,
            after,changed_port,frag,central,repeat=REPS_CALIB)
        assert migration["moved_bytes"]<=BUDGET
        lcb=mean_lcb(calib,len(roles["test"]),REPS_TEST,
                      migration["wall_clock_migration_and_index_update_ms"])
        p95_base=quantile95(calib,"old_ms")
        p95_action=quantile95(calib,"new_ms")
        accept=(bool(chosen) and not error_calib
             and len(calib)==len(roles["calibration"])*REPS_CALIB
             and lcb is not None and lcb["bootstrap_lower95_net_ms"]>0
             and p95_action<=p95_base*1.01)
        decision={"schema":"candidate3-DrugBank-fixed-prior-only-move-acceptance-v1",
          "graph_source_sha256":sha,
          "graph_source_bytes":len(raw),
          "graph_unique_rdf_triples":len(central),
          "graph_source_NTriples_lines":lines,
          "source_query_origin":"SYNTHETIC_DATA_DERIVED_NO_ORGANIC_LOG",
          "n_query_families":{k:len(v) for k,v in roles.items()},
          "query_family_hashes_by_role":{k:hashlib.sha256(
             ("\n".join(sorted(x["hash"] for x in vals))).encode()).hexdigest()
             for k,vals in roles.items()},
          "fixed_candidate":chosen,"candidate_selection_training_only":train,
          "actual_migration":migration,
          "calibration_repetitions":len(calib),
          "calibration_query_failures":error_calib[:10],
          "calibration_95pct_latency_baseline_ms":p95_base,
          "calibration_95pct_latency_action_ms":p95_action,
          "net_confidence_95":lcb,
          "accepted":"one_swap" if accept else "no_move",
          "does_not_use_heldout_query_labels":True,
          "acceptance_only_if_95_lower_positive_and_full_semantics_and_p95_safe":True}
        OUT.joinpath("DECISION_LOCKED_BEFORE_TEST.json").write_text(json.dumps(decision,indent=2))
        print("DRUGBANK_DECISION_SEALED_BEFORE_TEST",decision["accepted"],flush=True)
        # Original fully joined test results are only evaluated AFTER decision is written.
        test,error_test=pairs_evaluate(roles["test"],route,original_port,
                   after,changed_port,frag,central,repeat=REPS_TEST)
        exact=(len(test)==len(roles["test"])*REPS_TEST and not error_test)
        counterfactual=mean_lcb(test,len(roles["test"]),REPS_TEST,
                  migration["wall_clock_migration_and_index_update_ms"]) if exact else None
        deployed_if_accept={
          "deployed_action":decision["accepted"],
          "measured_migration_bytes":migration["moved_bytes"] if accept else 0,
          "actual_net_savings_ms":(
            round(sum(t["saving_ms"] for t in test)-migration["wall_clock_migration_and_index_update_ms"],4)
            if accept and exact else (0.0 if not accept else None)),
          "no_move_saved_migration_barrier_ms":migration["wall_clock_migration_and_index_update_ms"] if not accept else 0,
          "test_full_original_select_semantic_pass":exact}
        report={"schema":"candidate3-second-new-real-DrugBank-economic-admission-v1",
          "source_complete_sha256":sha,"original_triples":len(central),
          "original_ntriples_source_lines":lines,
          "frozen_decision":decision,
          "complete_holdout_query_repetitions":len(test),
          "all_original_select_semantically_pass":exact,
          "heldout_semantic_failures":error_test[:16],
          "counterfactual_always_migrate_outcome_after_lock":counterfactual,
          "post_lock_realized_selected_policy":deployed_if_accept,
          "original_static_shard_raw_bytes":loads,
          "original_max_per_shard_capacity_bytes":cap,
          "total_elapsed_seconds":round(time.perf_counter()-start,2),
          "paper_sota_economic_GO":False,
          "limitations":[
            "DrugBank NTriples complete original real RDF graph was newly fetched after precommitted source+strategy; no source sampling",
            "Query patterns generated from source subject predicate cooccurrence (synthetic), NOT a real user SPARQL timestamped log",
            "Only 1 bounded balanced two-predicate move vs no-move, not complete WISE/WASP/DIAERESIS benchmark",
            "Two independent physical four-worker configurations share the same GitHub Actions host, not real cross-host network",
            "Full original SELECT and bnode semantics verified for both original static and selected move after original source-conserving load",
            "Physical migration is paused during operation; not crash-safe atomic distributed transaction",
            "Confidence interval assumes calibration/test query-family exchangeability; without real temporal drift it cannot guarantee positive benefit",
            "Controller selection frozen before test, but cross-domain exploratory research path and source selection may still involve researcher degrees of freedom",
            "If abstained, no_move is safety rather than positive economic savings versus incumbent no_move"]}
        OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
        brief={k:v for k,v in report.items() if k!="heldout_semantic_failures"}
        brief["heldout_failures_count"]=len(error_test)
        print("DRUGBANK_ADMISSION_GATE_START",flush=True)
        print(json.dumps(brief,indent=2),flush=True)
        print("DRUGBANK_ADMISSION_GATE_END",flush=True)
    finally:
        workers.stop_group(original_worker)
        workers.stop_group(changed_worker)

if __name__=="__main__":main()
