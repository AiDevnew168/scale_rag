#!/usr/bin/env python3
"""Pinned 48 original SWDF TRAIN texts, randomized balanced same-run 3-arm test.

Engineering falsification only. Last 53 historical heldout days are NEVER read.
All 432 timed original SELECT executions and 288 semantic certifications must
pass; incomplete results are FAIL-CLOSED, never censored or called positive.
"""
import collections, hashlib, json, math, os, random, statistics, time
from pathlib import Path

from pyoxigraph import Store,RdfFormat
from candidate3_sparql_semantic_certifier import solution_rows,certify
import candidate3_feasible_raw_swdf_dated_source as raw
import candidate3_swdf_176day_physical_economic as source
import candidate3_trainonly_selective_fetch_physical as first
import candidate3_trainonly_second24_selective_fetch_physical as second
import candidate3_source_identity_worker as worker

OUT=Path("results_candidate3_SWDF_train48_same_runner_three_arm")
OUT.mkdir(exist_ok=True)
SEED=20261123
METHODS=("central_indexed","full_fragment_ship","constant_pushdown")
REPEATS=3
N_TEXTS=48
FIRST_SHA="108a618ab725e291d05967c1d81e58a1c5e8365804f88f7602bbe7370f26e09c"
SECOND_SHA="3e2fd328952e2ddc1c0ea913af49db15bfe4f867a30d1a1db492ffb4e80eaed5"


def fingerprint(rows):
    return hashlib.sha256("|".join(x["hash"] for x in rows).encode()).hexdigest()


def balanced_orders(seed):
    a=list(METHODS)
    random.Random(seed).shuffle(a)
    return [a[i:]+a[:i] for i in range(REPEATS)]


def process_rss_kib(pid):
    try:
        for x in Path(f"/proc/{pid}/status").read_text().splitlines():
            if x.startswith("VmRSS:"): return int(x.split()[1])
    except (OSError,ValueError):pass
    return None


def process_cpu_ticks(pid):
    try:
        s=Path(f"/proc/{pid}/stat").read_text()
        a=s[s.rfind(")")+2:].split()
        return int(a[11])+int(a[12])
    except (OSError,ValueError,IndexError):return None


def aggregate(rows):
    if len(rows)!=N_TEXTS*REPEATS:raise ValueError("Incomplete rows")
    summary={}
    for arm in METHODS:
        a=sorted(r["elapsed_ms"][arm] for r in rows)
        summary[arm]={
           "mean_ms":round(statistics.mean(a),6),
           "median_ms":round(statistics.median(a),6),
           "sample_p95_ms":round(a[math.ceil(.95*len(a))-1],6),
           "sample_max_ms":round(a[-1],6),
           "RDF_tcp_response_payload_bytes":sum(
               r["rdf_payload_bytes"][arm] for r in rows)}
    for arm in ("full_fragment_ship","constant_pushdown"):
        penalties=[r["elapsed_ms"][arm]-r["elapsed_ms"]["central_indexed"] for r in rows]
        summary[arm]["mean_penalty_relative_to_direct_indexed_central_ms"]=round(
            statistics.mean(penalties),6)
        summary[arm]["n_blocks_slower_than_direct_central"]=sum(x>0 for x in penalties)
    savings=[r["elapsed_ms"]["full_fragment_ship"]-
             r["elapsed_ms"]["constant_pushdown"] for r in rows]
    summary["mean_full_to_selective_saved_ms"]=round(statistics.mean(savings),6)
    return summary


def cluster_sensitivity(rows):
    bytext=collections.defaultdict(list)
    for r in rows:bytext[r["text_sha256"]].append(r)
    if len(bytext)!=N_TEXTS or any(len(v)!=REPEATS for v in bytext.values()):
        raise ValueError("Text cluster coverage drift")
    items=[]
    for h,obs in bytext.items():
        d=statistics.mean(x["elapsed_ms"]["constant_pushdown"]-
            x["elapsed_ms"]["central_indexed"] for x in obs)
        items.append({"hash":h,"family":obs[0]["family_sha256"],
                      "mean_pushdown_penalty_vs_central_ms":d})
    families=collections.defaultdict(list)
    for x in items:families[x["family"]].append(x)
    rng=random.Random(SEED)
    sample1=[]
    for _ in range(3000):
        sample1.append(statistics.mean(
            items[rng.randrange(len(items))]["mean_pushdown_penalty_vs_central_ms"]
            for _ in items))
    sample1.sort()
    sample2=[]
    keys=list(families)
    if len(keys)>=4:
        for _ in range(3000):
            selected=[keys[rng.randrange(len(keys))] for _ in keys]
            vals=[x["mean_pushdown_penalty_vs_central_ms"]
                  for k in selected for x in families[k]]
            sample2.append(statistics.mean(vals))
        sample2.sort()
    return {
       "n_unique_text_clusters":len(items),
       "n_distinct_predicate_families":len(families),
       "family_text_counts_descending":sorted((len(v) for v in families.values()),reverse=True),
       "n_texts_where_central_beats_selective":sum(x["mean_pushdown_penalty_vs_central_ms"]>0 for x in items),
       "n_predicate_families_where_central_beats_selective_mean":sum(
           statistics.mean(v["mean_pushdown_penalty_vs_central_ms"] for v in group)>0
           for group in families.values()),
       "query_cluster_resampling_2p5_97p5_ms_descriptive":[
           round(sample1[75],6),round(sample1[2924],6)],
       "predicate_family_resampling_2p5_97p5_ms_descriptive":
           [round(sample2[75],6),round(sample2[2924],6)] if sample2 else None,
       "resampling_not_prospective_confidence_interval":True}


