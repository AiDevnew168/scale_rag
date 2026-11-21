#!/usr/bin/env python3
"""WatDiv10M real predicate-byte, strict-family heldout PTCR stress test.

External corpus, no temporal sequence: five deterministic pseudo-time splits
by disjoint predicate-set families. In fold t: 2 groups historic, one recent
'previous month', one observed 'day0', one untouched test. This synthetic
order is NOT actual future timestamps. First swap day0 head-greedy, second
scored solely from previous patterns; compare with equal-byte-budget
day0-only second-greedy and no move. All stages share hard <=10% byte cap
and <=25MB raw N-Triples movement per one 2-swap decision.
"""
import hashlib, json, math
from collections import Counter
from pathlib import Path
import candidate3_official_watdiv_byte_transfer as wd

SEED=20261121
BUDGET=25_000_000
K=5
OUT=Path("results_candidate3_PTCR_watdiv_family_stress");OUT.mkdir(exist_ok=True)

def move(route,loads,weights,pair,cap):
    result={p:set(s) for p,s in route.items()}
    load=list(loads)
    if pair is None:return result,load,0
    a,b=pair
    assert len(route[a])==len(route[b])==1 and route[a]!=route[b]
    old_a=next(iter(route[a]));old_b=next(iter(route[b]))
    load[old_a]+=weights[b]-weights[a]
    load[old_b]+=weights[a]-weights[b]
    assert max(load)<=cap and min(load)>=0,(load,cap)
    result[a]={old_b};result[b]={old_a}
    return result,load,weights[a]+weights[b]

def changes(rows,static,part):
    cnt=Counter(r["pattern"] for r in rows)
    old={p:wd.span(static,p) for p in cnt}
    new={p:wd.span(part,p) for p in cnt}
    return {"n":len(rows),
      "request_touches_saved":sum(n*(old[p]-new[p]) for p,n in cnt.items()),
      "distinct_local_gain":sum(int(new[p]==1)-int(old[p]==1) for p in cnt),
      "distinct_patterns":len(cnt),
      "local_pct":round(100*sum(n*(new[p]==1) for p,n in cnt.items())/len(rows),3) if rows else None}

def select_first_under_same_budget(original,weights,loads,cap,day0):
    patterns=Counter(r["pattern"] for r in day0)
    baseline={p:wd.span(original,p) for p in patterns}
    available=sorted(p for p,loc in original.items() if len(loc)==1)
    best=(0,None,None)
    valid=0
    for idx,p in enumerate(available):
        for q in available[idx+1:]:
            if original[p]==original[q]:continue
            cost=weights[p]+weights[q]
            if cost>BUDGET:continue
            a=next(iter(original[p]));b=next(iter(original[q]))
            if loads[a]-weights[p]+weights[q]>cap or loads[b]-weights[q]+weights[p]>cap:continue
            valid+=1
            moved,_,_=move(original,loads,weights,(p,q),cap)
            gain=sum(n*(int(wd.span(moved,pat)==1)-int(baseline[pat]==1))
                     for pat,n in patterns.items() if p in pat or q in pat)
            rank=(gain,-cost)
            if rank>best[:2]:
                best=(gain,-cost,(p,q))
    return best[2] if best[0]>0 else None,{"eligible_under_25MB":valid,
        "selected_day0_local_gain":best[0],"selected_move_bytes":-best[1] if best[0]>0 else 0}

