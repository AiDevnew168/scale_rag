#!/usr/bin/env python3
"""Audit actual compressed JPEG bytes for frozen query-text-driven page moves.

Read only official image archive; no test gold enters the policy decisions.
This is a data-volume and idealized RTT break-even audit, NOT measured
end-to-end RAG latency or actual server memory placement.
"""
import hashlib, json, math, re, tarfile, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
import zstandard

ROOT="https://huggingface.co/datasets/diandianone123/topographrag-bench/resolve/main/"
IN=Path("results_text_prefetch_synthesis")
OUT=Path("results_physical_bytes")
OUT.mkdir(exist_ok=True)
PROFILES=[
    {"name":"100Mbps_20ms", "mbps":100, "rtt_ms":20},
    {"name":"1000Mbps_2ms", "mbps":1000, "rtt_ms":2},
    {"name":"10Mbps_50ms", "mbps":10, "rtt_ms":50},
]
def get_data():
    trace=json.loads((IN/"image_move_trace.json").read_text())
    report=json.loads((IN/"report.json").read_text())
    manifest=json.loads(Path("manifest.json").read_text())
    assert report["n_queries"]==114 and report["saved_shard_activations_gated_vs_static"]==11
    assert report["migration_diagnostics"]["gated_page_moves"]==40
    assert len(trace)==20 and sum(len(t["page_indices"]) for t in trace)==40
    return trace,report,manifest

def archive_sizes(names):
    # HEAD is confirmed 200 and size 1,066,344,475 bytes in prior workflow.
    url=ROOT+"archives/page_images.tar.zst"
    archive=Path("page_images.tar.zst")
    digest=hashlib.sha256()
    if not archive.exists():
        req=urllib.request.Request(url,headers={"User-Agent":"research-scale-rag/1.0"})
        with urllib.request.urlopen(req,timeout=160) as response,archive.open("wb") as dest:
            done=0
            while True:
                chunk=response.read(4*1024*1024)
                if not chunk:break
                dest.write(chunk);digest.update(chunk);done+=len(chunk)
                if done%(256*1024*1024)<len(chunk):
                    print("IMAGE_ARCHIVE_DOWNLOADED_MB",round(done/1e6),flush=True)
    else:
        with archive.open("rb") as f:
            for chunk in iter(lambda:f.read(4*1024*1024),b""):
                digest.update(chunk)
    print("IMAGE_ARCHIVE_SOURCE_SHA256",digest.hexdigest(),"BYTES",archive.stat().st_size,flush=True)
    remaining=set(names); found={};seen=0
    with archive.open("rb") as f:
        with zstandard.ZstdDecompressor().stream_reader(f) as reader:
            with tarfile.open(fileobj=reader,mode="r|") as tar:
                for member in tar:
                    if not member.isfile():continue
                    seen+=1
                    actual=member.name.lstrip("./")
                    found_name=actual if actual in remaining else None
                    if found_name is None:
                        matches=[p for p in remaining if actual.endswith("/"+p)]
                        if len(matches)==1:found_name=matches[0]
                    if found_name is not None:
                        found[found_name]=member.size
                        remaining.remove(found_name)
                        if not remaining:break
    print("IMAGE_MEMBER_COUNT_PROCESSED",seen,
          "FOUND",len(found),"MISSING",len(remaining),flush=True)
    if remaining:raise AssertionError("Missing original image files: "+repr(sorted(remaining)[:20]))
    return found,digest.hexdigest(),archive.stat().st_size

