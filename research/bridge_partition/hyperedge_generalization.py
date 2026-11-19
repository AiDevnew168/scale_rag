#!/usr/bin/env python3
"""Prospective month-three evaluation of full-hyperedge plus pair-net smoothing.

Train: organic WDQS 2017-06-12..06-25; dev: Jul10..Aug06; test: Aug07..Sep03.
Only June train selects top-120 predicates and builds graph and candidate
partitionings. July dev selects gamma from predeclared grid [0,.25,1,4].
August *unseen* test scores. Not RAG QA and NOT original hypergraph theory.
"""
import csv,gzip,io,urllib.request,hashlib,itertools,math,json,random
from pathlib import Path
from datetime import datetime
from collections import Counter,defaultdict
import mtkahypar
import temporal_wikidata as base
import temporal_hypergraph as dh
import month_ahead_wikidata as jm
OUT=Path("results_hyperedge_generalization");OUT.mkdir(exist_ok=True)
SEED=261119
BETAS=[0,0.25,1,4]
URL3="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/2017-08-07_2017-09-03/2017-08-07_2017-09-03_organic.tsv.gz"
def period(url,start):
    raw=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"AcademicWorkloadAudit/1.0"}),timeout=120).read()
    from urllib.parse import unquote_plus
    rows=[]
    for x in csv.DictReader(io.StringIO(gzip.decompress(raw).decode("utf8",errors="replace")),delimiter="\t"):
        try:
            stamp=datetime.strptime(x["timestamp"][:19],"%Y-%m-%d %H:%M:%S")
            day=(stamp-start).days
        except (ValueError,KeyError):continue
        if day<0 or day>=28:continue
        q=tuple(sorted(set(base.PATT.findall(unquote_plus(x["anonymizedQuery"])))))
        rows.append((day,q))
    print("REAL_PERIOD",url,"ROWS",len(rows),"SHA",hashlib.sha256(raw).hexdigest(),flush=True)
    return rows,hashlib.sha256(raw).hexdigest()

def hybrid(train,n,beta):
    full=Counter(q for _,q in train)
    edges=Counter()
    # Exact historical sets retain their original count with scale 16.
    for q,num in full.items():
        edges[q]+=16*num
    if beta>0:
        # Clique-expanded pairwise support net; normalized per query size.
        # All features come from TRAIN history; unseen combinations never enter.
        for (_,q) in train:
            inc=max(1,round(16/(len(q)-1)))
            for p in itertools.combinations(q,2):
                edges[p]+=int(round(beta*inc))
    edges={q:int(w) for q,w in edges.items() if w>0}
    K=4; mtkahypar.set_seed(SEED)
    mt=mtkahypar.initialize(1)
    ctx=mt.context_from_preset(mtkahypar.PresetType.DEFAULT)
    ctx.set_partitioning_parameters(K,0.0,mtkahypar.Objective.KM1)
    ctx.logging=False
    names=sorted(edges)
    hg=mt.create_hypergraph(ctx,n,len(names),[list(q) for q in names],
                            [1]*n,[edges[q] for q in names])
    mtkahypar.set_seed(SEED)
    p=hg.partition(ctx)
    labels=[int(p.block_id(i)) for i in range(n)]
    assert max(Counter(labels).values())<=math.ceil(n/K)
    return labels,len(edges)

def score(rows,part):
    spans=[len({part[p] for p in q}) for _,q in rows]
    return {"n":len(spans),"local_pct":round(100*sum(s==1 for s in spans)/len(spans),3),
       "mean_shards":round(sum(spans)/len(spans),5)}

def ci_days(rows,a,b):
    byday=defaultdict(list)
    for day,q in rows:byday[day].append(q)
    days=sorted(byday)
    num={day:sum((len({a[p] for p in q})==1)-(len({b[p] for p in q})==1)
               for q in byday[day]) for day in days}
    denom={d:len(byday[d]) for d in days}
    rng=random.Random(SEED)
    boots=[]
    for _ in range(3000):
        pick=[rng.choice(days) for _ in days]
        boots.append(100*sum(num[d] for d in pick)/sum(denom[d] for d in pick))
    boots.sort()
    return {"delta_local_pp":round(100*sum(num.values())/sum(denom.values()),3),
      "day_bootstrap_ci95_pp":[round(boots[74],3),round(boots[2924],3)]}

