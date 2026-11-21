#!/usr/bin/env python3
"""Bounded original-SWDF TRAIN-ONLY physical constant-pushdown experiment.

Exploratory capacity/engineering test, not novelty or economic migration proof.
Frozen: first 88 days only, ranks 25-48 of 24 SHA-ordered eligible original SELECTs,
two randomized paired repetitions each, original full source RDF unchanged.
No calibration/test query text, answers, or timing used. Zero query omissions
per frozen sampled selection; any engine, semantic, timeout error => invalid.
"""
import collections
import datetime
import gzip
import hashlib
import json
import random
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pyoxigraph import Store,RdfFormat
from candidate3_sparql_semantic_certifier import certify,characterize,solution_rows
import candidate3_feasible_raw_swdf_dated_source as raw
import candidate3_feasible_raw_swdf_strict_temporal as strict
import candidate3_swdf_176day_physical_economic as physical
import candidate3_source_identity_worker as worker
import candidate3_real_sparql_shards as network
import candidate3_swdf_real_full_sparql_economics as routing
import candidate3_selective_fetch_transport as selective

OUT=Path("results_candidate3_trainonly_second24_original_SWDF_selective_fetch_physical")
OUT.mkdir(exist_ok=True)
SEED=20261121
N_QUERY_TEXTS=24
REPEATS=2
SOURCE_SHA=physical.SOURCE_SHA


def first_88_days(path):
    days=set()
    with gzip.open(path,"rb") as f:
        for line in f:
            m=raw.APACHE.search(line.decode("utf8",errors="replace"))
            if m:
                d=physical.date_of_request(m)
                if d:days.add(d)
    days=sorted(days)
    if len(days)!=176:
        raise RuntimeError("Frozen source timeline changed")
    return set(days[:88])


def choose_train_only(path,predicates):
    train=first_88_days(path)
    unique={}
    for_candidate=collections.Counter()
    empty=Store() # syntactic check ONLY on public training requests
    with gzip.open(path,"rb") as f:
        for line in f:
            m=raw.APACHE.search(line.decode("utf8",errors="replace"))
            if not m or m.group(2).upper()!="GET":
                continue
            if physical.date_of_request(m) not in train:
                continue
            q=raw.parse_query(m.group(3))
            if q is None or not physical.SELECT_TOKEN.search(q) or len(q)>16000:
                continue
            h=hashlib.sha256(q.encode()).hexdigest()
            if h in unique:
                continue
            predicates_,error=strict.select_predicates(q)
            if error or not set(predicates_).issubset(predicates):
                continue
            try:
                filters=selective.compile_filters(q)
            except (ValueError,SyntaxError) as exc:
                for_candidate["invalid_bgp_compiler"]+=1
                continue
            if not any(spec is not None for spec in filters.values()):
                continue
            if characterize(q).kind not in ("full_bag","unordered_slice"):
                continue
            try:
                empty.query(q)
            except Exception:
                for_candidate["target_engine_incompatible_training_text"]+=1
                continue
            unique[h]={"query":q,"hash":h,
                       "pattern":tuple(sorted(filters)),
                       "filters":filters}
    ordered=sorted(unique.values(),key=lambda v:
                   hashlib.sha256((str(SEED)+":"+v["hash"]).encode()).hexdigest())
    if len(ordered)<2*N_QUERY_TEXTS:
        raise RuntimeError("Insufficient original, engine-compatible TRAIN-only texts")
    return ordered[N_QUERY_TEXTS:2*N_QUERY_TEXTS],{
        "all_train_eligible_anchored_engine_compatible_texts":len(ordered),
        "source_training_incompatible_or_unsupported":dict(for_candidate),
        "frozen_candidate_rank":"SHA256(seed:text_sha256) ascending",
        "chosen_query_texts":N_QUERY_TEXTS,
        "frozen_rank_start_1based":N_QUERY_TEXTS+1,
        "frozen_rank_end_1based":2*N_QUERY_TEXTS,
        "chosen_text_hashes":[v["hash"] for v in ordered[N_QUERY_TEXTS:2*N_QUERY_TEXTS]],
        "calibration_or_test_original_query_texts_examined":False,
        "candidate_selection_uses_real_RDF_answer_or_latency":False}


