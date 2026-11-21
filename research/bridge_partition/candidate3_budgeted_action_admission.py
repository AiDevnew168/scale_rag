#!/usr/bin/env python3
"""BEND admission: byte-aware evidence-minimax action selection (EXPLORATORY).

Consumes frozen same-budget real-WatDiv10M data artifact from GitHub Actions
44871515750, not recomputed or adjusted. For each disjoint pseudo-time fold,
choose a mode from: no-op, swap, 2swap, replica-only, swap+replica. Training
only: prior pseudo-month, current day0; both disjoint from heldout.
No test labels used in choosing a policy. Compare to baselines under the
same hypothetical critical path + transport cost. No actual SPARQL runtime,
physical migration, index rebuild or independent real time-series here.
"""
import json, random
from pathlib import Path
SOURCE_RUN=44871515750
SOURCE_ARTIFACT=14693877818
SOURCE_SHA="5f67565e8e654aff0b521501c16062244de042f34c45d562463e3e194e4436fe"
ROOT=Path("bundle")
OUT=Path("results_candidate3_BEND")
OUT.mkdir(exist_ok=True)
CONFIGS=[(t,net) for t in (0,0.5,1,5,20) for net in (100,1000)]
SEED=20261121
METHODS=["one_swap","two_swap_day0_greedy","PTCR_90_prior_tail",
 "two_swap_day0_per_byte","replicate_only_all","replicate_only_per_byte",
 "replicate_only_previous","replicate_only_day0",
 "one_swap_plus_replica_previous","one_swap_plus_replica_all",
 "one_swap_plus_replica_per_byte"]
PROFILE_LABEL="assumed critical path milliseconds per saved extra shard TOUCH"

def transfer_ms(bytes_,mbps):
    return bytes_*8/(1000*mbps)

def net_test(method,t,mbps):
    return (method["test"]["touches_saved"]*t
        -transfer_ms(method["moved_serialized_bytes"],mbps))

def choose(methods,previous_n,day0_n,heldout_n,t,mbps,objective,
           head_target):
    control={"no_move":{"previous":{"touches_saved":0,"distinct_single_shard_gain":0},
      "day0":{"touches_saved":0,"distinct_single_shard_gain":0},
      "test":{"touches_saved":0},"moved_serialized_bytes":0}}
    available={**control,**{k:v for k,v in methods.items() if k in METHODS}}
    scored=[]
    for name,action in available.items():
        prev=action["previous"]["touches_saved"]/previous_n
        day0=action["day0"]["touches_saved"]/day0_n
        if objective=="mean":
            predict=.5*(prev+day0)
        elif objective=="maximin":
            predict=min(prev,day0)
        elif objective=="head_only":
            predict=day0
        elif objective=="prior_only":
            predict=prev
        elif objective=="nonregression_maximin":
            if (action["previous"]["touches_saved"]<0
                or action["previous"]["distinct_single_shard_gain"]<0
                or (name!="no_move" and action["day0"]["touches_saved"]<.9*head_target)):
                continue
            predict=min(prev,day0)
        else:raise ValueError(objective)
        predicted=heldout_n*predict*t-transfer_ms(action["moved_serialized_bytes"],mbps)
        scored.append((predicted,-action["moved_serialized_bytes"],name))
    assert scored
    score,_,name=max(scored)
    return name,score

