#!/usr/bin/env python3
"""Candidate 3: temporal risk-admission feasibility, all pre-decision data chronological.
PROXY ONLY; historical intervals had been inspected before policy design.

Same frozen 120-node/4x30-ID placement and exact day0 head swap.
Days 1..3: counterfactual canary (no migration). Days 4..27: exclusively scored.
Methods share precisely the SAME future queries and 0 or 1 swap.
"""
import datetime, json, os, random
from pathlib import Path
from collections import Counter, defaultdict
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as locked
import dual_risk_swap_audit as dual

MONTHS={
 "january":("2018-01-01_2018-01-28",datetime.datetime(2018,1,1)),
 "february":("2018-01-29_2018-02-25",datetime.datetime(2018,1,29)),
 "march":("2018-02-26_2018-03-25",datetime.datetime(2018,2,26))
}
month=os.environ.get("ADMISSION_MONTH","january")
assert month in MONTHS
span,start=MONTHS[month]
url="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/"+span+"/"+span+"_organic.tsv.gz"
out=Path("results_risk_admission_"+month);out.mkdir(exist_ok=True)
CANARY_DAYS=3  # explicitly frozen; day0 then three days of feedback, future from day4
NOVEL_LIMIT=0  # empirical canary non-regression; NOT a future guarantee
SEED=20261121

def evaluate(rows,p):
    if not rows:return {"n":0,"local_pct":None,"extra_touches":0}
    spans=[locked.span(p,q) for d,q in rows]
    return {"n":len(spans),
      "local_pct":round(100*sum(s==1 for s in spans)/len(spans),4),
      "extra_touches":sum(s-1 for s in spans)}

def candidate_tables(initial,observed,canary,novel):
    d0,_=dual.gain_table(initial,observed)
    ck,_=dual.gain_table(initial,canary)
    nk,_=dual.gain_table(initial,novel)
    assert len(d0)==len(ck)==len(nk)==5401
    assert [(a[2]) for a in d0]==[a[2] for a in ck]==[a[2] for a in nk]
    return d0,ck,nk

def select(initial,d0,ck,nk):
    best=max(d0,key=lambda e:(e[0],e[1],-9999 if e[2] is None else -e[2][0],-9999 if e[2] is None else -e[2][1]))
    maxgain=best[0]
    assert maxgain>0 and best[2] is not None
    ix=d0.index(best)
    # All novelty observations are patterns absent from June train.
    def permitted(i):
        return (ck[i][0]>0 and nk[i][1]>=NOVEL_LIMIT and
                d0[i][0]>=.90*maxgain)
    viable=[i for i in range(1,len(d0)) if permitted(i)]
    chosen=max(viable,key=lambda i:(ck[i][0],nk[i][1],d0[i][0],-d0[i][2][0],-d0[i][2][1])) if viable else 0
    strong_head=ix if ck[ix][0]>0 and nk[ix][1]>=NOVEL_LIMIT else 0
    # Same canary observed window, unconstrained greedy: fair simple comparator.
    best_greedy=max(range(len(ck)),key=lambda i:(ck[i][0],d0[i][0],ck[i][1]))
    # Precommitted 90% day0 head with day0 uniqueness as tie-break.
    conservative=max((i for i in range(len(d0)) if d0[i][0]>=.90*maxgain),
       key=lambda i:(d0[i][1],d0[i][0]))
    return {"static":0,"locked_head":ix,"head_canary_reject":strong_head,
            "risk_admitted":chosen,"recent_canary_greedy":best_greedy,
            "day0_dual90":conservative},{
       "max_day0_gain":maxgain,"candidates_examined":len(d0)-1,
       "risk_candidates_allowed":len(viable),
       "locked_head_candidate_index":ix,
       "risk_candidate_index":chosen,
       "head_canary_accepted":bool(strong_head),
       "risk_accepted":bool(chosen),
       "risk_candidate_day0_gain":d0[chosen][0],
       "risk_candidate_canary_gain":ck[chosen][0],
       "risk_candidate_novel_distinct_canary_gain":nk[chosen][1],
       "head_candidate_canary_gain":ck[ix][0],
       "head_candidate_novel_distinct_canary_gain":nk[ix][1]}

