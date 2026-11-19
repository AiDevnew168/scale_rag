#!/usr/bin/env python3
"""Train-only minimax portfolio selection over EXISTING Mt-KaHyPar hypergraph partitions.

Exploratory robustness control, not a proposed novel graph algorithm.
Source questions and gold TRAIN pages are used for placement; test gold ONLY scores outcomes.
"""
import json, math, os, random, sys
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pilot
import direct_hypergraph as dh

SCENARIO=dh.MODE
WEIGHTS=(0,25,75,150,400,1000)
OUT=Path("results_portfolio_"+SCENARIO);OUT.mkdir(exist_ok=True)

def train_mean(part,train):
    return sum(len({part[p] for p in pilot.pages(q)})-1 for q in train)/len(train)
def adjacency(part):
    return sum(part[p]!=part[p+1] for p in range(len(part)-1))/max(1,len(part)-1)

def pick_candidates(n,train):
    # Strictly train-only: construct partitions at predeclared weights, then
    # choose Pareto minimax regret between query hypergraph span and adjacency.
    parts={w:dh.hypergraph_partition(n,train,4,query_weight=w) for w in WEIGHTS}
    means={w:train_mean(p,train) for w,p in parts.items()}
    adjs={w:adjacency(p) for w,p in parts.items()}
    mlo,mhi=min(means.values()),max(means.values())
    alo,ahi=min(adjs.values()),max(adjs.values())
    def rtrain(w):return (means[w]-mlo)/(mhi-mlo+1e-9)
    def radj(w):return (adjs[w]-alo)/(ahi-alo+1e-9)
    robust=min(WEIGHTS,key=lambda w:(max(rtrain(w),radj(w)),rtrain(w)+radj(w),w))
    # Exact TRAIN-only oracle for hyperedge span - likely overfits the past.
    best_train=min(WEIGHTS,key=lambda w:(means[w],w))
    # Explicit cheap fixed regularization, not selected from test.
    return parts,robust,best_train,{"chosen_robust_weight":robust,
      "best_train_weight":best_train,"train_cost_at_robust":means[robust],
      "train_cost_at_400":means[400],"adj_cost_at_robust":adjs[robust],
      "adj_cost_at_400":adjs[400]}

def main():
    qs=pilot.download("annotations/benchmark.json")
    manifest=pilot.download("manifest.json")
    npages={int(d["doc_id"]):len(d["files"]["page_images"]) for d in manifest["documents"]}
    cand=defaultdict(list)
    for q in qs:
        pp=pilot.pages(q)
        if len(pp)<2:continue
        doc=int(q["doc_id"])
        if min(pp)<0 or max(pp)>=npages[doc]:continue
        cand[doc].append(q)
    rng=random.Random(pilot.SEED)
    rows=[];decisions=[]
    for doc in sorted(cand):
        n=npages[doc]
        if n<8:continue
        split=dh.split_workload(cand[doc],rng)
        if split is None:continue
        train,test=split
        parts,robust,best_train,detail=pick_candidates(n,train)
        baseline_m=pilot.metis_pages(n,4,train,400)
        baseline_s=pilot.metis_pages(n,4,train,0)
        for name,part in {**{str(w):p for w,p in parts.items()},"metis":baseline_m,"structure":baseline_s}.items():
            assert max(Counter(part).values())<=math.ceil(n/4),(doc,name)
        decisions.append({"doc_id":doc,"n_train":len(train),"n_test":len(test),**detail})
        for q in test:
            pp=pilot.pages(q)
            row={"doc_id":doc,"qid":q.get("mh_id") or q.get("sq_id"),"type":q["question_type"],
                 "mtk_400":len({parts[400][p] for p in pp}),
                 "mtk_minimax":len({parts[robust][p] for p in pp}),
                 "mtk_train_oracle":len({parts[best_train][p] for p in pp}),
                 "metis_clique":len({baseline_m[p] for p in pp}),
                 "metis_structure":len({baseline_s[p] for p in pp})}
            rows.append(row)
    assert len(rows)>=200 and len(decisions)>=80
    methods=("metis_structure","metis_clique","mtk_400","mtk_minimax","mtk_train_oracle")
    summary={m:dh.mean_metrics(rows,m) for m in methods}
    paired={key:dh.ci(rows,*pair) for key,pair in {
        "minimax_vs_mtk400":("mtk_minimax","mtk_400"),
        "minimax_vs_clique_METIS":("mtk_minimax","metis_clique"),
        "minimax_vs_structure_METIS":("mtk_minimax","metis_structure"),
        "minimax_vs_train_best":("mtk_minimax","mtk_train_oracle")}.items()}
    report={"schema":"train-only-hypergraph-portfolio-v1",
      "scenario":SCENARIO,"n_queries":len(rows),"n_docs":len(decisions),
      "predeclared_weights":WEIGHTS,"objective":"minimax normalized regret, train support span versus adjacent-page edge cut",
      "method_metrics":summary,"paired":paired,
      "chosen_robust_weight_frequency":dict(Counter(str(d["chosen_robust_weight"]) for d in decisions)),
      "chosen_best_train_weight_frequency":dict(Counter(str(d["best_train_weight"]) for d in decisions)),
      "cautions":["Portfolio is a known conservative selection heuristic, not an original optimization method",
          "All candidate portfolios and selected candidate use TRAIN labels only; test labels only for scoring",
          "Same documents in train and test; only question IDs disjoint",
          "Only source page placement, not actual RAG or byte-memory latency",
          "Selection based on normalized regret is a heuristic; its performance on held-out queries is exploratory",
          "Predeclared 6 hyperedge weights and baseline; repeat experiments required for a paper"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
    OUT.joinpath("decisions.json").write_text(json.dumps(decisions,indent=2))
    print("ROBUST_PORTFOLIO_RESULT_START")
    print(json.dumps(report,indent=2))
    print("ROBUST_PORTFOLIO_RESULT_END")
if __name__=="__main__":main()
