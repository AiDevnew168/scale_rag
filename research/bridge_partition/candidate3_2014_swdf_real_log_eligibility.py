#!/usr/bin/env python3
"""New bounded 2014 real SWDF HTTP traffic eligibility audit (read-only).

Pre-declared source and stop rules from frozen protocol SHA 50c8582....
Not a source of calibration of any candidate policy. Preserves real timestamp.
The 2014 request log might NOT match DICE FEASIBLE SWDF RDF graph version:
if no graph alignment, only exploratory correctness, NO true time-series claim.
"""
import collections,datetime,hashlib,json,re,urllib.parse,urllib.request
from pathlib import Path
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.term import URIRef
SOURCE="https://raw.githubusercontent.com/AKSW/LSQ/develop/lsq-core/src/test/resources/logs/combined.swdf.log"
SOURCE_SHA="063805ee1d1d80ead68fc1c7d369fadf5a5810b9a61e0d2ac49a70b8db52b3de"
OUT=Path("results_candidate3_SWDF_2014_chronological")
OUT.mkdir(exist_ok=True)
ALLOW={"SelectQuery","Project","BGP","Slice","Distinct","Reduced","OrderBy","OrderCondition"}
DATE=re.compile(r'\[([^]]+)\]\s+"(GET|POST)\s+(.+?)\s+HTTP/[0-9.]+\s*"',re.I)
def structural(query):
    p=prepareQuery(query);nodes=[];triples=[]
    def walk(x):
        if isinstance(x,CompValue):
            nodes.append(x.name)
            if x.name=="BGP":triples.extend(x["triples"])
            for k,v in x.items():
                if k not in ("triples","_vars"):walk(v)
        elif isinstance(x,(tuple,list,set)):
            for v in x:walk(v)
    walk(p.algebra)
    if not nodes or not set(nodes).issubset(ALLOW):return None,"unsupported_algebra"
    if p.algebra.get("datasetClause"):return None,"dataset_clause"
    if not 2<=len(triples)<=6:return None,"not_2_to_6_triple_patterns"
    if not all(isinstance(pred,URIRef) for _,pred,_ in triples):return None,"variable_or_path_predicate"
    preds=tuple(sorted(set(str(p) for _,p,_ in triples)))
    if len(preds)<2:return None,"single_predicate"
    return preds,None

def main():
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"ScaleRAG-Independent-2014-SWDF-Eval/1.0"})
    with urllib.request.urlopen(req,timeout=50) as r:raw=r.read(2_000_000)
    assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    lines=raw.decode("utf8",errors="replace").splitlines()
    exclusion=collections.Counter();valid=[];all_dates=[]
    for line in lines:
        m=DATE.search(line)
        if not m:exclusion["http_log_parse"]+=1;continue
        try:stamp=datetime.datetime.strptime(m.group(1),"%d/%b/%Y:%H:%M:%S %z")
        except ValueError:exclusion["date_parse"]+=1;continue
        all_dates.append(stamp.isoformat())
        if m.group(2).upper()!="GET":
            exclusion["not_get_query"]+=1;continue
        query_string=urllib.parse.urlsplit(m.group(3)).query
        values=urllib.parse.parse_qs(query_string,keep_blank_values=True).get("query",[])
        if len(values)!=1:exclusion["missing_query"]+=1;continue
        query=values[0]
        if not re.search(r'\bSELECT\b',query,re.I):
            exclusion["not_SELECT"]+=1;continue
        try:preds,error=structural(query)
        except Exception as exc:
            exclusion["parse_"+type(exc).__name__]+=1;continue
        if error:
            exclusion[error]+=1;continue
        valid.append({"datetime":stamp.isoformat(),"sha":hashlib.sha256(query.encode()).hexdigest(),
                     "predicate_family":preds})
    unique={x["sha"]:x for x in valid}
    groups={x["predicate_family"] for x in unique.values()}
    sorted_records=sorted(valid,key=lambda r:(r["datetime"],r["sha"]))
    n=len(sorted_records)
    cut1=n//2;cut2=(n*7)//10
    split={"training":sorted_records[:cut1],"calibration":sorted_records[cut1:cut2],
           "test":sorted_records[cut2:]}
    oldsha={x["sha"] for x in split["training"]+split["calibration"]}
    testsha={x["sha"] for x in split["test"]}
    newest_novel=testsha-oldsha
    # A predeclared hard stop: insufficient or duplicate test is BLOCKED.
    eligibility=(len(unique)>=80 and len(testsha)>=20 and len(newest_novel)>=20
        and len({x["predicate_family"] for x in split["test"]})>=20)
    result={"schema":"candidate3-actual-2014-SWDF-timestamp-eligibility-v1",
      "frozen_protocol_commit":"50c8582c2ea7da54f32cc0f5ad2d0f954c3d178d",
      "raw_log_sha256":SOURCE_SHA,"url":SOURCE,
      "raw_http_requests":len(lines),
      "http_requests_with_timestamps":len(all_dates),
      "earliest_timestamp":min(all_dates) if all_dates else None,
      "latest_timestamp":max(all_dates) if all_dates else None,
      "strict_eligible_original_SELECT_occurrences":len(valid),
      "strict_unique_query_texts":len(unique),
      "distinct_eligible_predicate_families":len(groups),
      "exclusions":dict(exclusion),
      "real_temporal_split":{"request_counts":{k:len(v) for k,v in split.items()},
          "unique_text_hash_counts":{k:len({r["sha"] for r in v}) for k,v in split.items()},
          "independent_new_test_text_hashes":len(newest_novel),
          "test_family_count":len({r["predicate_family"] for r in split["test"]}),
          "duplicate_exact_text_between_past_and_test":len(oldsha&testsha)},
      "strict_eligible_count_gate":eligibility,
      "state":"ELIGIBLE_COUNT_ONLY" if eligibility else "BLOCKED_INSUFFICIENT_ELIGIBLE_CHRONOLOGICAL_SPQL",
      "matching_2014_RDF_graph_snapshot":"NOT_VERIFIED",
      "limitations":[
         "Source is a small 2007-line LSQ software test fixture, NOT the complete 2014 SWDF log",
         "Count/metadata only, no SPARQL results, traffic-label tuning or source-based policy optimization",
         "Cross-version 2014 traffic versus external SWDF full RDF dump requires independent matching-snapshot verification",
         "Original 2014 HTTP host may include SERVICE federated queries, filtered out under strict algebra contract",
         "Even if query count passes, no scientific paper acceptance without true matched graph, full answer equality, and real net economics"]}
    (OUT/"report.json").write_text(json.dumps(result,indent=2))
    print("CHRONO_SWDF_ELIGIBILITY_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("CHRONO_SWDF_ELIGIBILITY_END",flush=True)
if __name__=="__main__":main()
