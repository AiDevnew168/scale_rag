#!/usr/bin/env python3
"""Candidate 3 locked economic PROXY gate. Never assert measured distributed latency.

Uses already-frozen June hypergraph and December-developed one-swap policy.
Chronological day0 decision, days 1..end strictly scored; no test gold in decisions.
No bytes, RDF triples, distributed latency or query plans are available here.
"""
import datetime
import json
import os
import random
from collections import Counter, defaultdict
from pathlib import Path
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as frozen

MONTHS = {
    "january": ("2018-01-01_2018-01-28", datetime.datetime(2018, 1, 1)),
    "february": ("2018-01-29_2018-02-25", datetime.datetime(2018, 1, 29)),
    "march": ("2018-02-26_2018-03-25", datetime.datetime(2018, 2, 26)),
}
month=os.environ.get("GATE_MONTH","january")
assert month in MONTHS
span,start=MONTHS[month]
url=("https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/"
     f"{span}/{span}_organic.tsv.gz")
out=Path("results_candidate3_final_"+month)
out.mkdir(exist_ok=True)

def metrics(rows, placement):
    n=len(rows)
    spans=[frozen.span(placement,q) for _,q in rows]
    return dict(n=n,local_pct=round(100*sum(s==1 for s in spans)/n,4),
                extra_shard_touches=sum(s-1 for s in spans),
                total_shard_activations=sum(spans),
                mean_shards=round(sum(spans)/n,6))

def one_swap_unique_control(original, observed):
    from dual_risk_swap_audit import gain_table,choose,move
    entries,_=gain_table(original,observed)
    decisions=choose(entries)
    return {name:move(original,decision[2]) for name,decision in decisions.items()}, decisions

def daily_bootstrap(future, old, new, reps=2000):
    daily=defaultdict(list)
    for day,q in future:
        daily[day].append((frozen.span(old,q)-1)-(frozen.span(new,q)-1))
    days=sorted(daily)
    perday={str(day):{"n":len(daily[day]),"saved_extra_touches":sum(daily[day])} for day in days}
    # Day-cluster resampling: sample whole days, preserving day-specific query counts.
    rng=random.Random(20261121)
    chunks=[(sum(daily[d]),len(daily[d])) for d in days]
    draws=[]
    for _ in range(reps):
        sample=[chunks[rng.randrange(len(chunks))] for __ in chunks]
        draws.append(sum(a for a,b in sample)/sum(b for a,b in sample))
    draws.sort()
    return {"days":len(days),"observed_saved_touches_per_query":round(sum(a for a,b in chunks)/sum(b for a,b in chunks),8),
            "bootstrap_ci95_per_query":[round(draws[int(.025*reps)],8),round(draws[int(.975*reps)-1],8)],
            "daily_trace":perday}

def run():
    june,jsha=base.load()
    first=[(d,q) for d,q in june if d<14]
    freq=Counter()
    for _,q in first:freq.update(set(q))
    selected=tuple(x for x,_ in sorted(freq.items(),key=lambda v:(-v[1],v[0]))[:120])
    train,_=base.prop_stats(first,selected)
    original,_=hg.hybrid(train,120,0)
    assert len(original)==120 and sorted(Counter(original).values())==[30,30,30,30]
    raw,msha=hg.period(url,start)
    filt,_=base.prop_stats(raw,selected)
    firstday=min(d for d,_ in filt)
    day0=[r for r in filt if r[0]==firstday]
    future=[r for r in filt if r[0]>firstday]
    assert len(day0)>100 and len(future)>30000
    update,decision=frozen.optimizer_one_swap(original,day0)
    controls,control_decisions=one_swap_unique_control(original,day0)
    assert update==controls["head"],"Frozen head and multi-risk comparator diverged"
    methods={"fixed_no_migration":original,"frozen_one_swap":update,
             "unique_only_day0":controls["unique"],
             "dual_risk_90pct":controls["tail_with_90pct_day0_head"],
             "dual_risk_50pct":controls["tail_with_50pct_day0_head"]}
    known={q for _,q in train}
    groups={"all_future":future,
            "novel_requests":[r for r in future if r[1] not in known],
            "novel_distinct_patterns":[(0,q) for q in sorted({q for _,q in future if q not in known})],
            "all_distinct_patterns":[(0,q) for q in sorted({q for _,q in future})]}
    scored={k:{name:metrics(rows,p) for name,p in methods.items()} for k,rows in groups.items()}
    old=metrics(future,original)
    savings={name:old["extra_shard_touches"]-metrics(future,p)["extra_shard_touches"] for name,p in methods.items()}
    # An idealized *upper-bound* economics threshold. Real byte costs and network
    # critical-path behavior remain unknown. Positive touch saving is not latency.
    # If a touch saves delta_ms serial time, max transferrable bytes is
    # saved_touches * delta_ms * bandwidth_Mbps * 125; excludes overhead.
    scenarios={}
    for delta_ms in (0,1,5,20):
        for bw_mbps in (10,100,1000):
            key=f"saved_serial_ms_per_touch_{delta_ms}__bandwidth_Mbps_{bw_mbps}"
            scenarios[key]={name:{"saved_extra_touches":saving,
                     "best_case_time_saved_ms":saving*delta_ms,
                     "max_migration_bytes_to_break_even_before_overheads":
                         max(0,saving*delta_ms*bw_mbps*125)}
                     for name,saving in savings.items()}
    boot={name:daily_bootstrap(future,original,p) for name,p in methods.items() if name!="fixed_no_migration"}
    report={"schema":"candidate3-final-frozen-proxy-economic-gate-v1",
            "month":month,"training_sha256":jsha,"period_sha256":msha,
            "first_observed_day":firstday,"day0_queries":len(day0),
            "future_queries":len(future),"selected_predicates":120,
            "four_equal_id_capacity_shards":[30,30,30,30],
            "migration_budget":"one balanced two-ID exchange; physical bytes unknown",
            "frozen_decision":decision,
            "control_decisions":{k:{"day0_request_gain":v[0],
                   "day0_unique_gain":v[1],"pair":v[2]} for k,v in control_decisions.items()},
            "metrics":scored,"saved_extra_shard_touches_vs_no_migration":savings,
            "day_bootstrap":boot,"hypothetical_economic_thresholds":scenarios,
            "decision":"PROXY ONLY. No net-saving confirmation absent migration bytes and measured routing critical path.",
            "limitations":["Wikidata organic predicate co-occurrence only; not full RDF/SPARQL execution",
              "All test intervals were inspected earlier: post-hoc, not preregistered independent replication",
              "No actual transferred RDF bytes, byte-balanced partitions, storage replica comparator, or distributed timings",
              "No measured P50/P95 or per-query queueing/caching/network impact",
              "Even saving touches may yield zero critical-path gain with parallel routing",
              "Day bootstrap is correlated temporal uncertainty, not cross-domain generalization",
              "Controls are exact one-swap day0 decisions, not general global repacking or query-aware cache"] }
    out.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("CANDIDATE3_FINAL_START",flush=True)
    print(json.dumps({k:v for k,v in report.items() if k not in ("day_bootstrap","hypothetical_economic_thresholds")},indent=2),flush=True)
    print("CANDIDATE3_FINAL_END",flush=True)
if __name__=="__main__":run()