def infer_days(rows,policies,baseline):
    dayq=defaultdict(list)
    for day,q in rows:dayq[day].append(q)
    dates=sorted(dayq)
    base_sums={d:sum(locked.span(baseline,q)-1 for q in dayq[d]) for d in dates}
    comps={}
    for name,placement in policies.items():
        daily={d:{"n":len(dayq[d]),"saved_extra_touches":base_sums[d]-
              sum(locked.span(placement,q)-1 for q in dayq[d])} for d in dates}
        rng=random.Random(SEED)
        rec=[(v["saved_extra_touches"],v["n"]) for v in daily.values()]
        samples=[]
        for _ in range(1500):
            selected=[rec[rng.randrange(len(rec))] for __ in rec]
            samples.append(sum(z[0] for z in selected)/sum(z[1] for z in selected))
        samples.sort()
        comps[name]={"n_days":len(dates),"observed_saved_per_query":
            round(sum(x[0] for x in rec)/sum(x[1] for x in rec),7),
            "day_resampled_ci95_saved_per_query":[round(samples[37],7),round(samples[1462],7)],
            "per_day":{str(k):v for k,v in daily.items()}}
    return comps

def main():
    june,jsha=base.load()
    tr0=[(d,q) for d,q in june if d<14]
    f=Counter()
    for _,q in tr0:f.update(set(q))
    selected=tuple(p for p,_ in sorted(f.items(),key=lambda z:(-z[1],z[0]))[:120])
    hist,_=base.prop_stats(tr0,selected)
    initial,_=hg.hybrid(hist,120,0)
    assert sorted(Counter(initial).values())==[30]*4
    raw,msha=hg.period(url,start)
    rows,_=base.prop_stats(raw,selected)
    days=sorted({d for d,q in rows});assert len(days)>=20
    observed=[r for r in rows if r[0]==days[0]]
    canary=[r for r in rows if days[0]<r[0]<=days[CANARY_DAYS]]
    future=[r for r in rows if r[0]>days[CANARY_DAYS]]
    assert len(observed)>=100 and len(canary)>500 and len(future)>30000
    known={q for _,q in hist}
    novel_canary=[(0,q) for q in sorted({q for _,q in canary if q not in known})]
    assert len(novel_canary)>40
    entries,feedback,novel=candidate_tables(initial,observed,canary,novel_canary)
    choices,selection=select(initial,entries,feedback,novel)
    frozen,meta=locked.optimizer_one_swap(initial,observed)
    assert dual.move(initial,entries[choices["locked_head"]][2])==frozen, "Frozen policy changed"
    policies={name:dual.move(initial,entries[i][2]) for name,i in choices.items()}
    for p in policies.values():assert sorted(Counter(p).values())==[30]*4
    dominant=Counter(q for _,q in observed).most_common(1)[0][0]
    subsets={
      "all":future,
      "not_day0_dominant":[r for r in future if r[1]!=dominant],
      "novel_requests":[r for r in future if r[1] not in known],
      "distinct_novel_patterns":[(0,q) for q in sorted({q for _,q in future if q not in known})],
      "distinct_all_patterns":[(0,q) for q in sorted({q for _,q in future})]}
    metrics={sub:{name:evaluate(subrows,p) for name,p in policies.items()} for sub,subrows in subsets.items()}
    static=metrics["all"]["static"]
    gains={name:static["extra_touches"]-m["extra_touches"] for name,m in metrics["all"].items()}
    future_boot=infer_days(future,policies,initial)
    report={"schema":"candidate3-risk-admission-gate-v1","month":month,
     "sha256":{"June":jsha,"interval":msha},
     "splits":{"day0":days[0],"canary_ends_day":days[CANARY_DAYS],
        "future_begins_day":days[CANARY_DAYS+1],
        "day0_n":len(observed),"canary_n":len(canary),
        "canary_novel_distinct":len(novel_canary),"future_n":len(future)},
     "method":"Single exact balanced swap; day0 proposal, days1-3 guarded counterfactual; day4+ future exclusively scored",
     "choices":{name:entries[i][2] for name,i in choices.items()},
     "choice_notes":selection,
     "metrics":metrics,"saved_touches_vs_static":gains,
     "daily_cluster_uncertainty":future_boot,
     "canary_head_early_benefit_lost_if_wait":feedback[choices["locked_head"]][0],
     "limitations":[
       "EXPLORATORY on previously opened 2018 intervals, not independent paper confirmation",
       "Predicate co-occurrence is a PROXY, not full RDF query execution",
       "No physical RDF bytes, byte-equal capacity, migration time, system latency or WISE executables",
       "Canary guard constrains observed novel distinct patterns only, not future guarantees",
       "Three-day canary delays migration; economic benefit during delay omitted from common-future comparison",
       "Day-cluster bootstrap does not repair reuse of test families",
       "Proposed risk objective is standard constrained selection; algorithmic novelty not established"]}
    out.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("RISK_ADMISSION_RESULT_START",flush=True)
    print(json.dumps({k:v for k,v in report.items() if k not in ("daily_cluster_uncertainty",)},indent=2),flush=True)
    print("RISK_ADMISSION_RESULT_END",flush=True)
if __name__=="__main__":main()