def choose(static,one,loads,weights,cap,day0,previous,first_cost):
    # Previous traces are structurally disjoint from the original history set.
    # Both observed and previous are causally accessible for this pseudo-time.
    head=changes(day0,static,one)["distinct_local_gain"]
    # Use WEIGHTED request local gain for head threshold (not distinct).
    def weighted_local(rows,part):
        count=Counter(r["pattern"] for r in rows)
        return sum(n*(wd.span(part,p)==1) for p,n in count.items())
    head=weighted_local(day0,one)-weighted_local(day0,static)
    assert head>=0
    options=[]
    available=sorted(p for p,loc in one.items() if len(loc)==1)
    for ix,a in enumerate(available):
        for b in available[ix+1:]:
            if one[a]==one[b]:continue
            aa=next(iter(one[a]));bb=next(iter(one[b]))
            if loads[aa]-weights[a]+weights[b]>cap:continue
            if loads[bb]-weights[b]+weights[a]>cap:continue
            cost=weights[a]+weights[b]
            if first_cost+cost>BUDGET:continue
            moved,_,_=move(one,loads,weights,(a,b),cap)
            d=changes(previous,static,moved)
            hd=weighted_local(day0,moved)-weighted_local(day0,static)
            options.append({"second_swap":[a,b],
                "total_migration_bytes":first_cost+cost,
                "day0_local_gain":hd,
                "prior_request_touches_saved":d["request_touches_saved"],
                "prior_distinct_local_gain":d["distinct_local_gain"]})
    primary=changes(previous,static,one)
    fallback={"second_swap":None,"total_migration_bytes":first_cost,
        "day0_local_gain":head,
        "prior_request_touches_saved":primary["request_touches_saved"],
        "prior_distinct_local_gain":primary["distinct_local_gain"]}
    options.append(fallback)
    def argmax(cands,field,penalty=False):
        if not cands:return {"second_swap":None,"is_static":True,"total_migration_bytes":0}
        return max(cands,key=lambda r:(r[field],
              -r["total_migration_bytes"],r["day0_local_gain"],
              str(r["second_swap"])))
    safe=[r for r in options if r["prior_request_touches_saved"]>=0
          and r["prior_distinct_local_gain"]>=0 and r["day0_local_gain"]>=.9*head]
    selected={
      "one_swap":fallback,
      "two_swap_day0_greedy":argmax(options,"day0_local_gain"),
      "PTCR_90_prior_tail":argmax(safe,"prior_request_touches_saved"),
      "PTCR_90_head":argmax(safe,"day0_local_gain")}
    # Equal total byte budget, gain-per-byte greedy control
    viable=[r for r in options if r["total_migration_bytes"]>0]
    if viable:
        chosen=max(viable,key=lambda r:(r["day0_local_gain"]/r["total_migration_bytes"],
           r["day0_local_gain"],-r["total_migration_bytes"]))
        selected["two_swap_day0_per_byte"]=chosen
    else:selected["two_swap_day0_per_byte"]=fallback
    return selected,{"evaluated_second_swaps":len(options)-1,
      "safe_eligible":len(safe),"head_first":head,
      "first_migration_bytes":first_cost}

