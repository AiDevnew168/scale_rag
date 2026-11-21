#!/usr/bin/env python3
"""Exhaustive 5,400-swap ORACLE feasibility (never deploy future-optimized swaps).

Historically inspected 2018 Wikidata organic query traffic. Frozen June trained
Mt-KaHyPar partition and day0-only locked policy unchanged. Future is used ONLY
to score hypothetical all-swaps oracle upper bounds on the defined 1-swap class.
The question is whether head gain and no novel harm are even jointly possible
under fixed 4x30 predicate-ID equal-count capacity.
"""
import datetime, json, os
from collections import Counter,defaultdict
from pathlib import Path
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as locked

SPAN={
 "january":("2018-01-01_2018-01-28",datetime.datetime(2018,1,1)),
 "february":("2018-01-29_2018-02-25",datetime.datetime(2018,1,29)),
 "march":("2018-02-26_2018-03-25",datetime.datetime(2018,2,26)),
}
MONTH=os.environ.get("ORACLE_MONTH","january")
assert MONTH in SPAN
name,start=SPAN[MONTH]
URL="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/"+name+"/"+name+"_organic.tsv.gz"
OUT=Path("results_candidate3_oracle_"+MONTH)
OUT.mkdir(exist_ok=True)

def audit(part,observed,future,known):
    # One fixed representative pattern per future distinct predicate combination.
    patcounts=Counter(q for _,q in future)
    pats=sorted(patcounts)
    weights=[patcounts[p] for p in pats]
    novel=[int(p not in known) for p in pats]
    base_spans=[locked.span(part,p) for p in pats]
    links=defaultdict(set)
    for k,p in enumerate(pats):
        for x in p:links[x].add(k)
    day0=Counter(q for _,q in observed)
    day0_pats=list(day0)
    day0_weights=[day0[q] for q in day0_pats]
    links_obs=defaultdict(set)
    for k,p in enumerate(day0_pats):
        for x in p:links_obs[x].add(k)
    base_obs=[locked.span(part,p) for p in day0_pats]
    curr=list(part)
    candidates=[{"swap":None,"observed_day0_local_gain":0,
      "future_request_touches_saved":0,"future_request_local_gain":0,
      "future_novel_request_touches_saved":0,
      "future_novel_distinct_local_gain":0,
      "future_novel_distinct_touches_saved":0}]
    for i in range(len(curr)):
        for j in range(i+1,len(curr)):
            if curr[i]==curr[j]:continue
            relevant=links[i]|links[j]
            relevant_obs=links_obs[i]|links_obs[j]
            curr[i],curr[j]=curr[j],curr[i]
            o_gain=sum(day0_weights[t]*(int(locked.span(curr,day0_pats[t])==1)-int(base_obs[t]==1))
                       for t in relevant_obs)
            ft=fl=nt=nul=nut=0
            for t in relevant:
                new_span=locked.span(curr,pats[t])
                saved=base_spans[t]-new_span
                local=int(new_span==1)-int(base_spans[t]==1)
                ft+=weights[t]*saved
                fl+=weights[t]*local
                if novel[t]:
                    nt+=weights[t]*saved
                    nul+=local
                    nut+=saved
            curr[i],curr[j]=curr[j],curr[i]
            candidates.append({"swap":[i,j],
              "observed_day0_local_gain":o_gain,
              "future_request_touches_saved":ft,
              "future_request_local_gain":fl,
              "future_novel_request_touches_saved":nt,
              "future_novel_distinct_local_gain":nul,
              "future_novel_distinct_touches_saved":nut})
    assert len(candidates)==5401
    frozen,original_choice=locked.optimizer_one_swap(part,observed)
    frozen_pair=original_choice["move"]
    selected=next(x for x in candidates if x["swap"]==frozen_pair)
    w=list(part)
    w[frozen_pair[0]],w[frozen_pair[1]]=w[frozen_pair[1]],w[frozen_pair[0]]
    assert w==frozen,"Frozen policy mutated unexpectedly"
    def pick(items):
        return max(items,key=lambda x:(x["future_request_touches_saved"],
                    x["future_request_local_gain"],x["observed_day0_local_gain"],
                    -x["swap"][0] if x["swap"] else -999,
                    -x["swap"][1] if x["swap"] else -999))
    oracle=pick(candidates)
    regimes={
      "strict_novel_unique_local_nonregression":
        [x for x in candidates if x["future_novel_distinct_local_gain"]>=0],
      "strict_novel_request_touch_nonregression":
        [x for x in candidates if x["future_novel_request_touches_saved"]>=0],
      "joint_novel_unique_and_request_nonregression":
        [x for x in candidates if x["future_novel_distinct_local_gain"]>=0 and x["future_novel_request_touches_saved"]>=0],
      "joint_nonregression_and_positive_day0_observed_gain":
        [x for x in candidates if x["future_novel_distinct_local_gain"]>=0
         and x["future_novel_request_touches_saved"]>=0 and x["observed_day0_local_gain"]>0],
      "joint_nonregression_with_at_least_90pct_of_best_day0":
        [x for x in candidates if x["future_novel_distinct_local_gain"]>=0
         and x["future_novel_request_touches_saved"]>=0
         and x["observed_day0_local_gain"]>=0.90*original_choice["training_day0_saved_requests"]],
    }
    def summary_candidate(x):
        return {k:v for k,v in x.items()}
    results={}
    for label,eligible in regimes.items():
        results[label]={"eligible_including_noop":len(eligible),
             "eligible_actual_swaps":sum(x["swap"] is not None for x in eligible),
             "best_hindsight":summary_candidate(pick(eligible)) if eligible else None}
    total_static_touches=sum((s-1)*w for s,w in zip(base_spans,weights))
    n_novel_requests=sum(w for w,b in zip(weights,novel) if b)
    output={
      "schema":"candidate3-exhaustive-one-swap-future-oracle-feasibility-v1",
      "month":MONTH,"future_requests":len(future),
      "future_distinct_patterns":len(pats),
      "future_novel_requests":n_novel_requests,
      "future_novel_distinct_patterns":sum(novel),
      "static_future_extra_shard_touches":total_static_touches,
      "candidate_swaps":5400,
      "frozen_day0_choice":summary_candidate(selected),
      "oracle_unconstrained_future_best":summary_candidate(oracle),
      "hindsight_regimes":results,
      "size_of_class":"All 5,400 single balanced two-ID swaps plus zero-migration",
      "theoretical_pairwise_no_harm_impossibility":
         "For every nontrivial exchange of nodes i in A, j in B, choose z!=i in A: the query {i,z} requires 1 shard before and 2 shards after. Hence universal no-harm over ALL possible unknown patterns is mathematically impossible under nontrivial swaps.",
      "limitations":[
        "2018 benchmark months were inspected previously; post-hoc exploratory",
        "Future queried for ORACLE scoring only. ORACLE is not an executable predictive policy.",
        "No actual byte capacity, migration bytes, RDF joins, runtime or user-facing answer quality.",
        "No causal guarantee from temporal correlation. No alternative partitions beyond one swap.",
        "Novel means not seen in June 2017 historic train set, not newly invented ever.",
        "Equal ID counts not equal physical RDF memory; only necessary model diagnostic."]}
    OUT.joinpath("report.json").write_text(json.dumps(output,indent=2))
    print("ORACLE_RISK_START",flush=True);print(json.dumps(output,indent=2),flush=True);print("ORACLE_RISK_END",flush=True)

def main():
    june,sh=base.load()
    earlier=[(d,q) for d,q in june if d<14]
    freq=Counter()
    for _,q in earlier:freq.update(set(q))
    selected=tuple(p for p,_ in sorted(freq.items(),key=lambda z:(-z[1],z[0]))[:120])
    hist,_=base.prop_stats(earlier,selected)
    part,_=hg.hybrid(hist,120,0)
    assert sorted(Counter(part).values())==[30]*4
    raw,interval_sha=hg.period(URL,start)
    period,_=base.prop_stats(raw,selected)
    first=min(d for d,_ in period)
    day0=[v for v in period if v[0]==first]
    future=[v for v in period if v[0]>first]
    assert len(day0)>100 and len(future)>30000
    audit(part,day0,future,{q for _,q in hist})
if __name__=="__main__":main()
