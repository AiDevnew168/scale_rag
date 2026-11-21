#!/usr/bin/env python3
"""Past-month Tail-Compensated Repartitioning (PTCR), exploratory online causal.

Current day0 decides frozen first swap; previous complete calendar log is a
causally available proxy for the new-pattern tails. Exact 5,400-second-swap
search with >=90% observed day0 first head preservation, hard prior month
novel distinct-locality and novel request touch nonregression, no future
access until scoring. Also test simpler two-swap head-greedy, June-only
shadow-pair and static one-swap. Unit ID capacity, not RDF bytes.
"""
import datetime, json, os, math, time, random
from collections import Counter,defaultdict
from pathlib import Path
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as locked

MONTHS={
 "january":("2018-01-01_2018-01-28",datetime.datetime(2018,1,1),
    "2017-12-03_2017-12-30",datetime.datetime(2017,12,3)),
 "february":("2018-01-29_2018-02-25",datetime.datetime(2018,1,29),
    "2018-01-01_2018-01-28",datetime.datetime(2018,1,1)),
 "march":("2018-02-26_2018-03-25",datetime.datetime(2018,2,26),
    "2018-01-29_2018-02-25",datetime.datetime(2018,1,29))
}
month=os.environ.get("PTCR_MONTH","january")
assert month in MONTHS
current_name,start,previous_name,past_start=MONTHS[month]
ROOT="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/"
def source_url(x):return ROOT+x+"/"+x+"_organic.tsv.gz"
out=Path("results_candidate3_PTCR_"+month);out.mkdir(exist_ok=True)

def build(rows):
    patterns=Counter(q for _,q in rows)
    keys=sorted(patterns)
    weights=[patterns[q] for q in keys]
    idx=defaultdict(set)
    for k,q in enumerate(keys):
        for j in q:idx[j].add(k)
    return keys,weights,idx

def metrics(rows,static,candidate,prior_set):
    counts=Counter(q for _,q in rows)
    base={q:locked.span(static,q) for q in counts}
    spans={q:locked.span(candidate,q) for q in counts}
    return {
      "future_requests":len(rows),
      "all_extra_shard_touches_saved":sum(n*(base[q]-spans[q]) for q,n in counts.items()),
      "novel_request_extra_shard_touches_saved":
        sum(n*(base[q]-spans[q]) for q,n in counts.items() if q not in prior_set),
      "novel_distinct_single_shard_gain":
        sum(int(spans[q]==1)-int(base[q]==1) for q in counts if q not in prior_set),
      "future_novel_distinct_count":sum(q not in prior_set for q in counts)
    }

def search(static,first,day0,past,seen_june):
    dayp,dayw,dayix=build(day0)
    tail=[r for r in past if r[1] not in seen_june]
    pastp,pastw,pastix=build(tail)
    assert len(dayp)>50 and len(pastp)>50
    origloc=[int(locked.span(static,q)==1) for q in dayp]
    oneloc=[int(locked.span(first,q)==1) for q in dayp]
    oldtail=[locked.span(static,q) for q in pastp]
    firsttail=[locked.span(first,q) for q in pastp]
    one_head=sum(w*(a-b) for w,a,b in zip(dayw,oneloc,origloc))
    prior_tail_touch=sum(w*(o-n) for w,o,n in zip(pastw,oldtail,firsttail))
    prior_tail_unique=sum(int(n==1)-int(o==1) for o,n in zip(oldtail,firsttail))
    first_control={"second_swap":None,
        "day0_local_gain":one_head,
        "prior_novel_touch_gain":prior_tail_touch,
        "prior_novel_distinct_local_gain":prior_tail_unique,
        "prior_novel_distinct_n":len(pastp)}
    candidate=[first_control]
    curr=list(first)
    for i in range(len(curr)):
        for j in range(i+1,len(curr)):
            if first[i]==first[j]:continue
            od=dayix[i]|dayix[j]
            pd=pastix[i]|pastix[j]
            curr[i],curr[j]=curr[j],curr[i]
            dh=sum(dayw[k]*(int(locked.span(curr,dayp[k])==1)-oneloc[k])
                   for k in od)
            pr=0;pu=0
            for k in pd:
                s=locked.span(curr,pastp[k])
                pr+=pastw[k]*(firsttail[k]-s)
                pu+=int(s==1)-int(firsttail[k]==1)
            curr[i],curr[j]=curr[j],curr[i]
            candidate.append({"second_swap":[i,j],
              "day0_local_gain":one_head+dh,
              "prior_novel_touch_gain":prior_tail_touch+pr,
              "prior_novel_distinct_local_gain":prior_tail_unique+pu,
              "prior_novel_distinct_n":len(pastp)})
    assert len(candidate)==5401
    def select(records,primary):
        if not records:return {"second_swap":None,"day0_local_gain":0,
               "prior_novel_touch_gain":0,"prior_novel_distinct_local_gain":0,
               "prior_novel_distinct_n":len(pastp),"abstained":True}
        return max(records,key=lambda r:(
             r[primary],r["day0_local_gain"],
             -(r["second_swap"][0] if r["second_swap"] else 9999),
             -(r["second_swap"][1] if r["second_swap"] else 9999)))
    c90=math.ceil(.9*one_head)
    c75=math.ceil(.75*one_head)
    safe=[r for r in candidate if r["prior_novel_touch_gain"]>=0
          and r["prior_novel_distinct_local_gain"]>=0]
    keep90=[r for r in safe if r["day0_local_gain"]>=c90]
    keep75=[r for r in safe if r["day0_local_gain"]>=c75]
    policies={
        "no_move":{"second_swap":None,"day0_local_gain":0,"is_static":True},
        "frozen_one_swap":first_control,
        "two_swap_day0_greedy":select(candidate,"day0_local_gain"),
        "PTCR_90_prior_novel_touches":select(keep90,"prior_novel_touch_gain"),
        "PTCR_90_day0_head":select(keep90,"day0_local_gain"),
        "PTCR_75_prior_novel_touches":select(keep75,"prior_novel_touch_gain"),
        "PTCR_75_day0_head":select(keep75,"day0_local_gain"),
    }
    return policies,{"one_swap_head_day0_gain":one_head,
       "prior_new_patterns":len(pastp),
       "prior_new_requests":len(tail),
       "first_prior_novel_request_gain":prior_tail_touch,
       "first_prior_novel_distinct_gain":prior_tail_unique,
       "feasible_safe_candidates":len(safe),
       "feasible_safe_90head":len(keep90),
       "feasible_safe_75head":len(keep75)}

