#!/usr/bin/env python3
"""Direct Mt-KaHyPar vs METIS held-out page-workload comparison.

Real benchmark annotations; all test gold is used for scoring ONLY.
No LLM, physical latency, entity graph or query-time routing are measured.
"""
import itertools, json, math, os, random, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import mtkahypar

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilot

SEED=pilot.SEED
MODE=os.getenv("BRIDGE_SCENARIO", "random")
assert MODE in ("random","bridge_to_synthesis","synthesis_to_bridge")
OUT=Path("results_hypergraph_"+MODE);OUT.mkdir(exist_ok=True)
MTK=mtkahypar.initialize(1)
mtkahypar.set_seed(SEED)

def hypergraph_partition(n, training, k, *, query_weight=400, objective="KM1"):
    # One ORIGINAL page = one node. Unlike clique-expansion METIS, each
    # historic multi-page query contributes ONE hyperedge over the whole page set.
    # This minimizes sum over training queries of (#involved_shards - 1).
    edges=Counter()
    for a in range(n-1):
        edges[(a,a+1)]+=100
    for q in training:
        nodes=pilot.pages(q)
        if len(nodes)>1:edges[nodes]+=query_weight
    pins=list(edges)
    weights=[int(edges[t]) for t in pins]
    ctx=MTK.context_from_preset(mtkahypar.PresetType.DEFAULT)
    ctx.set_partitioning_parameters(
        k,0.0,mtkahypar.Objective.KM1 if objective=="KM1" else mtkahypar.Objective.CUT)
    ctx.logging=False
    hg=MTK.create_hypergraph(ctx,n,len(pins),[list(t) for t in pins],
                             [1]*n,weights)
    p=hg.partition(ctx)
    labels=[int(p.block_id(v)) for v in range(n)]
    counts=Counter(labels)
    # hard equal max capacity consistent with baseline METIS post-repair
    assert len(counts)==k and max(counts.values())<=math.ceil(n/k), (n,counts)
    return labels

def split_workload(group, rng):
    q=sorted(group,key=lambda q:q.get("mh_id") or q.get("sq_id") or "")
    rng.shuffle(q)
    if MODE=="random":
        if len(q)<4:return None
        cut=max(2,min(len(q)-2,round(.6*len(q))))
        return q[:cut],q[cut:]
    source,target=(("bridge_chain","synthesis") if MODE=="bridge_to_synthesis"
                   else ("synthesis","bridge_chain"))
    tr=[x for x in q if x["question_type"]==source]
    te=[x for x in q if x["question_type"]==target]
    return (tr,te) if len(tr)>=2 and te else None

def mean_metrics(rows, mode):
    v=[r[mode] for r in rows]
    return {"n":len(v),"one_shard_pct":round(100*sum(x==1 for x in v)/len(v),3),
            "mean_activated_shards":round(float(np.mean(v)),4),
            "mean_extra_shards":round(float(np.mean(v))-1,4)}

def ci(rows,a,b):
    group=defaultdict(list)
    for r in rows:group[r["doc_id"]].append(r)
    docs=sorted(group)
    rng=random.Random(SEED)
    local=100*sum((r[a]==1)-(r[b]==1) for r in rows)/len(rows)
    span=np.mean([r[a]-r[b] for r in rows])
    boots=[]
    for t in range(2000):
        drawn=[rng.choice(docs) for _ in docs]
        draw=[r for doc in drawn for r in group[doc]]
        boots.append(100*sum((r[a]==1)-(r[b]==1) for r in draw)/len(draw))
    return {"delta_local_pp":round(float(local),3),
        "delta_mean_shards":round(float(span),4),
        "ci95_local_pp":list(map(lambda x:round(float(x),3),np.percentile(boots,[2.5,97.5]))),
        "wins":sum(r[a]==1 and r[b]!=1 for r in rows),
        "losses":sum(r[b]==1 and r[a]!=1 for r in rows)}

