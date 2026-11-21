#!/usr/bin/env python3
"""Candidate 3: anchored second-swap feasibility frontier and deployable controls.

Fixed June-2017-trained 120-ID Mt-KaHyPar baseline. Original day0-only
highest locality first swap is UNCHANGED. Enumerate every possible second
balanced swap (5,400), in a new two-swap action budget. Oracle uses future
ONLY to establish an upper bound, NEVER as deployable policy. Compare
training-only greedy second swap and no second swap fairly.

All Jan/Feb/Mar 2018 data have ALREADY been inspected: exploratory only.
No physical predicate RDF byte weights; per-swap cost is ID movement count.
"""
import datetime, json, os, time
from collections import Counter, defaultdict
from pathlib import Path
import temporal_wikidata as base
import hyperedge_generalization as hg
import december_burst_swap as locked

MONTHS={
 "january":("2018-01-01_2018-01-28", datetime.datetime(2018,1,1)),
 "february":("2018-01-29_2018-02-25", datetime.datetime(2018,1,29)),
 "march":("2018-02-26_2018-03-25", datetime.datetime(2018,2,26)),
}
month=os.environ.get("COMP_MONTH","january")
assert month in MONTHS
span,start=MONTHS[month]
url="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/"+span+"/"+span+"_organic.tsv.gz"
out=Path("results_candidate3_compensated_"+month);out.mkdir(exist_ok=True)

def index_rows(rows):
    counts=Counter(q for _,q in rows)
    pats=sorted(counts)
    weights=[counts[q] for q in pats]
    links=defaultdict(set)
    for k,q in enumerate(pats):
        for x in q:links[x].add(k)
    return pats,weights,links

def candidate_metrics(part,obs,fu,known,reference):
    op,ow,ol=index_rows(obs)
    fp,fw,fl=index_rows(fu)
    novel=[int(q not in known) for q in fp]
    base_os=[locked.span(reference,q) for q in op]
    base_fs=[locked.span(reference,q) for q in fp]
    curr_os=[locked.span(part,q) for q in op]
    curr_fs=[locked.span(part,q) for q in fp]
    base_obs_local=sum(w*int(s==1) for s,w in zip(base_os,ow))
    base_ft=sum(w*(s-1) for s,w in zip(base_fs,fw))
    base_novel_ft=sum(w*(s-1) for s,w,n in zip(base_fs,fw,novel) if n)
    base_novel_local=sum(int(s==1) for s,n in zip(base_fs,novel) if n)
    def from_spans(os,fs):
        return {
         "day0_local_gain":sum(w*int(s==1) for s,w in zip(os,ow))-base_obs_local,
         "future_touches_saved":base_ft-sum(w*(s-1) for s,w in zip(fs,fw)),
         "novel_request_touches_saved":base_novel_ft-sum(w*(s-1) for s,w,n in zip(fs,fw,novel) if n),
         "novel_distinct_local_gain":sum(int(s==1) for s,n in zip(fs,novel) if n)-base_novel_local
        }
    first=from_spans(curr_os,curr_fs)
    best_actual=None;choices=[]
    working=list(part)
    for i in range(len(part)):
        for j in range(i+1,len(part)):
            if part[i]==part[j]:continue
            # Score only queries touched by this second exchange.
            obsidx=ol[i]|ol[j]
            futidx=fl[i]|fl[j]
            working[i],working[j]=working[j],working[i]
            gd=0;ft=0;nt=0;nl=0
            for k in obsidx:
                s=locked.span(working,op[k])
                gd+=ow[k]*(int(s==1)-int(curr_os[k]==1))
            for k in futidx:
                s=locked.span(working,fp[k]);delta=curr_fs[k]-s
                ft+=fw[k]*delta
                if novel[k]:
                    nt+=fw[k]*delta
                    nl+=int(s==1)-int(curr_fs[k]==1)
            working[i],working[j]=working[j],working[i]
            record={
                "second_swap":[i,j],
                "day0_local_gain":first["day0_local_gain"]+gd,
                "future_touches_saved":first["future_touches_saved"]+ft,
                "novel_request_touches_saved":first["novel_request_touches_saved"]+nt,
                "novel_distinct_local_gain":first["novel_distinct_local_gain"]+nl,
                "second_step_day0_gain":gd,
                "future_delta_over_first":ft
            }
            choices.append(record)
    assert len(choices)==5400
    def best(records,objective):
        if not records:return None
        return max(records,key=lambda z:(
          z[objective],z["day0_local_gain"],-z["second_swap"][0],-z["second_swap"][1]))
    def brief(x):return x
    first_row={"second_swap":None,**first}
    all_records=choices+[first_row]
    head_threshold=int(.9*first["day0_local_gain"]+0.99999)
    regimes={
        "best_unrestricted_future_oracle":all_records,
        "best_joint_novel_safe_oracle":[x for x in all_records if
          x["novel_request_touches_saved"]>=0 and x["novel_distinct_local_gain"]>=0],
        "best_joint_safe_and_ge90_head_oracle":[x for x in all_records if
          x["novel_request_touches_saved"]>=0 and x["novel_distinct_local_gain"]>=0
          and x["day0_local_gain"]>=head_threshold],
        "best_ge90_head_future_oracle":[x for x in all_records if
          x["day0_local_gain"]>=head_threshold],
        "best_ge75_head_joint_safe_oracle":[x for x in all_records if
          x["novel_request_touches_saved"]>=0 and x["novel_distinct_local_gain"]>=0
          and x["day0_local_gain"]>=.75*first["day0_local_gain"]],
    }
    results={name:{"eligible":len(records),
       "best":brief(best(records,"future_touches_saved")) if records else None}
       for name,records in regimes.items()}
    # Unlike the oracle, deployable controls have no access to future rows.
    # Best empirical head second swap, with deterministic tie break.
    greedy=max(choices,key=lambda x:(x["day0_local_gain"],
            -x["second_swap"][0],-x["second_swap"][1]))
    if greedy["day0_local_gain"]<first["day0_local_gain"]:
        greedy=first_row
    # Main novelty diagnostic: exact one-swap upper bound already available
    # from previous independent script. No expectation that greedy improves future.
    selected={
      "one_swap_original_frozen":first_row,
      "two_swap_day0_greedy":greedy,
    }
    return {"reference":{"future_n":len(fu),"day0_n":len(obs),
                           "future_unique_patterns":len(fp),
                           "novel_unique":sum(novel),
                           "base_future_extra_touches":base_ft},
       "first_swap":first,
       "head_threshold_90pct_day0":head_threshold,
       "hindsight_oracle_regimes":results,
       "deployable_controls":selected,
       "two_swap_candidates":len(choices)}

