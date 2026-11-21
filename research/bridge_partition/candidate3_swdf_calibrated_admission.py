#!/usr/bin/env python3
"""Candidate 3 witnessed admission on calibration-only measured SPARQL costs.

A/B benchmark of four *frozen* candidate actions on 34 calibration pattern
families, including real physical four-shard Oxigraph move/replica costs. Uses
a 2.5% query-family bootstrap lower bound of estimated next 102-query
net latency; abstains unless >0 (also hard 25MB migration and 10% shard byte
ceiling). This is an *assumption-dependent* confidence gate, not a formal
distribution-free future guarantee. The 102 exact-hash and predicate-family
disjoint holdout is touched ONLY AFTER the action is selected and decision
JSON persisted. Frozen source and code published before the first heldout
performance from the preceding full-SPARQL action test is retrieved.
"""
import collections,hashlib,json,math,random,statistics,time
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_paired_full_sparql as paired
import candidate3_real_sparql_shards as engine

OUT=Path("results_candidate3_SWDF_measured_admission");OUT.mkdir(exist_ok=True)
SEED=20261121
BOOT=3000
DELTA=.05
TEST_REPEAT=2
def sampled_one_per_family(rows):
    picked={}
    for r in sorted(rows,key=lambda x:x["text_hash"]):
        picked.setdefault(r["family"],r)
    return list(picked.values())

def paired_eval(queries,central,base_ports,action_ports,base_route,action_route,frag,
                repeat=1,seed=SEED):
    records=[];errors=[]
    rng=random.Random(seed)
    for r in queries:
        h=r["text_hash"]
        try:
            truth=engine.evaluate(central,r["query"])
            for j in range(repeat):
                if rng.randrange(2)==0:
                    base=core.query_four_workers(r["query"],r["pattern"],base_route,base_ports,frag)
                    alt=core.query_four_workers(r["query"],r["pattern"],action_route,action_ports,frag)
                else:
                    alt=core.query_four_workers(r["query"],r["pattern"],action_route,action_ports,frag)
                    base=core.query_four_workers(r["query"],r["pattern"],base_route,base_ports,frag)
                if base["answer"]!=truth or alt["answer"]!=truth:
                    raise AssertionError("full query answer mismatch against centralized truth")
                records.append({"family":json.dumps(r["family"]),
                    "query_sha":h,"repeat":j,
                    "saved_ms":base["wall_ms"]-alt["wall_ms"],
                    "baseline_ms":base["wall_ms"],"action_ms":alt["wall_ms"],
                    "baseline_bytes":base["network_bytes"],"action_bytes":alt["network_bytes"],
                    "baseline_contacts":base["shard_contacts"],"action_contacts":alt["shard_contacts"],
                    "truth_nonempty":truth["count"]>0})
        except Exception as e:
            errors.append({"query_sha":h,"error":type(e).__name__+": "+str(e)[:300]})
    return records,errors

def calibrate(rows,cost_ms,future_n):
    # One measured query per calibration family. Blocks are 34 *query families*.
    byfam=collections.defaultdict(list)
    for r in rows:byfam[r["family"]].append(r["saved_ms"])
    values=[statistics.mean(xs) for xs in byfam.values()]
    if len(values)<20:
        return {"admissible":False,"reason":"too_few_independent_calibration_families",
            "n_calibration_families":len(values)}
    rng=random.Random(SEED)
    estimates=sorted(statistics.mean([values[rng.randrange(len(values))]
              for _ in values])*future_n-cost_ms for __ in range(BOOT))
    return {"admissible":estimates[74]>0,
         "calibration_query_families":len(values),
         "calibration_mean_saved_ms_per_family_query":round(statistics.mean(values),5),
         "expected_future_horizon_requests":future_n,
         "measured_full_move_and_index_update_ms":cost_ms,
         "bootstrap_net_after_migration_lower95_ms":round(estimates[74],4),
         "bootstrap_net_after_migration_upper95_ms":round(estimates[2924],4),
         "positive_certification_is_conditional_on_future_family_exchangeability":True}