def day_cluster_ci(rows, alt, baseline):
    day=defaultdict(lambda:Counter())
    for d,q in rows:day[d][q]+=1
    blocks=[]
    for d,counts in sorted(day.items()):
        delta=sum(n*(locked.span(baseline,q)-locked.span(alt,q)) for q,n in counts.items())
        blocks.append((delta,sum(counts.values())))
    assert len(blocks)>=20
    rng=random.Random(20261121)
    boots=[]
    for _ in range(3000):
        chosen=[blocks[rng.randrange(len(blocks))] for __ in blocks]
        boots.append(10000*sum(v[0] for v in chosen)/sum(v[1] for v in chosen))
    boots.sort()
    return {"days":len(blocks),"saved_extra_touches":sum(x[0] for x in blocks),
      "saved_extra_touches_per_10000_future_requests":round(
        10000*sum(x[0] for x in blocks)/sum(x[1] for x in blocks),4),
      "day_cluster_bootstrap95_per_10000_requests":[round(boots[74],4),round(boots[2924],4)]}

def main():
    tic=time.perf_counter()
    raw,jsha=base.load()
    trainraw=[r for r in raw if r[0]<14]
    fq=Counter()
    for _,q in trainraw:fq.update(set(q))
    selected=tuple(p for p,_ in sorted(fq.items(),key=lambda x:(-x[1],x[0]))[:120])
    hist,_=base.prop_stats(trainraw,selected)
    static,_=hg.hybrid(hist,120,0)
    assert sorted(Counter(static).values())==[30]*4
    past_raw,prevsha=hg.period(source_url(previous_name),past_start)
    past,_=base.prop_stats(past_raw,selected)
    nowraw,nowsha=hg.period(source_url(current_name),start)
    current,_=base.prop_stats(nowraw,selected)
    first_day=min(d for d,_ in current)
    day0=[r for r in current if r[0]==first_day]
    future=[r for r in current if r[0]>first_day]
    first,meta=locked.optimizer_one_swap(static,day0)
    seen={q for _,q in hist}
    policies,diag=search(static,first,day0,past,seen)
    output={}
    placements={}
    for name,choice in policies.items():
        part=list(static) if choice.get("is_static",False) or choice.get("abstained",False) else list(first)
        if choice.get("second_swap") is not None and not choice.get("abstained",False):
            i,j=choice["second_swap"];part[i],part[j]=part[j],part[i]
        assert sorted(Counter(part).values())==[30]*4
        placements[name]=part
        output[name]={"decision":choice,"future_outcome":metrics(future,static,part,seen)}
    result={"schema":"candidate3-causal-previous-month-tail-compensated-repartitioning-v1",
      "month":month,"sources_sha256":{"June":jsha,"previous_month":prevsha,"current_month":nowsha},
      "available_before_decision":[
        "June original training first 14 days",
        previous_name+" full 28-day preceding month organic requests",
        current_name+" first actually present 24-hour day"],
      "future_evaluation_only":current_name+" days after the observed first day",
      "frozen_first_swap":meta,
      "diagnostics":diag,"policies":output,
      "paired_day_cluster_uncertainty":{
        "PTCR90_vs_frozen":day_cluster_ci(future,placements["PTCR_90_prior_novel_touches"],placements["frozen_one_swap"]),
        "PTCR90_vs_greedy_two_swap":day_cluster_ci(future,placements["PTCR_90_prior_novel_touches"],placements["two_swap_day0_greedy"])},
      "elapsed_sec":round(time.perf_counter()-tic,2),
      "limitations":[
        "All Jan/Feb/Mar 2018 logs have been opened and analyzed in prior experiments; exploratory retrospective only",
        "Previous FULL month available chronologically; current future never used in candidate selection",
        "Previous novel patterns are absent from June historic training; no predictive assurance they persist",
        "Equal 30 predicate-ID capacity, not physical RDF byte capacity or migration cost",
        "Two swaps allow up to 4 moved IDs, twice the 1-swap migration burden",
        "If no prior-safe candidate satisfies observed head constraint, PTCR abstains: static no migration",
        "Sufficiency of observed prior-tail protection under arbitrary distribution shift NOT guaranteed",
        "No real SPARQL joins, P95 latency, WISE/WASP, or equal-byte replication benchmark",
        "Policy is a constrained multiobjective local search, not yet a demonstrated original algorithm"]}
    out.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("PTCR_CAUSAL_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("PTCR_CAUSAL_END",flush=True)

if __name__=="__main__":main()
