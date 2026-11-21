#!/usr/bin/env python3
"""Post-result ENGINEERING ONLY: source-original selected filter-index build cost.

Reuses the exact 24 TRAIN query hashes from completed run 44918517226.
No test/calibration queries; no new benchmark time/answer claims.
Measure CPU/wall and Python allocated bytes of reconstructing index_original_lines
over exact physical shard/predicate fragments to expose non-free initialization.
This is a one-process simulation of four worker cache objects, not actual
per-worker RSS, migration/rollback economics, or an online adaptive policy.
"""
import gc
import gzip
import hashlib
import json
import math
import time
import tracemalloc
from pathlib import Path

import candidate3_swdf_176day_physical_economic as physical
import candidate3_feasible_raw_swdf_dated_source as raw
import candidate3_trainonly_selective_fetch_physical as train
import candidate3_swdf_real_full_sparql_economics as router
import candidate3_selective_fetch_transport as filterer

OUT=Path("results_candidate3_trainonly_filter_index_build_cost")
OUT.mkdir(exist_ok=True)
EXPECTED_24_SHA_JOINED="028afc6b5634bf596c11ccb481ce2ed778ae572ae22502f2bdf16264851ca384"
RUN_SOURCE_SHA="1fcbed5174c7925b7af17ccec88aabf03eaea7bf"
MAX_WALL_SEC=650


def target_fragments(chosen,route,fragmented,packs):
    selection={}
    for row in chosen:
        groups=router.shards_for_query(row["pattern"],route,fragmented)
        for shard,ps in groups.items():
            for p in ps:
                if row["filters"][p] is None:
                    continue
                if p not in packs[shard]:
                    raise RuntimeError("Routed fragment missing from immutable source worker pack")
                selection[(shard,p)] = packs[shard][p]
    return selection


def profile(fragments, source_sha, selection_hash):
    started=time.perf_counter()
    gc.collect()
    tracemalloc.start()
    before_current, before_peak=tracemalloc.get_traced_memory()
    original_source_bytes=sum(len(v) for v in fragments.values())
    all_cache={}
    rows=[]
    errors=[]
    for (shard,p),body in sorted(fragments.items()):
        if time.perf_counter()-started>MAX_WALL_SEC:
            errors.append({"reason":"bounded_total_time_exceeded"});break
        t0=time.perf_counter()
        try:
            values=filterer.index_original_lines(body)
            if len(values)==0 and body.strip():
                raise RuntimeError("Parsed source triples vanished")
            all_cache[(shard,p)]=values
            now_current,now_peak=tracemalloc.get_traced_memory()
            rows.append({"source_predicate_sha256":hashlib.sha256(p.encode()).hexdigest(),
                         "physical_shard":shard,
                         "indexed_original_source_bytes":len(body),
                         "indexed_original_triples":len(values),
                         "cold_build_ms":round((time.perf_counter()-t0)*1000,5),
                         "current_python_traced_heap_bytes":now_current-before_current,
                         "peak_python_traced_heap_bytes":now_peak-before_current})
        except Exception as exc:
            errors.append({"physical_shard":shard,
                           "predicate_sha256":hashlib.sha256(p.encode()).hexdigest(),
                           "error_type":type(exc).__name__})
            break
    now,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "schema":"candidate3-postresult-trainonly-original-NTriples-filter-index-profile-v1",
        "status":"COMPLETE_ENGINEERING_PROFILE" if not errors else "INVALID_OR_INCOMPLETE_PROFILE",
        "source_original_run_commit":RUN_SOURCE_SHA,
        "previous_24_training_texts_joined_hash":selection_hash,
        "n_original_worker_predicate_fragments_requested":len(fragments),
        "n_indexed_without_error":len(rows),
        "original_selected_fragment_source_bytes":original_source_bytes,
        "original_parsed_triples_count":sum(r["indexed_original_triples"] for r in rows),
        "cold_index_build_wall_total_ms":round(sum(r["cold_build_ms"] for r in rows),5),
        "total_profile_wall_ms":round((time.perf_counter()-started)*1000,5),
        "additional_live_python_traced_heap_bytes":max(0,now-before_current),
        "python_traced_peak_extra_bytes":max(0,peak-before_current),
        "per_fragment_deidentified_metrics":rows,
        "errors":errors,
        "all_hashes_and_original_training_selection_unchanged":True,
        "source_original_RDF_fragment_lines_used_not_reconstructed":True,
        "four_workers_emulated_in_one_profile_process":True,
        "worker_service_real_RSS_or_cache_eviction_measured":False,
        "full_production_index_RAM_or_CPU_startup_costs_measured":False,
        "benchmark_latency_gain_not_double_subtracted_or_claimed_as_net":True,
        "journal_GO":False,
    }


def main():
    source_graph,bypred,weights,packs,loads,route,cap=physical.load_real_source()
    del source_graph,bypred,loads,cap
    p=OUT/"SWDF.log.gz"
    download=physical.graphsource.gdown.download(id=raw.SOURCE_ID,
             output=str(p),quiet=True,fuzzy=True)
    if not download or not p.is_file() or raw.sha_file(p)!=physical.SOURCE_SHA:
        raise RuntimeError("Original source log download/hash mismatch")
    chosen,meta=train.choose_train_only(p,{k[1:-1] for k in weights})
    signature=hashlib.sha256("\n".join(x["hash"] for x in chosen).encode()).hexdigest()
    if signature!=EXPECTED_24_SHA_JOINED:
        raise RuntimeError("Frozen first-24 training sample has changed")
    fragmented={p for p,shards in route.items() if len(shards)>1}
    fragments=target_fragments(chosen,route,fragmented,packs)
    if not fragments:
        raise RuntimeError("No actual fragment indexes selected")
    print("PINNED_TRAIN24_INDEX_PROFILE_SELECTED",
          json.dumps({"n_original_texts":len(chosen),"source_predicate_fragments":len(fragments),
                      "signature_sha256":signature}),flush=True)
    result=profile(fragments,physical.SOURCE_SHA,signature)
    result["original_source_raw_log_SHA256"]=physical.SOURCE_SHA
    result["original_RDF_ZIP_SHA256"]=physical.GRAPH_SHA
    (OUT/"report.json").write_text(json.dumps(result,indent=2))
    print("COLD_FILTER_INDEX_PROFILE_START",flush=True)
    print(json.dumps({k:v for k,v in result.items() if k!="per_fragment_deidentified_metrics"},
         indent=2),flush=True)
    print("COLD_FILTER_INDEX_PROFILE_END",flush=True)
    if result["status"]!="COMPLETE_ENGINEERING_PROFILE":
        raise RuntimeError("Incomplete source-original cold index profile")


if __name__=="__main__":
    main()
