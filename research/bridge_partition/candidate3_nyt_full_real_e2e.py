#!/usr/bin/env python3
"""Brand-new original NYT RDF full 4-worker SELECT correctness/economics.

The ORIGINAL 335,198-triple NYT dataset was not used in previous candidate3
experiments. The test queries are STRICTLY synthetic from source predicate
co-occurrences, not organic logs. Protocol frozen at:
CANDIDATE3_FROZEN_NYT_NEW_REAL_GRAPH_ENGINEERING_GATE.md.

All query family membership split and selected before any query is run.
Only historic+calibration query families choose a byte-capped swap. Four
physical independent TCP Oxigraph stores run exact original SELECT and
source-identity-preserving fragment transfer, central full RDF verifies.
"""
import collections,hashlib,json,math,random,statistics,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_nyt_real_graph_preflight as source
import candidate3_real_sparql_shards as transport
import candidate3_source_identity_worker as workers
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_ptcr_watdiv_byte_stress as swap
from candidate3_sparql_semantic_certifier import certify,solution_rows

OUT=Path("results_candidate3_nyt_full_real_SPARQL")
OUT.mkdir(exist_ok=True)
SOURCE_SHA="aac49186ab45899f8f467f9264367ddad76a8a08c6011cb618a5c2d6fe4aed85"
K=5;SEED=20261121;REPS=3
BUDGET=25_000_000
STRICT_P95_TOLERANCE=.01

def prepare():
    raw=source.get_full_raw()
    assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    subs,freq,groups,n=source.families(raw)
    assert n==335198 and len(groups)>=125
    chosen=groups[:125]
    roles={"training":[],"calibration":[],"test":[]}
    for pattern,support in chosen:
        identity="candidate3-NYT-real-graph-disjoint-v1:"+str(SEED)+":"+json.dumps(pattern)
        fold=int(hashlib.sha256(identity.encode()).hexdigest(),16)%K
        role="training" if fold<=2 else ("calibration" if fold==3 else "test")
        body=" . ".join("?s "+p+" ?o"+str(i) for i,p in enumerate(pattern))+" ."
        query="SELECT DISTINCT ?s WHERE { "+body+" } LIMIT 3"
        roles[role].append({"pattern":pattern,"support":support,
         "query":query,"hash":hashlib.sha256(query.encode()).hexdigest()})
    assert sum(map(len,roles.values()))==125
    assert len(roles["test"])>=20 and len(roles["training"])>=50
    assert not(set(x["pattern"] for x in roles["test"]) &
        set(x["pattern"] for x in roles["training"]+roles["calibration"]))
    by_pred=collections.defaultdict(list);sizes=collections.Counter()
    for line in raw.splitlines(keepends=True):
        if not line.strip():continue
        p=line.split(None,2)[1].decode()
        by_pred[p].append(line);sizes[p]+=len(line)
    assert sum(sizes.values())==len(raw)
    cap=math.ceil(len(raw)*1.10/4)
    packs,loads,route=transport.payloads_by_shard(by_pred,sizes,cap)
    assert len(packs)==4 and max(loads)<=cap
    return raw,roles,by_pred,sizes,cap,packs,loads,route

def run_query(ports,route,row,frag):
    group=core.shards_for_query(row["pattern"],route,frag)
    start=time.perf_counter()
    def fetch(item):
        i,ps=item
        buf,ms=transport.call(ports[i],"/raw-fragments",
             json.dumps({"predicates":sorted(ps)}).encode(),
             {"Content-Type":"application/json"},timeout=80)
        return buf
    with ThreadPoolExecutor(max_workers=4) as pool:
        bufs=list(pool.map(fetch,sorted(group.items())))
    physical_data=b"".join(bufs)
    local=Store()
    # Avoid distributed blank-node parsing collision from background load
    # chunks: serial source-preserving RDF load is an explicit strategy.
    local.load(input=physical_data,format=RdfFormat.N_TRIPLES)
    original_rows=solution_rows(local,row["query"])
    took=(time.perf_counter()-start)*1000
    return {"store":local,"wall_ms":took,"response_rows":len(original_rows[1]),
      "tcp_payload_bytes":len(physical_data),"shards":len(group)}

