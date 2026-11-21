#!/usr/bin/env python3
"""Only source metadata for an independent 2026 real RDF/query benchmark.

No graph or SPARQL result payload is read. Fail closed for SSL/network and
oversized assets. Eligibility remains BLOCKED pending full source matching.
"""
import hashlib,json,urllib.request,datetime
from pathlib import Path

URL="https://zenodo.org/api/records/22140177"
OUT=Path("results_candidate3_external_largeRDF_preflight");OUT.mkdir(exist_ok=True)
def main():
    report={"schema":"candidate3-fresh-LargeRDFBench-metadata-only-v1",
      "predeclared_protocol_commit":"6a7de564f5de21fa4124a1de0846ca3ad6bc7fd7",
      "metadata_url":URL,"state":"BLOCKED_UNTIL_SOURCE_AND_MATCHING_QUERIES",
      "no_test_query_outputs_inspected":True,"inventory":[]}
    try:
        req=urllib.request.Request(URL,headers={"Accept":"application/json",
          "User-Agent":"ScaleRAG-frozen-metadata-only-science/1.0"})
        with urllib.request.urlopen(req,timeout=45) as response:
            raw=response.read(3_000_001)
        assert len(raw)<=3_000_000
        d=json.loads(raw)
        report["metadata_sha256"]=hashlib.sha256(raw).hexdigest()
        report["record_id"]=d.get("id")
        report["doi"]=d.get("doi")
        report["title"]=d.get("metadata",{}).get("title")
        report["version"]=d.get("metadata",{}).get("version")
        for item in d.get("files",[]):
            report["inventory"].append({
              "key":item.get("key"),"size_bytes":item.get("size"),
              "checksum":item.get("checksum"),
              "url":item.get("links",{}).get("self"),
              "type":item.get("mimetype")})
        report["state"]="METADATA_AVAILABLE_FULL_DATA_AND_QUERY_ALIGNMENT_NOT_CHECKED"
    except Exception as e:
        report["network_error"]=type(e).__name__+": "+str(e)[:300]
    (OUT/"report.json").write_text(json.dumps(report,indent=2))
    print("LARGERDF_METADATA_START",flush=True);print(json.dumps(report,indent=2),flush=True)
    print("LARGERDF_METADATA_END",flush=True)
if __name__=="__main__":main()
