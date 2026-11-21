#!/usr/bin/env python3
"""Source eligibility preflight for *genuine* cross-domain LSQ2 query logs.

Only a bounded 200-query sample per source. NO model selection, tuning,
performance or train/test evaluation. Source might be unavailable; fail closed.
Do not treat this preflight as prospective benchmark confirmation.
"""
import hashlib,json,urllib.parse,urllib.request,datetime
from pathlib import Path
from collections import Counter

OUT=Path("results_candidate3_LSQ_preflight")
OUT.mkdir(exist_ok=True)
ENDPOINT="https://lsq.aksw.org/sparql"
PROFILES={
 "dbpedia":"PREFIX lsqv: <http://lsq.aksw.org/vocab#> SELECT DISTINCT ?text FROM <http://lsq.aksw.org/dbpedia> WHERE { ?q lsqv:text ?text } LIMIT 200",
 "swdf_with_timestamp":"""PREFIX lsqv: <http://lsq.aksw.org/vocab#>
 PREFIX prov: <http://www.w3.org/ns/prov#>
 SELECT ?text ?stamp FROM <http://lsq.aksw.org/swdf>
 WHERE { ?q lsqv:text ?text . ?q lsqv:hasRemoteExec ?re . ?re prov:atTime ?stamp }
 LIMIT 200"""
}
def one(name,query):
    params=urllib.parse.urlencode({"query":query,"format":"application/sparql-results+json"})
    full=ENDPOINT+"?"+params
    req=urllib.request.Request(full,headers={
        "Accept":"application/sparql-results+json",
        "User-Agent":"ScaleRAG-research-source-eligibility-audit/1.0"})
    with urllib.request.urlopen(req,timeout=22) as response:
        raw=response.read(4_000_001)
        assert len(raw)<=4_000_000, "Result size cap"
        content_type=response.headers.get("Content-Type","")
    parsed=json.loads(raw)
    data=parsed.get("results",{}).get("bindings",[])
    texts=[r.get("text",{}).get("value","") for r in data]
    stamps=[r.get("stamp",{}).get("value") for r in data if "stamp" in r]
    assert all(isinstance(s,str) for s in texts)
    return {"status":"available","result_count":len(data),
        "distinct_exact_query_texts":len(set(texts)),
        "first200_sha256":hashlib.sha256(raw).hexdigest(),
        "mime_type":content_type,
        "timestamp_count":len(stamps),"first_timestamp":stamps[0] if stamps else None,
        "last_timestamp":stamps[-1] if stamps else None,
        "contains_SELECT":sum("SELECT" in t.upper() for t in texts),
        "contains_predicate_IRIs":sum("http://" in t or "https://" in t for t in texts),
        "sample_query_length_range":[min(map(len,texts)),max(map(len,texts))] if texts else None,
        "not_actual_random_sample":True,
        "query_texts_not_saved_to_logs":True}
def main():
    x={"schema":"candidate3-cross-domain-LSQ2-raw-SPARQL-source-preflight-v1",
       "endpoint":ENDPOINT,"sources":{},
       "limitations":[
         "Bounded unrandomized first 200; no validity inference on the full query logs",
         "No initial RDF graph or matching snapshot verified",
         "No adaptation, baseline, F1, SPARQL answer checks, time-series splits or economic measurements",
         "No future query samples observed for algorithm selection",
         "An unavailable endpoint is a BLOCKER, not evidence of no data"]}
    for name,query in PROFILES.items():
        try:x["sources"][name]=one(name,query)
        except Exception as exc:
            x["sources"][name]={"status":"blocked","reason":type(exc).__name__+": "+str(exc)[:450]}
    x["status"]="usable_bounded_source" if all(v["status"]=="available" and v["result_count"]>10
        for v in x["sources"].values()) else "blocked_or_partial"
    OUT.joinpath("report.json").write_text(json.dumps(x,indent=2))
    print("LSQ_PREFLIGHT_START",flush=True);print(json.dumps(x,indent=2),flush=True)
    print("LSQ_PREFLIGHT_END",flush=True)
if __name__=="__main__":main()
