#!/usr/bin/env python3
"""Pre-specified chronological canary: day0 proposer, day1 validator, later-days test.

Exploratory because historical months have been opened already. The winning
December-derived one-swap policy remains untouched. Canary does not inspect
days >=2 when making decisions. No physical data migration measured.
"""
import datetime
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as frozen

MONTHS={
 "january":("2018-01-01_2018-01-28", datetime.datetime(2018,1,1)),
 "february":("2018-01-29_2018-02-25", datetime.datetime(2018,1,29)),
 "march":("2018-02-26_2018-03-25", datetime.datetime(2018,2,26)),
}
month=os.environ.get("CANARY_MONTH","january")
assert month in MONTHS
span,start=MONTHS[month]
url=("https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/"
     f"{span}/{span}_organic.tsv.gz")
out=Path("results_candidate3_canary_"+month)
out.mkdir(exist_ok=True)

def count(rows,p):
    s=[frozen.span(p,q) for _,q in rows]
    return {"n":len(s),"local_pct":round(100*sum(x==1 for x in s)/len(s),4) if s else None,
            "extra_touches":sum(x-1 for x in s)}

def novel_distinct(rows,known):
    return [(0,q) for q in sorted(set(q for _,q in rows if q not in known))]

def compare(rows,old,new):
    a=count(rows,old)
    b=count(rows,new)
    return {"n":a["n"],"delta_local_pp":round(b["local_pct"]-a["local_pct"],4) if a["n"] else None,
            "saved_extra_touches":a["extra_touches"]-b["extra_touches"],
            "static":a,"candidate":b}

def decision(canary,novel,lower_bound_pp):
    return bool(canary["saved_extra_touches"]>0 and novel["n"]>=20
                and novel["delta_local_pp"]>=lower_bound_pp)

def main():
    june,sha=base.load()
    old=[(d,q) for d,q in june if d<14]
    f=Counter()
    for _,q in old:f.update(set(q))
    selected=tuple(x for x,_ in sorted(f.items(),key=lambda x:(-x[1],x[0]))[:120])
    hist,_=base.prop_stats(old,selected)
    partition,_=hg.hybrid(hist,120,0)
    assert sorted(Counter(partition).values())==[30,30,30,30]
    raw,rsha=hg.period(url,start)
    rows,_=base.prop_stats(raw,selected)
    days=sorted({d for d,_ in rows})
    assert len(days)>=20,(month,len(days))
    day0=[r for r in rows if r[0]==days[0]]
    day1=[r for r in rows if r[0]==days[1]]
    future=[r for r in rows if r[0]>days[1]]
    assert len(day0)>100 and len(day1)>100 and len(future)>10000
    swapped,decision_detail=frozen.optimizer_one_swap(partition,day0)
    dominant,count_d=Counter(q for _,q in day0).most_common(1)[0]
    known={q for _,q in hist}
    validation_all=compare(day1,partition,swapped)
    validation_novel=compare(novel_distinct(day1,known),partition,swapped)
    policies={"static":partition,"frozen_head":swapped}
    for bound,name in [(0,"strict_zero_novel_loss"),(-1.0,"at_most_1pp_novel_loss")]:
        policies[name]=swapped if decision(validation_all,validation_novel,bound) else partition
    test_sets={
       "all_future":future,
       "outside_day0_dominant_pattern":[r for r in future if r[1]!=dominant],
       "novel_requests":[r for r in future if r[1] not in known],
       "novel_distinct_patterns":novel_distinct(future,known),
       "all_distinct_patterns":[(0,q) for q in sorted({q for _,q in future})]}
    metrics={s:{n:count(rows,p) for n,p in policies.items()} for s,rows in test_sets.items()}
    impact={s:{n:{"saved_extra_touches":metrics[s]["static"]["extra_touches"]-m["extra_touches"],
                  "delta_local_pp":round(m["local_pct"]-metrics[s]["static"]["local_pct"],4)}
               for n,m in metrics[s].items() if n!="static"} for s in metrics}
    result={
        "schema":"candidate3-day0-propose-day1-canary-days2plus-heldout-v1",
        "month":month,"train_sha":sha,"eval_sha":rsha,
        "observed_day0_n":len(day0),"canary_day1_n":len(day1),"future_n":len(future),
        "days_tested":len(days)-2,"dominant_day0_frequency":count_d,
        "dominant_future_frequency":sum(q==dominant for _,q in future),
        "frozen_swap":decision_detail,
        "canary_all":validation_all,"canary_novel_unique":validation_novel,
        "canary_accepted":{"strict_zero_novel_loss":policies["strict_zero_novel_loss"]==swapped,
                           "at_most_1pp_novel_loss":policies["at_most_1pp_novel_loss"]==swapped},
        "heldout_metrics":metrics,"heldout_impact":impact,
        "limitations":[
          "Months previously inspected; no new independent pre-registered experiment",
          "No future day2+ used in training, candidate optimization or canary selection",
          "Day1 observed labels use known June training only",
          "No structural novelty guarantee; day1 observed novelty may not predict later novelty",
          "No actual RDF bytes, full join execution, distributed latency, physical replication, or byte capacity",
          "Dominant-pattern exclusion is a diagnostic, not a proposed deployable policy"] }
    out.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("CANARY_RESULT_START",flush=True)
    print(json.dumps({k:v for k,v in result.items() if k!="heldout_metrics"},indent=2),flush=True)
    print("CANARY_RESULT_END",flush=True)
if __name__=="__main__":main()
