#!/usr/bin/env python3
"""Online shard-local cache replication with *equal hard storage budgets*.

Observed phase-2 support traces are the only feedback. Future test support
labels are held out from all placement and replication decisions. This remains
an oracle-trace proxy, not real GraphRAG request routing.
"""
import itertools,json,math,os,random
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import pilot
from online_adaptation import bootstrap,test_stats
SEED=310119;K=4
SOURCE=os.environ.get("ONLINE_SOURCE","bridge_chain")
assert SOURCE in ("bridge_chain","synthesis")
TARGET="synthesis" if SOURCE=="bridge_chain" else "bridge_chain"
OUT=Path("results_replication_"+SOURCE);OUT.mkdir(exist_ok=True)

def select_copies(primary,history,budget,method):
    """Deterministic cap-aware document-page replicas; at most one extra per page."""
    n=len(primary);limit=math.ceil((n+budget)/K)
    counts=Counter(primary);extra=Counter()
    used=set();copies=set()
    queries=[(pilot.pages(q),q) for q in history]
    universe=list(range(n)) # identical candidate page universe for all methods
    possibilities=[(p,s) for p in universe for s in range(K) if s!=primary[p]]
    # All strategies use identical page-copy limits and shard storage ceiling.
    for _ in range(budget):
        gains=[]
        if method=="greedy":
            base=[pilot.min_active(pp,primary,copies) for pp,q in queries]
        for p,s in possibilities:
            if p in used or counts[s]+extra[s]>=limit:continue
            if method=="frequency":
                benefit=sum((p in pp) and any(primary[v]==s for v in pp if v!=p)
                            for pp,q in queries)
                freq=sum(p in pp for pp,q in queries)
                key=(benefit,freq,-p,-s)
            elif method=="greedy":
                gain=sum(start-pilot.min_active(pp,primary,copies|{(p,s)})
                         for (pp,q),start in zip(queries,base))
                # Even zero-gain replicas are allocated so storage is equal.
                freq=sum(p in pp for pp,q in queries)
                key=(gain,freq,-p,-s)
            else:raise ValueError(method)
            gains.append((key,p,s))
        if not gains:break
        _,p,s=max(gains)
        copies.add((p,s));used.add(p);extra[s]+=1
    assert len(copies)<=budget
    assert all(counts[s]+extra[s]<=limit for s in range(K))
    return copies

def main():
    qs=pilot.download("annotations/benchmark.json")
    manifest=pilot.download("manifest.json")
    ns={int(d["doc_id"]):len(d["files"]["page_images"]) for d in manifest["documents"]}
    group=defaultdict(list)
    for q in qs:
        pp=pilot.pages(q);d=int(q["doc_id"])
        if len(pp)>=2 and pp and min(pp)>=0 and max(pp)<ns[d]:group[d].append(q)
    rows=[];infos=[]
    for doc in sorted(group):
        n=ns[doc]
        if n<20:continue
        past=[x for x in group[doc] if x["question_type"]==SOURCE]
        incoming=[x for x in group[doc] if x["question_type"]==TARGET]
        if len(past)<2 or len(incoming)<4:continue
        rng=random.Random(SEED+doc);rng.shuffle(incoming)
        split=max(2,len(incoming)//2)
        seen,future=incoming[:split],incoming[split:]
        if len(future)<2:continue
        old=pilot.metis_pages(n,K,past,400)
        structure=pilot.metis_pages(n,K,past,0)
        budget=max(1,int(.05*n))
        # Main fairest comparison uses EXACT same base assignment.
        candidates={
          "old_static":(old,set()),
          "structure_static":(structure,set()),
          "old_hist_freq":(old,select_copies(old,past,budget,"frequency")),
          "old_hist_greedy":(old,select_copies(old,past,budget,"greedy")),
          "old_update_freq":(old,select_copies(old,past+seen,budget,"frequency")),
          "old_update_greedy":(old,select_copies(old,past+seen,budget,"greedy")),
          "old_feedback_freq":(old,select_copies(old,seen,budget,"frequency")),
          "structure_update_freq":(structure,select_copies(structure,past+seen,budget,"frequency"))
        }
        totals={key:len(copies) for key,(part,copies) in candidates.items()}
        if len({totals[k] for k in ("old_hist_freq","old_hist_greedy",
             "old_update_freq","old_update_greedy","old_feedback_freq")})!=1:
            # Do not silently report unfair equal-budget comparisons.
            raise AssertionError(f"Unequal copy count in doc {doc}: {totals}")
        infos.append({"doc_id":doc,"pages":n,"budget":budget,"copies":totals,
           "seen_ids":[q.get("mh_id") or q.get("sq_id") for q in seen],
           "future_ids":[q.get("mh_id") or q.get("sq_id") for q in future]})
        for q in future:
            pp=pilot.pages(q)
            row={"doc_id":doc,"qid":q.get("mh_id") or q.get("sq_id"),
                 "n_evidence_pages":len(pp)}
            for key,(part,copies) in candidates.items():
                row[key]=pilot.min_active(pp,part,copies)
            rows.append(row)
    assert len(rows)>175 and len(infos)>=35,(len(rows),len(infos))
    methods=list(candidates)
    report={"schema":"realtime-shift-copy-capped-v1",
      "seed":SEED,"history_family":SOURCE,"new_family":TARGET,
      "n_docs":len(infos),"n_future_queries":len(rows),
      "n_observed_new_queries":sum(len(x["seen_ids"]) for x in infos),
      "n_pages":sum(x["pages"] for x in infos),
      "total_copies":sum(x["copies"]["old_hist_freq"] for x in infos),
      "page_copy_budget":sum(x["budget"] for x in infos),
      "copies_pct":round(100*sum(x["copies"]["old_hist_freq"] for x in infos)/sum(x["pages"] for x in infos),3),
      "methods":{m:test_stats(rows,m) for m in methods},
      "paired":{
        "update_frequency_vs_history_frequency":bootstrap(rows,"old_update_freq","old_hist_freq"),
        "update_greedy_vs_history_greedy":bootstrap(rows,"old_update_greedy","old_hist_greedy"),
        "update_greedy_vs_update_frequency":bootstrap(rows,"old_update_greedy","old_update_freq"),
        "feedback_frequency_vs_history_frequency":bootstrap(rows,"old_feedback_freq","old_hist_freq"),
        "update_frequency_vs_no_copy":bootstrap(rows,"old_update_freq","old_static"),
        "history_frequency_vs_no_copy":bootstrap(rows,"old_hist_freq","old_static"),
        "structure_updated_frequency_vs_structure_static":bootstrap(rows,"structure_update_freq","structure_static")},
      "limitations":["Gold TRAIN supports emulate successful observed query traces; future gold is used only in scorer",
        "No direct image pixels, extraction KG, distributed latency, actual byte-memory or router",
        "One replica per page, globally <= floor(5% pages), every destination shard <= ceil((pages+budget)/4)",
        "All comparison methods on original METIS base have exactly the same replica counts",
        "Zero-feedback page candidates are legal and may be chosen after positive-value candidates to satisfy equal-copy budget",
        "All test questions unseen when selecting copies, yet same documents",
        "Re-choosing replicated pages ignores real invalidation and copy replacement bandwidth",
        "Exploratory after repeated reuse of the benchmark; not an independent confirmation"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
    OUT.joinpath("split_manifest.json").write_text(json.dumps(infos,indent=2))
    print("REPLICATION_GATE_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("REPLICATION_GATE_END",flush=True)
if __name__=="__main__":main()
