#!/usr/bin/env python3
"""Original dated 176-day SWDF four-worker physical economic test.

SOURCE/SCIENTIFIC LOCK:
- Frozen raw log SHA and pretest sampling protocol, see
  CANDIDATE3_LOCKED_DATED_SWDF_PHYSICAL_SAMPLING_ADDENDUM_2026_11_21.md
- 88 train days, next 17 action construction, 18 separate calibration,
  final 53 chronologically heldout test days (no test QUERY ENGINE answers or
  time measured until frozen decision artifact written).
- 12 deterministic source-eligible original query *occurrences* per UTC day.
- Four real indexed Oxigraph worker processes with localhost TCP original RDF
  fragments + complete unchanged original original SPARQL SELECT and strict
  independently authored semantic certifier. Candidate action costs physically
  measured under strict 25MB and 1.1x byte cap.
- No dynamic-adjustment or retuning after seeing heldout test outputs.
- This is historical observational **exploratory** engineering, NOT a new
  totally independent unseen-SWDF domain (cleaned SWDF had been used before),
  NOT verified as-of-2014 graph snapshot, and NOT a Spark/DIAERESIS equal
  architecture competitor nor cross-host proof.
"""
import collections,datetime,gzip,hashlib,heapq,json,math,random,statistics,time,zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pyoxigraph import Store,RdfFormat
import candidate3_feasible_raw_swdf_dated_source as raw
import candidate3_feasible_raw_swdf_strict_temporal as strict
import candidate3_swdf_locked_audit as graphsource
import candidate3_real_sparql_shards as network
import candidate3_source_identity_worker as worker
import candidate3_swdf_real_full_sparql_economics as planner
import candidate3_nyt_full_real_e2e as queries
from candidate3_sparql_semantic_certifier import certify

OUT=Path("results_candidate3_SWDF_176day_physical_economics")
OUT.mkdir(exist_ok=True)
SOURCE_SHA="2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df"
GRAPH_SHA="65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb"
SEED=20261121
PER_DAY=12
N_REPEATS=2
ACTIONS=("no_move","one_swap","two_swap_greedy","replica_only","swap_replica")
MAX_BYTES=25_000_000
MAX_QUERY_MS=80_000
MAX_OUTPUT_BYTES=5_000_000
TEST_ERRORS_TO_KEEP=15

def load_real_source():
    gp=graphsource.downloaded()
    assert raw.sha_file(gp)==GRAPH_SHA
    with zipfile.ZipFile(gp) as z:source=z.read("swdf.nt")
    normalized=[]
    for line in source.splitlines(keepends=True):
        if not line.strip():continue
        try:line.decode("utf8")
        except UnicodeDecodeError:line=line.decode("latin1").encode("utf8")
        normalized.append(line)
    graph=b"".join(normalized)
    bypred=collections.defaultdict(list);weights=collections.Counter()
    for line in normalized:
        parts=line.split(None,2)
        assert len(parts)==3 and parts[1].startswith(b"<")
        pred=parts[1].decode("utf8")
        bypred[pred].append(line)
        weights[pred]+=len(line)
    assert sum(weights.values())==len(graph)
    cap=math.ceil(len(graph)*1.10/4)
    packs,loads,route=network.payloads_by_shard(bypred,weights,cap)
    assert len(route)>=10 and max(loads)<=cap
    return graph,bypred,weights,packs,loads,route,cap

def date_of_request(m):
    try:
        d=datetime.datetime.strptime(m.group(1),"%d/%b/%Y:%H:%M:%S %z")
        return d.astimezone(datetime.timezone.utc).date().isoformat()
    except ValueError:return None

