#!/usr/bin/env python3
"""Metadata-only access check for an *unopened* third-party SWDF RDF+query pair.

No query bodies, RDF triples or answer labels are read. Enumerated URLs are
published by DICE or RDF-HDT, not invented benchmark evidence. An unavailable
source is a blocked confirmatory gate. Bounded 2MB HTML directory inspection
only; no silent replacement with the previously inspected WatDiv.
"""
import json,urllib.request,urllib.error,re,hashlib,html
from pathlib import Path
OUT=Path("results_candidate3_source_access");OUT.mkdir(exist_ok=True)
SOURCES={
 "real_SPARQL_query_file":"https://raw.githubusercontent.com/dice-group/feasible/master/SWDF-CleanQueries.txt",
 "feasible_original_SWDF_dump":"https://drive.google.com/file/d/0B1tUDhWNTjO-cjBqUG1BZF9RTnM/view?usp=sharing",
 "RDF_HDT_catalogue":"https://www.rdfhdt.org/datasets/",
 "DICE_SWDF_dump_index":"https://hobbitdata.informatik.uni-leipzig.de/benchmarks-data/datasets-dumps/",
 "DICE_SWDF_queries_index":"https://hobbitdata.informatik.uni-leipzig.de/rdf-partitioning/benchmarkQueries/",
 "SWDF_SaGe_2017":"https://sage.ls2n.fr/see/swdf-2017",
}
def metadata(url,catalog=False):
    req=urllib.request.Request(url,headers={
      "User-Agent":"Candidate3-third-party-source-preflight/1.0",
      "Range":"bytes=0-0" if not catalog else "bytes=0-2097151"})
    with urllib.request.urlopen(req,timeout=18) as r:
        status=r.status;content_type=r.headers.get("Content-Type","")
        length=r.headers.get("Content-Length","")
        final=r.url;accepted=r.headers.get("Accept-Ranges","")
        body=r.read(2_000_001 if catalog else 512)
    result={"status":"reachable","http_code":status,
       "content_type":content_type,"advertised_content_length":length,
       "accept_ranges":accepted,
       "resolved_url_host":urllib.request.urlparse(final).hostname if hasattr(urllib.request,'urlparse') else "",
       "read_bytes":len(body)}
    if catalog and "text" in content_type:
        h=body.decode("utf8",errors="replace")
        candidates=re.findall(r'href=["\']([^"\']+)["\']',h,re.I)
        relevant=[html.unescape(v) for v in candidates if
              any(s in v.lower() for s in ("swdf","dogfood","dog-food","hdt",".nt",".rdf"))]
        result["relative_candidate_links"]=relevant[:45]
        result["html_listing_partial"]=len(body)>=2_000_000
    return result
def main():
    result={"schema":"candidate3-external-SWDF-real-log-graph-access-preflight-v1",
      "sources":{},"source_queries_unopened":True,"source_RDF_unopened":True,
      "source_graph_alignment_unverified":True}
    for k,url in SOURCES.items():
        try:result["sources"][k]=metadata(url,catalog=k in
                   ("RDF_HDT_catalogue","DICE_SWDF_dump_index","DICE_SWDF_queries_index"))
        except Exception as exc:
            result["sources"][k]={"status":"blocked",
              "exception":type(exc).__name__,"detail":str(exc)[:400]}
    result["status"]="graph_and_query_candidate_found" if (
        result["sources"]["real_SPARQL_query_file"]["status"]=="reachable" and
        any(result["sources"].get(k,{}).get("status")=="reachable" for k in
          ("feasible_original_SWDF_dump","RDF_HDT_catalogue","DICE_SWDF_dump_index"))
         ) else "missing_external_graph_or_queries"
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("SOURCE_ACCESS_START");print(json.dumps(result,indent=2));print("SOURCE_ACCESS_END")
if __name__=="__main__":main()