def request_one(ports,route,fragmented,row,method):
    groups=routing.shards_for_query(row["pattern"],route,fragmented)
    requests=selective.work_requests(groups,row["filters"])
    start=time.perf_counter()
    def fetch(entry):
        i,predicates=entry
        if method=="full":
            body=json.dumps({"predicates":sorted(predicates)}).encode()
            endpoint="/raw-fragments"
        elif method=="constant_pushdown":
            body=json.dumps({"filters":predicates}).encode()
            endpoint="/selective-fragments"
        else:
            raise RuntimeError("Unknown method")
        payload,server_wall=network.call(ports[i],endpoint,body,
            {"Content-Type":"application/json"},timeout=120)
        return payload,server_wall
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses=list(executor.map(fetch,sorted(requests.items())))
    data=b"".join(r[0] for r in responses)
    fetched_ms=(time.perf_counter()-start)*1000
    tmp=Store()
    tmp.load(input=data,format=RdfFormat.N_TRIPLES)
    _variables,_solutions=solution_rows(tmp,row["query"])
    end_ms=(time.perf_counter()-start)*1000
    return {"wall_ms":end_ms,"rdf_fetch_ms":fetched_ms,
            "ntriples_rdf_tcp_bytes":len(data),"shard_contacts":len(responses),
            "temp":tmp,"solution_rows":len(_solutions)}