def main():
    started=time.perf_counter()
    june,jsha=base.load()
    old=[(d,q) for d,q in june if d<14]
    f=Counter()
    for _,q in old:f.update(set(q))
    selected=tuple(p for p,_ in sorted(f.items(),key=lambda z:(-z[1],z[0]))[:120])
    hist,_=base.prop_stats(old,selected)
    part,_=hg.hybrid(hist,120,0)
    assert sorted(Counter(part).values())==[30,30,30,30]
    raw,rsha=hg.period(url,start)
    period,_=base.prop_stats(raw,selected)
    first_day=min(d for d,_ in period)
    observed=[r for r in period if r[0]==first_day]
    future=[r for r in period if r[0]>first_day]
    first,selection=locked.optimizer_one_swap(part,observed)
    assert selection["move"] and selection["training_day0_saved_requests"]>0
    report=candidate_metrics(first,observed,future,
            {q for _,q in hist},part)
    assert report["first_swap"]["day0_local_gain"]==selection["training_day0_saved_requests"]
    report.update({
       "schema":"candidate3-anchored-exhaustive-second-swap-compensation-v1",
       "month":month,
       "original_sources_sha256":{"June":jsha,"evaluation":rsha},
       "first_locked_day0_swap":selection["move"],
       "first_locked_day0_details":selection,
       "elapsed_sec":round(time.perf_counter()-started,1),
       "limitations":[
          "2-swap ORACLE uses future labels only for feasibility; NOT a predictive algorithm or fair competitor",
          "Only second swap exhaustive with first locked frozen; NOT all possible two-swap combinations",
          "Day0 greedy control uses only day0, never future",
          "All Jan-Feb-Mar workloads previously inspected; NOT new prospective evidence",
          "Hard constraint is count=30 IDs per shard, NOT physical RDF bytes",
          "Cost doubles for 2 swaps unless overlapping positions; real byte cost unmeasured",
          "Novel = absent from June training; no per-future-query protection guarantee",
          "SPARQL query predicate sets only, no full SPARQL joins or RAG QA"]})
    out.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("COMPENSATION_ORACLE_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("COMPENSATION_ORACLE_END",flush=True)

if __name__=="__main__":main()