def get_dated_sample(sourcepath,predicates):
    # Full date inventory first, independent of eligible query complexity.
    days=set()
    with gzip.open(sourcepath,"rb") as f:
        for line in f:
            m=raw.APACHE.search(line.decode("utf8",errors="replace"))
            if m:
                d=date_of_request(m)
                if d:days.add(d)
    days=sorted(days)
    assert len(days)==176
    train=set(days[:88]);construct=set(days[88:105])
    calibration=set(days[105:123]);test=set(days[123:])
    assert (len(train),len(construct),len(calibration),len(test))==(88,17,18,53)
    which={d:("train" if d in train else "construction" if d in construct
        else "calibration" if d in calibration else "test") for d in days}
    parse_cache={}
    reservoir=collections.defaultdict(list)
    counts=collections.Counter()
    exclude=collections.Counter()
    seen_exact=collections.defaultdict(set)
    seen_family=collections.defaultdict(set)
    original_selects=0
    with gzip.open(sourcepath,"rb") as f:
        for ordinal,line in enumerate(f):
            m=raw.APACHE.search(line.decode("utf8",errors="replace"))
            if not m or m.group(2).upper()!="GET":continue
            day=date_of_request(m)
            if day is None:continue
            q=raw.parse_query(m.group(3))
            if q is None:continue
            if "SELECT" not in q.upper():continue
            original_selects+=1
            h=hashlib.sha256(q.encode()).hexdigest()
            if h not in parse_cache:
                if len(q)>16000:
                    parse_cache[h]=(None,"over_16KB")
                else:
                    preds,err=strict.select_predicates(q)
                    if err is None and not all(x in predicates for x in preds):
                        preds,err=None,"predicate_absent_from_original_RDF"
                    parse_cache[h]=(preds,err)
            ps,err=parse_cache[h]
            if err is not None:
                exclude[err]+=1
                continue
            role=which[day]
            counts[day]+=1
            fkey=hashlib.sha256(json.dumps(ps).encode()).hexdigest()
            seen_exact[role].add(h);seen_family[role].add(fkey)
            key=hashlib.sha256(f"{SEED}:{day}:{ordinal}:{h}".encode()).digest()
            # Heap root is greatest selected key -> true fixed-size minimum.
            rank=-int.from_bytes(key,"big")
            row={"query":q,"pattern":tuple("<"+p+">" for p in ps),
                  "text_hash":h,"family":ps,"day":day,"ordinal":ordinal,
                  "priority_sha256":key.hex()}
            bucket=reservoir[day]
            if len(bucket)<PER_DAY:heapq.heappush(bucket,(rank,ordinal,row))
            elif rank>bucket[0][0]:
                heapq.heapreplace(bucket,(rank,ordinal,row))
    sampled={"train":[],"construction":[],"calibration":[],"test":[]}
    for day,items in reservoir.items():
        name=which[day]
        sampled[name].extend(row for _,_,row in sorted(items,key=lambda x:(x[0],x[1]),
               reverse=True))
    for name in sampled:
        sampled[name].sort(key=lambda r:(r["day"],r["priority_sha256"]))
    assert counts and len(sampled["test"])>=20
    summary={"source_raw_SHA256":SOURCE_SHA,
      "calendar_days":{"train":88,"construction":17,"calibration":18,"test":53},
      "observed_exact_eligible_occurrences_by_split":{
          label:sum(n for d,n in counts.items() if which[d]==label)
          for label in sampled},
      "sampled_original_query_occurrences_by_split":{k:len(v) for k,v in sampled.items()},
      "original_strict_eligible_unique_texts_by_split":{k:len(v) for k,v in seen_exact.items()},
      "observed_predicate_families_by_split":{k:len(v) for k,v in seen_family.items()},
      "future_test_new_exact_texts_vs_pretest":len(seen_exact["test"]-(seen_exact["train"]|
            seen_exact["construction"]|seen_exact["calibration"])),
      "future_test_new_families_vs_pretest":len(seen_family["test"]-(seen_family["train"]|
            seen_family["construction"]|seen_family["calibration"])),
      "n_UTC_days_with_eligible_query":len(counts),
      "true_inclusion_probability_per_day":{
          d:round(min(1,PER_DAY/n),6) for d,n in sorted(counts.items())},
      "SPARQL_parser_exclusions_counts":dict(exclude),
      "n_original_SELECT_lexical_seen":original_selects,
      "original_full_queries_exported_or_logged":False}
    return sampled,counts,summary

