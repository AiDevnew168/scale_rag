#!/usr/bin/env python3
"""Frozen 2017 June placement, prospective *different interval* July-Aug query logs.

All model selection, top120 node selection, hypergraph construction ONLY
uses June12–June25 training. July10-Aug06 traces are an independent later
source interval, never used for tuning, node choice or placement.
"""
import csv,gzip,io,itertools,json,hashlib,urllib.request,math
from pathlib import Path
from collections import Counter
from datetime import datetime
import temporal_wikidata as a
import temporal_hypergraph as h
import mtkahypar
TOP=120;K=4
URL="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/2017-07-10_2017-08-06/2017-07-10_2017-08-06_organic.tsv.gz"
OUT=Path("results_temporal_next_month");OUT.mkdir(exist_ok=True)
START=datetime(2017,7,10)
def nextmonth():
    b=urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":"AcademicWorkloadAudit/1.0"}),timeout=120).read()
    from urllib.parse import unquote_plus
    result=[]
    for row in csv.DictReader(io.StringIO(gzip.decompress(b).decode("utf8",errors="replace")),delimiter="\t"):
        try:
            date=datetime.strptime(row["timestamp"][:19],"%Y-%m-%d %H:%M:%S")
            day=(date-START).days
        except(ValueError,KeyError):continue
        if not 0<=day<28:continue
        props=tuple(sorted(set(a.PATT.findall(unquote_plus(row["anonymizedQuery"])))))
        result.append((day,props))
    print("MONTH2_SHA256",hashlib.sha256(b).hexdigest(),"ORIGINAL_REQUESTS",len(result),flush=True)
    return result,hashlib.sha256(b).hexdigest()
def main():
    all_june, june_sha=a.load()
    train_raw=[r for r in all_june if r[0]<14]
    freq=Counter()
    for _,q in train_raw:freq.update(q)
    selected=tuple(p for p,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:TOP])
    train,_=a.prop_stats(train_raw,selected)
    test_raw,month2_sha=nextmonth()
    test,excluded=a.prop_stats(test_raw,selected)
    assert len(test)>=1000,len(test)
    co=Counter()
    for _,q in train:co.update(itertools.combinations(q,2))
    metis=a.balanced_metis(selected,co)
    pop=[i*K//len(selected) for i in range(len(selected))]
    hyper=h.partition_direct(train,len(selected),mtkahypar.Objective.KM1)
    variants={"popularity":pop,"historical_clique_METIS":metis,"direct_hypergraph_KM1":hyper}
    metrics={k:a.score(test,k,p) for k,p in variants.items()}
    paired={
      "KM1_vs_METIS":a.paired_day_ci(test,hyper,metis),
      "KM1_vs_popularity":a.paired_day_ci(test,hyper,pop),
      "METIS_vs_popularity":a.paired_day_ci(test,metis,pop)}
    report={"schema":"month-ahead-independent-real-wikidata-log-v1",
      "train_period":"June 12-25 2017","test_period":"July 10-August 6 2017",
      "source_train_sha256":june_sha,"source_test_sha256":month2_sha,
      "test_url":URL,"n_original_test_queries":len(test_raw),
      "n_eligible_test_queries":len(test),"n_selected_properties":TOP,
      "original_query_exclusion":excluded,"metrics":metrics,"paired":paired,
      "caveats":["Genuine chronologically later test interval and file unseen in previous partition optimization",
        "This remains a predicate-ID coaccess query-span proxy, NOT physical KG shard latency",
        "Evaluation only covers queries with 2–12 of the top 120 TRAIN predicates",
        "Hypergraph KM1 and METIS are prior established methods",
        "No empirical RAG answer quality, direct triple join execution or true property byte weights"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("MONTH_AHEAD_RESULT_START")
    print(json.dumps(report,indent=2))
    print("MONTH_AHEAD_RESULT_END")
if __name__=="__main__":main()
