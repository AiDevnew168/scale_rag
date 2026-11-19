#!/usr/bin/env python3
"""Retrospective design; operational day-0 burst-adaptation on real Dec 2017 Wikidata.

Only day 0 of the December file is observed before selecting a single balanced
two-predicate swap. Days 1..27 are future evaluation and never inform the swap.
Candidate weak partition beta=.25 was previously chosen by July validation;
this rescue policy is DESIGNED AFTER inspecting December, so exploratory.
"""
import datetime, itertools, json
from pathlib import Path
from collections import Counter,defaultdict
import mtkahypar
import temporal_wikidata as base
import hyperedge_generalization as hg
from novel_december_gate import DEC_URL
OUT=Path("results_december_hot_repair");OUT.mkdir(exist_ok=True)
SEED=261119
def count_patterns(rows):
    return Counter(q for _,q in rows)
def span(part,q):
    return len({part[x] for x in q})
def optimizer_one_swap(original,observed):
    """Exact single-swap maximum empirical observed whole-hyperedge locality."""
    pat_counts=count_patterns(observed)
    p=list(original)
    patterns=list(pat_counts)
    counts=[pat_counts[q] for q in patterns]
    linked=defaultdict(set)
    for idx,q in enumerate(patterns):
        for x in q:linked[x].add(idx)
    existing=[span(p,q)==1 for q in patterns]
    best=(0,None)
    evaluated=0
    for i in range(len(p)):
        for j in range(i+1,len(p)):
            if p[i]==p[j]:continue
            idxset=linked[i]|linked[j]
            p[i],p[j]=p[j],p[i]
            gain=sum(counts[t]*((span(p,patterns[t])==1)-existing[t]) for t in idxset)
            p[i],p[j]=p[j],p[i]
            evaluated+=1
            if gain>best[0]:
                best=(gain,(i,j))
    updated=list(p)
    if best[1] is not None:
        i,j=best[1];updated[i],updated[j]=updated[j],updated[i]
    assert max(Counter(updated).values())<=30
    return updated,{"training_day0_saved_requests":best[0],
                    "move":list(best[1]) if best[1] else [],"evaluated_swaps":evaluated,
                    "observed_unique_query_patterns":len(pat_counts)}
def report_subset(rows,methods):
    return {name:{"n":len(rows),
        "local_pct":round(100*sum(span(p,q)==1 for _,q in rows)/len(rows),3),
        "mean_activated_shards":round(sum(span(p,q) for _,q in rows)/len(rows),4)}
            for name,p in methods.items()}
def main():
    june,sha=base.load()
    first=[(d,q) for d,q in june if d<14]
    freq=Counter()
    for d,q in first:freq.update(set(q))
    selected=tuple(x for x,_ in sorted(freq.items(),key=lambda v:(-v[1],v[0]))[:120])
    train,_=base.prop_stats(first,selected)
    a0,_=hg.hybrid(train,120,0)
    a25,_=hg.hybrid(train,120,.25)
    dec,sha2=hg.period(DEC_URL,datetime.datetime(2017,12,3))
    data,_=base.prop_stats(dec,selected)
    first_day=min(day for day,_ in data)
    observed=[r for r in data if r[0]==first_day]
    future=[r for r in data if r[0]>first_day]
    print("FIRST_OBSERVED_DAY",first_day,"OBSERVED_N",len(observed),"FUTURE_N",len(future),flush=True)
    assert len(observed)>100 and len(future)>50000
    beta25_update,detail25=optimizer_one_swap(a25,observed)
    beta0_update,detail0=optimizer_one_swap(a0,observed)
    variants={"frozen_strong_KM1":a0,"frozen_tail_tuned_beta025":a25,
              "one_swap_tail_tuned":beta25_update,"one_swap_strong":beta0_update}
    full=report_subset(future,variants)
    first_pattern,count=count_patterns(observed).most_common(1)[0]
    prior_patterns={q for _,q in train}
    novel=[(d,q) for d,q in future if q not in prior_patterns]
    newhead=[(d,q) for d,q in future if q==first_pattern]
    bytype={
        "all_later_requests":full,
        "previously_unseen_combinations":report_subset(novel,variants),
        "day0_top_pattern_repeat":report_subset(newhead,variants),
    }
    paired={name:base.paired_day_ci(future,variants[name],a0) for name in (
       "frozen_tail_tuned_beta025","one_swap_tail_tuned","one_swap_strong")}
    maincomp=base.paired_day_ci(future,beta25_update,a25)
    result={"schema":"december-first-day-burst-adaptive-one-swap-v1",
      "original_sha256":{"june":sha,"december":sha2},
      "source_december":DEC_URL,
      "train_policy":"June12-25 feature IDs; July tuning beta .25 was chosen earlier, NOT independently here",
      "observed_new_period":"First date actually present in December file (recorded as observed_day)",
      "observed_day_relative_to_Dec3":first_day,
      "future_heldout_period":"December 4-30 2017",
      "observed_eligible_requests":len(observed),
      "future_eligible_requests":len(future),
      "future_novel_requests":len(novel),
      "day0_top_pattern":{"predicates":[selected[i] for i in first_pattern],
                          "index_ids":first_pattern,"n_day0_requests":count,
                          "future_repeats":len(newhead),
                          "span_before_beta025":span(a25,first_pattern),
                          "span_after_beta025_swap":span(beta25_update,first_pattern),
                          "span_frozen_strong":span(a0,first_pattern)},
      "one_swap_decisions_from_day0_only":{
          "tail_tuned_beta025":detail25,"strong_baseline":detail0},
      "metrics_by_subgroup":bytype,
      "paired_vs_strong_frozen_day_block":paired,
      "paired_tail_one_swap_vs_tail_static_day_block":maincomp,
      "known_limitations":[
        "Crucial experiment constructed POST HOC after inspecting December traffic concentration; no independent confirmatory claim",
        "Day-0 observed incoming request pattern is allowed; days 1-27 are unseen to the swap decision",
        "Only one two-node balanced swap, exactly equal 120 predicate ID capacities; not actual byte-matched physical RDF data",
        "Full SPARQL requests not reconstructed, only co-occurrence of 2-12 June-selected predicates",
        "The original strong KM1 baseline was previously built by existing Mt-KaHyPar, not novel",
        "No distributed measured service latency, migration bytes or natural-language GraphRAG QA"] }
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    OUT.joinpath("partitions.json").write_text(json.dumps(variants,indent=2))
    print("DECEMBER_HOT_REPAIR_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("DECEMBER_HOT_REPAIR_END",flush=True)
if __name__=="__main__":main()