def main():
    started=time.perf_counter()
    graph,bypred,weights,packs,loads,route,cap=physical.load_real_source()
    source_path=OUT/"SWDF.log.gz"
    got=physical.graphsource.gdown.download(id=raw.SOURCE_ID,
                    output=str(source_path),quiet=True,fuzzy=True)
    if not got or not source_path.is_file() or raw.sha_file(source_path)!=SOURCE_SHA:
        raise RuntimeError("Original source trace failed immutable SHA check")
    chosen,freeze_meta=choose_train_only(source_path,{p[1:-1] for p in weights})
    frozen={"schema":"candidate3-trainonly-constant-pushdown-physical-freeze-v1",
        "source_sha256":SOURCE_SHA,"RDF_archive_sha256":physical.GRAPH_SHA,
        "training_original_UTC_days":88,"n_query_texts":N_QUERY_TEXTS,
        "train_only_second_cohort_rank_start":25,
        "first_24_latency_seen_before_this_second_lock":True,
        "paired_repeats":REPEATS,"candidate_selection":freeze_meta,
        "original_queries_unchanged":True,"no_2014_heldout_reuse":True,
        "no_migration_policy_claim":True}
    (OUT/"selection_frozen_before_training_answers.json").write_text(
        json.dumps(frozen,indent=2))
    print("TRAIN_ONLY_SECOND24_PUSHDOWN_SELECTION_FROZEN",
          hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest(),flush=True)
    central=Store()
    central.load(input=graph,format=RdfFormat.N_TRIPLES)
    del graph
    fragmented={p for p,loc in route.items() if len(loc)>1}
    ports,workers=worker.start_group(packs)
    timing=[]
    errors=[]
    rng=random.Random(SEED)
    try:
        for i,row in enumerate(chosen):
            for repetition in range(REPEATS):
                try:
                    order=["full","constant_pushdown"]
                    rng.shuffle(order)
                    runs={}
                    for method in order:
                        runs[method]=request_one(ports,route,fragmented,row,method)
                    check={}
                    for method in ("full","constant_pushdown"):
                        check[method]=certify(central,runs[method]["temp"],row["query"])
                    if any(c["status"]!="PASS" for c in check.values()):
                        errors.append({"index":i,"text_sha256":row["hash"],
                            "repetition":repetition,
                            "full_status":check["full"]["status"],
                            "pushdown_status":check["constant_pushdown"]["status"],
                            "error_kind":"SPARQL_SEMANTIC_MISMATCH"})
                        continue
                    a=runs["full"];b=runs["constant_pushdown"]
                    if b["ntriples_rdf_tcp_bytes"]>a["ntriples_rdf_tcp_bytes"]:
                        raise RuntimeError("Selective byte count exceeds full predicate body")
                    timing.append({"text_sha256":row["hash"],"repetition":repetition,
                        "full_ms":round(a["wall_ms"],4),
                        "pushdown_ms":round(b["wall_ms"],4),
                        "full_rdf_bytes":a["ntriples_rdf_tcp_bytes"],
                        "pushdown_rdf_bytes":b["ntriples_rdf_tcp_bytes"],
                        "full_shard_contacts":a["shard_contacts"],
                        "pushdown_shard_contacts":b["shard_contacts"],
                        "saved_ms":round(a["wall_ms"]-b["wall_ms"],4)})
                except Exception as exc:
                    errors.append({"index":i,"text_sha256":row["hash"],
                                   "repetition":repetition,
                                   "error_kind":type(exc).__name__})
                if (i+1)%4==0 and repetition==REPEATS-1:
                    print("TRAIN_ONLY_SECOND24_PUSHDOWN_PROGRESS",i+1,"of",N_QUERY_TEXTS,flush=True)
    finally:
        worker.stop_group(workers)
    valid=len(timing)==N_QUERY_TEXTS*REPEATS and not errors
    ratios=[1-r["pushdown_rdf_bytes"]/r["full_rdf_bytes"]
         for r in timing if r["full_rdf_bytes"]>0]
    result={"schema":"candidate3-trainonly-source-physical-constant-pushdown-v1",
        "frozen_selection":frozen,
        "physical_workers":4,"worker_hosts":1,
        "real_TCP_source_NTriples_response":True,
        "original_source_graph_triples":len(central),
        "n_expected_pairs":N_QUERY_TEXTS*REPEATS,
        "n_semantically_legal_pairs":len(timing),
        "all_original_queries_correct":valid,
        "errors":errors[:30],
        "deidentified_original_training_paired_rows":timing,
        "training_only_median_RDF_response_byte_reduction":
            round(statistics.median(ratios),5) if ratios and valid else None,
        "training_only_mean_latency_saved_ms":
            round(statistics.mean(r["saved_ms"] for r in timing),5) if valid else None,
        "training_only_median_latency_saved_ms":
            round(statistics.median(r["saved_ms"] for r in timing),5) if valid else None,
        "training_only_ratio_of_queries_with_positive_byte_savings":
            round(sum(x>0 for x in ratios)/len(ratios),5) if ratios and valid else None,
        "no_result_excluded_from_valid_economic_aggregate":valid,
        "benchmark_wall_seconds":round(time.perf_counter()-started,2),
        "first24_known_timing_not_independent_temporal_validation":True,
        "includes_worker_index_construction_and_baseline_source_parsing":False,
        "request_order_randomized":True,
        "source_RDF_snapshot_event_time_aligned":False,
        "compares_adpart_or_wise_original_engine":False,
        "proves_novelty_or_prospective_profit":False,
        "journal_GO":False}
    (OUT/"report.json").write_text(json.dumps(result,indent=2))
    print("TRAIN_ONLY_SECOND24_ORIGINAL_PUSHDOWN_PHYSICAL_REPORT_START",flush=True)
    print(json.dumps({k:v for k,v in result.items()
        if k not in ("deidentified_original_training_paired_rows","frozen_selection")},
        indent=2),flush=True)
    print("TRAIN_ONLY_SECOND24_ORIGINAL_PUSHDOWN_PHYSICAL_REPORT_END",flush=True)
    if not valid:
        raise RuntimeError("Frozen original training query semantic or runtime gate failed")


if __name__=="__main__":
    main()
