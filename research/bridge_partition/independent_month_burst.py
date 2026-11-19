#!/usr/bin/env python3
"""LOCKED temporal cross-month test of already implemented day0 single-swap policy.

The exact single-swap policy is imported unchanged from december_burst_swap.py.
No January or February query logs used for tuning or training. First populated
calendar day is observed, remainder are future test.
"""
import datetime,json,os
from pathlib import Path
from collections import Counter
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as locked
MONTH=os.environ.get("HOT_MONTH","january")
MONTHS={
 "january":("2018-01-01_2018-01-28",datetime.datetime(2018,1,1)),
 "february":("2018-01-29_2018-02-25",datetime.datetime(2018,1,29)),
}
assert MONTH in MONTHS,MONTH
span,start=MONTHS[MONTH]
URL=(f"https://analytics.wikimedia.org/datasets/one-off/wikidata/"
     f"sparql_query_logs/{span}/{span}_organic.tsv.gz")
OUT=Path("results_independent_hot_"+MONTH);OUT.mkdir(exist_ok=True)
def main():
    june,sha=base.load()
    first=[(d,q) for d,q in june if d<14]
    freq=Counter()
    for d,q in first:freq.update(set(q))
    selected=tuple(x for x,_ in sorted(freq.items(),key=lambda v:(-v[1],v[0]))[:120])
    train,_=base.prop_stats(first,selected)
    original,_=hg.hybrid(train,120,0)
    # beta .25 was picked by a prior July dev study, comparator only.
    prior_tail,_=hg.hybrid(train,120,.25)
    raw,sha2=hg.period(URL,start)
    filtered,_=base.prop_stats(raw,selected)
    assert len(filtered)>10000
    firstday=min(d for d,_ in filtered)
    day0=[r for r in filtered if r[0]==firstday]
    future=[r for r in filtered if r[0]>firstday]
    assert len(day0)>100 and len(future)>10000,(len(day0),len(future))
    # FROZEN helper, identical across both unseen 2018 months.
    updated,decision=locked.optimizer_one_swap(original,day0)
    tail_updated,tail_decision=locked.optimizer_one_swap(prior_tail,day0)
    policies={
       "strong_static":original,"strong_one_swap":updated,
       "tail_static":prior_tail,"tail_one_swap":tail_updated}
    known_train={q for _,q in train}
    new=[r for r in future if r[1] not in known_train]
    known=[r for r in future if r[1] in known_train]
    onepattern,n=count_patterns(day0).most_common(1)[0]
    topfuture=[r for r in future if r[1]==onepattern]
    result={
      "schema":"independent-2018-month-day0-burst-swap-v1",
      "LOCKED_method":"Import unchanged exact observed-one-swap from december_burst_swap.py",
      "month":MONTH,"source_url":URL,
      "sha256":{"june_training":sha,"future_month":sha2},
      "train_june_questions":len(train),
      "first_observed_day_relative":firstday,
      "observed_day0_questions":len(day0),
      "future_queries":len(future),
      "future_new_pattern_requests":len(new),
      "day0_dominant_pattern":{
         "properties":[selected[i] for i in onepattern],
         "observed_requests":n,
         "future_repeats":len(topfuture),
         "initial_strong_span":locked.span(original,onepattern),
         "after_strong_swap_span":locked.span(updated,onepattern)},
      "decision_strong":decision,"decision_tail":tail_decision,
      "metrics":{
         "all_future":locked.report_subset(future,policies),
         "new_combinations":locked.report_subset(new,policies),
         "known_combinations":locked.report_subset(known,policies),
         "first_day_dominant_pattern":locked.report_subset(topfuture,policies) if topfuture else {}},
      "paired":{
        "strong_swap_vs_strong_static":base.paired_day_ci(future,updated,original),
        "tail_swap_vs_tail_static":base.paired_day_ci(future,tail_updated,prior_tail),
        "tail_swap_vs_strong_static":base.paired_day_ci(future,tail_updated,original)},
      "limitations":[
        "Two completely later source time windows were not used to invent the frozen policy; source dataset and family is same Wikidata 2017-2018 logs",
        "The policy itself emerged post-hoc from December, not from an independently preregistered multi-benchmark protocol",
        "Only direct-property co-occurrence among top120 June-selected predicates; no full SPARQL joins or GraphRAG answers",
        "120 equal-weight predicate IDs are not byte-weighted graph partitions",
        "All latency and network assertions would require a distributed executor",
        "Future query sets never used in selecting day0 swap; all future labels scorer-only"]}
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("INDEPENDENT_HOT_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("INDEPENDENT_HOT_END",flush=True)
def count_patterns(rows):return Counter(q for _,q in rows)
if __name__=="__main__":main()
