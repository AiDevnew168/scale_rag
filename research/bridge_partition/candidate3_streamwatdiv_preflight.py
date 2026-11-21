#!/usr/bin/env python3
"""Independent RDF preflight on a *new* publicly released Stream WatDiv archive.
This is NOT the frozen Wikidata organic query workload; synthetic generated
SPARQL and RDF stream. Physical byte imbalance is independently testable.
"""
import gzip, hashlib, io, json, urllib.request, zipfile
from collections import Counter,defaultdict
from pathlib import Path
URL=("https://zenodo.org/records/23016810/files/"
     "stream-watdiv-static-1-stream-1-seed-42-q10-m6-c1.zip?download=1")
OUT=Path("results_candidate3_streamwatdiv_preflight")
OUT.mkdir(exist_ok=True)

def main():
    r={"schema":"candidate3-independent-streamwatdiv-preflight-v1",
       "source":URL,
       "expected":"56,915 static RDF triples, 58,555 streamed triples, 39,069 updates, 10 generated queries",
       "limitations":["Independent data family; cannot be used to claim effect on unseen Wikidata organic traffic",
       "10 query templates only; workload order not equal to organic SPARQL user traffic",
       "Physical predicate grouping is not a full distributed query executor",
       "This is dataset feasibility and physical byte audit, NOT economic profit"]}
    try:
        req=urllib.request.Request(URL,headers={"User-Agent":"ScaleRAG-StreamWatDiv-RDF-Physical-Audit/1.0"})
        with urllib.request.urlopen(req,timeout=90) as src:
            raw=src.read(16*1024*1024+1)
        if len(raw)>16*1024*1024:raise RuntimeError("source exceeds safety size limit")
        r["downloaded_zip_bytes"]=len(raw)
        r["zip_sha256"]=hashlib.sha256(raw).hexdigest()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            listing=[{"name":a.filename,"bytes_uncompressed":a.file_size} for a in z.infolist()]
            r["file_inventory"]=listing
            s=next((a.filename for a in z.infolist() if a.filename.endswith("static.nt")),None)
            q=next((a.filename for a in z.infolist() if a.filename.endswith("queries.sparql")),None)
            e=next((a.filename for a in z.infolist() if a.filename.endswith("stream-events.jsonl")),None)
            assert s and q and e
            predicate=Counter()
            ntriples=0;bytes_total=0
            with z.open(s) as f:
                for line in f:
                    if not line.strip():continue
                    parts=line.strip().split(None,2)
                    if len(parts)<3:continue
                    p=parts[1].decode("utf8",errors="replace")
                    predicate[p]+=len(line)
                    ntriples+=1;bytes_total+=len(line)
            querybytes=z.read(q)
            r["queries_sparql_bytes"]=len(querybytes)
            r["queries_preview_first_3500_chars"]=querybytes[:3500].decode("utf8",errors="replace")
            with z.open(e) as f:
                ev=[]
                for _ in range(3):
                    ev.append(next(f).decode("utf8",errors="replace")[:650])
            r["first_three_events"]=ev
            r["static_triples_parsed"]=ntriples
            r["static_serialized_bytes"]=bytes_total
            r["predicates_count"]=len(predicate)
            r["top_15_predicates_bytes"]=predicate.most_common(15)
            r["min_max_predicate_bytes"]=[min(predicate.values()),max(predicate.values())]
            # Lower bound for any four-way placement at exact equality.
            r["theoretical_lower_bound_max_shard_bytes"]=max(max(predicate.values()),
                    (bytes_total+3)//4)
            cap=(bytes_total+3)//4
            ordered=predicate.most_common()
            balances=[0]*4
            assignments={}
            for p,nb in ordered:
                target=min(range(4),key=lambda k:(balances[k],k))
                balances[target]+=nb;assignments[p]=target
            r["largest_first_balanced_shard_bytes"]=balances
            r["within_plus10pct_mean_bytes"]=all(x<=1.1*bytes_total/4 for x in balances)
            r["max_shard_over_mean_factor"]=round(max(balances)/(bytes_total/4),4)
            r["static_ntriples_usable_for_full_predicate_migration"]=True
        r["status"]="dataset_loaded_and_byte_audited"
    except Exception as exc:
        r["status"]="preflight_failed"
        r["error"]=type(exc).__name__+": "+str(exc)[:500]
    OUT.joinpath("report.json").write_text(json.dumps(r,indent=2))
    print("STREAM_WATDIV_START");print(json.dumps(r,indent=2));print("STREAM_WATDIV_END")
if __name__=="__main__":main()
