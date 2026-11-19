#!/usr/bin/env python3
"""Chronologically held-out Wikidata 2017 workload-placement refresh.

Days 0:14 are historical train. Days 14:21 are NEW OBSERVED traffic.
Days 21:28 are completely unseen future test requests. Partition nodes
are fixed top-120 predicates selected exclusively on historical train days.

Page/graph RAG accuracy is NOT measured; equal-weight predicate placement
proxy for future cross-partition SPARQL query span, no physical latency.
"""
import itertools,json,math,random
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import temporal_wikidata as base

OUT=Path("results_temporal_refresh");OUT.mkdir(exist_ok=True)
SEED=261119;K=4;N=120
def to_weight_matrix(records,n,decay_half_life=None,ref_day=20):
    W=np.zeros((n,n),dtype=float)
    for day,pp in records:
        w=1. if decay_half_life is None else 2.**(-(ref_day-day)/decay_half_life)
        for i,j in itertools.combinations(pp,2):
            W[i,j]+=w;W[j,i]+=w
    return W

def metis_from_matrix(W,items):
    co=Counter()
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            if W[i,j]>0:
                co[(i,j)]=max(1,int(round(W[i,j]))) # same relative weight as original temporal baseline
    return base.balanced_metis(items,co)

def optimal_label_moves(a,b):
    return min(sum(u!=p[v] for u,v in zip(a,b))
               for p in itertools.permutations(range(K)))