def main():
    tick=time.perf_counter()
    graph,by_pred,sizes,role,packs,loads,route,cap=core.prepare_source()
    plans,metadata=core.choose_plans(role["training"],role["calibration"],
                                      route,loads,sizes,cap)
    central=Store()
    central.bulk_load(input=graph,format=RdfFormat.N_TRIPLES)
    del graph
    calib=sampled_one_per_family(role["calibration"])
    assert len(calib)>=20
    future_count=len(role["holdout"])
    frag={p for p,owners in route.items() if len(owners)>1}
    base_ports,base_workers=paired.start_group(packs)
    audit={}
    try:
        for name,plan in plans.items():
            if name=="no_move":continue
            ports,workers=paired.start_group(packs)
            try:
                alt,mig=core.physically_apply(plan,by_pred,route,loads,sizes,cap,ports)
                records,errors=paired_eval(calib,central,base_ports,ports,
                    route,alt,frag,repeat=1,seed=SEED+len(name))
                verdict=calibrate(records,mig["wall_clock_migration_and_index_update_ms"],
                                  future_count)
                if errors or len(records)!=len(calib):
                    verdict.update({"admissible":False,
                                    "reason":"calibration_full_answer_errors_or_timeouts"})
                audit[name]={"frozen_plan":plan,
                    "calibration_pairs":len(records),
                    "calibration_failures":errors[:10],
                    "migration":mig,
                    "pretest_admission":verdict}
                print("CALIBRATED_ACTION",name,json.dumps(verdict),flush=True)
            finally:paired.shutdown(workers)
        candidates=[(detail["pretest_admission"].get("bootstrap_net_after_migration_lower95_ms",-float("inf")),name)
             for name,detail in audit.items() if detail["pretest_admission"]["admissible"]]
        if candidates:
            _,selected=max(candidates,key=lambda x:(x[0],x[1]))
        else:selected="no_move"
        # Seal action before any holdout SPARQL query execution.
        decision={"schema":"candidate3-calibration-only-policy-decision-v1",
          "selected_action":selected,
          "model_used_zero_heldout_query_answers":True,
          "candidate_hard_max_move_bytes":25_000_000,
          "n_calibration_family_queries":len(calib),
          "n_exact_disjoint_heldout_requests":future_count,
          "admission_requires_bootstrap_lower95_net_ms_gt_zero":True,
          "calibration_evidence":audit}
        OUT.joinpath("decision_frozen_before_test.json").write_text(
            json.dumps(decision,indent=2))
        print("ADMISSION_FROZEN_BEFORE_HELDOUT",selected,flush=True)
        if selected=="no_move":
            alt_ports=base_ports
            altworkers=[]
            altloc=route
            migration={"moved_bytes":0,"wall_clock_migration_and_index_update_ms":0,
                 "post_shard_bytes":loads}
        else:
            alt_ports,altworkers=paired.start_group(packs)
            altloc,migration=core.physically_apply(plans[selected],by_pred,route,loads,
                sizes,cap,alt_ports)
        try:
            heldout,errors=paired_eval(role["holdout"],central,base_ports,
                alt_ports,route,altloc,frag,repeat=TEST_REPEAT,seed=SEED+907)
        finally:
            if altworkers:paired.shutdown(altworkers)
    finally:paired.shutdown(base_workers)
    n_heldout_novel_families=len({r["family"] for r in role["holdout"]})
    n_correct=len(heldout)
    expected=future_count*TEST_REPEAT
    if n_correct==expected and not errors:
        interval=core.cost_ci(heldout,migration["wall_clock_migration_and_index_update_ms"])
    else:interval=None
    result={"schema":"candidate3-SWDF-measured-SPARQL-calibration-only-abstaining-admission-v1",
       "source_sha":{"graph_zip":"65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb",
           "queries":"7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3"},
       "selected":selected,
       "pretest_calibration_evidence":audit,
       "physical_selected_migration":migration,
       "heldout_distinct_family_count":n_heldout_novel_families,
       "heldout_queries":future_count,
       "heldout_nonempty_answers_from_paired_eval":sum(int(r["truth_nonempty"])
          for r in heldout)//TEST_REPEAT,
       "n_correct_full_SPARKQL_answers_both_policies":n_correct,
       "n_expected_pairs":expected,
       "mismatches_or_errors":errors[:20],
       "net_paired_ci_after_actual_migration":interval,
       "contact_savings":sum(r["baseline_contacts"]-r["action_contacts"] for r in heldout),
       "network_NTriples_bytes_saved":sum(r["baseline_bytes"]-r["action_bytes"] for r in heldout),
       "elapsed_seconds":round(time.perf_counter()-tick,3),
       "paper_SOTA_dominance_claim":False,
       "limitations":[
         "Entire source is real DICE SWDF graph and real-log cleaned SELECTs, but no verified original event timestamps or snapshot correspondence",
         "Four live independent TCP Oxigraph stores on same machine; eager predicate triple gather rather than optimized distributed join",
         "Calibration-family bootstrap LCB only valid under exchangeability/stationarity of future query families: NOT distribution-free drift guarantee",
         "No actual cross-machine network, crash-consistent migration, WISE/WASP/AdPart run or real production economic price",
         "Choosing no move is a valid abstaining output, not evidence of surpassing existing dynamic RDF partitioners",
         "No claim that query samples/repetitions increase number of statistically independent pattern families"]
       }
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("SWDF_ADMISSION_FINAL_START",flush=True)
    print(json.dumps({k:v for k,v in result.items() if k!="pretest_calibration_evidence"}|
      {"pretest_action_summaries":{x:v["pretest_admission"] for x,v in audit.items()}},
      indent=2),flush=True)
    print("SWDF_ADMISSION_FINAL_END",flush=True)
if __name__=="__main__":main()