def safe_stage(original_rows,base_route,base_ports,alt_route,alt_ports,fragmented,
               central,original_truth_cache,nreps,seed,strict_stop):
    rng=random.Random(seed)
    series=[];error_detail=[];correct=0;nonempty=0;results=collections.Counter()
    for r in original_rows:
        for rep in range(nreps):
            try:
                if rng.randrange(2):
                    base=queries.run_query(base_ports,base_route,r,fragmented)
                    alt=queries.run_query(alt_ports,alt_route,r,fragmented)
                else:
                    alt=queries.run_query(alt_ports,alt_route,r,fragmented)
                    base=queries.run_query(base_ports,base_route,r,fragmented)
                b=certify(central,base["store"],r["query"],original_truth_cache)
                a=certify(central,alt["store"],r["query"],original_truth_cache)
                bstatus=b["status"];astatus=a["status"]
                results["base_"+bstatus]+=1;results["alt_"+astatus]+=1
                if bstatus!="PASS" or astatus!="PASS":
                    if len(error_detail)<TEST_ERRORS_TO_KEEP:
                        error_detail.append({"query_hash":r["text_hash"],"day":r["day"],
                            "base_status":bstatus,"alt_status":astatus,
                            "b_reason":b.get("reason","")[:110],
                            "a_reason":a.get("reason","")[:110]})
                    continue
                correct+=1
                nonempty+=base["response_rows"]>0
                series.append({"day":r["day"],"hash":r["text_hash"],
                    "saving_ms":base["wall_ms"]-alt["wall_ms"],
                    "baseline_ms":base["wall_ms"],"alternative_ms":alt["wall_ms"],
                    "traffic_TCP_RDF_bytes_saved":base["tcp_payload_bytes"]-alt["tcp_payload_bytes"],
                    "shard_contacts_saved":base["shards"]-alt["shards"]})
            except Exception as e:
                results["execution_exception"]+=1
                if len(error_detail)<TEST_ERRORS_TO_KEEP:
                    error_detail.append({"query_hash":r["text_hash"],"day":r["day"],
                        "reason":type(e).__name__+":"+str(e)[:155]})
        if strict_stop and (sum(v for k,v in results.items() if k not in ("base_PASS","alt_PASS")))>0:
            # Strict exploratory candidate: fail closed; don't keep querying
            # and selectively ignore invalid responses.
            break
    return {"n_requested":len(original_rows)*nreps,
       "n_semantically_correct_paired":correct,
       "n_central_nonempty_correct_paired":nonempty,
       "status_counts":dict(results),
       "source_error_examples":error_detail,
       "all_original_queries_semantically_valid":
          correct==len(original_rows)*nreps,
       "matched_correct_pair_sum_saved_ms":
          round(sum(x["saving_ms"] for x in series),5),
       "mean_ms_saved_per_correct_pair":
          round(statistics.mean(x["saving_ms"] for x in series),5) if series else None,
       "observed_RDF_payload_bytes_saved_correct_queries":
          sum(x["traffic_TCP_RDF_bytes_saved"] for x in series),
       "observed_contacts_saved_correct_queries":
          sum(x["shard_contacts_saved"] for x in series),
       "p50_baseline_correct_query_ms":
          round(statistics.median(x["baseline_ms"] for x in series),4) if series else None,
       "p50_alt_correct_query_ms":
          round(statistics.median(x["alternative_ms"] for x in series),4) if series else None,
       "paired_records":series}

