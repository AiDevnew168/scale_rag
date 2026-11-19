#!/usr/bin/env python3
"""Online workload shift: 10%-migration swap adaptation against frozen placement.

Real TopoGraphRAG query support-page traces. NOT end-to-end RAG or novel algorithm.
For each document, phase 1 has historical queries of one topology; half of
subsequent phase-2 queries are OBSERVED at adaptation time, and the other half
are entirely unseen evaluation queries. No phase-2 evaluation gold enters
partition construction or refinement. All cost/quality proxies only.
"""
import json, math, random, itertools, os
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import pilot

SEED=310119
MODE=os.environ.get("ONLINE_SOURCE","bridge_chain")
assert MODE in ("bridge_chain","synthesis")
TARGET="synthesis" if MODE=="bridge_chain" else "bridge_chain"
OUT=Path("results_online_"+MODE);OUT.mkdir(exist_ok=True)
CAP_FRACTION=0.10
K=4

def mean_span(part,queries):
    if not queries:return 0.
    return sum(len({part[p] for p in pilot.pages(q)})-1 for q in queries)/len(queries)

def online_refine(initial,history,feedback,budget):
    """Train-only local two-vertex swap heuristic, no learned parameter."""
    labels=list(initial)
    n=len(labels)
    swaps=0
    # Weight the now-visible target-family workload twice as much as
    # historical workload; fixed a priori.
    def loss(part):
        return .33333333*mean_span(part,history)+.66666667*mean_span(part,feedback)
    best=loss(labels)
    for _ in range(budget//2):
        options=[]
        for a in range(n):
            for b in range(a+1,n):
                if labels[a]==labels[b]:continue
                labels[a],labels[b]=labels[b],labels[a]
                delta=loss(labels)-best
                labels[a],labels[b]=labels[b],labels[a]
                if delta < -1e-8:options.append((delta,a,b))
        if not options:break
        _,a,b=min(options)
        labels[a],labels[b]=labels[b],labels[a]
        best=loss(labels)
        swaps+=1
    return labels,2*swaps

def test_stats(rows,method):
    n=len(rows)
    return {"n":n,"local_pct":round(100*sum(x[method]==1 for x in rows)/n,3),
        "mean_shards":round(sum(x[method] for x in rows)/n,4)}

def bootstrap(rows,a,b):
    rng=random.Random(SEED); bydoc=defaultdict(list)
    for x in rows:bydoc[x["doc_id"]].append(x)
    ids=sorted(bydoc);boots=[]
    for _ in range(1200):
        selected=[r for doc in [rng.choice(ids) for _ in ids] for r in bydoc[doc]]
        boots.append(100*sum((r[a]==1)-(r[b]==1) for r in selected)/len(selected))
    return {"delta_local_pp":round(100*sum((r[a]==1)-(r[b]==1) for r in rows)/len(rows),3),
       "ci95_pp":list(map(lambda x:round(float(x),3),np.percentile(boots,[2.5,97.5]))),
       "wins":sum(x[a]==1 and x[b]!=1 for x in rows),
       "losses":sum(x[b]==1 and x[a]!=1 for x in rows)}

def main():
    questions=pilot.download("annotations/benchmark.json")
    manifest=pilot.download("manifest.json")
    sizes={int(d["doc_id"]):len(d["files"]["page_images"]) for d in manifest["documents"]}
    groups=defaultdict(list)
    for q in questions:
        pp=pilot.pages(q);d=int(q["doc_id"])
        if len(pp)>=2 and 0<=min(pp) and max(pp)<sizes[d]:
            groups[d].append(q)
    records=[];splits=[];stats=Counter()
    for d in sorted(groups):
        n=sizes[d]
        if n<20:continue
        hist=[q for q in groups[d] if q["question_type"]==MODE]
        incoming=[q for q in groups[d] if q["question_type"]==TARGET]
        if len(hist)<2 or len(incoming)<4:continue
        rng=random.Random(SEED+d)
        rng.shuffle(incoming)
        nf=max(2,len(incoming)//2)
        feedback=incoming[:nf];future=incoming[nf:]
        if len(future)<2:continue
        initial=pilot.metis_pages(n,K,hist,400)
        structure=pilot.metis_pages(n,K,hist,0)
        # An ordinary full repartition with both old and newly observed
        # supports has no migration budget: compare its migration cost.
        rebuilt=pilot.metis_pages(n,K,hist+feedback,400)
        budget=math.floor(CAP_FRACTION*n)
        adapted,moves=online_refine(initial,hist,feedback,budget)
        assert max(Counter(adapted).values())<=math.ceil(n/K)
        assert moves<=budget
        # Block-label symmetry: compute minimal true moved pages under
        # permutation of four shard names for all methods.
        permutations=list(itertools.permutations(range(K)))
        def migrations(a,b):
            return min(sum(x!=perm[y] for x,y in zip(a,b)) for perm in permutations)
        full_moves=migrations(initial,rebuilt)
        assert migrations(initial,adapted)<=moves
        splits.append({"doc_id":d,"n_pages":n,
          "historical_ids":[q.get("mh_id") or q.get("sq_id") for q in hist],
          "observed_new_ids":[q.get("mh_id") or q.get("sq_id") for q in feedback],
          "future_ids":[q.get("mh_id") or q.get("sq_id") for q in future],
          "migration_budget_pages":budget,"online_moves":moves,
          "full_rebuild_moved_pages":full_moves})
        for q in future:
            pp=pilot.pages(q)
            row={"doc_id":d,"qid":q.get("mh_id") or q.get("sq_id"),
                 "type":q["question_type"],"n_needed_pages":len(pp)}
            for name,part in (("static",initial),("structure",structure),
                  ("online_10pct",adapted),("full_rebuild",rebuilt)):
                row[name]=len({part[p] for p in pp})
            records.append(row)
    if len(splits)<15 or len(records)<60:
        raise RuntimeError(f"Not enough independent docs after prospective eligibility: {len(splits)} docs, {len(records)} queries")
    modes=("structure","static","online_10pct","full_rebuild")
    report={"schema":"bridge-workload-adaptation-real-v1",
       "seed":SEED,"historical_family":MODE,"new_family":TARGET,
       "n_documents":len(splits),"n_future_queries":len(records),
       "n_observed_new_queries":sum(len(x["observed_new_ids"]) for x in splits),
       "n_historical_queries":sum(len(x["historical_ids"]) for x in splits),
       "placement":{name:test_stats(records,name) for name in modes},
       "paired":{"online_vs_static":bootstrap(records,"online_10pct","static"),
                 "full_rebuild_vs_static":bootstrap(records,"full_rebuild","static"),
                 "online_vs_full_rebuild":bootstrap(records,"online_10pct","full_rebuild"),
                 "static_vs_structure":bootstrap(records,"static","structure")},
       "migration":{"total_page_moves_online":sum(x["online_moves"] for x in splits),
          "total_page_moves_full_rebuild":sum(x["full_rebuild_moved_pages"] for x in splits),
          "total_page_budget":sum(x["migration_budget_pages"] for x in splits),
          "total_original_pages":sum(x["n_pages"] for x in splits),
          "online_moved_pct":round(100*sum(x["online_moves"] for x in splits)/sum(x["n_pages"] for x in splits),3),
          "full_rebuild_moved_pct":round(100*sum(x["full_rebuild_moved_pages"] for x in splits)/sum(x["n_pages"] for x in splits),3)},
       "cautions":["Only oracle ground-truth source page support proxy, no actual retrieval accuracy or latency",
          "History and feedback use gold answer support pages as ideal observed traces",
          "Test future queries unseen, but source documents shared with observed feedback",
          "Swap refinement and full METIS rebuild are pre-existing simple methods, NOT novel",
          "Equal-weight page capacity, not real byte memory or replica updates",
          "This is post-exploration on the same benchmark, so estimates are exploratory"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(r)+"\n" for r in records))
    OUT.joinpath("manifest.json").write_text(json.dumps(splits,indent=2))
    print("ONLINE_GATE_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("ONLINE_GATE_END",flush=True)
if __name__=="__main__":main()
