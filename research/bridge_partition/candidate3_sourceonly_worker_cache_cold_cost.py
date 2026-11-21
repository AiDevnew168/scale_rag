#!/usr/bin/env python3
"""Original graph-only source fragment cache cold/warm microbenchmark.

Source-only, no original SWDF access log read, no SPARQL answers or user IP.
Known-possible cold cost of optional constant-filtered NTriples HTTP fetch.
"""
import hashlib
import json
import re
import statistics
import time
from pathlib import Path

from pyoxigraph import RdfFormat, Store
import candidate3_swdf_176day_physical_economic as physical
import candidate3_source_identity_worker as worker
import candidate3_real_sparql_shards as network
import candidate3_selective_fetch_transport as selective

OUT=Path("results_candidate3_sourceonly_worker_cold_cache_cost")
OUT.mkdir(exist_ok=True)


def process_rss(pid):
    """Linux VmRSS in KiB, not total heap allocation or peak memory."""
    status=Path(f"/proc/{pid}/status")
    if not status.exists():
        return None
    for line in status.read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return None


def choose_source_fragment(packs):
    rows=sorted(
        ((len(payload),i,p,payload) for i,store in enumerate(packs)
            for p,payload in store.items()),reverse=True)
    for size,shard,p,raw in rows:
        for line in raw.splitlines(keepends=True):
            m=re.match(rb"^<([^>]+)>[ \t]",line)
            if m:
                return {"size":size,"shard":shard,"predicate":p,
                        "subject":["iri",m.group(1).decode("utf8")],
                        "payload":raw}
    raise ValueError("No original NTriples NamedNode subject to select")


def main():
    original_graph,bypred,weights,packs,loads,route,cap=physical.load_real_source()
    selected=choose_source_fragment(packs)
    shard=selected["shard"]
    raw=selected["payload"]
    frozen={"schema":"candidate3-sourceonly-original-graph-cache-probe-freeze-v1",
        "original_RDF_zip_SHA256":physical.GRAPH_SHA,
        "original_graph_ntriples_sha256":hashlib.sha256(original_graph).hexdigest(),
        "deterministic_selection":"max_original_source_predicate_fragment_with_named_subject",
        "predicate_sha256":hashlib.sha256(selected["predicate"].encode()).hexdigest(),
        "original_fragment_SHA256":hashlib.sha256(raw).hexdigest(),
        "original_fragment_bytes":len(raw),
        "original_query_log_read":False,
        "profiled_worker_id":shard,
        "fixed_request_order":["full","full","cold_selective","warm_selective"]+
                         ["warm_selective"]*4+["full"],
        "one_host_four_indexed_workers":True}
    (OUT/"pre_execution_selection.json").write_text(json.dumps(frozen,indent=2))
    print("SOURCEONLY_COLD_CACHE_PROBE_FROZEN",
        hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest(),
        flush=True)
    ports,processes=worker.start_group(packs)
    cache_before=process_rss(processes[shard].pid)
    results=[]
    filtered_reference=selective.filter_fragment(
        raw,[{"subject":selected["subject"],"object":None}])
    # Reference local calculation is outside timed request path, not on worker
    try:
        for sequence,kind in enumerate(frozen["fixed_request_order"]):
            if kind=="full":
                endpoint="/raw-fragments"
                post=json.dumps({"predicates":[selected["predicate"]]}).encode()
            else:
                endpoint="/selective-fragments"
                post=json.dumps({"filters":{selected["predicate"]:[
                    {"subject":selected["subject"],"object":None}]}}).encode()
            body,elapsed=network.call(ports[shard],endpoint,post,
                               {"Content-Type":"application/json"},timeout=120)
            expected=raw if kind=="full" else filtered_reference
            if body!=expected:
                raise RuntimeError("Original NTriples source byte identity failure")
            results.append({"sequence":sequence,"kind":kind,
                            "wall_ms":round(elapsed,6),"rdf_payload_bytes":len(body),
                            "source_identity_exact":True})
            if kind=="cold_selective":
                cache_after=process_rss(processes[shard].pid)
        full=[r["wall_ms"] for r in results if r["kind"]=="full"]
        warm=[r["wall_ms"] for r in results if r["kind"]=="warm_selective"]
        cold=next(r["wall_ms"] for r in results if r["kind"]=="cold_selective")
        output={"schema":"candidate3-real-source-four-worker-cold-parse-RSS-probe-v1",
            "frozen_source_selection":frozen,
            "all_replies_original_fragment_byte_identical":True,
            "requests":results,
            "original_fragment_bytes":len(raw),
            "selected_source_bytes":len(filtered_reference),
            "fraction_source_response_bytes_saved":round(
                1-len(filtered_reference)/len(raw),6),
            "cold_selective_http_wall_ms":cold,
            "warm_selective_http_median_ms":statistics.median(warm),
            "cold_minus_warm_http_ms":round(cold-statistics.median(warm),6),
            "full_http_median_ms":statistics.median(full),
            "worker_RSS_KiB_before_first_filtered_request":cache_before,
            "worker_RSS_KiB_after_first_filtered_request":cache_after,
            "worker_RSS_change_KiB":
                (cache_after-cache_before if cache_before is not None and
                    cache_after is not None else None),
            "worker_cache_memory_per_full_training_workload_measured":False,
            "not_original_SPARQL_query_wall_time":True,
            "not_a_paper_or_real_migration_profit_claim":True}
        (OUT/"report.json").write_text(json.dumps(output,indent=2))
        print("SOURCEONLY_COLD_CACHE_REPORT_START",flush=True)
        print(json.dumps(output,indent=2),flush=True)
        print("SOURCEONLY_COLD_CACHE_REPORT_END",flush=True)
    finally:
        worker.stop_group(processes)


if __name__=="__main__":
    main()
