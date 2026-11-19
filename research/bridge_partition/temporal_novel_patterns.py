#!/usr/bin/env python3
"""Frequency-dedup and novel-pattern held-out second-month diagnostic.

Report both query-weighted and unique predicate-combination-weighted scores.
Train model is frozen using June12-25 only. No test data in partitioners.
"""
import itertools,json,math
from collections import Counter
from pathlib import Path
import mtkahypar
import temporal_wikidata as b
import temporal_hypergraph as h
import month_ahead_wikidata as month
OUT=Path("results_temporal_novelty");OUT.mkdir(exist_ok=True)
def summarize(samples,variants):
    if not samples:return {"n":0}
    return {"n":len(samples),
        "local_pct":{k:round(100*sum(len({part[x] for x in q})==1 for _,q in samples)/len(samples),3)
                     for k,part in variants.items()},
        "mean_shards":{k:round(sum(len({part[x] for x in q}) for _,q in samples)/len(samples),4)
                     for k,part in variants.items()}}
def main():
    original,june_sha=b.load()
    past=[r for r in original if r[0]<14]
    freq=Counter()
    for _,q in past:freq.update(q)
    selected=tuple(p for p,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:120])
    train,_=b.prop_stats(past,selected)
    future_raw,future_sha=month.nextmonth()
    future,_=b.prop_stats(future_raw,selected)
    co=Counter()
    for _,q in train:co.update(itertools.combinations(q,2))
    variants={"popularity":[i*4//120 for i in range(120)],
       "coaccess_METIS":b.balanced_metis(selected,co),
       "direct_KM1":h.partition_direct(train,120,mtkahypar.Objective.KM1)}
    prior_patterns={q for _,q in train}
    novel=[r for r in future if r[1] not in prior_patterns]
    repeated=[r for r in future if r[1] in prior_patterns]
    unique={}
    for day,q in future:
        unique.setdefault(q,(day,q))
    uniq=list(unique.values())
    unique_novel=[r for r in uniq if r[1] not in prior_patterns]
    # Remove day and keep unique predicate set, not exact SPARQL query string.
    report={"schema":"historical-hyperedge-novel-pattern-generalization-v1",
      "source_sha256":future_sha,"past_sha256":june_sha,
      "training_unique_predicate_patterns":len(prior_patterns),
      "test_unique_predicate_patterns":len(unique),
      "subgroups":{"all_requests":summarize(future,variants),
                   "future_pattern_seen_in_training":summarize(repeated,variants),
                   "future_pattern_not_seen_in_training":summarize(novel,variants),
                   "unique_future_patterns":summarize(uniq,variants),
                   "unique_future_novel_patterns":summarize(unique_novel,variants)},
      "cautions":["Entire time-month test file has already been evaluated previously; subgroup diagnostics exploratory",
       "Novel means unseen PROPERTY-SET combination among selected 120 properties, not novel NL question",
       "Deduplication weights each property-set once, independent of traffic volume",
       "Not actual distributed RAG graph triple latency or memory budget"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("TEMPORAL_NOVEL_START");print(json.dumps(report,indent=2));print("TEMPORAL_NOVEL_END")
if __name__=="__main__":main()