def summarize_day_blocks(stage,counts,move_ms):
    data=stage["paired_records"]
    if not stage["all_original_queries_semantically_valid"]:
        return {"valid":False,"reason":"ORIGINAL_FULL_SPARQL_SEMANTIC_CORRECTNESS_FAIL"}
    if not data:return {"valid":False,"reason":"NO_VALID_QUERIES"}
    byday=collections.defaultdict(list)
    for r in data:byday[r["day"]].append(r["saving_ms"])
    # Day point-estimate is inverse inclusion-weighted; actual whole 53-day
    # full net was NOT measured; this is only a stratified sampled estimate.
    day_gain={d:statistics.mean(v)*counts[d] for d,v in byday.items()}
    actual_sampled=sum(x["saving_ms"] for x in data)-move_ms
    if len(day_gain)<14:
        return {"valid":False,"reason":"TOO_FEW_DISTINCT_CALENDAR_DAYS",
                "actual_sampled_total_net_ms":round(actual_sampled,4)}
    rng=random.Random(SEED)
    keys=sorted(day_gain)
    boot=[]
    for _ in range(2500):
        block=[keys[rng.randrange(len(keys))] for i in keys]
        boot.append(sum(day_gain[d] for d in block)-move_ms)
    boot.sort()
    return {"valid":True,
       "sampled_actual_realized_net_vs_static_ms":round(actual_sampled,4),
       "projected_unexecuted_original_full_period_net_point_ms":
          round(sum(day_gain.values())-move_ms,4),
       "day_cluster_bootstrap_95_projected_net_ms":
          [round(boot[62],4),round(boot[2437],4)],
       "calibration_day_bootstrap_is_not_proof_future_independent":True,
       "n_calendar_day_blocks":len(keys),
       "per_day_stratified_weights_documented":True}