def refine_swaps(initial,W,budget,penalty=0.0):
    """Standard observed-workload improving balanced two-vertex swaps.

    Hamming moves <= 10% n. All decisions use train/dev pair frequencies ONLY.
    Partition capacities preserved exactly by each swap. No test references.
    """
    p=list(initial)
    moved=0
    for iteration in range(budget//2):
        byblock=np.stack([W[:,np.asarray(p)==b].sum(axis=1)
                          for b in range(K)],axis=1)
        opts=[]
        for i in range(len(p)):
            ai=p[i]
            for j in range(i+1,len(p)):
                aj=p[j]
                if ai==aj:continue
                # Exact delta in weighted pairwise cut on swap of i,j.
                delta=(byblock[i,ai]-byblock[i,aj] +
                       byblock[j,aj]-byblock[j,ai] + 2*W[i,j])
                if delta < -1e-6:
                    opts.append((delta,i,j))
        if not opts:break
        delta,i,j=min(opts)
        p[i],p[j]=p[j],p[i]
        moved+=2
    assert Counter(initial)==Counter(p)
    assert moved<=budget
    return p,moved

def quick_test_swap_delta():
    rng=random.Random(SEED)
    W=np.asarray([[rng.randrange(4) for j in range(12)] for i in range(12)],dtype=float)
    W=(W+W.T)/2;np.fill_diagonal(W,0)
    p=[i%4 for i in range(12)]
    for i in range(12):
        for j in range(i+1,12):
            if p[i]==p[j]:continue
            B=np.stack([W[:,np.asarray(p)==b].sum(axis=1) for b in range(4)],axis=1)
            delta=B[i,p[i]]-B[i,p[j]]+B[j,p[j]]-B[j,p[i]]+2*W[i,j]
            def cost(part):
                return sum(W[a,b] for a in range(12) for b in range(a+1,12)
                           if part[a]!=part[b])
            q=list(p);q[i],q[j]=q[j],q[i]
            assert abs((cost(q)-cost(p))-delta)<1e-6,(i,j,delta)
    print("SWAP_DELTA_UNITTEST_PASS",flush=True)

def eval_subset(test,part):
    rows=[(day,len({part[x] for x in pp})) for day,pp in test]
    return {"n":len(rows),"local_pct":round(100*sum(span==1 for _,span in rows)/len(rows),3),
            "mean_shards":round(float(np.mean([s for _,s in rows])),5),
            "p90":float(np.percentile([s for _,s in rows],90)),
            "daily_local_pct":{str(d):round(100*sum(dd==d and s==1 for dd,s in rows)/
                   sum(dd==d for dd,s in rows),3) for d in sorted({d for d,_ in rows})}}

def day_bootstrap(test,first,second):
    dates=sorted({d for d,_ in test})
    stats={d:[0,0] for d in dates}
    for day,pp in test:
        stats[day][1]+=1
        stats[day][0]+=int(len({first[x] for x in pp})==1)-int(len({second[x] for x in pp})==1)
    obs=100*sum(v[0] for v in stats.values())/sum(v[1] for v in stats.values())
    rng=random.Random(SEED)
    sims=[]
    for _ in range(6000):
        selected=[stats[rng.choice(dates)] for _ in dates]
        sims.append(100*sum(v[0] for v in selected)/sum(v[1] for v in selected))
    return {"delta_local_pp":round(float(obs),3),
      "day_block_ci95_pp":[round(float(v),3) for v in np.percentile(sims,[2.5,97.5])]}

def main():
    quick_test_swap_delta()
    raw,sha=base.load()
    train_raw=[x for x in raw if x[0]<14]
    dev_raw=[x for x in raw if 14<=x[0]<21]
    test_raw=[x for x in raw if x[0]>=21]
    freq=Counter()
    for day,pp in train_raw:freq.update(set(pp))
    selected=tuple(p for p,v in sorted(freq.items(),
                             key=lambda x:(-x[1],x[0]))[:N])
    assert len(selected)==N
    train,st=base.prop_stats(train_raw,selected)
    dev,sd=base.prop_stats(dev_raw,selected)
    test,se=base.prop_stats(test_raw,selected)
    assert len(test)>20000 and min(len(train),len(dev))>10000
    wtrain=to_weight_matrix(train,N)
    wdev=to_weight_matrix(dev,N)
    w_all=wtrain+wdev
    w_recent=to_weight_matrix(train+dev,N,decay_half_life=7,ref_day=20)
    placements={
      "static_first14":metis_from_matrix(wtrain,selected),
      "recent7_only":metis_from_matrix(wdev,selected),
      "all21_equal":metis_from_matrix(w_all,selected),
      "recency_half7":metis_from_matrix(w_recent,selected)}
    static=placements["static_first14"]
    budget=int(.1*N)
    # Counterfactually allow only 12 of 120 predicate placements to move.
    # normalize both periods so newer 7d data are not implicitly upweighted
    # by a different number of samples.
    wblend=(wtrain/max(1,len(train))) + (wdev/max(1,len(dev)))
    for name,W in (("bounded_dev7",wdev),("bounded_blend21",wblend),
                   ("bounded_recent21",w_recent)):
        placements[name],moves=refine_swaps(static,W,budget)
        assert moves<=budget
    p=placements
    results={name:eval_subset(test,part) for name,part in p.items()}
    comparisons=[("recent7_only","static_first14"),
      ("all21_equal","static_first14"),("recency_half7","static_first14"),
      ("bounded_dev7","static_first14"),("bounded_blend21","static_first14"),
      ("bounded_recent21","static_first14"),
      ("bounded_dev7","all21_equal")]
    deltas={a+"_vs_"+b:day_bootstrap(test,p[a],p[b]) for a,b in comparisons}
    sizes={name:optimal_label_moves(static,part) for name,part in p.items()}
    for name,part in p.items():
        assert max(Counter(part).values())==N/K,(name,Counter(part))
        if name.startswith("bounded_"):assert sizes[name]<=budget
    report={"schema":"wikidata-prospective-28day-bound-migration-v1",
       "source":base.URL,"source_sha256":sha,"seed":SEED,
       "original_source_rows":len(raw),"n_nodes":N,"n_shards":K,
       "train_days":"2017-06-12..2017-06-25","observed_new_days":"2017-06-26..2017-07-02",
       "future_test_days":"2017-07-03..2017-07-09",
       "filtered_queries":{"historical14":len(train),"observed_new7":len(dev),
                           "unseen_future7":len(test)},
       "methods":results,"paired":deltas,
       "migrated_predicates":sizes,
       "migration_budget_nodes":budget,
       "caveats":["Real dated Wikidata SPARQL, not text GraphRAG with PDF/image KG retrieval",
        "Top-120 predicates chosen on historic 14d only; test restricted to multifacet queries containing 2-12 of them",
        "Predicates treated as equal-weight nodes; no real storage bytes, triple volume or network latency",
        "No test queries, predicates coaccess, or answers used to choose placements",
       "The coaccess-to-backbone ratio is aligned with the original temporal baseline",
        "Migration counts are exact Hamming minimized over unlabeled shard permutations",
        "All underlying algorithms are established baseline heuristics, not new mathematical novelty",
        "Only seven future days; day-block CI estimates exploratory, no independent replicate stream"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("partitions.json").write_text(json.dumps(p,indent=2))
    print("WIKIDATA_REFRESH_REPORT_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("WIKIDATA_REFRESH_REPORT_END",flush=True)
if __name__=="__main__":main()