def summarize():
    trace,preflight,manifest=get_data()
    byid={int(doc["doc_id"]):doc for doc in manifest["documents"]}
    page_paths={}
    need=set()
    for d in trace:
        ident=d["doc_id"]
        n=d["n_pages"]
        allpaths=byid[ident]["files"]["page_images"]
        mapping={}
        for p in allpaths:
            m=re.search(r"_(\d+)\.(?:jpg|jpeg|png)$",p,re.I)
            if m:mapping[int(m.group(1))]=p.lstrip("./")
        if set(mapping)!=set(range(n)):
            raise AssertionError(f"Document {ident}: unmatched image-page index mapping")
        page_paths[ident]=mapping
        need.update(mapping.values())
    sizes,archive_sha,archive_bytes=archive_sizes(need)
    individual=[];tot_moved=0;tot_save=0;total_saved_replication=0
    total_storage=0;baseline_overcap=0;post_overcap=0
    for d in trace:
        doc=d["doc_id"];before=d["initial_shards"];after=d["post_move_shards"]
        n=d["n_pages"];idx=d["page_indices"]
        paths=page_paths[doc]
        moved_bytes=sum(sizes[paths[i]] for i in idx)
        total_bytes=sum(sizes[paths[i]] for i in range(n))
        avg=total_bytes/4
        max_before=max(sum(sizes[paths[i]] for i in range(n) if before[i]==b) for b in range(4))
        max_after=max(sum(sizes[paths[i]] for i in range(n) if after[i]==b) for b in range(4))
        # report diagnostics only: was the page-count-balanced assignment
        # actually balanced under a hypothetical strict +10% byte budget?
        cap=math.ceil(1.10*avg)
        baseline_overcap+=int(max_before>cap)
        post_overcap+=int(max_after>cap)
        save=d["saved_shard_activations"];replica_save=d["replica_savings"]
        tot_moved+=moved_bytes;tot_save+=save;total_saved_replication+=replica_save
        total_storage+=total_bytes
        individual.append({"doc_id":doc,"n_original_pages":n,
           "moved_pages":len(idx),"moved_jpeg_bytes":moved_bytes,
           "image_bytes_total":total_bytes,
           "oracle_activations_saved":save,
           "oracle_activations_saved_if_copy_instead":replica_save,
           "max_before_jpeg_bytes_per_shard":max_before,
           "max_after_jpeg_bytes_per_shard":max_after,
           "strict_byte_cap_plus10pct":cap,
           "fits_plus10pct_before":max_before<=cap,
           "fits_plus10pct_after":max_after<=cap,
           "single_batch_break_even":{p["name"]:(
                  round((moved_bytes*8/(p["mbps"]*1e6))*1000 / (save*p["rtt_ms"]),3)
                  if save>0 else None) for p in PROFILES}
        })
    assert tot_save==11 and tot_moved>0
    physical={
      "schema":"official-page-jpeg-migration-cost-v1",
      "source_archive_sha256":archive_sha,"source_archive_compressed_bytes":archive_bytes,
      "page_images_found":len(sizes),
      "policy":"frozen text-only query topology gated page swap; 20 changed documents",
      "changed_documents":len(trace),"moved_pages":sum(d["moved_pages"] for d in individual),
      "actual_moved_jpeg_bytes":tot_moved,
      "actual_moved_jpeg_megabytes":round(tot_moved/1e6,3),
      "total_original_jpeg_megabytes_in_changed_docs":round(total_storage/1e6,3),
      "single_batch_test_queries":preflight["n_queries"],
      "saved_ideal_shard_activations_from_move":tot_save,
      "saved_ideal_shard_activations_from_replication":total_saved_replication,
      "storage_bytes_added_by_same_transfer_replication":tot_moved,
      "moved_jpeg_bytes_per_ideal_shard_activation_saved":round(tot_moved/tot_save),
      "byte_capacity_diagnostics":{
         "changed_documents_not_feasible_at_plus10pct_before":baseline_overcap,
         "changed_documents_not_feasible_at_plus10pct_after":post_overcap,
         "note":"The PAGE-count partition was not byte-balanced; strictly comparable real byte placement requires repartitioning. +10% is a hypothetical diagnostic, not claimed setup."},
      "idealized_break_even":{
          p["name"]:{"assumed_bandwidth_Mbps":p["mbps"],"assumed_extra_shard_RTT_ms":p["rtt_ms"],
              "image_migration_ms":round(1000*tot_moved*8/(p["mbps"]*1e6),2),
              "one_batch_saved_serial_shard_RTT_ms":tot_save*p["rtt_ms"],
              "repeated_identical_batches_to_amortize_transferred_bytes":math.ceil(
                  (1000*tot_moved*8/(p["mbps"]*1e6))/(tot_save*p["rtt_ms"]))}
          for p in PROFILES},
      "limitations":[
        "These are actual original JPEG image FILE BYTES, not live server networking or memory measurements",
        "Source PDF layout text, OCR and graph node byte costs are excluded",
        "Ideal latency model assumes saved shard activations serialize one RTT each; network joins may execute in parallel, invalidating the assumed saving",
        "No transfer setup, checksum, cache invalidation, disk write, routing, query waiting, or rebalance overhead",
        "Replicate instead of move is an EXTRA STORAGE baseline, not equal-capacity; do not equate with migration under unchanged shard RAM",
        "Incoming batch query text is known, no test gold enters planning; gold only scores shard activation",
        "These 45 documents were used in prior exploratory method selection and are not a new independent dataset"]}
    OUT.joinpath("report.json").write_text(json.dumps(physical,indent=2))
    OUT.joinpath("per_document.json").write_text(json.dumps(individual,indent=2))
    print("PHYSICAL_BYTE_RESULT_START",flush=True)
    print(json.dumps(physical,indent=2),flush=True)
    print("PHYSICAL_BYTE_RESULT_END",flush=True)

if __name__=="__main__":
    summarize()
