#!/usr/bin/env python3
"""Compositional Shadow-Compensation (CSC): exploratory, training-only 2-swap.

Main conjecture: instead of using another high-volume burst swap, spend the
second swap to restore locality of June-learned predicate co-access pairs that
did not recur on the currently observed day0. This is a PRIOR-ONLY 'shadow
tail' proxy for potentially recombined future queries. No future rows enter
decision. Two-swap uses double the migration count and is not byte-matched.

A genuine scientific innovation claim requires statistically positive future
net economics over equal-budget 2-swap and prior art, neither assumed here.
"""
import datetime, json, os, itertools, time
from collections import Counter,defaultdict
from pathlib import Path
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as locked

MONTHS={
 "january":("2018-01-01_2018-01-28",datetime.datetime(2018,1,1)),
 "february":("2018-01-29_2018-02-25",datetime.datetime(2018,1,29)),
 "march":("2018-02-26_2018-03-25",datetime.datetime(2018,2,26))
}
month=os.environ.get("CSC_MONTH","january")
assert month in MONTHS
name,start=MONTHS[month]
url="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/"+name+"/"+name+"_organic.tsv.gz"
out=Path("results_candidate3_CSC_"+month);out.mkdir(exist_ok=True)

def make_index(questions,weighted=True):
    counts=Counter(q for _,q in questions) if weighted else Counter({q:1 for _,q in questions})
    pats=sorted(counts)
    weights=[counts[p] for p in pats]
    links=defaultdict(set)
    for idx,p in enumerate(pats):
        for i in p:links[i].add(idx)
    return pats,weights,links

def shadow_pairs(hist,observed,initial):
    # Exclude pairs that are explicitly present on the current day0.
    obs_pairs={p for _,q in observed for p in itertools.combinations(q,2)}
    support=Counter()
    for q in sorted({q for _,q in hist}):
        support.update(itertools.combinations(q,2))
    unseen_support={p:w for p,w in support.items() if p not in obs_pairs}
    # Alternative completely uniform counterfactual pair support:
    # each unordered pair originally placed together on 1 shard, regardless
    # of whether seen. Unit weight. Both use June partition only.
    uniform={p:1 for p in itertools.combinations(range(len(initial)),2)
             if initial[p[0]]==initial[p[1]]}
    return unseen_support,uniform

def score_pair(part,pairs):
    return sum(w*int(part[i]==part[j]) for (i,j),w in pairs.items())

def one_candidate_after_frozen(initial,first,observed,hist):
    first_head=locked.optimizer_one_swap(initial,observed)[1]["training_day0_saved_requests"]
    assert first_head>0
    op,ow,ol=make_index(observed,weighted=True)
    base_loc=[int(locked.span(initial,p)==1) for p in op]
    first_loc=[int(locked.span(first,p)==1) for p in op]
    base_head=sum(w*v for w,v in zip(ow,base_loc))
    first_head_full=sum(w*v for w,v in zip(ow,first_loc))-base_head
    assert first_head_full==first_head
    prior,uniform=shadow_pairs(hist,observed,initial)
    assert len(prior)>0
    def pindex(pairs):
        idx=defaultdict(list)
        for (i,j),w in pairs.items():
            idx[i].append((i,j,w));idx[j].append((i,j,w))
        return idx
    pi=pindex(prior);ui=pindex(uniform)
    start_prior=score_pair(first,prior)
    start_uni=score_pair(first,uniform)
    current=list(first)
    records=[]
    for i in range(len(first)):
        for j in range(i+1,len(first)):
            if first[i]==first[j]:continue
            relevant=ol[i]|ol[j]
            affected_prior=set((a,b,w) for a,b,w in pi[i]+pi[j])
            affected_uni=set((a,b,w) for a,b,w in ui[i]+ui[j])
            current[i],current[j]=current[j],current[i]
            gain=sum(ow[t]*(int(locked.span(current,op[t])==1)-first_loc[t])
                     for t in relevant)
            prior_delta=sum(w*(int(current[a]==current[b])-int(first[a]==first[b]))
                            for a,b,w in affected_prior)
            uni_delta=sum(w*(int(current[a]==current[b])-int(first[a]==first[b]))
                            for a,b,w in affected_uni)
            current[i],current[j]=current[j],current[i]
            records.append({"second_swap":[i,j],
              "observed_day0_local_gain":first_head+gain,
              "shadow_support_delta_over_frozen":prior_delta,
              "shadow_pair_cohost_score":start_prior+prior_delta,
              "uniform_pair_cohost_score":start_uni+uni_delta})
    assert len(records)==5400
    single={"second_swap":None,"observed_day0_local_gain":first_head,
      "shadow_support_delta_over_frozen":0,
      "shadow_pair_cohost_score":start_prior,
      "uniform_pair_cohost_score":start_uni}
    records.append(single)
    def key(x,field):
        pair=x["second_swap"]
        return (x[field],x["observed_day0_local_gain"],
           -(pair[0] if pair else 999),-(pair[1] if pair else 999))
    policies={"locked_one_swap":single}
    for name,fraction in (("shadow_prior_90",.90),("shadow_prior_75",.75),
                          ("uniform_pairs_90",.90),("uniform_pairs_75",.75)):
        eligible=[r for r in records if r["observed_day0_local_gain"]+1e-9>=fraction*first_head]
        field="shadow_pair_cohost_score" if name.startswith("shadow") else "uniform_pair_cohost_score"
        policies[name]=max(eligible,key=lambda x:key(x,field))
    policies["two_step_day0_greedy"]=max(records,key=lambda x:key(x,"observed_day0_local_gain"))
    return policies,{"head_day0_gain":first_head,"candidate_count":5400,
       "shadow_historical_pair_support":len(prior),
       "uniform_original_cohost_pairs":len(uniform),
       "shadow_june_unique_patterns":len(set(q for _,q in hist)),
       "shadow_pair_proxy_excludes_day0_pairs":True}

