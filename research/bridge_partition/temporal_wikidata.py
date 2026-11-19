#!/usr/bin/env python3
"""Prospective 14/7/7-day timestamped SPARQL predicate workload partition audit.

Not an RAG accuracy benchmark. Predicates stand in for equal-weight placement
units. Source is actual Wikidata 2017 organic user query traffic. No future query
data enter model building or partition selection.
"""
import csv,gzip,hashlib,io,itertools,json,math,random,re,urllib.request
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np,pymetis
from sklearn.metrics import average_precision_score,roc_auc_score
SEED=261119
K=4
TOP=120
URL="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/2017-06-12_2017-07-09/2017-06-12_2017-07-09_organic.tsv.gz"
OUT=Path("results_temporal");OUT.mkdir(exist_ok=True)
PATT=re.compile(r"(?:www\.wikidata\.org/prop/direct/|wdt:)(P\d+)",re.I)
START=datetime(2017,6,12)
def load():
    req=urllib.request.Request(URL,headers={"User-Agent":"AcademicWorkloadAudit/1.0"})
    b=urllib.request.urlopen(req,timeout=120).read()
    source_sha=hashlib.sha256(b).hexdigest()
    rows=[]
    for row in csv.DictReader(io.StringIO(gzip.decompress(b).decode("utf8",errors="replace")),delimiter="\t"):
        try:
            stamp=datetime.strptime(row["timestamp"][:19],"%Y-%m-%d %H:%M:%S")
            day=(stamp-START).days
        except (ValueError,KeyError):continue
        if not 0<=day<28:continue
        from urllib.parse import unquote_plus
        s=unquote_plus(row["anonymizedQuery"])
        pp=tuple(sorted(set(PATT.findall(s))))
        rows.append((day,pp))
    print("ORIGINAL_ROWS",len(rows),"ARCHIVE_SHA256",source_sha,flush=True)
    return rows,source_sha
def pairs(query):
    return itertools.combinations(query,2)
def balanced_metis(labels,pair_counts):
    n=len(labels)
    neighbors=[[] for _ in range(n)]
    for (i,j),weight in pair_counts.items():
        if i==j:continue
        neighbors[i].append((j,weight))
        neighbors[j].append((i,weight))
    # A small uniform backbone ensures all isolated predicates are represented.
    for i in range(n-1):
        neighbors[i].append((i+1,1))
        neighbors[i+1].append((i,1))
    xadj=[0];adjncy=[];w=[]
    for nb in neighbors:
        for j,weight in nb:
            adjncy.append(j);w.append(int(weight))
        xadj.append(len(adjncy))
    _,part=pymetis.part_graph(K,xadj=xadj,adjncy=adjncy,eweights=w,
                             vweights=[1]*n,
                             options=pymetis.Options(seed=SEED))
    part=list(part);counts=Counter(part);cap=math.ceil(n/K)
    # Hard post-balance with minimum weighted edge cut change.
    steps=0
    while max(counts.values())>cap:
        options=[]
        for i,old in enumerate(part):
            if counts[old]<=cap:continue
            for target in range(K):
                if target==old or counts[target]>=cap:continue
                penalty=sum(weight*(int(target!=part[j])-int(old!=part[j])) for j,weight in neighbors[i])
                options.append((penalty,i,target,old))
        if not options:raise AssertionError("Cannot balance")
        _,i,target,old=min(options)
        part[i]=target;counts[old]-=1;counts[target]+=1
        steps+=1
        if steps>n*K:raise AssertionError("Balance fix loop")
    assert max(counts.values())<=cap
    return part
def prop_stats(queries,selected):
    ids={p:i for i,p in enumerate(selected)}
    kept=[];skipped=Counter()
    for day,props in queries:
        filtered=tuple(sorted({ids[p] for p in props if p in ids}))
        if not 2<=len(filtered)<=12:
            skipped["not_2_to_12_selected_properties"]+=1;continue
        kept.append((day,filtered))
    return kept,dict(skipped)
def score(rows,name,part):
    spans=[len({part[x] for x in q}) for day,q in rows]
    return {"n":len(spans),"local_pct":round(100*sum(x==1 for x in spans)/len(spans),3),
            "mean_active":round(float(np.mean(spans)),5),
            "p90_active":float(np.percentile(spans,90)),
            "by_day":{str(day):round(100*sum(len({part[x] for x in q})==1 for dd,q in rows if dd==day)/
                            sum(dd==day for dd,_ in rows),3)
                      for day in sorted({d for d,_ in rows})}}
