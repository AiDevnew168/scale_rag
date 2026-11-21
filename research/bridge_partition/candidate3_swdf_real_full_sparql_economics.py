#!/usr/bin/env python3
"""Real 4-shard distributed Oxigraph on unseen original FEASIBLE SWDF RDF+SPARQL.

Original graph: complete DICE FEASIBLE 'swdf.nt' 61MB, pinned SHA; 57MB
query logs, rdflib algebra filtered and 34 family-disjoint heldout groups.
Every original SELECT is run unmodified, comparing complete response multiset
against a centralized full-RDF Oxigraph store. Four independent live TCP
shard workers each execute real predicate CONSTRUCT queries; coordinator
performs the original query on the gathered fragments. Four arrangements:
no-move, one_swap, one_replica, swap_then_replica, greedy_two_swap.
All changes constrained by identical 4-shard byte limits and 25MB maximum
payload. Real physical edits are applied, migration time measured.
Only training+calibration may choose actions; test family labels remain sealed
until action policy locked. This is localhost, not a native federated join
optimizer. WISE/WASP full implementations not available and not claimed.
"""
import collections, hashlib, io, json, math, multiprocessing as mp, random
import statistics, time, zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pyoxigraph import Store,RdfFormat
import candidate3_swdf_locked_audit as sd
import candidate3_real_sparql_shards as engine
import candidate3_paired_full_sparql as paired
import candidate3_official_watdiv_byte_transfer as wd
import candidate3_byte_matched_replication as replica
import candidate3_ptcr_watdiv_byte_stress as ptcr

OUT=Path("results_candidate3_swdf_real_federated")
OUT.mkdir(exist_ok=True)
BUDGET=25_000_000
CAP_SLACK=1.10
TEST_REPEAT=2
MAX_TEST=102
MAX_CALIB=40
BOOT=2000
SEED=20261121

def prepare_source():
    graphpath=sd.downloaded()
    with zipfile.ZipFile(graphpath) as z:
        assert z.namelist()==["swdf.nt"]
        graph=z.read("swdf.nt")
    assert hashlib.sha256(graph).hexdigest()=="97575d036db4e55fa89f25231d3afb2c427555bce4a60fc429f902ddf7c45400"
    queryraw=sd.get_queries()
    assert hashlib.sha256(queryraw).hexdigest()=="7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3"
    allrecs,_=sd.parse_records(queryraw)
    by_pred=collections.defaultdict(list);size=collections.Counter()
    for line in graph.splitlines(keepends=True):
        if not line.strip():continue
        p=line.split(None,2)[1].decode()
        by_pred[p].append(line);size[p]+=len(line)
    rows=[r for r in allrecs if all("<"+p+">" in size for p in r["predicates"])]
    unique={}
    for r in rows:unique.setdefault(r["text_sha256"],r)
    patterns=sorted({r["predicates"] for r in unique.values()})
    order=sorted(patterns,key=lambda p:hashlib.sha256(
      ("candidate3-swdf-prelocked-v1:"+str(SEED)+":"+json.dumps(p)).encode()).hexdigest())
    folds={p:i%5 for i,p in enumerate(order)}
    role={"training":[],"calibration":[],"holdout":[]}
    for r in unique.values():
        k=folds[r["predicates"]]
        target="holdout" if k==0 else ("calibration" if k==1 else "training")
        role[target].append({"query":r["query"],"text_hash":r["text_sha256"],
          "pattern":tuple("<"+p+">" for p in r["predicates"]),
          "family":r["predicates"]})
    for v in role.values():v.sort(key=lambda r:r["text_hash"])
    assert {r["text_hash"] for r in role["training"]+role["calibration"]}.isdisjoint(
      {r["text_hash"] for r in role["holdout"]})
    assert len(role["holdout"])==102 and len({r["family"] for r in role["holdout"]})==34
    total=sum(size.values())
    cap=math.ceil(total*CAP_SLACK/4)
    packs,loads,route=engine.payloads_by_shard(by_pred,size,cap)
    assert len(packs)==4 and max(loads)<=cap
    return graph,by_pred,size,role,packs,loads,route,cap