def measure(policy,initial,first,seen,future,observed):
    arr=list(first)
    p=policy["second_swap"]
    if p is not None:
        i,j=p;arr[i],arr[j]=arr[j],arr[i]
    pat=Counter(q for _,q in future)
    oldspans={q:locked.span(initial,q) for q in pat}
    saved=sum(n*(oldspans[q]-locked.span(arr,q)) for q,n in pat.items())
    novel_pats=[q for q in pat if q not in seen]
    nov_touches=sum(pat[q]*(oldspans[q]-locked.span(arr,q)) for q in novel_pats)
    nov_unique_local=sum(int(locked.span(arr,q)==1)-int(oldspans[q]==1) for q in novel_pats)
    prior_local=sum(locked.span(arr,q)==1 for q in set(q for _,q in observed))
    return {"future_touches_saved_vs_static":saved,
      "future_novel_request_touches_saved_vs_static":nov_touches,
      "future_novel_distinct_single_shard_count_gain":nov_unique_local,
      "future_n":len(future),"novel_distinct_n":len(novel_pats),
      "original_day0_distinct_local_patterns":prior_local}

def main():
    tic=time.perf_counter()
    june,jsha=base.load()
    hist_raw=[r for r in june if r[0]<14]
    f=Counter()
    for _,q in hist_raw:f.update(set(q))
    selected=tuple(p for p,_ in sorted(f.items(),key=lambda z:(-z[1],z[0]))[:120])
    hist,_=base.prop_stats(hist_raw,selected)
    initial,_=hg.hybrid(hist,120,0)
    assert sorted(Counter(initial).values())==[30]*4
    raw,source_sha=hg.period(url,start)
    rows,_=base.prop_stats(raw,selected)
    day0=min(d for d,_ in rows)
    obs=[r for r in rows if r[0]==day0]
    future=[r for r in rows if r[0]>day0]
    first,firstdetails=locked.optimizer_one_swap(initial,obs)
    policies,diag=one_candidate_after_frozen(initial,first,obs,hist)
    seen={q for _,q in hist}
    results={name:{"decision":decision,
             "future_metrics":measure(decision,initial,first,seen,future,obs)}
             for name,decision in policies.items()}
    result={"schema":"candidate3-compositional-shadow-compensation-exploratory-v1",
       "month":month,"june_source_sha256":jsha,"month_source_sha256":source_sha,
       "frozen_first_day0_swap":firstdetails,
       "control_and_shadow_parameters":diag,
       "policies":results,
       "elapsed_sec":round(time.perf_counter()-tic,2),
       "limitations":[
         "The June shadow prior is known but unseen day0 coaccess PAIRS, not known future novel query patterns",
         "Only observed day0 and June history are used to select secondary candidate; test future scoring only",
         "Anchor first swap frozen; compare with equal two-swap day0 greedy, 1-swap and 0 move",
         "Two swaps incur up to 4 predicate-ID moves, rather than 2; this is NOT equal byte cost",
         "Uniform pair shadow conservatively penalizes disruption of initial co-host pairs, not future guarantee",
         "Monthly 2018 query logs previously opened; exploratory post-hoc, NOT independent preregistered result",
         "Cannot claim risk guarantee for unseen future due to unrestricted distribution drift",
         "No actual RDF byte capacities, real migration/indices, 4-shard SPARQL latency or WISE/WASP baseline",
         "Shadow compensation is a heuristic proposal, not yet an established original mathematical contribution"]}
    out.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("CSC_SHADOW_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("CSC_SHADOW_END",flush=True)

if __name__=="__main__":main()
