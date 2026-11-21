#!/usr/bin/env python3
"""Five held-out *query pattern-family-disjoint* folds on official WatDiv10M.

Source: official 10.9M N-Triples, warmup 12.1k eligible queries, 121
predicate combinations. Previous five nominal test files repeat all warmup
queries. This script therefore constructs 5 fixed SHA order folds *by
predicate-set identity*, not by exact query text or occurrence. Every test
pattern is strictly absent from that fold's training set, by construction.
This is an exploratory cross-pattern generalization test, NOT real-time data
drift, independent dataset replications, nor SPARQL execution.
"""
import hashlib, io, json, random
from collections import Counter,defaultdict
from pathlib import Path
import candidate3_official_watdiv_byte_transfer as wd
SEED=20261121
K=5
OUT=Path("results_candidate3_watdiv_pattern_disjoint")
OUT.mkdir(exist_ok=True)

def report_metric(rows,part):
    if not rows:return {"n":0,"touches":0,"local":None}
    z=[wd.span(part,r["pattern"]) for r in rows]
    return {"n":len(z),"touches":sum(x-1 for x in z),
      "local":round(100*sum(x==1 for x in z)/len(z),4)}

def main():
    graph=wd.grab(wd.DATA,85*1024*1024,wd.HASH_GRAPH)
    weights,physical=wd.physical_size_table(graph)
    del graph
    data=wd.parse_workloads(wd.grab(wd.QUERIES,40*1024*1024,wd.HASH_QUERY))
    original=data["watdiv-stress-100/warmup.sparql"]["records"]
    rows=[r for r in original if len(r["pattern"])>=2 and
         all(p in weights for p in r["pattern"])]
    patterns=sorted({r["pattern"] for r in rows})
    assert len(patterns)>=50 and len(rows)>1000
    pattern_order=sorted(patterns,key=lambda p:hashlib.sha256(
        ("locked-pattern-fold-v1:"+str(SEED)+":"+json.dumps(p)).encode()).hexdigest())
    folds={p:i%K for i,p in enumerate(pattern_order)}
    static,route,loads,cap=wd.byte_layout(weights)
    assert max(loads)<=cap
    out=[]
    savings={"head_local":[],"all_touches":[],"gain_per_byte":[]}
    holdout_patterns_each=[]
    for k in range(K):
        observed=[r for r in rows if folds[r["pattern"]]!=k]
        future=[r for r in rows if folds[r["pattern"]]==k]
        train_patterns={r["pattern"] for r in observed}
        fut_patterns={r["pattern"] for r in future}
        train_hash={r["text_hash"] for r in observed}
        future_hash={r["text_hash"] for r in future}
        assert not(train_patterns&fut_patterns)
        assert not(train_hash&future_hash)
        methods,stats=wd.candidate(route,weights,loads,cap,observed)
        base=wd.metric(future,route)
        results={}
        for key,c in methods.items():
            chosen=c["placement"];score=wd.metric(future,chosen)
            moved=c["decision"]["move_bytes"]
            saved=base["extra_shard_touches"]-score["extra_shard_touches"]
            gain_by_pattern={}
            for pattern in sorted(fut_patterns):
                ct=sum(1 for row in future if row["pattern"]==pattern)
                gain_by_pattern[str(pattern)]=ct*(wd.span(route,pattern)-wd.span(chosen,pattern))
            assert sum(gain_by_pattern.values())==saved
            # Lower-bound ideal serial critical-path saved ms per removed
            # touch needed to pay byte transfer at theoretical 100 Mbit/s.
            migration_ms_100mbps=moved*8/(100*1000)
            needed=(migration_ms_100mbps/saved) if saved>0 else None
            results[key]={"pair":c["decision"]["pair"],
                "physical_predicate_payload_move_bytes":moved,
                "observed_train_touches_saved":c["decision"].get("observed_touches_saved",0),
                "heldout":score,"heldout_extra_shard_touches_saved":saved,
                "ideal_100Mbps_transfer_ms":round(migration_ms_100mbps,4),
                "minimum_serial_critical_path_ms_per_saved_touch_for_break_even_at_100Mbps":
                    round(needed,4) if needed is not None else None,
                "pattern_cluster_saved_touches":gain_by_pattern}
            savings[key].append(saved)
        holdout_patterns_each.append(len(fut_patterns))
        out.append({"fold":k,"n_train":len(observed),"n_test":len(future),
          "n_train_pattern_families":len(train_patterns),
          "n_test_pattern_families":len(fut_patterns),
          "overlap_exact_query_text_hash":len(train_hash&future_hash),
          "overlap_pattern_family":len(train_patterns&fut_patterns),
          "static":base,"candidate_search":stats,"results":results})
    assert sum(x["n_test"] for x in out)==len(rows)
    summary={}
    for name,v in savings.items():
        patterns_by_gain=[]
        for fold in out:
            patterns_by_gain.extend(list(fold["results"][name]["pattern_cluster_saved_touches"].values()))
        assert len(patterns_by_gain)==len(patterns)
        r=random.Random(SEED)
        sims=sorted(sum(patterns_by_gain[r.randrange(len(patterns_by_gain))]
                      for _ in patterns_by_gain) for __ in range(4000))
        summary[name]={"total_saved_extra_touches_all_folds":sum(v),
           "positive_folds":sum(x>0 for x in v),"negative_folds":sum(x<0 for x in v),
           "zero_folds":sum(x==0 for x in v),
           "pattern_cluster_bootstrap_95_total_saved_touches":[sims[99],sims[3899]],
           "physical_migration_total_bytes_all_folds":sum(
                fold["results"][name]["physical_predicate_payload_move_bytes"] for fold in out),
           "mean_touch_saving_per_heldout_query":round(sum(v)/len(rows),7)}
    result={"schema":"candidate3-original-WatDiv10M-fivefold-exact-pattern-disjoint-v1",
       "source":{"graph":wd.ROOT+wd.DATA,"graph_sha256":wd.HASH_GRAPH,
                 "stress_archive":wd.ROOT+wd.QUERIES,"stress_sha256":wd.HASH_QUERY},
       "fixed_grouping":"SHA256 of predicate-set identity sorted by fixed seed "+str(SEED),
       "n_folds":K,"n_total_eligible_query_occurrences":len(rows),
       "n_exact_distinct_texts":len({x["text_hash"] for x in rows}),
       "n_pattern_families":len(patterns),
       "physical":physical,
       "byte_cap":cap,"physical_shards_analytical_bytes":loads,
       "n_fragmented_predicates":sum(len(v)>1 for v in route.values()),
       "frozen_baseline":"greedy weight-only physical byte-balanced predicate placement, no workload tuning",
       "folds":out,"summary":summary,
       "limitations":[
         "The same WatDiv benchmark corpus is inspected again; exploratory 5-fold cross-validation, not independent confirmation",
         "Training/test disjoint by distinct predicate combination; repeated exact query texts across former warmup/test files are not used as new samples",
         "All 5 folds are partitions of one synthetic workload generator, not independent organic traffic shifts",
         "Physical RDF predicate raw bytes counted exactly; fragmented placement is analytical not materialized",
         "No real SPARQL execution, physical index migration, production latency or WISE/WASP implementations",
         "Break-even is conditional on serialized nonparallel extra shard-touch latency and ideal 100Mbps data transport only",
         "No true economic profitability or new algorithm claimed"]}
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    brief=dict(result)
    brief["folds"]=[{k:v for k,v in fold.items() if k!="results"}|
        {"results":{name:{k:v for k,v in data.items() if k!="pattern_cluster_saved_touches"}
                    for name,data in fold["results"].items()}} for fold in out]
    print("PATTERN_FOLD_GATE_START");print(json.dumps(brief,indent=2));print("PATTERN_FOLD_GATE_END")
if __name__=="__main__":main()
