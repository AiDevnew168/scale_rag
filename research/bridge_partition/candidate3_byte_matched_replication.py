#!/usr/bin/env python3
"""Candidate 3: budget-matched selective replication / swap+replica adversary.

Uses pinned WatDiv10M 10.9M physical NTriples and 121 predicate families.
All five pseudo-time folds have ZERO family overlap among past, day0 and
heldout test. An action costs raw serialized RDF bytes and consumes storage
in the target shard, which stays within a strict +10% mean-byte limit.
Budget 25 MB for every tested policy; no test labels used for decisions.

A fragment of an elephant predicate MUST be read from every shard that
owns a fragment. A fully replicated (unsplit) predicate may be read from
ANY shard with one copy. Thus routing span = exact 4-shard set-cover.
No full query execution. Prior dataset was inspected earlier: exploratory.
"""
import hashlib,json,math
from collections import Counter
from pathlib import Path
import candidate3_official_watdiv_byte_transfer as wd
import candidate3_ptcr_watdiv_byte_stress as ptcr

SEED=20261121
K=5
CAP_BUDGET=25_000_000
OUT=Path("results_candidate3_selective_replica")
OUT.mkdir(exist_ok=True)

def span(locations,pattern,fragments):
    mandatory=0
    singleton=[]
    for p in pattern:
        shards=locations[p]
        if p in fragments:
            for j in shards:mandatory|=1<<j
        else:
            singleton.append(sum(1<<j for j in shards))
    best=5
    for mask in range(1,16):
        if mask&mandatory!=mandatory:continue
        if all(mask&options for options in singleton):
            best=min(best,mask.bit_count())
    assert best<=4,(pattern,locations)
    return best

def scores(rows,static,placement,fragments):
    freqs=Counter(r["pattern"] for r in rows)
    return {"n":len(rows),"pattern_families":len(freqs),
      "touches_saved":sum(n*(span(static,q,fragments)-span(placement,q,fragments)) for q,n in freqs.items()),
      "distinct_single_shard_gain":sum(
          int(span(placement,q,fragments)==1)-int(span(static,q,fragments)==1)
          for q in freqs)}

def choose_replica(current,static,weights,loads,cap,spent,observed,prior,fragments,head_min=None,
                   objective="all"):
    # Single-copy no-op is always allowed, and may dominate all candidates.
    assert spent<=CAP_BUDGET
    original_head=scores(observed,static,current,fragments)["touches_saved"]
    baseline_previous=scores(prior,static,current,fragments)["touches_saved"]
    if head_min is None:head_min=-10**9
    ranked=(0.0,0,0,None,None)
    valid=0
    for p in sorted(weights):
        if p in fragments:continue
        if len(current[p])!=1:continue
        moved=weights[p]
        if spent+moved>CAP_BUDGET:continue
        for target in range(4):
            if target in current[p] or loads[target]+moved>cap:continue
            altered={k:v for k,v in current.items()}
            altered[p]=current[p]|{target}
            head=scores(observed,static,altered,fragments)["touches_saved"]
            if head<head_min:continue
            previous=scores(prior,static,altered,fragments)["touches_saved"]
            if objective=="all":
                utility=(head-original_head)+(previous-baseline_previous)
            elif objective=="previous":
                utility=previous-baseline_previous
            elif objective=="day0":
                utility=head-original_head
            elif objective=="per_byte":
                utility=((head-original_head)+(previous-baseline_previous))/moved
            else:raise ValueError(objective)
            rank=(utility,-moved,head,p,target)
            valid+=1
            if rank>ranked:
                ranked=rank
    # Need positive gain. Never pay bytes just to reassign no measurable gain.
    p,target=ranked[3],ranked[4]
    if p is None:
        return current,loads,{"replica":None,"extra_bytes":0,
                 "head_held":original_head,"safe_previous":baseline_previous,
                 "options_eligible":valid}
    new={k:set(v) for k,v in current.items()};new[p].add(target)
    loads_new=list(loads);loads_new[target]+=weights[p]
    assert max(loads_new)<=cap
    return new,loads_new,{"replica":[p,target],"extra_bytes":weights[p],
        "head_held":scores(observed,static,new,fragments)["touches_saved"],
        "safe_previous":scores(prior,static,new,fragments)["touches_saved"],
        "options_eligible":valid}