def main():
    allq=pilot.download("annotations/benchmark.json")
    man=pilot.download("manifest.json")
    assert len(allq)==2024 and len(man["documents"])==201
    npages={int(d["doc_id"]):len(d["files"]["page_images"]) for d in man["documents"]}
    candidates=defaultdict(list)
    filtered=Counter()
    for q in allq:
        pp=pilot.pages(q)
        if len(pp)<2:
            filtered["one_evidence_page"]+=1;continue
        doc=int(q["doc_id"])
        if max(pp)>=npages[doc] or min(pp)<0:
            filtered["page_out_of_range"]+=1;continue
        candidates[doc].append(q)
    methods=("contiguous","metis_structure","metis_clique_workload",
             "mtk_hypergraph_km1","mtk_hypergraph_cut",
             "mtk_hypergraph_structural")
    rng=random.Random(SEED)
    rows=[];splits=[];violations=Counter()
    for doc in sorted(candidates):
        n=npages[doc]
        if n<8:continue
        s=split_workload(candidates[doc],rng)
        if not s:continue
        train,test=s
        k=4
        variants={
            "contiguous":pilot.part_contig(n,k),
            "metis_structure":pilot.metis_pages(n,k,train,0),
            "metis_clique_workload":pilot.metis_pages(n,k,train,400),
            "mtk_hypergraph_km1":hypergraph_partition(n,train,k,objective="KM1"),
            "mtk_hypergraph_cut":hypergraph_partition(n,train,k,objective="CUT"),
            "mtk_hypergraph_structural":hypergraph_partition(n,[],k,objective="KM1")
        }
        for name,partition in variants.items():
            counts=Counter(partition)
            if len(counts)!=k or max(counts.values())>math.ceil(n/k):
                violations[name]+=1
        splits.append({"doc_id":doc,"pages":n,"n_train":len(train),"n_test":len(test),
         "train_ids":[x.get("mh_id") or x.get("sq_id") for x in train],
         "test_ids":[x.get("mh_id") or x.get("sq_id") for x in test]})
        for q in test:
            pages=pilot.pages(q)
            row={"doc_id":doc,"qid":q.get("mh_id") or q.get("sq_id"),
                 "kind":q["question_type"],"n_required_pages":len(pages)}
            for name,labels in variants.items():
                row[name]=len({labels[p] for p in pages})
            rows.append(row)
    assert len({r["qid"] for r in rows})==len(rows)
    assert len(rows)>=200 and len(splits)>=80,(len(rows),len(splits))
    assert not violations, dict(violations)
    report={"schema":"bridge-direct-mtkahypar-real-v1","mode":MODE,
      "source":"diandianone123/topographrag-bench","seed":SEED,
      "methods":{m:mean_metrics(rows,m) for m in methods},
      "paired":{
       "direct_km1_vs_clique_METIS":ci(rows,"mtk_hypergraph_km1","metis_clique_workload"),
       "direct_km1_vs_structure_METIS":ci(rows,"mtk_hypergraph_km1","metis_structure"),
       "direct_km1_vs_contiguous":ci(rows,"mtk_hypergraph_km1","contiguous"),
       "direct_km1_vs_hyper_structural":ci(rows,"mtk_hypergraph_km1","mtk_hypergraph_structural"),
       "direct_cut_vs_direct_km1":ci(rows,"mtk_hypergraph_cut","mtk_hypergraph_km1")},
      "by_type":{kind:{m:mean_metrics([r for r in rows if r["kind"]==kind],m)
                  for m in methods}
                 for kind in ("bridge_chain","synthesis")
                 if any(r["kind"]==kind for r in rows)},
      "n_docs":len(splits),"n_test_queries":len(rows),
      "n_train_queries":sum(x["n_train"] for x in splits),
      "hard_shard_balance_violations":dict(violations),
      "partitioner":{"name":"Mt-KaHyPar","package":"mtkahypar","version_pip":"1.7.1",
        "preset":"DEFAULT","imbalance":0.0,"objective":["KM1","CUT"],
        "adjacency_edge_weight":100,"historic_query_hyperedge_weight":400,
        "node_weight":"1 equal-weight page","k":4,"threads":1},
      "caveats":["Measured metric is oracle minimum active partitions given test GOLD support pages, not actual runtime",
       "Hypergraph query nets use gold TRAIN supports as ideal historical traces",
       "Train and test share source documents; test query IDs are disjoint",
       "No LLM, multimodal image pixels, real memory bytes, network latency, or complete retrieval",
       "Hyperedge weight is fixed manually without independent hyperparameter tuning",
       "Mt-KaHyPar is an established state-of-the-art style baseline, NOT a novel technique",
       "Sample used in previous feasibility work; intervals are exploratory"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
    OUT.joinpath("split_manifest.json").write_text(json.dumps(splits,indent=2))
    print("DIRECT_HYPERGRAPH_REPORT_START")
    print(json.dumps(report,indent=2))
    print("DIRECT_HYPERGRAPH_REPORT_END")
if __name__=="__main__":main()
