#!/usr/bin/env python3
"""Hard-migration-budget projection of fully recomputed partition.

Controls for previously observed 10%-budget swap failure. Ground-truth
support from the *future test* queries is scorer-only, never input to placement.
No novel algorithm claimed: these are ordinary projection/swap baselines.
"""
import itertools, json, math, os, random
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import pilot
from online_adaptation import bootstrap, test_stats, online_refine

SEED=310119
MODE=os.environ.get("ONLINE_SOURCE","bridge_chain")
assert MODE in ("bridge_chain","synthesis")
TARGET="synthesis" if MODE=="bridge_chain" else "bridge_chain"
OUT=Path("results_projection_"+MODE); OUT.mkdir(exist_ok=True)
K=4

def align_target(initial,target):
    perms=itertools.permutations(range(K))
    # Remap target labels into old label space. Labels have no semantic identity.
    perm=max(perms,key=lambda p:(sum(initial[i]==p[target[i]] for i in range(len(initial))),
                                   tuple(-x for x in p)))
    target=[perm[x] for x in target]
    return target

def oracle_hamming(a,b):
    best=min(sum(x!=perm[y] for x,y in zip(a,b))
             for perm in itertools.permutations(range(K)))
    return best

def costs(lab,qs):
    # Counts over exactly the visible historical or feedback query traces.
    if not qs:return 0,0
    spans=[len({lab[x] for x in pilot.pages(q)}) for q in qs]
    return sum(x==1 for x in spans),sum(x-1 for x in spans)

