#!/usr/bin/env python3
"""Temporal exact-hyperedge placement comparison using identical real source.

This is a standard Mt-KaHyPar KM1 baseline, not an original algorithm.
Workload obtained exclusively from 14 earliest days, 7 final days scored.
"""
import itertools,json,math,random
from collections import Counter
from pathlib import Path
import mtkahypar
import temporal_wikidata as base
SEED=base.SEED
OUT=Path("results_temporal_hg");OUT.mkdir(exist_ok=True)
K=4
def partition_direct(train, n, objective):
    counts=Counter(q for _,q in train)
    edges=[tuple(x) for x in counts]
    weights=[counts[x] for x in edges]
    assert edges and all(len(x)>1 for x in edges)
    mt=mtkahypar.initialize(1)
    ctx=mt.context_from_preset(mtkahypar.PresetType.DEFAULT)
    ctx.set_partitioning_parameters(K,0.0,objective)
    ctx.logging=False
    mtkahypar.set_seed(SEED)
    hg=mt.create_hypergraph(ctx,n,len(edges),[list(p) for p in edges],
                            [1]*n,weights)
    mtkahypar.set_seed(SEED)
    res=hg.partition(ctx)
    labels=[int(res.block_id(i)) for i in range(n)]
    assert max(Counter(labels).values())<=math.ceil(n/K)
    return labels
def main():
    data,sha=base.load()
    train_raw=[x for x in data if x[0]<14]
    test_raw=[x for x in data if x[0]>=21]
    freq=Counter()
    for _,q in train_raw:freq.update(q)
    selected=tuple(p for p,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:120])
    train,_=base.prop_stats(train_raw,selected)
    test,_=base.prop_stats(test_raw,selected)
    co=Counter()
    for _,q in train:co.update(itertools.combinations(q,2))
    metis=base.balanced_metis(selected,co)
    popularity=[(i*K)//len(selected) for i in range(len(selected))]
    direct=partition_direct(train,len(selected),mtkahypar.Objective.KM1)
    cut=partition_direct(train,len(selected),mtkahypar.Objective.CUT)
    methods={"popularity":popularity,"clique_METIS":metis,"direct_KM1":direct,"direct_CUT":cut}
    report={"schema":"real-timestamped-direct-hypergraph-strong-baseline-v1",
       "source_sha256":sha,"train_q":len(train),"test_q":len(test),
       "metrics":{k:base.score(test,k,p) for k,p in methods.items()},
       "paired":{a:base.paired_day_ci(test,methods[a],metis)
                 for a in ("direct_KM1","direct_CUT")},
       "constraints":{"k":K,"node_weight":"equal predicate ID","imbalance":0,
                "mtkahypar_version":"1.7.1","same_input":"first 14 day train"},
       "limitations":["Prior test set already inspected with METIS: hypergraph comparison is exploratory",
           "Exact hyperedge objective is mature existing method; not our novel solver",
           "Predicate ID equal-size surrogate not Wikidata physical shard bytes",
           "No full RAG answers or actual network latency"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("TEMPORAL_HG_START");print(json.dumps(report,indent=2));print("TEMPORAL_HG_END")
if __name__=="__main__":main()