def main():
    paths=list(ROOT.rglob("report.json"))
    assert len(paths)==1,paths
    source=json.loads(paths[0].read_text())
    assert source["schema"]=="candidate3-WatDiv10M-real-byte-capped-replication-vs-PTCR-v1"
    assert source["source_sha"]["graph"]=="1d0a8a4725c98974eb7347ce3e6d9cab44f9f40389589809674254151b745af6"
    assert len(source["results_by_fold"])==5
    assert source["budget_max_serialized_migration_bytes_per_fold"]==25_000_000
    assert source["exact_pattern_overlap_between_pretest_and_test"]==0
    profile={}
    for t,mbps in CONFIGS:
        key=f"assumed_{t:g}ms_per_touch_{mbps}Mbps"
        rows=[]
        methods_to_score={method:{"net_ms":0.0,"saved_touches":0,"bytes":0}
          for method in METHODS}
        for rule in ("mean","maximin","head_only","prior_only","nonregression_maximin"):
            methods_to_score["selector_"+rule]={"net_ms":0.0,"saved_touches":0,"bytes":0,"choices":[]}
        methods_to_score["never_move"]={"net_ms":0.0,"saved_touches":0,"bytes":0}
        methods_to_score["future_oracle_upper_bound"]={"net_ms":0.0,"saved_touches":0,"bytes":0,"choices":[]}
        for f in source["results_by_fold"]:
            scoremap=f["methods"]
            for method in METHODS:
                a=scoremap[method]
                methods_to_score[method]["net_ms"]+=net_test(a,t,mbps)
                methods_to_score[method]["saved_touches"]+=a["test"]["touches_saved"]
                methods_to_score[method]["bytes"]+=a["moved_serialized_bytes"]
            for rule in ("mean","maximin","head_only","prior_only","nonregression_maximin"):
                first_gain=scoremap["one_swap"]["day0"]["touches_saved"]
                choice,predicted=choose(scoremap,f["n_previous"],f["n_day0"],
                    f["n_test"],t,mbps,rule,first_gain)
                a=scoremap.get(choice,{"test":{"touches_saved":0},"moved_serialized_bytes":0})
                methods_to_score["selector_"+rule]["net_ms"]+=net_test(a,t,mbps)
                methods_to_score["selector_"+rule]["saved_touches"]+=a["test"]["touches_saved"]
                methods_to_score["selector_"+rule]["bytes"]+=a["moved_serialized_bytes"]
                methods_to_score["selector_"+rule]["choices"].append({"fold":f["fold"],"choice":choice,
                   "predicted_net_ms":round(predicted,4),"realized_test_net_ms":round(net_test(a,t,mbps),4)})
            # Upper bound hindsight oracle is NOT a deployable option.
            a=max([(0,"no_move",{"test":{"touches_saved":0},"moved_serialized_bytes":0})]
                +[(net_test(v,t,mbps),k,v) for k,v in scoremap.items() if k in METHODS],
                key=lambda x:(x[0],-x[2]["moved_serialized_bytes"]))
            methods_to_score["future_oracle_upper_bound"]["net_ms"]+=a[0]
            methods_to_score["future_oracle_upper_bound"]["saved_touches"]+=a[2]["test"]["touches_saved"]
            methods_to_score["future_oracle_upper_bound"]["bytes"]+=a[2]["moved_serialized_bytes"]
            methods_to_score["future_oracle_upper_bound"]["choices"].append(a[1])
        profile[key]={"assumed_per_avoided_touch_ms":t,"hypothetical_raw_transfer_Mbps":mbps,
                      "comparison":{name:{k:round(v,4) if isinstance(v,float) else v
                        for k,v in d.items()} for name,d in methods_to_score.items()}}
    report={"schema":"candidate3-budgeted-evidence-nonregression-action-admission-v1",
      "artifact_source":{"actions_run":SOURCE_RUN,"artifact_id":SOURCE_ARTIFACT,"artifact_digest_sha256":SOURCE_SHA},
      "method":"Choose 0, 1 or 2 swaps, 1 replica, or 1swap+1replica by training-only prior/day0 min, mean, or risk constrained evidence net value; test scoring segregated",
      "hypothetical_scenarios":profile,
      "strong_caveats":[
        "Entire source graph/query corpus has already been examined in development; this is post hoc exploratory action evaluation",
        "Five disjoint synthetic pseudo-time folds share same generator and do not represent independent organic queries",
        "No real SPARQL engine execution or measured latency: critical path milliseconds per shard touch ASSUMED",
        "Only ideal serialized NTriples transport, no index, cache, storage, queueing, multi-server synchronization, or replication updates",
        "Selector choosing a proven component on previous/day0 does not prove novel algorithm versus prior-art WISE/WASP",
        "If user wants high quality journal, must prospectively lock algorithm and test on new real log+corresponding complete RDF under byte cap",
        "Future-oracle upper bound is intentionally future aware and must NEVER be interpreted as deployable"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    compact={"schema":report["schema"],"artifact_source":report["artifact_source"],
      "cases":{k:{"top":sorted(((n,v["net_ms"]) for n,v in d["comparison"].items()),
                          key=lambda x:-x[1])[:8],
          "selectors":{n:v for n,v in d["comparison"].items() if n.startswith("selector_")}}
        for k,d in profile.items() if ("5ms_per_touch" in k or "1ms_per_touch" in k or "20ms_per_touch" in k)}}
    print("BEND_ECONOMICS_START",flush=True)
    print(json.dumps(compact,indent=2),flush=True)
    print("BEND_ECONOMICS_END",flush=True)
if __name__=="__main__":main()