def project(initial,target,old_queries,new_queries,budget,strategy):
    """Swap projection with hard exactly conserved block counts.

    target: FULL rebuild from observable history + new feedback (no future).
    strategy:
      target_only: choose swap reducing target Hamming, tie-break feedback gain.
      feedback_gated: require feedback-span improvement; target distance tie-break.
      feedback_local: maximize observable local completions, tie-break target.
    """
    labels=list(initial)
    target=align_target(labels,target)
    moved=0
    old_old,old_span=costs(labels,old_queries)
    new_local,new_span=costs(labels,new_queries)
    for step in range(budget//2):
        opts=[]
        n=len(labels)
        for i in range(n):
            for j in range(i+1,n):
                if labels[i]==labels[j]:continue
                before=int(labels[i]!=target[i])+int(labels[j]!=target[j])
                after=int(labels[j]!=target[i])+int(labels[i]!=target[j])
                hgain=before-after
                if strategy in ("target_only","feedback_gated") and hgain<=0:
                    continue
                labels[i],labels[j]=labels[j],labels[i]
                lc,sp=costs(labels,new_queries)
                oc,os=costs(labels,old_queries)
                labels[i],labels[j]=labels[j],labels[i]
                gain_span=new_span-sp
                gain_local=lc-new_local
                gain_hist=old_span-os
                if strategy=="feedback_gated":
                    if gain_span<=0:continue
                    key=(gain_span,hgain,gain_local,gain_hist,-i,-j)
                elif strategy=="feedback_local":
                    if gain_local<=0:continue
                    key=(gain_local,gain_span,hgain,gain_hist,-i,-j)
                else:
                    key=(hgain,gain_span,gain_hist,-i,-j)
                opts.append((key,i,j,lc,sp,oc,os))
        if not opts:break
        _,i,j,new_local,new_span,old_old,old_span=max(opts)
        labels[i],labels[j]=labels[j],labels[i]
        moved+=2
    # swaps preserve exact old block counts and hard capacities
    assert Counter(labels)==Counter(initial)
    assert moved<=budget
    return labels,moved

def main():
    questions=pilot.download("annotations/benchmark.json")
    manifest=pilot.download("manifest.json")
    sizes={int(d["doc_id"]):len(d["files"]["page_images"])
           for d in manifest["documents"]}
    groups=defaultdict(list)
    for q in questions:
        pp=pilot.pages(q);d=int(q["doc_id"])
        if len(pp)>=2 and min(pp)>=0 and max(pp)<sizes[d]:
            groups[d].append(q)
    rows=[];docs=[]
    for doc in sorted(groups):
        n=sizes[doc]
        if n<20:continue
        hist=[q for q in groups[doc] if q["question_type"]==MODE]
        incoming=[q for q in groups[doc] if q["question_type"]==TARGET]
        if len(hist)<2 or len(incoming)<4:continue
        rng=random.Random(SEED+doc)
        rng.shuffle(incoming)
        nseen=max(2,len(incoming)//2)
        feedback,future=incoming[:nseen],incoming[nseen:]
        if len(future)<2:continue
        old=pilot.metis_pages(n,K,hist,400)
        rebuilt=pilot.metis_pages(n,K,hist+feedback,400)
        budget=math.floor(.10*n)
        variants={"static":old,"full_rebuild":rebuilt}
        migrations={"static":0,"full_rebuild":oracle_hamming(old,rebuilt)}
        adapt,m=online_refine(old,hist,feedback,budget)
        variants["old_span_swaps"]=adapt;migrations["old_span_swaps"]=m
        for strategy in ("target_only","feedback_gated","feedback_local"):
            candidate,m=project(old,rebuilt,hist,feedback,budget,strategy)
            variants[strategy]=candidate;migrations[strategy]=m
        for key,part in variants.items():
            assert max(Counter(part).values())<=math.ceil(n/K),(doc,key)
            if key not in ("static","full_rebuild"):
                assert migrations[key]<=budget
                assert oracle_hamming(old,part)<=migrations[key]
        docs.append({"doc_id":doc,"n_pages":n,"n_history":len(hist),
          "n_observed":len(feedback),"n_future":len(future),
          "move_budget":budget,"moves":migrations,
          "future_ids":[q.get("mh_id") or q.get("sq_id") for q in future]})
        for q in future:
            pp=pilot.pages(q)
            row={"doc_id":doc,"qid":q.get("mh_id") or q.get("sq_id"),
                 "kind":q["question_type"],"pages":len(pp)}
            for key,part in variants.items():
                row[key]=len({part[p] for p in pp})
            rows.append(row)
    assert len(rows)>=150 and len(docs)>=30,(len(rows),len(docs))
    keys=("static","old_span_swaps","target_only","feedback_gated","feedback_local","full_rebuild")
    report={"schema":"bounded-repartition-project-2026-v1",
      "source":"diandianone123/topographrag-bench","seed":SEED,
      "historical":MODE,"future":TARGET,"n_docs":len(docs),
      "n_test_queries":len(rows),
      "n_old_queries":sum(x["n_history"] for x in docs),
      "n_feedback_queries":sum(x["n_observed"] for x in docs),
      "budget":"floor(0.1*n_pages) moved pages per document, balance-preserving swaps",
      "metrics":{m:test_stats(rows,m) for m in keys},
      "paired":{f"{m}_vs_static":bootstrap(rows,m,"static") for m in keys[1:]},
      "migration":{m:{"moves":sum(x["moves"][m] for x in docs),
          "move_pct":round(100*sum(x["moves"][m] for x in docs)/sum(x["n_pages"] for x in docs),3)}
          for m in keys},
      "cautions":["All source page supports in history and feedback are oracle ideal successful query traces",
        "Future test gold never enters any placement; test source docs shared with historical query workload",
        "Full rebuild does not respect the 10% migration cap and is NOT a fair constrained competitor",
        "This is structural page locality, not end-to-end RAG, latency, RAM bytes, nor a KG",
        "Objectives and hyperparameters explored post hoc on the same benchmark",
        "Methods are simple pre-existing-style swap projections, not proposed novel graph optimization"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
    OUT.joinpath("splits.json").write_text(json.dumps(docs,indent=2))
    print("PROJECTION_GATE_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("PROJECTION_GATE_END",flush=True)

if __name__=="__main__":main()
