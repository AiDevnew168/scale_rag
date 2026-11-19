#!/usr/bin/env python3
"""Independent December 2017 confirmation of August post-hoc tail hypothesis.

LOCKED beforehand:
- top120 Wikidata predicates from June12-25 2017 organic logs
- observed update ONLY June26-Jul02 2017
- fixed 4 equally weighted shards, hard max 30 predicates/shard
- frozen Mt-KaHyPar KM1 vs up to 12 moved predicates via observed-coaccess swaps
- primary estimand: complete one-shard SPARQL pattern coverage gain on
  predicate-set combinations absent from BOTH historic and observed logs.
- secondary: all requests, historically seen requests, unique novel patterns.
No December requests inform any placement, tuning or filtering of models.
These are SPARQL co-occurrence proxy costs, not NL GraphRAG answer quality.
"""
import json,math,itertools
from collections import Counter
from datetime import datetime
from pathlib import Path
import mtkahypar
import temporal_wikidata as a
import temporal_hypergraph as h
import temporal_refresh as r
import august_confirm as ac

N=120;K=4;SEED=261119
OUT=Path("results_december_novel_confirm");OUT.mkdir(exist_ok=True)
URL=("https://analytics.wikimedia.org/datasets/one-off/wikidata/"
     "sparql_query_logs/2017-12-03_2017-12-30/"
     "2017-12-03_2017-12-30_organic.tsv.gz")
ac.TEST_URL=URL
ac.START=datetime(2017,12,3)

def distinct(rows):
    seen=set();out=[]
    for day,pp in rows:
        if pp not in seen:seen.add(pp);out.append((day,pp))
    return out

def subgroup(test,partitions,methods):
    if not test:return {"n":0}
    metrics={name:r.eval_subset(test,partitions[name]) for name in methods}
    pairs=(("hyper_bounded","hyper_static"),
           ("hyper_bounded","metis_bounded"),
           ("metis_bounded","metis_static"),
           ("hyper_static","metis_static"))
    comparisons={a+"_vs_"+b:r.day_bootstrap(test,partitions[a],partitions[b])
                 for a,b in pairs}
    return {"n":len(test),"methods":metrics,"paired":comparisons}

def main():
    r.quick_test_swap_delta()
    first_month,train_sha=a.load()
    history=[q for q in first_month if q[0]<14]
    observation=[q for q in first_month if 14<=q[0]<21]
    freq=Counter()
    for day,props in history:freq.update(set(props))
    selected=tuple(p for p,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:N])
    train,_=a.prop_stats(history,selected)
    dev,_=a.prop_stats(observation,selected)
    assert len(selected)==N and len(train)>40000 and len(dev)>20000
    metis_static=ac.old_metis(train,selected)
    hyper_static=h.partition_direct(train,N,mtkahypar.Objective.KM1)
    wdev=r.to_weight_matrix(dev,N)
    metis_bounded,mmove=r.refine_swaps(metis_static,wdev,12)
    hyper_bounded,hmove=r.refine_swaps(hyper_static,wdev,12)
    partitions={"metis_static":metis_static,"metis_bounded":metis_bounded,
                "hyper_static":hyper_static,"hyper_bounded":hyper_bounded}
    for name,p in partitions.items():
        assert len(p)==N and max(Counter(p).values())==30
    assert r.optimal_label_moves(metis_static,metis_bounded)<=12
    assert r.optimal_label_moves(hyper_static,hyper_bounded)<=12
    future_raw,future_sha=ac.august_queries()
    test,excluded=a.prop_stats(future_raw,selected)
    assert len(future_raw)>300000 and len(test)>100000
    seen={pp for day,pp in train+dev}
    truly_new=[(day,pp) for day,pp in test if pp not in seen]
    known=[(day,pp) for day,pp in test if pp in seen]
    unique_new=distinct(truly_new)
    assert len(truly_new)>1000 and len(unique_new)>100
    parts={
      "primary_truly_new_request_weighted":truly_new,
      "secondary_unique_truly_new_patterns":unique_new,
      "secondary_seen_patterns":known,
      "secondary_all_requests":test}
    methods=tuple(partitions)
    summaries={name:subgroup(group,partitions,methods)
               for name,group in parts.items()}
    primary=summaries["primary_truly_new_request_weighted"]["paired"]["hyper_bounded_vs_hyper_static"]
    report={"schema":"december-independent-tail-robust-hypergraph-v1",
      "hypothesis_predeclared_before_future_file_download":True,
      "source_test_url":URL,
      "source_test_sha256":future_sha,"source_training_sha256":train_sha,
      "train_period":"June 12-25 2017",
      "observed_feedback_period":"June 26-July 2 2017",
      "future_independent_period":"Dec 3-30 2017",
      "n_raw_future":len(future_raw),"n_eligible_future":len(test),
      "n_train":len(train),"n_observed":len(dev),
      "n_nodes":N,"n_shards":K,"hard_max_nodes_per_shard":30,
      "hard_migration_limit_nodes":12,
      "actual_moved_nodes":{"hyper_bounded":hmove,"metis_bounded":mmove},
      "min_relabelled_moved_nodes":{
         "hyper_bounded":r.optimal_label_moves(hyper_static,hyper_bounded),
         "metis_bounded":r.optimal_label_moves(metis_static,metis_bounded)},
      "subgroups":summaries,
      "primary_gate":{"observed_delta_pp":primary["delta_local_pp"],
         "day_block_ci95_pp":primary["day_block_ci95_pp"],
         "sign_positive_ci95":primary["day_block_ci95_pp"][0]>0},
      "limitations":["Independent December 2017 file, but earlier August subgroup was inspected before locking this gate",
         "Organic SPARQL predicate-set query-span proxy; no natural-language GraphRAG QA",
         "Only queries whose property sets have 2-12 of top120 history-only selected IDs are scored",
         "Same 4 equal-weight predicate-node hard capacities; no bytes or physical latency",
         "Novel means a *new combination* of selected Wikidata predicates, not a new SPARQL intent or natural-language entity",
         "Day bootstrap CI includes only 28 time blocks and may miss temporal confounders",
         "Baseline hypergraph and swap heuristics are established methods, not novel algorithms"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("partitions.json").write_text(json.dumps(partitions,indent=2))
    print("DECEMBER_NOVEL_GATE_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("DECEMBER_NOVEL_GATE_END",flush=True)
if __name__=="__main__":main()