def main():
    graph=wd.grab(wd.DATA,85*1024*1024,wd.HASH_GRAPH)
    weights,phys=wd.physical_size_table(graph);del graph
    corpora=wd.parse_workloads(wd.grab(wd.QUERIES,40*1024*1024,wd.HASH_QUERY))
    records=corpora["watdiv-stress-100/warmup.sparql"]["records"]
    records=[r for r in records if len(r["pattern"])>=2 and
       all(p in weights for p in r["pattern"])]
    patterns=sorted({r["pattern"] for r in records})
    assert len(patterns)==121
    order=sorted(patterns,key=lambda p:hashlib.sha256(
      ("locked-pattern-fold-v1:"+str(SEED)+":"+json.dumps(p)).encode()).hexdigest())
    folds={p:i%K for i,p in enumerate(order)}
    _,original,original_loads,cap=wd.byte_layout(weights)
    fold_reports=[]
    for testfold in range(K):
        groups={
          "historic":[(testfold+2)%K,(testfold+3)%K],
          "previous":[(testfold+1)%K],
          "current_day0":[(testfold+4)%K],
          "test":[testfold]}
        partition={label:[r for r in records if folds[r["pattern"]] in fids]
                   for label,fids in groups.items()}
        ids={label:{r["pattern"] for r in rows} for label,rows in partition.items()}
        for a in ids:
            for b in ids:
                if a!=b:assert not(ids[a]&ids[b])
        pair,baseline_search=select_first_under_same_budget(
          original,weights,original_loads,cap,partition["current_day0"])
        one,loads,first_cost=move(original,original_loads,weights,pair,cap)
        assert first_cost<=BUDGET
        chosen,detail=choose(original,one,loads,weights,cap,
          partition["current_day0"],partition["previous"],first_cost)
        scores={}
        for name,candidate in chosen.items():
            if candidate.get("is_static",False):part=original;paid=0
            else:part,_,second_cost=move(one,loads,weights,candidate["second_swap"],cap)
            actual_cost=(first_cost if not candidate.get("is_static",False) else 0)+(
                0 if candidate.get("is_static",False) or candidate.get("second_swap") is None
                else sum(weights[p] for p in candidate["second_swap"]))
            assert actual_cost<=BUDGET
            result=changes(partition["test"],original,part)
            scores[name]={"decision":candidate,"real_predicate_raw_move_bytes":actual_cost,
              "heldout":result,
              "ideal_100Mbps_line_rate_transfer_ms":round(actual_cost*8/100_000,3),
              "break_even_ms_per_saved_touch_at_100Mbps":
                 round(actual_cost*8/100_000/result["request_touches_saved"],4)
                   if result["request_touches_saved"]>0 else None}
        fold_reports.append({"heldout_fold":testfold,
          "n_test":len(partition["test"]),
          "n_history":len(partition["historic"]),
          "n_previous":len(partition["previous"]),
          "n_day0":len(partition["current_day0"]),
          "pattern_family_overlap_all_stages":0,
          "first_day0_swap":pair,
          "search_diagnostics":detail,
          "methods":scores})
    summary={}
    for method in fold_reports[0]["methods"]:
        xs=[r["methods"][method]["heldout"]["request_touches_saved"] for r in fold_reports]
        bs=[r["methods"][method]["real_predicate_raw_move_bytes"] for r in fold_reports]
        summary[method]={"saved_touches_all_5fold":sum(xs),
          "total_raw_migrated_bytes_all_5fold":sum(bs),
          "positive_folds":sum(x>0 for x in xs),
          "negative_folds":sum(x<0 for x in xs),
          "zero_folds":sum(x==0 for x in xs)}
    report={"schema":"candidate3-WatDiv10M-disjoint-pseudo-month-two-swap-byte-budget-v1",
      "graph_sha256":wd.HASH_GRAPH,"queries_sha256":wd.HASH_QUERY,
      "n_triples":phys["triples_parsed"],"n_eligible_queries":len(records),
      "n_distinct_predicate_families":len(patterns),
      "per_decision_raw_NTriples_migration_budget":BUDGET,
      "per_shard_raw_data_cap_bytes":cap,
      "physical_byte_shard_balance":original_loads,
      "method":"Historical 2 folds, causally prior 1 fold, day0 1 fold, heldout 1 fold; deterministic fold groups with no exact pattern overlap; synthetic pseudo-time",
      "folds":fold_reports,"summary":summary,
      "known_limitations":[
        "NOT real chronological source: pseudo-month labels are artificial and based on synthetic generated query families",
        "Corpus was inspected and used earlier; NOT an independent prospective test",
        "Raw serialized NTriples weights exact, but physical fragment routing and index update not executed",
        "No SPARQL answer execution, P95 latency, actual migration duration or monetary net benefit",
        "First stage and second stage use complete prior/day0 pseudo-family partitions, not 24h traffic windows",
        "Zero harm only constrained on PREVIOUS patterns, not guaranteed for unseen heldout",
        "One-swap baseline can use less migration than two-swap; all strategies have same *maximum* 25MB byte budget",
        "WISE/WASP/MTGA and memory-matched replication not implemented",
        "This heuristic does not yet establish method novelty or prior-art superiority"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    short={k:v for k,v in report.items() if k!="folds"}
    short["folds"]=[{"fold":r["heldout_fold"],"test_n":r["n_test"],
       "first_swap":r["first_day0_swap"],"search":r["search_diagnostics"],
       "metrics":{name:{"saved":v["heldout"]["request_touches_saved"],
                   "bytes":v["real_predicate_raw_move_bytes"]}
           for name,v in r["methods"].items()}} for r in fold_reports]
    print("PTCR_WATDIV_DISJOINT_START",flush=True)
    print(json.dumps(short,indent=2),flush=True)
    print("PTCR_WATDIV_DISJOINT_END",flush=True)
if __name__=="__main__":main()