def main():
    started=time.perf_counter()
    graph,bypred,weights,packs,loads,route,cap=load_real_source()
    rawpath=OUT/"SWDF.log.gz"
    dl=graphsource.gdown.download(id=raw.SOURCE_ID,output=str(rawpath),
        quiet=True,fuzzy=True)
    assert dl and rawpath.is_file()
    assert raw.sha_file(rawpath)==SOURCE_SHA
    requested,daycounts,source_audit=get_dated_sample(rawpath,
       {p[1:-1] for p in weights})
    assert source_audit["observed_exact_eligible_occurrences_by_split"]=={
        "train":4707,"construction":None,"calibration":None,"test":1441} or (
        source_audit["observed_exact_eligible_occurrences_by_split"]["train"]==4707
        and source_audit["observed_exact_eligible_occurrences_by_split"]["test"]==1441
        and source_audit["observed_exact_eligible_occurrences_by_split"]["construction"]+
           source_audit["observed_exact_eligible_occurrences_by_split"]["calibration"]==994)
    actions,construction_meta=planner.choose_plans(requested["train"],
        requested["construction"],route,loads,weights,cap)
    assert set(actions)==set(ACTIONS)
    assert all(plan["planned_bytes"]<=MAX_BYTES for plan in actions.values())
    source_audit["initial_four_shard_bytes"]=loads
    source_audit["per_worker_raw_byte_cap"]=cap
    source_audit["graph_original_full_normalized_SHA256"]=hashlib.sha256(graph).hexdigest()
    source_audit["graph_unique_source_predicates"]=len(weights)
    freeze={"schema":"candidate3-frozen-176day-original-SWDF-economics-v1",
       "date_split":"88_train + 17_construction + 18_calibration + 53_untouched_test",
       "source_sha256":SOURCE_SHA,
       "frozen_UTC_calendar_day_query_sample":PER_DAY,
       "training_and_action_construction_only_plans":actions,
       "selected_actual_action":"no_move",
       "why_selected":"Future full SPARQL critical-path reward L1 shift bound and full physical rollback cap are NOT independently certified. Conservative economic certificate therefore ABSTAINS.",
       "candidate_selection_observed_test_answers":False,
       "candidate_selection_observed_test_lagged_runtime":False,
       "source_eligibility_summary":source_audit}
    decision=OUT/"decision_frozen_before_test.json"
    decision.write_text(json.dumps(freeze,indent=2))
    decision_hash=hashlib.sha256(decision.read_bytes()).hexdigest()
    print("ORIGINAL_2014_SWDF_ACTIONS_FROZEN_BEFORE_TEST",decision_hash,flush=True)
    del rawpath
    central=Store()
    central.bulk_load(input=graph,format=RdfFormat.N_TRIPLES)
    del graph
    fragmented={p for p,locations in route.items() if len(locations)>1}
    original_ports,original_workers=worker.start_group(packs)
    result={}
    try:
        for name in ACTIONS:
            if name=="no_move":
                ports=original_ports;workers=[];newroute=route
                moved={"moved_bytes":0,"wall_clock_migration_and_index_update_ms":0}
            else:
                ports,workers=worker.start_group(packs)
                newroute,moved=planner.physically_apply(
                    actions[name],bypred,route,loads,weights,cap,ports)
            try:
                cal=safe_stage(requested["calibration"],route,original_ports,
                    newroute,ports,fragmented,central,{},N_REPEATS,
                    seed=SEED+97+len(name),strict_stop=False)
                test=safe_stage(requested["test"],route,original_ports,
                    newroute,ports,fragmented,central,{},N_REPEATS,
                    seed=SEED+901+len(name),strict_stop=False)
                economic=summarize_day_blocks(test,daycounts,
                    moved["wall_clock_migration_and_index_update_ms"])
                result[name]={"movement":moved,
                    "original_calibration":{k:v for k,v in cal.items() if k!="paired_records"},
                    "original_temporal_test":{k:v for k,v in test.items() if k!="paired_records"},
                    "economic":economic,
                    "full_query_correctness_gate":cal["all_original_queries_semantically_valid"]
                        and test["all_original_queries_semantically_valid"]}
                print("DATED_SWDF_PHYSICAL_POLICY",name,json.dumps({
                    "calibration_valid":cal["all_original_queries_semantically_valid"],
                    "test_valid":test["all_original_queries_semantically_valid"],
                    "n_heldout_semantic_pass":test["n_semantically_correct_paired"],
                    "n_heldout_requested":test["n_requested"],
                    "movement_bytes":moved["moved_bytes"],
                    "economic":economic}),flush=True)
            finally:
                if workers:worker.stop_group(workers)
    finally:worker.stop_group(original_workers)
    output={"schema":"candidate3-original-authentic-176day-four-process-semantic-economic-v1",
       "frozen_decision_SHA256_before_ANY_test_answer":decision_hash,
       "selected_real_policy":"no_move",
       "counterfactual_actions_evaluated_after_frozen_policy":list(result),
       "initial_training_source_audit":source_audit,
       "n_source_original_RDF_unique_central_triples":len(central),
       "methods":result,
       "elapsed_time_seconds":round(time.perf_counter()-started,2),
       "paper_confirmatory_positive_economic_GO":False,
       "no_Go_reasons":[
         "Related earlier FEASIBLE SWDF cleaned query source was already inspected, so this is NOT an untouched domain",
         "As-of-2014 SWDF RDF snapshot version alignment is NOT verified",
         "Policy real admission is no_move because a future full-runtime L1 drift upper limit is unknown",
         "Four independently indexed TCP Oxigraph workers on ONE runner, NOT true cross-host Spark/HDFS federation",
         "DIAERESIS/WISE/WASP original executable not benchmarked against same 176day query population and source model",
         "Counterfactual sampled net is NOT an executed full real-production request horizon or monetized dollars",
         "Bootstrap across days describes uncertainty conditional on day resampling; calendar days can be autocorrelated"]}
    OUT.joinpath("report.json").write_text(json.dumps(output,indent=2))
    summary={k:v for k,v in output.items() if k not in ("methods","initial_training_source_audit")}
    summary["methods"]={key:{"movement":v["movement"],"test":v["original_temporal_test"],
         "economic":v["economic"]} for key,v in result.items()}
    for method in summary["methods"].values():
        method["test"].pop("source_error_examples",None)
    print("DATED_176DAY_PHYSICAL_ECONOMIC_START",flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    print("DATED_176DAY_PHYSICAL_ECONOMIC_END",flush=True)
if __name__=="__main__":main()