def main():
    june,sha1=base.load()
    training=[r for r in june if r[0]<14]
    freq=Counter()
    for _,q in training:freq.update(q)
    selected=[p for p,_ in sorted(freq.items(),key=lambda t:(-t[1],t[0]))[:120]]
    train,_=base.prop_stats(training,selected)
    july,sha2=period(jm.URL,jm.START)
    dev,_=base.prop_stats(july,selected)
    august,sha3=period(URL3,datetime(2017,8,7))
    test,skipped=base.prop_stats(august,selected)
    print("SPLITS",len(train),len(dev),len(test),flush=True)
    assert len(test)>50000
    parts={};n_edges={}
    for beta in BETAS:
        p,e=hybrid(train,120,beta)
        parts[str(beta)]=p;n_edges[str(beta)]=e
    # July dev *only* determines chosen method. Ties prefer simpler beta.
    devscores={beta:score(dev,parts[str(beta)]) for beta in BETAS}
    selected_beta=min(BETAS,key=lambda b:(devscores[b]["mean_shards"],
                            -devscores[b]["local_pct"],b))
    baseline=parts[str(0)]
    metis_co=Counter()
    for _,q in train:metis_co.update(itertools.combinations(q,2))
    metis=base.balanced_metis(selected,metis_co)
    testscores={str(beta):score(test,parts[str(beta)]) for beta in BETAS}
    testscores["metis_clique"]=score(test,metis)
    chosen=parts[str(selected_beta)]
    novelty=set(q for _,q in train)
    fresh=[r for r in test if r[1] not in novelty]
    known=[r for r in test if r[1] in novelty]
    report={"schema":"prospective-month-three-hybrid-hyperedge-gate-v1",
       "train_period":"June 12–25, 2017","dev_period":"July 10–August 6, 2017",
       "test_period":"August 7–September 3, 2017",
       "source_sha256":{"train":sha1,"dev":sha2,"test":sha3},
       "eligible_counts":{"train":len(train),"dev":len(dev),"test":len(test),
                          "novel_patterns":len(fresh),"seen_patterns":len(known)},
       "node_count":120,"k_shards":4,"hard_max_shard_size":30,
       "betas":BETAS,"hyperedge_counts":n_edges,
       "selected_beta_from_dev":selected_beta,
       "dev_scores":{str(b):devscores[b] for b in BETAS},
       "test_scores":testscores,
       "test_paired":{"selected_vs_direct_KM1":ci_days(test,chosen,baseline),
           "selected_vs_METIS":ci_days(test,chosen,metis)},
       "test_novel_patterns":{"selected":score(fresh,chosen),"direct":score(fresh,baseline),
           "METIS":score(fresh,metis),"selected_vs_direct":ci_days(fresh,chosen,baseline)},
       "test_seen_patterns":{"selected":score(known,chosen),"direct":score(known,baseline)},
       "limitations":["Only SPARQL predicate-set locality proxy, not KG storage, RAG QA, network latency",
         "Unseen August benchmark interval not used for constructing or choosing beta",
         "July data previously examined for other purposes; dev-based model choice is exploratory",
         "Equal predicate weights; not full physical triple placement or byte-aware shard capacity",
         "Hybrid smoothing is a standard regularization control, not evidence of a novel algorithm",
         "28 test days may be strongly autocorrelated; day bootstrap is exploratory"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("train_predicates.json").write_text(json.dumps(selected,indent=2))
    print("HYBRID_MONTH3_START");print(json.dumps(report,indent=2));print("HYBRID_MONTH3_END")
if __name__=="__main__":main()