def paired_day_ci(rows,a,b):
    rng=random.Random(SEED)
    byday=defaultdict(list)
    for d,q in rows:byday[d].append(q)
    days=sorted(byday)
    def diff(picked):
        obs=[q for day in picked for q in byday[day]]
        return 100*sum((len({a[x] for x in q})==1)-(len({b[x] for x in q})==1)
                       for q in obs)/len(obs)
    boots=[diff([rng.choice(days) for _ in days]) for _ in range(3000)]
    return {"delta_local_pp":round(diff(days),3),
       "day_block_ci95_pp":list(map(lambda v:round(float(v),3),
                                  np.percentile(boots,[2.5,97.5])))}
def main():
    raw,sha=load()
    train_raw=[r for r in raw if r[0]<14]
    dev_raw=[r for r in raw if 14<=r[0]<21]
    test_raw=[r for r in raw if r[0]>=21]
    freq=Counter()
    for day,q in train_raw:freq.update(set(q))
    selected=tuple(p for p,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:TOP])
    train,train_skip=prop_stats(train_raw,selected)
    dev,dev_skip=prop_stats(dev_raw,selected)
    test,test_skip=prop_stats(test_raw,selected)
    assert min(len(x) for x in (train,dev,test))>=1000,(len(train),len(dev),len(test))
    co=Counter()
    for day,q in train:co.update(pairs(q))
    n=len(selected)
    mtk=balanced_metis(selected,co)
    contig=[(i*K)//n for i in range(n)]
    random_part=list(contig);random.Random(SEED).shuffle(random_part)
    # Classic independent frequency-stripe heuristic, also no test use.
    frequency_striped=[i%K for i in range(n)]
    variants={"random":random_part,"frequency_striped":frequency_striped,
              "contiguous_by_train_popularity":contig,"historical_coaccess_metis":mtk}
    for name,part in variants.items():assert max(Counter(part).values())<=math.ceil(n/K)
    agg={name:score(test,name,part) for name,part in variants.items()}
    # Joint-coaccess prediction value above popularity-only inductive score.
    pairlist=list(itertools.combinations(range(n),2))
    seen=set()
    for day,q in test:seen.update(pairs(q))
    labels=np.array([int(p in seen) for p in pairlist])
    pair_score=np.array([co.get(p,0) for p in pairlist],dtype=float)
    marginal=np.array([freq[selected[i]]*freq[selected[j]]
                      for i,j in pairlist],dtype=float)
    metrics={}
    if 0<labels.sum()<len(labels):
        for name,values in {"history_pair_count":pair_score,
                            "train_frequency_product":marginal}.items():
            metrics[name]={"average_precision":round(float(average_precision_score(labels,values)),5),
                "roc_auc":round(float(roc_auc_score(labels,values)),5)}
    report={"schema":"timestamped-real-wikidata-workload-v1","source_url":URL,
      "source_sha256":sha,"n_original_rows":len(raw),"top_predicates":TOP,
      "split_policy":{"train_days":"2017-06-12 through 2017-06-25",
        "dev_days":"2017-06-26 through 2017-07-02",
        "test_days":"2017-07-03 through 2017-07-09"},
      "original_requests":{"train":len(train_raw),"dev":len(dev_raw),"test":len(test_raw)},
      "covered_multifacet_queries":{"train":len(train),"dev":len(dev),"test":len(test)},
      "skipped":{"train":train_skip,"dev":dev_skip,"test":test_skip},
      "test_pairwise":metrics,
      "test_placement":agg,
      "paired":{"coaccess_vs_frequency":paired_day_ci(test,mtk,frequency_striped),
                "coaccess_vs_contiguous":paired_day_ci(test,mtk,contig)},
      "known_caveats":["Real timestamped SPARQL logs, NOT natural-language RAG or query-answer accuracy",
         "Predicate IDs are equal-weight toy placement units, not actual graph triples/bytes",
         "No direct comparison with full SWORD/WISE, direct hypergraph or dynamic partitioners",
         "Top 120 properties selected using TRAIN only; evaluation restricted to queries with 2–12 of them",
         "7 consecutive test days yield wide dependence-aware uncertainty; confidence intervals exploratory",
         "Query parser uses direct property pattern; not a complete SPARQL syntax parser",
         "No real distributed execution or network latency measurements"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("train_predicates.json").write_text(json.dumps(selected,indent=2))
    print("TEMPORAL_REAL_REPORT_START")
    print(json.dumps(report,indent=2))
    print("TEMPORAL_REAL_REPORT_END")
if __name__=="__main__":main()