def choose_plans(train,calib,route,loads,sizes,cap):
    # For both unchanged byte cap and max payload, all decisions are prior-only.
    action={}
    pair,meta=ptcr.select_first_under_same_budget(route,sizes,loads,cap,calib)
    one,load1,cost1=ptcr.move(route,loads,sizes,pair,cap)
    assert cost1<=BUDGET
    action["no_move"]={"swaps":[],"replicate":None,"planned_bytes":0}
    action["one_swap"]={"swaps":[pair] if pair else [],"replicate":None,
                        "planned_bytes":cost1}
    # A greedy second move with a *total* <=25MB cap.
    decisions,detail=ptcr.choose(route,one,load1,sizes,cap,calib,train,cost1)
    selected=decisions["two_swap_day0_greedy"]["second_swap"]
    action["two_swap_greedy"]={"swaps":[p for p in (pair,selected) if p],
       "replicate":None,
       "planned_bytes":cost1+sum(sizes[p] for p in selected) if selected else cost1}
    fragmented={p for p in route if len(route[p])>1}
    rep,_,repd=replica.choose_replica(
       route,route,sizes,loads,cap,0,calib,train,fragmented,objective="all")
    action["replica_only"]={"swaps":[],"replicate":repd["replica"],
       "planned_bytes":repd["extra_bytes"]}
    hyb,_,hybd=replica.choose_replica(one,route,sizes,load1,cap,cost1,
         calib,train,fragmented,objective="all")
    action["swap_replica"]={"swaps":[pair] if pair else [],
        "replicate":hybd["replica"],"planned_bytes":cost1+hybd["extra_bytes"]}
    for x in action.values():assert x["planned_bytes"]<=BUDGET
    return action,{"first_decision":pair,"first_meta":meta,
        "two_swap_eligible":detail,"fragmented_predicates":len(fragmented)}

def physically_apply(plan,by_pred,route,loads,sizes,cap,ports):
    current={p:set(v) for p,v in route.items()}
    newloads=list(loads);records=[];total=0
    tick=time.perf_counter()
    for pair in plan["swaps"]:
        assert pair is not None
        new,meta=engine.transfer_pair(pair,by_pred,current,ports)
        current=new
        size=sum(sizes[p] for p in pair)
        total+=size;records.append({"type":"balanced_predicate_swap",
                    "predicates":pair,"metadata":meta,"payload_bytes":size})
        newloads0=ptcr.move({p:set(v) for p,v in current.items()},newloads,
                         sizes,None,cap)[1] # physical counts updated separately
        del newloads0
        # Track load deltas using original endpoints after swap.
        # Initial old src locations for pair are recoverable from updated 'current'.
        a,b=pair
        dst_a=next(iter(current[a]));dst_b=next(iter(current[b]))
        old_a=dst_b;old_b=dst_a
        newloads[old_a]+=sizes[b]-sizes[a]
        newloads[old_b]+=sizes[a]-sizes[b]
        assert max(newloads)<=cap and min(newloads)>=0
    if plan["replicate"] is not None:
        p,target=plan["replicate"]
        assert len(current[p])==1 and target not in current[p]
        raw=b"".join(by_pred[p])
        res,ms=engine.call(ports[target],"/insert",raw,{"X-Predicate":p},timeout=120)
        ack=json.loads(res)
        assert ack["sha256"]==hashlib.sha256(raw).hexdigest()
        current[p].add(target);newloads[target]+=sizes[p]
        total+=sizes[p]
        records.append({"type":"selective_replica","predicate":p,
             "target_shard":target,"payload_bytes":sizes[p],
             "store_index_update_ms":round(ms,4)})
        assert max(newloads)<=cap
    assert total==plan["planned_bytes"]
    return current,{"moved_bytes":total,
       "wall_clock_migration_and_index_update_ms":round((time.perf_counter()-tick)*1000,4),
       "post_shard_bytes":newloads,"operations":records,
       "queries_stopped_during_move":True}

def shards_for_query(pattern,locations,frag):
    mandatory=set()
    for p in pattern:
        if p in frag:mandatory.update(locations[p])
    best=None
    for mask in range(1,16):
        chosen={i for i in range(4) if mask&(1<<i)}
        if not mandatory.issubset(chosen):continue
        if all(chosen & locations[p] for p in pattern):
            ranking=(len(chosen),mask)
            if best is None or ranking<best[0]:
                best=(ranking,chosen)
    if best is None:raise ValueError("Cannot route all predicates")
    chosen=best[1]
    groups=collections.defaultdict(list)
    for p in pattern:
        if p in frag:
            for i in sorted(locations[p]):groups[i].append(p)
        else:
            j=min(chosen & locations[p]);groups[j].append(p)
    return groups