def main():
    started=time.perf_counter()
    graph,bypred,weights,packs,loads,route,cap=source.load_real_source()
    rawlog=OUT/"SWDF.log.gz"
    got=source.graphsource.gdown.download(id=raw.SOURCE_ID,
                      output=str(rawlog),quiet=True,fuzzy=True)
    if not got or not rawlog.is_file() or raw.sha_file(rawlog)!=source.SOURCE_SHA:
        raise RuntimeError("Original source log failed immutable SHA")
    allowed={p[1:-1] for p in weights}
    cohort_a,_=first.choose_train_only(rawlog,allowed)
    cohort_b,_=second.choose_train_only(rawlog,allowed)
    chosen=cohort_a+cohort_b
    if (len(chosen)!=N_TEXTS or fingerprint(cohort_a)!=FIRST_SHA or
        fingerprint(cohort_b)!=SECOND_SHA or
        len(set(x["hash"] for x in chosen))!=N_TEXTS):
        raise RuntimeError("Frozen original 48-text cohort has drifted")
    order=list(range(N_TEXTS))
    random.Random(SEED).shuffle(order)
    frozen={"schema":"candidate3-frozen-SWDF-48train-text-three-arm-same-run-v1",
      "log_sha256":source.SOURCE_SHA,"graph_zip_sha256":source.GRAPH_SHA,
      "cohort_one_hash":FIRST_SHA,"cohort_two_hash":SECOND_SHA,
      "n_unique_original_training_texts":48,
      "repetitions_per_text":REPEATS,
      "three_methods":METHODS,
      "query_index_order":order,
      "method_order_seed":SEED,
      "method_order_rule":"3 cyclic permutations of seeded 3-arm order per text",
      "earlier_training_results_already_seen":True,
      "original_future_holdout_reused":False,
      "original_SOURCE_query_never_rewritten":True}
    (OUT/"protocol_frozen_before_new_same_run_answers.json").write_text(
        json.dumps(frozen,indent=2))
    print("SAME_RUN_TRAIN48_FROZEN",
        hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest(),flush=True)
    # Allocate/load both competitors on the SAME runner before timed requests.
    t=time.perf_counter()
    central=Store()
    central.load(input=graph,format=RdfFormat.N_TRIPLES)
    central_build_ms=(time.perf_counter()-t)*1000
    del graph
    t=time.perf_counter()
    ports,workers=worker.start_group(packs)
    worker_start_ms=(time.perf_counter()-t)*1000
    before={p.pid:{"VmRSS_KiB":process_rss_kib(p.pid),
                   "cpu_ticks":process_cpu_ticks(p.pid)} for p in workers}
    fragmented={p for p,locations in route.items() if len(locations)>1}
    rows=[];errors=[]
    timing_start=time.perf_counter()
    try:
        for position,index in enumerate(order):
            selected=chosen[index]
            family=hashlib.sha256(json.dumps(
                sorted(selected["pattern"])).encode()).hexdigest()
            for rep,methods in enumerate(balanced_orders(SEED+position)):
                done={};failed=False
                for arm in methods:
                    try:
                        if arm=="central_indexed":
                            t=time.perf_counter()
                            columns,solutions=solution_rows(central,selected["query"])
                            done[arm]={"elapsed_ms":(time.perf_counter()-t)*1000,
                                       "bytes":0,"nrows":len(solutions),"store":central}
                        else:
                            mode="full" if arm=="full_fragment_ship" else "constant_pushdown"
                            result=first.request_one(ports,route,fragmented,selected,mode)
                            done[arm]={"elapsed_ms":result["wall_ms"],
                                       "bytes":result["ntriples_rdf_tcp_bytes"],
                                       "nrows":result["solution_rows"],
                                       "store":result["temp"]}
                    except Exception as exc:
                        errors.append({"kind":"PHYSICAL_EXECUTION_ERROR",
                            "text_sha256":selected["hash"],"repeat":rep,
                            "arm":arm,"exception_type":type(exc).__name__})
                        failed=True;break
                if failed:continue
                certified={}
                for arm in ("full_fragment_ship","constant_pushdown"):
                    certified[arm]=certify(central,done[arm]["store"],selected["query"])
                if any(x["status"]!="PASS" for x in certified.values()):
                    errors.append({"kind":"ORIGINAL_FULL_SPARQL_INVALID",
                        "text_sha256":selected["hash"],"repeat":rep,
                        "full_status":certified["full_fragment_ship"]["status"],
                        "selective_status":certified["constant_pushdown"]["status"]})
                if done["constant_pushdown"]["bytes"]>done["full_fragment_ship"]["bytes"]:
                    errors.append({"kind":"SELECTED_BYTES_EXCEED_FULL",
                        "text_sha256":selected["hash"],"repeat":rep})
                rows.append({
                  "text_sha256":selected["hash"],
                  "family_sha256":family,
                  "cohort":"ranks_1_24" if index<24 else "ranks_25_48",
                  "query_order":position,
                  "repeat":rep,
                  "method_order":methods,
                  "elapsed_ms":{a:round(done[a]["elapsed_ms"],6) for a in METHODS},
                  "rdf_payload_bytes":{a:done[a]["bytes"] for a in METHODS},
                  "solution_counts":{a:done[a]["nrows"] for a in METHODS},
                  "status":{a:certified[a]["status"]
                            for a in ("full_fragment_ship","constant_pushdown")}})
            if (position+1)%8==0:
                print("SAME_RUN_TRAIN48_PROGRESS",position+1,"of",N_TEXTS,
                      "errors",len(errors),flush=True)
    finally:
        after={p.pid:{"VmRSS_KiB":process_rss_kib(p.pid),
                      "cpu_ticks":process_cpu_ticks(p.pid)} for p in workers}
        worker.stop_group(workers)
    valid=len(rows)==N_TEXTS*REPEATS and not errors
    if len(rows)!=N_TEXTS*REPEATS:
        errors.append({"kind":"MISSING_FROZEN_REQUEST_BLOCKS",
            "requested":N_TEXTS*REPEATS,"recorded":len(rows)})
    output={
      "schema":"candidate3-SWDF-48text-same-run-3arm-strong-central-baseline-v1",
      "frozen":frozen,
      "original_central_indexed_graph_triples":len(central),
      "real_workers_four_on_one_host":True,
      "expected_matched_3arm_query_blocks":N_TEXTS*REPEATS,
      "completed_matched_3arm_blocks":len(rows),
      "original_complete_SELECT_semantic_all_pass":valid,
      "errors":errors[:40],
      "deidentified_all_method_query_timings":rows,
      "per_arm_metrics":aggregate(rows) if valid else None,
      "query_and_family_clustering":cluster_sensitivity(rows) if valid else None,
      "central_graph_index_load_wall_ms":round(central_build_ms,6),
      "four_worker_index_group_start_wall_ms":round(worker_start_ms,6),
      "indexed_worker_process_RSS_CPU_before":before,
      "indexed_worker_process_RSS_CPU_after":after,
      "timed_and_certified_query_phase_wall_s":round(
          time.perf_counter()-timing_start,3),
      "entire_program_wall_s":round(time.perf_counter()-started,3),
      "original_full_index_vs_temporary_per_query_index_cost_is_part_of_architecture":True,
      "three_arms_measured_on_same_runner_and_source_query":True,
      "not_an_independent_temporal_or_multihost_test":True,
      "published_AdPart_WISE_CostFed_baseline_executed":False,
      "complete_online_cache_eviction_maintenance_rollback_costed":False,
      "paper_positive_GO":False}
    (OUT/"report.json").write_text(json.dumps(output,indent=2))
    print("SAME_RUN_TRAIN48_RESULT_START",flush=True)
    print(json.dumps({k:v for k,v in output.items()
       if k not in ("frozen","deidentified_all_method_query_timings",
                    "indexed_worker_process_RSS_CPU_before",
                    "indexed_worker_process_RSS_CPU_after")},indent=2),flush=True)
    print("SAME_RUN_TRAIN48_RESULT_END",flush=True)
    if not valid:
        raise RuntimeError("Full original SPARQL certification or cohort completeness failed")


if __name__=="__main__":
    main()