def main():
    graph=wd.grab(wd.DATA,85*1024*1024,wd.HASH_GRAPH)
    weights,phys=wd.physical_size_table(graph)
    del graph
    groups=wd.parse_workloads(wd.grab(wd.QUERIES,40*1024*1024,wd.HASH_QUERY))
    rec=[r for r in groups["watdiv-stress-100/warmup.sparql"]["records"]
       if len(r["pattern"])>=2 and all(p in weights for p in r["pattern"])]
    patterns=sorted({r["pattern"] for r in rec})
    assert len(patterns)==121
    order=sorted(patterns,key=lambda p:hashlib.sha256(
        ("locked-pattern-fold-v1:"+str(SEED)+":"+json.dumps(p)).encode()).hexdigest())
    membership={p:i%K for i,p in enumerate(order)}
    _,static,base_load,cap=wd.byte_layout(weights)
    fragmented={p for p,s in static.items() if len(s)>1}
    assert max(base_load)<=cap
    out=[]
    for fold in range(K):
        ids={"historic":[(fold+2)%K,(fold+3)%K],
             "previous":[(fold+1)%K],
             "day0":[(fold+4)%K],
             "heldout":[fold]}
        split={label:[r for r in rec if membership[r["pattern"]] in group]
               for label,group in ids.items()}
        assert len(set(r["pattern"] for r in split["previous"])&
                   set(r["pattern"] for r in split["heldout"]))==0
        day0=split["day0"];prior=split["previous"];future=split["heldout"]
        first,firstdetails=ptcr.select_first_under_same_budget(static,weights,base_load,cap,day0)
        one,one_load,one_bytes=ptcr.move(static,base_load,weights,first,cap)
        assert one_bytes<=CAP_BUDGET
        # Same budget robust move alternatives; use prior script for comparator.
        swap_policies,second_diag=ptcr.choose(static,one,one_load,weights,cap,day0,prior,one_bytes)
        results={}
        for method,info in swap_policies.items():
            if info.get("is_static",False):
                moved=static;spend=0
            else:
                moved,_,_=ptcr.move(one,one_load,weights,info["second_swap"],cap)
                spend=one_bytes+(
                  sum(weights[p] for p in info["second_swap"]) if info["second_swap"] else 0)
            assert spend<=CAP_BUDGET
            results[method]={"decision":info,
                "moved_serialized_bytes":spend,
                "test":scores(future,static,moved,fragmented),
                "previous":scores(prior,static,moved,fragmented),
                "day0":scores(day0,static,moved,fragmented)}
        for mode in ("all","per_byte","previous","day0"):
            moved,_,detail=choose_replica(static,static,weights,base_load,cap,0,day0,prior,fragmented,
                     objective=mode)
            results["replicate_only_"+mode]={"decision":detail,
                 "moved_serialized_bytes":detail["extra_bytes"],
                 "test":scores(future,static,moved,fragmented),
                 "previous":scores(prior,static,moved,fragmented),
                 "day0":scores(day0,static,moved,fragmented)}
        first_head=scores(day0,static,one,fragmented)["touches_saved"]
        for mode in ("previous","all","per_byte"):
            moved,loads,detail=choose_replica(one,static,weights,one_load,cap,one_bytes,
                day0,prior,fragmented,head_min=math.ceil(.9*first_head),objective=mode)
            total=one_bytes+detail["extra_bytes"]
            assert total<=CAP_BUDGET and max(loads)<=cap
            results["one_swap_plus_replica_"+mode]={"decision":detail,
                "moved_serialized_bytes":total,
                "test":scores(future,static,moved,fragmented),
                "previous":scores(prior,static,moved,fragmented),
                "day0":scores(day0,static,moved,fragmented)}
        out.append({"fold":fold,"n_test":len(future),"n_previous":len(prior),
                    "n_day0":len(day0),"first_swap":first,
                    "byte_capacity":cap,"first_swap_bytes":one_bytes,
                    "second_swap_diagnostics":second_diag,
                    "methods":results})
    methods=list(out[0]["methods"])
    summary={name:{"total_saved_touches":sum(f["methods"][name]["test"]["touches_saved"] for f in out),
             "total_migrated_bytes":sum(f["methods"][name]["moved_serialized_bytes"] for f in out),
             "fold_saved":[f["methods"][name]["test"]["touches_saved"] for f in out],
             "positive_folds":sum(f["methods"][name]["test"]["touches_saved"]>0 for f in out),
             "negative_folds":sum(f["methods"][name]["test"]["touches_saved"]<0 for f in out)}
             for name in methods}
    report={"schema":"candidate3-WatDiv10M-real-byte-capped-replication-vs-PTCR-v1",
       "source_sha":{"graph":wd.HASH_GRAPH,"query":wd.HASH_QUERY},
       "raw_ntriples_triples":phys["triples_parsed"],
       "raw_total_bytes":phys["raw_total_bytes"],
       "fragmented_predicates":sorted(fragmented),
       "budget_max_serialized_migration_bytes_per_fold":CAP_BUDGET,
       "byte_cap_per_shard":cap,"initial_shard_bytes":base_load,
       "exact_pattern_overlap_between_pretest_and_test":0,
       "results_by_fold":out,"summary":summary,
       "limitations":[
         "Same inspected WatDiv source; exploratory pseudo-time family-disjoint 5fold CV, NOT real new user chronological traffic",
         "Non-fragmented predicate replication uses true raw NTriple byte costs and capacity, routing uses exact four-shard minimum set cover",
         "A query involving fragmented elephant predicates must contact all shards storing their fragments",
         "No physical replica or full Oxigraph query execution; no actual indexes or replica synchronization overhead",
         "No WISE/WASP library, replication implementation benchmark or original research novelty proof",
         "Five folds reuse synthetic corpus; not independent domain replications",
         "A replica stores an EXTRA full predicate copy and its byte budget counts explicitly",
         "Equal maximum migration+replication cost 25MB; actual storage capacity also enforced",
         "Streaming graph bytes not materialized into physical 4-shard on-disk RDF stores",
         "No net production latency or monetary savings measured"] }
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    short={k:v for k,v in report.items() if k!="results_by_fold"}
    short["folds"]=[{"fold":f["fold"],"n_test":f["n_test"],
        "metrics":{m:{"saved":v["test"]["touches_saved"],
            "bytes":v["moved_serialized_bytes"],
            "decision":v["decision"]}
            for m,v in f["methods"].items()}} for f in out]
    print("SELECTIVE_REPLICA_GATE_START",flush=True)
    print(json.dumps(short,indent=2),flush=True)
    print("SELECTIVE_REPLICA_GATE_END",flush=True)
if __name__=="__main__":main()
