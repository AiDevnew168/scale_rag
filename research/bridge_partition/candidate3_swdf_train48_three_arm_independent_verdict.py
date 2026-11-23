#!/usr/bin/env python3
"""Independent fail-closed audit of 48 x 3 original source-query three-arm report.

No query text or IP, no external downloads, no modification of benchmark.
Green benchmark workflow alone is not a publishable performance result.
"""
import argparse,collections,json,math,statistics
from pathlib import Path

SCHEMA="candidate3-SWDF-48text-same-run-3arm-strong-central-baseline-v1"
ARMS=("central_indexed","full_fragment_ship","constant_pushdown")
EXPECTED_FIRST="108a618ab725e291d05967c1d81e58a1c5e8365804f88f7602bbe7370f26e09c"
EXPECTED_SECOND="3e2fd328952e2ddc1c0ea913af49db15bfe4f867a30d1a1db492ffb4e80eaed5"


def fail(reason):
    return {"schema":"candidate3-48trainingtext-independent-3arm-audit-v1",
            "status":"INVALID_EVIDENCE","reason":reason,
            "can_claim_real_production_profit":False,"journal_GO":False}


def check(report):
    if report.get("schema")!=SCHEMA:
        return fail("schema_mismatch")
    frozen=report.get("frozen",{})
    if (frozen.get("cohort_one_hash")!=EXPECTED_FIRST or
        frozen.get("cohort_two_hash")!=EXPECTED_SECOND or
        frozen.get("original_future_holdout_reused") is not False or
        frozen.get("original_SOURCE_query_never_rewritten") is not True or
        frozen.get("n_unique_original_training_texts")!=48 or
        frozen.get("repetitions_per_text")!=3):
        return fail("frozen_original_text_selection_drift")
    rows=report.get("deidentified_all_method_query_timings")
    if (not isinstance(rows,list) or len(rows)!=144 or
        report.get("completed_matched_3arm_blocks")!=144 or
        report.get("expected_matched_3arm_query_blocks")!=144 or
        report.get("errors") or
        report.get("original_complete_SELECT_semantic_all_pass") is not True):
        return fail("semantic_or_execution_coverage_incomplete")
    bytext=collections.defaultdict(list)
    cohort=collections.defaultdict(set)
    for r in rows:
        h=r.get("text_sha256")
        if not isinstance(h,str) or len(h)!=64:
            return fail("query_hash_invalid")
        if r.get("cohort") not in ("ranks_1_24","ranks_25_48"):
            return fail("cohort_id_invalid")
        rep=r.get("repeat")
        if type(rep) is not int or rep not in (0,1,2):
            return fail("repeat_out_of_bounds")
        order=r.get("method_order",[])
        if (len(order)!=3 or set(order)!=set(ARMS) or
            set(r.get("elapsed_ms",{}))!=set(ARMS) or
            set(r.get("rdf_payload_bytes",{}))!=set(ARMS) or
            set(r.get("solution_counts",{}))!=set(ARMS)):
            return fail("missing_method_or_order")
        if not isinstance(r.get("family_sha256"),str) or len(r["family_sha256"])!=64:
            return fail("predicate_family_hash_invalid")
        if not all(r.get("status",{}).get(a)=="PASS" for a in ARMS[1:]):
            return fail("SPARQL_semantics_not_certified")
        for arm in ARMS:
            t=r["elapsed_ms"][arm]
            payload=r["rdf_payload_bytes"][arm]
            n=r["solution_counts"][arm]
            if (type(t) not in (int,float) or not math.isfinite(t) or t<0 or
                type(payload) is not int or payload<0 or
                type(n) is not int or n<0):
                return fail("nonfinite_or_negative_physical_metric")
        if (r["rdf_payload_bytes"]["central_indexed"]!=0 or
            r["rdf_payload_bytes"]["full_fragment_ship"]<=0 or
            r["rdf_payload_bytes"]["constant_pushdown"]>
                    r["rdf_payload_bytes"]["full_fragment_ship"]):
            return fail("RDF_payload_bytes_constraint_violated")
        bytext[h].append(r)
        cohort[r["cohort"]].add(h)
    if len(bytext)!=48 or any(len(v)!=3 for v in bytext.values()):
        return fail("text_or_repeat_not_unique")
    if len(cohort["ranks_1_24"])!=24 or len(cohort["ranks_25_48"])!=24:
        return fail("cohort_not_24_plus_24")
    for h,triplet in bytext.items():
        if {r["repeat"] for r in triplet}!={0,1,2}:
            return fail("missing_or_duplicate_repeat")
        if len({r["family_sha256"] for r in triplet})!=1:
            return fail("family_changed_across_repeats")
        if len({r["cohort"] for r in triplet})!=1:
            return fail("cohort_changed_across_repeats")
        for pos in range(3):
            if {r["method_order"][pos] for r in triplet}!=set(ARMS):
                return fail("balanced_method_order_broken")
    # All checks above completed before any performance summary is allowed.
    def stats(arm):
        v=sorted(r["elapsed_ms"][arm] for r in rows)
        return {"mean_ms":round(statistics.mean(v),6),
                "sample_p95_ms":round(v[math.ceil(.95*len(v))-1],6),
                "max_ms":round(v[-1],6)}
    metrics={arm:stats(arm) for arm in ARMS}
    pertext=[]
    for h,rr in bytext.items():
        pertext.append({
            "source_text_sha256":h,
            "family_sha256":rr[0]["family_sha256"],
            "central_ms":statistics.mean(x["elapsed_ms"][ARMS[0]] for x in rr),
            "selective_ms":statistics.mean(x["elapsed_ms"][ARMS[2]] for x in rr)})
    byfam=collections.defaultdict(list)
    for r in pertext:byfam[r["family_sha256"]].append(r)
    central_better=sum(r["central_ms"]<r["selective_ms"] for r in pertext)
    family_better=sum(statistics.mean(r["central_ms"] for r in rr)<
                      statistics.mean(r["selective_ms"] for r in rr)
                      for rr in byfam.values())
    byte_full=sum(r["rdf_payload_bytes"]["full_fragment_ship"] for r in rows)
    byte_sel=sum(r["rdf_payload_bytes"]["constant_pushdown"] for r in rows)
    central=metrics["central_indexed"]
    sel=metrics["constant_pushdown"]
    scoping_no_go=(central["mean_ms"]<sel["mean_ms"] and
                   central["sample_p95_ms"]<sel["sample_p95_ms"] and
                   central_better>=40)
    # Scope NO-GO to exactly the single-host 304k-triple coordinator; never all RDF.
    return {"schema":"candidate3-48trainingtext-independent-3arm-audit-v1",
       "status":"VALID_ENGINEERING_EVIDENCE",
       "n_original_train_texts":48,"n_certified_three_arm_query_blocks":144,
       "all_432_original_timed_SELECT_calls_accounted":True,
       "mean_and_p95_by_arm":metrics,
       "direct_centralized_speedup_over_selective_mean_factor":round(
            sel["mean_ms"]/central["mean_ms"],4) if central["mean_ms"]>0 else None,
       "n_query_text_clusters_central_outperforms_selective":central_better,
       "n_predicate_set_families":len(byfam),
       "n_predicate_families_central_outperforms_selective":family_better,
       "source_original_RDF_response_body_bytes_saved_full_to_selective":
             byte_full-byte_sel,
       "single_host_304k_RDF_temp_store_coordinator_competitiveness":
          "NO_GO" if scoping_no_go else "UNRESOLVED_STRONG_BASELINE",
       "cannot_extrapolate_to_BillionTriple_true_multi_host":True,
       "prior_results_already_seen_not_independent_test":True,
       "actual_AdPart_WISE_CostFed_runtimes_compared":False,
       "can_claim_real_production_profit":False,"journal_GO":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("report",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    result=check(json.loads(args.report.read_text()))
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if result["status"]!="VALID_ENGINEERING_EVIDENCE":
        raise SystemExit(2)


if __name__=="__main__":
    main()
