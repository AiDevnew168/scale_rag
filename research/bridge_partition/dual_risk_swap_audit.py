#!/usr/bin/env python3
"""HISTORIC-ONLY multi-risk swap audit on genuine future months.

Compare standard max-observed-request-gain single-swap with alternative
day0-only objectives that retain >=90% or >=50% of best day0 request gain
and then maximize distinct day0-pattern gains. Future query IDs never enter
the decision. All 2018 evaluations exploratory, since months had earlier
been opened during prior experiments.
"""
import datetime, json, os, itertools, random
from pathlib import Path
from collections import Counter, defaultdict
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as frozen

MONTH = os.environ.get("RISK_MONTH","march")
MONTHS = {
 "january":("2018-01-01_2018-01-28",datetime.datetime(2018,1,1)),
 "february":("2018-01-29_2018-02-25",datetime.datetime(2018,1,29)),
 "march":("2018-02-26_2018-03-25",datetime.datetime(2018,2,26))}
assert MONTH in MONTHS
span,start=MONTHS[MONTH]
url=(f"https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/"
     f"{span}/{span}_organic.tsv.gz")
OUT=Path("results_dual_risk_"+MONTH);OUT.mkdir(exist_ok=True)

def gain_table(original, observed):
    pat_counts=Counter(q for _,q in observed)
    patterns=sorted(pat_counts)
    weights=[pat_counts[x] for x in patterns]
    linked=defaultdict(set)
    for z,q in enumerate(patterns):
        for u in q:linked[u].add(z)
    original=[int(x) for x in original]
    baseline=[frozen.span(original,q)==1 for q in patterns]
    entries=[(0,0,None)]
    for i in range(len(original)):
        for j in range(i+1,len(original)):
            if original[i]==original[j]:continue
            relevant=linked[i]|linked[j]
            original[i],original[j]=original[j],original[i]
            fg=0;ug=0
            for t in relevant:
                delta=int(frozen.span(original,patterns[t])==1)-int(baseline[t])
                fg+=delta*weights[t];ug+=delta
            original[i],original[j]=original[j],original[i]
            entries.append((fg,ug,(i,j)))
    return entries,len(patterns)

def choose(entries):
    top=max(x[0] for x in entries)
    bestfreq=max(entries,key=lambda x:(x[0],x[1],-99999 if x[2] is None else -x[2][0],-99999 if x[2] is None else -x[2][1]))
    variants={"head":bestfreq}
    for fraction,name in ((.90,"tail_with_90pct_day0_head"),(.50,"tail_with_50pct_day0_head")):
        eligible=[x for x in entries if x[0]>=top*fraction and x[0]>=0]
        # Normalized safeguard pertains to OBSERVED day0 ONLY.
        variants[name]=max(eligible,key=lambda x:(x[1],x[0],-99999 if x[2] is None else -x[2][0],-99999 if x[2] is None else -x[2][1]))
    variants["unique"]=max(entries,key=lambda x:(x[1],x[0]))
    return variants

def move(original,assignment):
    p=list(original)
    if assignment:
        i,j=assignment
        p[i],p[j]=p[j],p[i]
    assert max(Counter(p).values())<=30
    return p

def score(patterns,partition):
    n=len(patterns)
    return {"n":n,"local_pct":round(100*sum(frozen.span(partition,q)==1 for q in patterns)/n,3) if n else None,
            "mean_shards":round(sum(frozen.span(partition,q) for q in patterns)/n,4) if n else None}

def main():
    june,sha=base.load()
    old=[(d,q) for d,q in june if d<14]
    freq=Counter()
    for _,q in old:freq.update(set(q))
    selected=tuple(p for p,_ in sorted(freq.items(),key=lambda z:(-z[1],z[0]))[:120])
    hist,_=base.prop_stats(old,selected)
    original,_=hg.hybrid(hist,120,0)
    raw,newsha=hg.period(url,start)
    sub,_=base.prop_stats(raw,selected)
    first=min(d for d,_ in sub)
    day0=[x for x in sub if x[0]==first]
    future=[x for x in sub if x[0]>first]
    assert len(day0)>=100 and len(future)>=30000
    entries,n_patterns=gain_table(original,day0)
    decisions=choose(entries)
    perms={"frozen":original}
    for name,(_,_,pair) in decisions.items():
        perms[name]=move(original,pair)
    seen_hist={q for _,q in hist}
    fut_patterns=sorted({q for _,q in future})
    novel_patterns=sorted(set(fut_patterns)-seen_hist)
    subset_novel=[q for _,q in future if q not in seen_hist]
    subsets={
        "all_future_requests":[q for _,q in future],
        "all_distinct_future_patterns":fut_patterns,
        "novel_future_requests":subset_novel,
        "distinct_novel_patterns":novel_patterns}
    result={"schema":"wikidata-observed-dual-risk-swap-v1","month":MONTH,
      "train_source_sha256":sha,"month_source_sha256":newsha,
      "n_day0_queries":len(day0),"n_day0_unique_patterns":n_patterns,
      "n_future_queries":len(future),"n_future_unique_patterns":len(fut_patterns),
      "n_future_novel_unique_patterns":len(novel_patterns),
      "candidate_swap_count":len(entries)-1,
      "decisions":{name:{"day0_request_gain":fg,"day0_unique_pattern_gain":ug,
                          "swap":list(pair) if pair else None}
                   for name,(fg,ug,pair) in decisions.items()},
      "metrics":{part:{name:score(queries,p) for name,p in perms.items()}
                 for part,queries in subsets.items()},
      "limitations":[
        "All three 2018 time intervals were previously inspected; this dual-risk selection is post-hoc exploratory, not independent confirmation",
        "All placements share original four blocks of exactly 30 predicate IDs",
        "Only day0 observed query patterns enter swaps; all later queries scorer-only",
        "Distinct patterns counted once; not user/domain-independent statistical samples",
        "No byte memory, measured migration, network join cost, GraphRAG answer accuracy, or full RDF triples",
        "Pareto selection uses a simple weighted constraint, NOT a new algorithm"]}
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("DUAL_RISK_START");print(json.dumps(result,indent=2));print("DUAL_RISK_END")
if __name__=="__main__":main()
