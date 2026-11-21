#!/usr/bin/env python3
"""Original SWDF TRAIN-only strong centralized indexed-Oxigraph baseline.

No new algorithms, no 53-day heldout, and no causal cross-run speedup claim.
"""
import hashlib
import json
import os
import random
import statistics
import time
from pathlib import Path

from pyoxigraph import Store,RdfFormat
import candidate3_feasible_raw_swdf_dated_source as raw
import candidate3_swdf_176day_physical_economic as source
import candidate3_trainonly_selective_fetch_physical as train
from candidate3_sparql_semantic_certifier import solution_rows

OUT=Path("results_candidate3_original_SWDF_first24_train_central_indexed")
OUT.mkdir(exist_ok=True)
EXPECTED_PIPE_FINGERPRINT="108a618ab725e291d05967c1d81e58a1c5e8365804f88f7602bbe7370f26e09c"


def process_rss_kib():
    status=Path(f"/proc/{os.getpid()}/status")
    if status.exists():
        for line in status.read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    return None


def p95(samples):
    s=sorted(samples)
    return s[(95*len(s)+99)//100-1]


def main():
    graph,bypred,weights,packs,loads,route,cap=source.load_real_source()
    source_path=OUT/"SWDF.log.gz"
    got=source.graphsource.gdown.download(id=raw.SOURCE_ID,
                     output=str(source_path),quiet=True,fuzzy=True)
    if not got or not source_path.exists() or raw.sha_file(source_path)!=source.SOURCE_SHA:
        raise RuntimeError("Source chronology SHA mismatch, no inference")
    chosen,summary=train.choose_train_only(source_path,
                      {p[1:-1] for p in weights})
    fingerprint=hashlib.sha256(
        "|".join(r["hash"] for r in chosen).encode()).hexdigest()
    if fingerprint!=EXPECTED_PIPE_FINGERPRINT:
        raise RuntimeError("Source TRAIN first24 selected query identity drift")
    freeze={"schema":"candidate3-original-SWDF-centralized-fully-indexed-training-control-freeze-v1",
      "original_query_source_SHA256":source.SOURCE_SHA,
      "original_graph_zip_SHA256":source.GRAPH_SHA,
      "original_training_days":88,"n_unique_source_texts":24,"query_repeats":2,
      "first24_text_hash_joined_fingerprint":fingerprint,
      "selected_because_query_latency":False,
      "unmodified_original_source_queries":True,
      "future_calendar_query_texts_used":False,
      "known_earlier_distributed_training_results":True,
      "centralized_full_graph_index_is_a_strong_single_host_nonfederated_baseline":True}
    (OUT/"selection_frozen_before_centralized_timings.json").write_text(
        json.dumps(freeze,indent=2))
    print("CENTRAL_INDEXED_FIRST24_TRAIN_SOURCE_FROZEN",
          hashlib.sha256(json.dumps(freeze,sort_keys=True).encode()).hexdigest(),
          flush=True)
    del source_path
    rss_pre=process_rss_kib()
    began=time.perf_counter()
    central=Store()
    central.load(input=graph,format=RdfFormat.N_TRIPLES)
    build_ms=(time.perf_counter()-began)*1000
    graph_sha=hashlib.sha256(graph).hexdigest()
    del graph
    rss_post=process_rss_kib()
    requests=[(i,rep) for i in range(len(chosen)) for rep in range(2)]
    random.Random(20261121).shuffle(requests)
    measurements=[];errors=[]
    for pos,(i,rep) in enumerate(requests):
        row=chosen[i]
        began=time.perf_counter()
        try:
            variables,answers=solution_rows(central,row["query"])
            ms=(time.perf_counter()-began)*1000
            measurements.append({"query_text_sha256":row["hash"],"rep":rep,
              "query_position":pos,"central_indexed_full_query_ms":round(ms,6),
              "n_solution_rows":len(answers),
              "n_projection_variables":len(variables)})
        except Exception as exc:
            errors.append({"query_text_sha256":row["hash"],"rep":rep,
                           "exception_type":type(exc).__name__})
    complete=not errors and len(measurements)==48
    durations=[x["central_indexed_full_query_ms"] for x in measurements]
    out={"schema":"candidate3-SWDF-first24-original-query-centralized-indexed-control-v1",
      "frozen_selection":freeze,
      "original_graph_sha256":graph_sha,
      "n_central_indexed_RDF_triples":len(central),
      "central_index_build_wall_ms":round(build_ms,6),
      "central_process_VmRSS_pre_index_KiB":rss_pre,
      "central_process_VmRSS_post_index_KiB":rss_post,
      "n_original_train_full_SELECT_executions_expected":48,
      "n_original_train_full_SELECT_executions_observed":len(measurements),
      "all_original_queries_executed":complete,
      "central_indexed_full_source_query_mean_ms":round(statistics.mean(durations),6) if complete else None,
      "central_indexed_full_source_query_median_ms":round(statistics.median(durations),6) if complete else None,
      "central_indexed_full_source_query_p95_ms":round(p95(durations),6) if complete else None,
      "deidentified_timing_and_answer_cardinality":measurements,
      "errors":errors[:24],
      "comparison_with_prior_four_worker_run_is_UNPAIRED_and_DESCRIPTIVE":True,
      "only_one_host_graph_size_not_Distributed_SOTA":True,
      "actual_published_AdPart_WISE_CostFed_runs":False,
      "journal_GO":False}
    (OUT/"report.json").write_text(json.dumps(out,indent=2))
    print("CENTRAL_INDEXED_ORIGINAL_TRAIN24_RESULT_START",flush=True)
    print(json.dumps({k:v for k,v in out.items()
                      if k not in ("deidentified_timing_and_answer_cardinality","frozen_selection")},indent=2),flush=True)
    print("CENTRAL_INDEXED_ORIGINAL_TRAIN24_RESULT_END",flush=True)
    if not complete:
        raise RuntimeError("Original SPARQL centralized run incomplete; scientific gate fail")


if __name__=="__main__":
    main()