def query_four_workers(query,pattern,loc,ports,frag):
    groups=shards_for_query(pattern,loc,frag)
    total_start=time.perf_counter()
    def fetch(entry):
        j,ps=entry
        body=json.dumps({"predicates":sorted(ps)}).encode()
        raw,lat=engine.call(ports[j],"/construct",body,
             {"Content-Type":"application/json"},timeout=120)
        return j,raw,lat
    with ThreadPoolExecutor(max_workers=4) as pool:
        answers=list(pool.map(fetch,sorted(groups.items())))
    network_ms=(time.perf_counter()-total_start)*1000
    data=b"".join(raw for _,raw,_ in answers)
    temp=Store()
    temp.bulk_load(input=data,format=RdfFormat.N_TRIPLES)
    answer=engine.evaluate(temp,query)
    return {"answer":answer,
      "wall_ms":round((time.perf_counter()-total_start)*1000,4),
      "fetch_ms":round(network_ms,4),
      "network_bytes":len(data),
      "shard_contacts":len(answers)}

def quantiles(rows):
    a=sorted(rows)
    if not a:return None
    return {"mean_ms":round(statistics.mean(a),4),
      "p50_ms":round(statistics.median(a),4),
      "p95_ms":round(a[math.ceil(.95*len(a))-1],4),
      "p99_ms":round(a[math.ceil(.99*len(a))-1],4)}

def cost_ci(observations,migration_ms):
    # Resample *families*, never repeated observations as independent.
    by_fam=collections.defaultdict(list)
    for row in observations:
        by_fam[row["family"]].append(row["saved_ms"])
    blocks=[sum(v)/TEST_REPEAT for v in by_fam.values()]
    assert len(blocks)>0
    rng=random.Random(SEED)
    sims=sorted(sum(blocks[rng.randrange(len(blocks))] for _ in blocks)-migration_ms
                for __ in range(BOOT))
    return {"n_independent_families":len(blocks),
        "net_ms_point":round(sum(blocks)-migration_ms,4),
        "net_ms_CI95":[round(sims[49],4),round(sims[1949],4)]}

