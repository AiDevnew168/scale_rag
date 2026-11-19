#!/usr/bin/env python3
"""Diagnostic future-label oracle for one balanced page swap (never deployable).

Find BEST possible one-swap placement on unseen target queries to determine
whether the inability to predict a useful migration, rather than absence of
any useful local move, limits the practical online swap heuristic.
Gold unseen queries used ONLY by this explicitly labeled oracle scorer.
Same underlying real TopoGraphRAG documents, no direct RAG runtime.
"""
import json, math, random, os, itertools
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pilot
from online_adaptation import online_refine, mean_span, test_stats, bootstrap
MODE=os.environ.get("ONLINE_SOURCE","bridge_chain")
TARGET="synthesis" if MODE=="bridge_chain" else "bridge_chain"
OUT=Path("results_swap_oracle_"+MODE);OUT.mkdir(exist_ok=True)
SEED=310119

def complete(part,q):
    return len({part[p] for p in pilot.pages(q)})==1

def oracle_one_swap(part,qs):
    """Exact best one two-page swap: complete-local query count, no multi-swap claim."""
    initial_score=sum(complete(part,q) for q in qs)
    best=(initial_score,None)
    n=len(part)
    pp=[pilot.pages(q) for q in qs]
    for i in range(n):
        for j in range(i+1,n):
            if part[i]==part[j]:continue
            part[i],part[j]=part[j],part[i]
            score=sum(len({part[p] for p in nodes})==1 for nodes in pp)
            part[i],part[j]=part[j],part[i]
            if score>best[0]:best=(score,(i,j))
    updated=list(part)
    if best[1] is not None:
        i,j=best[1];updated[i],updated[j]=updated[j],updated[i]
    return updated,best[0]-initial_score

def main():
    allq=pilot.download("annotations/benchmark.json")
    manifest=pilot.download("manifest.json")
    ns={int(d["doc_id"]):len(d["files"]["page_images"]) for d in manifest["documents"]}
    by=defaultdict(list)
    for q in allq:
        pp=pilot.pages(q);d=int(q["doc_id"])
        if len(pp)>=2 and 0<=min(pp) and max(pp)<ns[d]:by[d].append(q)
    rows=[];docs=[];eligible=Counter()
    for d in sorted(by):
        n=ns[d]
        if not 20<=n<=39:continue
        hist=[q for q in by[d] if q["question_type"]==MODE]
        target=[q for q in by[d] if q["question_type"]==TARGET]
        if len(hist)<2 or len(target)<4:continue
        rng=random.Random(SEED+d);rng.shuffle(target)
        seen=target[:max(2,len(target)//2)]
        future=target[max(2,len(target)//2):]
        if len(future)<2:continue
        part=pilot.metis_pages(n,4,hist,400)
        adapted,moves=online_refine(part,hist,seen,int(.1*n))
        oracle,gain=oracle_one_swap(part,future)
        assert max(Counter(oracle).values())<=math.ceil(n/4)
        assert gain>=0
        eligible["oracle_positive_docs"]+=int(gain>0)
        docs.append({"doc_id":d,"n_pages":n,"n_future":len(future),
            "train_query_n":len(hist),"observed_query_n":len(seen),
            "oracle_extra_local_queries":gain,"adaptation_page_moves":moves})
        for q in future:
            pp=pilot.pages(q)
            rows.append({"doc_id":d,"qid":q.get("mh_id") or q.get("sq_id"),
              "static":len({part[p] for p in pp}),
              "actual_feedback_adaptation":len({adapted[p] for p in pp}),
              "future_oracle_one_swap":len({oracle[p] for p in pp})})
    if len(docs)<12 or len(rows)<40:raise RuntimeError(f"Insufficient eligible cases {len(docs)} docs {len(rows)} queries")
    report={"schema":"bridge-one-swap-oracle-diagnostic-v1","scenario":MODE+"_to_"+TARGET,
      "n_docs":len(docs),"n_future_queries":len(rows),
      "oracle_positive_docs":eligible["oracle_positive_docs"],
      "means":{m:test_stats(rows,m) for m in ("static","actual_feedback_adaptation","future_oracle_one_swap")},
      "paired":{"oracle_vs_static":bootstrap(rows,"future_oracle_one_swap","static"),
       "actual_vs_static":bootstrap(rows,"actual_feedback_adaptation","static"),
       "oracle_vs_actual":bootstrap(rows,"future_oracle_one_swap","actual_feedback_adaptation")},
      "cautions":["Future GOLD used directly to optimize oracle one swap: diagnostic headroom ONLY, not a deployable algorithm",
       "Exact maximum is only over zero or one cross-shard two-page swaps, NOT all possible <=10% migration moves",
       "Same document benchmark repeatedly analyzed, exploratory intervals only",
       "This is a page-span proxy, no real retrieval, memory bytes or network latency"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_doc.json").write_text(json.dumps(docs,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
    print("SWAP_ORACLE_START");print(json.dumps(report,indent=2));print("SWAP_ORACLE_END")
if __name__=="__main__":main()