def bootstrap(rows,migration_ms):
    byfam=collections.defaultdict(list)
    for r in rows:byfam[r["family"]].append(r["saving_ms"])
    values=[statistics.mean(v) for v in byfam.values()]
    if len(values)<20:return {"valid":False,"reason":"insufficient_independent_query_families"}
    rng=random.Random(SEED)
    samples=sorted(sum(values[rng.randrange(len(values))] for _ in values)*REPS-migration_ms
          for __ in range(2000))
    return {"n_independent_families":len(values),
       "net_savings_ms":round(sum(x["saving_ms"] for x in rows)-migration_ms,4),
       "family_bootstrap_CI95_net_savings_ms":[round(samples[49],4),round(samples[1949],4)]}

def main():
    start=time.perf_counter()
    raw,roles,by_pred,sizes,cap,packs,loads,route=prepare()
    candidate,selection=swap.select_first_under_same_budget(route,sizes,loads,cap,
          [{"pattern":r["pattern"]} for r in roles["training"]+roles["calibration"]])
    assert selection["selected_move_bytes"]<=BUDGET
    static=Store()
    static.load(input=raw,format=RdfFormat.N_TRIPLES)
    assert len(static)>0
    frag={p for p in route if len(route[p])>1}
    frozen_decision={"source_sha256":SOURCE_SHA,
      "role_membership_hash_by_role":{k:hashlib.sha256(
          "\n".join(sorted(r["hash"] for r in v)).encode()).hexdigest()
            for k,v in roles.items()},
      "n_query_families_by_role":{k:len(v) for k,v in roles.items()},
      "selected_pretest_one_swap":candidate,
      "observed_only_metadata":selection,"truth_test_not_accessed":True}
    OUT.joinpath("decision_sealed_before_test.json").write_text(
       json.dumps(frozen_decision,indent=2))
    truth={};nonempty=0
    # Central complete-original result evaluation is only after action sealed.
    for r in roles["test"]:
        vars_,solutions=solution_rows(static,r["query"])
        nonempty+=int(len(solutions)>0)
        truth[r["hash"]]=len(solutions)
    assert nonempty>=5
    oldports,oldworkers=workers.start_group(packs)
    result={"schema":"candidate3-fresh-NYT-real-RDF-4worker-full-SPARQL-economics-v1",
       "source_sha256":SOURCE_SHA,"source_triples":len(static),
       "query_origin":"SYNTHETIC_FROM_UNSEEN_REAL_NYT_GRAPH_NOT_REAL_ORGANIC_LOG",
       "role_counts":frozen_decision["n_query_families_by_role"],
       "heldout_central_nonempty":nonempty,
       "storage_cap_per_worker_original_raw_bytes":cap,
       "original_raw_shard_loads":loads,
       "frozen_decision":frozen_decision,
       "methods":{}}
    try:
        for method in ("no_move","one_swap"):
            if method=="no_move":
                newports=oldports;newworkers=[]
                newroute=route
                migration={"moved_bytes":0,"wall_clock_migration_and_index_update_ms":0}
            else:
                newports,newworkers=workers.start_group(packs)
                plan={"swaps":[candidate] if candidate else [],
                     "replicate":None,"planned_bytes":selection["selected_move_bytes"]}
                newroute,migration=core.physically_apply(plan,by_pred,route,
                            loads,sizes,cap,newports)
            errors=[];records=[]
            rng=random.Random(SEED)
            cache={}
            try:
                for r in roles["test"]:
                    for repetition in range(REPS):
                        try:
                            if rng.randrange(2):
                                baseline=run_query(oldports,route,r,frag)
                                action=run_query(newports,newroute,r,frag)
                            else:
                                action=run_query(newports,newroute,r,frag)
                                baseline=run_query(oldports,route,r,frag)
                            bo=certify(static,baseline["store"],r["query"],cache)
                            ao=certify(static,action["store"],r["query"],cache)
                            # Both original SELECT responses MUST be provably
                            # legal; a legal but different LIMIT row is okay.
                            if bo["status"]!="PASS" or ao["status"]!="PASS":
                                errors.append({"hash":r["hash"],"repeat":repetition,
                                   "baseline":bo,"alternative":ao})
                            records.append({"family":json.dumps(r["pattern"]),
                                "repeat":repetition,
                                "original_response_both_legal":bo["status"]=="PASS" and ao["status"]=="PASS",
                                "saving_ms":baseline["wall_ms"]-action["wall_ms"],
                                "baseline_ms":baseline["wall_ms"],"action_ms":action["wall_ms"],
                                "shards_saved":baseline["shards"]-action["shards"],
                                "physical_bytes_saved":baseline["tcp_payload_bytes"]-action["tcp_payload_bytes"]})
                        except Exception as e:
                            errors.append({"hash":r["hash"],"repeat":repetition,
                                "type":type(e).__name__,"error":str(e)[:190]})
                exact=len(records)==len(roles["test"])*REPS and not errors
                delta=bootstrap(records,migration["wall_clock_migration_and_index_update_ms"]) if exact else None
                old95=sorted(r["baseline_ms"] for r in records)[math.ceil(.95*len(records))-1] if records else None
                new95=sorted(r["action_ms"] for r in records)[math.ceil(.95*len(records))-1] if records else None
                result["methods"][method]={"migration":migration,
                  "n_heldout_query_repetitions":len(records),
                  "original_SELECT_semantics_PASS_all":exact,
                  "nonpassing":errors[:20],
                  "summed_TCP_bytes_saved":sum(x["physical_bytes_saved"] for x in records),
                  "summed_shard_contacts_saved":sum(x["shards_saved"] for x in records),
                  "end_to_end_baseline_p95_ms":round(old95,4) if old95 else None,
                  "end_to_end_alternative_p95_ms":round(new95,4) if new95 else None,
                  "p95_within_1pct":(new95<=old95*1.01) if old95 else None,
                  "net_economic":delta,
                  "paper_GO":False}
                print("NYT_PHYSICAL_ACTION",method,json.dumps({
                  k:v for k,v in result["methods"][method].items()
                        if k not in ("migration","nonpassing")}),flush=True)
            finally:
                if newworkers:workers.stop_group(newworkers)
    finally:workers.stop_group(oldworkers)
    result["total_elapsed_seconds"]=round(time.perf_counter()-start,2)
    result["paper_REAL_ORGANIC_TIME_SERIES_GO"]=False
    result["faithful_published_partition_baseline_MATCHED_GO"]=False
    result["limitations"]=[
       "Real original NYT complete RDF graph never inspected in prior candidate3 runs; query workload synthetic from its own subject-predicate co-occurrences",
       "Original fivefold cross-family assignment frozen before any unseen test query execution",
       "Full source exact graph retained; no arbitrary RDF triple sample or query-result selection",
       "Only static vs a frozen single migration; not comprehensive prior-art superiority or four-machine network benchmark",
       "All worker TCP services share one hosted VM; coordinator fetches predicate payloads, not distributed native joins",
       "No genuinely novel real-user SPARQL log or chronology, and no contemporaneously aligned user queries",
       "No author-original WISE/WASP/DIAERESIS matched-policy end-to-end comparison on NYT",
       "We cannot claim paper novelty or production economic superiority even if this engineering regression passes"]
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    summary=dict(result)
    summary["methods"]={k:{kk:vv for kk,vv in v.items() if kk!="nonpassing"}|
       {"n_failed":len(v["nonpassing"])} for k,v in result["methods"].items()}
    print("NYT_FULL_REAL_E2E_START");print(json.dumps(summary,indent=2))
    print("NYT_FULL_REAL_E2E_END")
if __name__=="__main__":main()