def main():
    started=time.perf_counter()
    graph,by_pred,sizes,role,packs,loads,route,cap=prepare_source()
    plans,choice=choose_plans(role["training"],role["calibration"],
                 route,loads,sizes,cap)
    # Decisions frozen BEFORE the first test query or correctness response.
    OUT.joinpath("frozen_actions.json").write_text(json.dumps(
        {"plans":plans,"source_graph_sha":sd.GRAPH_SHA,
          "heldout_query_count":len(role["holdout"]),
          "heldout_unique_families":len({x["family"] for x in role["holdout"]}),
          "move_budget":BUDGET,"shard_cap":cap},indent=2))
    reference=Store()
    reference.bulk_load(input=graph,format=RdfFormat.N_TRIPLES)
    central_size=len(reference)
    del graph
    truth={};central_fail={}
    for r in role["holdout"]:
        try:truth[r["text_hash"]]=engine.evaluate(reference,r["query"])
        except Exception as ex:
            central_fail[r["text_hash"]]=type(ex).__name__+": "+str(ex)[:180]
    nonempty=sum(x["count"]>0 for x in truth.values())
    allresults={}
    fragmented={p for p in route if len(route[p])>1}
    base_ports,base_processes=paired.start_group(packs)
    try:
        for name,plan in plans.items():
            if name=="no_move":continue
            ports,workers=paired.start_group(packs)
            try:
                newloc,migration=physically_apply(plan,by_pred,route,loads,
                    sizes,cap,ports)
                rows=[];bad=[]
                ordered=role["holdout"]
                rng=random.Random(SEED+len(name))
                for i,r in enumerate(ordered):
                    h=r["text_hash"]
                    if h in central_fail:continue
                    for rep in range(TEST_REPEAT):
                        try:
                            if rng.randrange(2):
                                b=query_four_workers(r["query"],r["pattern"],route,base_ports,fragmented)
                                a=query_four_workers(r["query"],r["pattern"],newloc,ports,fragmented)
                            else:
                                a=query_four_workers(r["query"],r["pattern"],newloc,ports,fragmented)
                                b=query_four_workers(r["query"],r["pattern"],route,base_ports,fragmented)
                            if a["answer"]!=truth[h] or b["answer"]!=truth[h]:
                                raise AssertionError("Central-vs-distributed complete multiset mismatch")
                            rows.append({"family":json.dumps(r["family"]),
                                "query_sha256":h,
                                "saved_ms":b["wall_ms"]-a["wall_ms"],
                                "baseline_ms":b["wall_ms"],"action_ms":a["wall_ms"],
                                "baseline_bytes":b["network_bytes"],
                                "action_bytes":a["network_bytes"],
                                "baseline_shards":b["shard_contacts"],
                                "action_shards":a["shard_contacts"]})
                        except Exception as e:
                            bad.append({"query_sha256":h,"error":type(e).__name__+": "+str(e)[:250]})
                complete=(len(rows)==len(truth)*TEST_REPEAT and not bad)
                allresults[name]={"migration":migration,
                    "n_correct_paired_executions":len(rows),
                    "n_failed_query_execution":len(bad),
                    "error_examples":bad[:12],
                    "all_eligible_heldout_answers_exact":complete and not central_fail,
                    "timing":{"static":quantiles([x["baseline_ms"] for x in rows]),
                              "action":quantiles([x["action_ms"] for x in rows])},
                    "total_network_bytes_saved":sum(
                         x["baseline_bytes"]-x["action_bytes"] for x in rows),
                    "total_shard_contacts_saved":sum(
                         x["baseline_shards"]-x["action_shards"] for x in rows),
                    "paired_net_economic_ci":cost_ci(rows,migration["wall_clock_migration_and_index_update_ms"]) if rows else None,
                    "timed_query_count":len(rows)//TEST_REPEAT}
                print("METHOD_DONE",name,json.dumps({k:v for k,v in allresults[name].items() if k!="error_examples"}),flush=True)
            finally:paired.shutdown(workers)
    finally:paired.shutdown(base_processes)
    report={"schema":"candidate3-original-SWDF-end2end-four-shard-SPARQL-economic-v1",
     "source_graph_sha256":sd.GRAPH_SHA,
     "source_query_sha256":"7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3",
     "physical_dataset_RDF_triples":central_size,
     "shard_raw_bytes_initial":loads,
     "shard_per_worker_raw_byte_limit":cap,
     "migration_max_raw_bytes_per_action":BUDGET,
     "frozen_train_calibration_only_decision":choice,
     "candidate_actions":plans,
     "n_heldout_exact_disjoint_texts":len(role["holdout"]),
     "n_heldout_predicate_families":len({x["family"] for x in role["holdout"]}),
     "n_nonempty_central_answers":nonempty,
     "central_query_errors":len(central_fail),
     "central_error_examples":list(central_fail.items())[:10],
     "method_results":allresults,
     "elapsed_sec":round(time.perf_counter()-started,2),
     "confirmed_paper_Go":False,
     "known_limitations":[
      "Actual complete SWDF graph from DICE FEASIBLE and actual (cleaned) real query-log source, but recording-era graph version alignment not confirmed.",
      "Real 4 independent TCP Oxigraph workers per action; all four workers on the same GitHub Actions VM, NOT cross-host network.",
      "The coordinator eagerly fetches complete predicate fragments then runs unmodified SPARQL SELECT; NOT optimized distributed joins.",
      "Cache warmup and host scheduling variance may affect paired timing; test order randomly interleaved per query.",
      "No online queries during moves and no crash-safe distributed transaction; migration recovery not proven.",
      "No distinct real-user chronological request times; holdout strictly predicate-family-disjoint but source lacks time stamps.",
      "Physical raw RDF payload bytes and Oxigraph index update elapsed times measured; not all production infrastructure/storage costs.",
      "All recorded failed/empty query outcomes included in denominator; if below min nonempty, no confirmatory statistical claim.",
      "No faithful runnable WISE/WASP/MTGA source comparison available on same coordinator and storage semantics.",
      "No cash dollar financial savings, cross-host throughput or prospective natural workload drift guarantee."]
    }
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("REAL_SWDF_FULL_E2E_START",flush=True)
    print(json.dumps({k:v for k,v in report.items() if k!="method_results"}|
       {"method_results":{name:{k:v for k,v in val.items() if k!="error_examples"}
           for name,val in allresults.items()}},indent=2),flush=True)
    print("REAL_SWDF_FULL_E2E_END",flush=True)
if __name__=="__main__":main()
