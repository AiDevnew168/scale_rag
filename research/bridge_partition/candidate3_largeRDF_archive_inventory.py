#!/usr/bin/env python3
"""Metadata only: enumerate 2026 real Bio2RDF graphs via HTTP range ZIP.

Neither graph triples, query text nor expected result values are read.
Requires HTTP 206; NEVER streams 5GB ZIP merely to guess.
"""
import hashlib,io,json,urllib.request,zipfile
from pathlib import Path
from remotezip import RemoteZip

PREFIX="https://zenodo.org/api/records/22140177/files/"
RDF=PREFIX+"rdf_datasets.zip/content"
QUERIES=PREFIX+"queries.zip/content"
EXPECTED_QUERY_MD5="10a2e5fb7a69ff9da66d9d5bf977a77e"
OUT=Path("results_candidate3_external_largeRDF_archive_index");OUT.mkdir(exist_ok=True)

def read_query_listing():
    with urllib.request.urlopen(urllib.request.Request(QUERIES,
             headers={"User-Agent":"ScaleRAG-frozen-metadata/1.0"}),timeout=45) as r:
        data=r.read(1_000_001)
    assert len(data)<=1_000_000
    assert hashlib.md5(data).hexdigest()==EXPECTED_QUERY_MD5
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return [{"name":f.filename,"compressed_bytes":f.compress_size,
            "uncompressed_bytes":f.file_size} for f in z.infolist()]

def try_ranged_listing():
    req=urllib.request.Request(RDF,headers={"Range":"bytes=-1024",
            "User-Agent":"ScaleRAG-frozen-http-zip-inventory/1.0"})
    with urllib.request.urlopen(req,timeout=70) as resp:
        status=resp.status
        content_range=resp.headers.get("Content-Range")
        if status!=206:
            return {"status":"BLOCKED_NO_HTTP_RANGE","status_code":status,
                "content_range":content_range}
        body=resp.read(1025)
    assert len(body)<=1024
    with RemoteZip(RDF,timeout=100) as z:
        entries=[{"name":f.filename,"compressed_bytes":f.compress_size,
                "uncompressed_bytes":f.file_size}
            for f in z.infolist()]
    return {"status":"RANGE_CONTENTS_LISTED","status_code":status,
       "content_range":content_range,"members":entries}

def main():
    report={"schema":"candidate3-fresh-LargeRDFBench-range-only-index-v1",
        "frozen_protocol_commit":"6a7de564f5de21fa4124a1de0846ca3ad6bc7fd7",
        "graph_source":RDF,"query_source":QUERIES,
        "expected_queries_md5":EXPECTED_QUERY_MD5,
        "future_query_contents_unopened":True,
        "reference_answers_unopened":True,
        "graph_triples_unopened":True}
    try:report["queries_index"]=read_query_listing()
    except Exception as exc:report["queries_error"]=type(exc).__name__+": "+str(exc)[:220]
    try:report["rdf_index"]=try_ranged_listing()
    except Exception as exc:report["rdf_index"]={"status":"BLOCKED",
              "error":type(exc).__name__+": "+str(exc)[:350]}
    (OUT/"report.json").write_text(json.dumps(report,indent=2))
    print("LARGERDF_RANGE_INVENTORY_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("LARGERDF_RANGE_INVENTORY_END",flush=True)
if __name__=="__main__":main()
