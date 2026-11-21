#!/usr/bin/env python3
"""Fail-closed external verdict on frozen original TRAIN-only physical sample.

No hidden test-set reuse or implied novel journal claim. All metrics are
conditional on the fixed 24 original training texts, not full trace profit.
"""
import argparse
import collections
import json
import math
import statistics
from pathlib import Path

EXPECTED_SCHEMA="candidate3-trainonly-source-physical-constant-pushdown-v1"
N_QUERY_TEXTS=24
N_REPEATS=2


def finite(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)


def p95(values):
    x=sorted(values)
    return x[math.ceil(0.95*len(x))-1]


def interpret(report):
    basic={"journal_GO":False,
           "heldout_independent_generalization_demonstrated":False,
           "published_original_adpart_wise_baseline_evaluated":False,
           "real_deployment_migration_profit_verified":False}
    if report.get("schema")!=EXPECTED_SCHEMA:
        return basic|{"status":"UNSUPPORTED_REPORT_SCHEMA"}
    freeze=report.get("frozen_selection",{})
    selection=freeze.get("candidate_selection",{})
    if (freeze.get("n_query_texts")!=N_QUERY_TEXTS or
        freeze.get("paired_repeats")!=N_REPEATS or
        freeze.get("training_original_UTC_days")!=88 or
        selection.get("calibration_or_test_original_query_texts_examined") is not False or
        freeze.get("no_2014_heldout_reuse") is not True):
        return basic|{"status":"INVALID_FROZEN_SELECTION"}
    rows=report.get("deidentified_original_training_paired_rows",[])
    expected=N_QUERY_TEXTS*N_REPEATS
    if (report.get("n_expected_pairs")!=expected or
        report.get("n_semantically_legal_pairs")!=expected or
        report.get("all_original_queries_correct") is not True or
        report.get("errors") or len(rows)!=expected):
        return basic|{"status":"INVALID_OR_INCOMPLETE_SPARQL"}
    counted=collections.Counter()
    groups=collections.defaultdict(list)
    keys=set()
    for row in rows:
        if not isinstance(row,dict):
            return basic|{"status":"MALFORMED_PAIR"}
        h=row.get("text_sha256")
        k=row.get("repetition")
        if not isinstance(h,str) or len(h)!=64 or type(k) is not int or k not in (0,1):
            return basic|{"status":"INVALID_QUERY_REPEAT_KEY"}
        if (h,k) in keys:
            return basic|{"status":"DUPLICATED_PAIR"}
        keys.add((h,k));counted[h]+=1;groups[h].append(row)
        if not all(finite(row.get(name)) for name in ("full_ms","pushdown_ms",
            "full_rdf_bytes","pushdown_rdf_bytes","saved_ms")):
            return basic|{"status":"NONFINITE_PAIR"}
        if (row["full_ms"]<0 or row["pushdown_ms"]<0 or
            row["full_rdf_bytes"]<=0 or row["pushdown_rdf_bytes"]<0 or
            row["pushdown_rdf_bytes"]>row["full_rdf_bytes"]):
            return basic|{"status":"INVALID_PHYSICAL_MEASUREMENT"}
        if abs(row["full_ms"]-row["pushdown_ms"]-row["saved_ms"])>0.00025:
            return basic|{"status":"UNMATCHED_WALL_TIME_PAIR"}
        if type(row["full_rdf_bytes"]) is not int or type(row["pushdown_rdf_bytes"]) is not int:
            return basic|{"status":"INVALID_RDF_BYTE_COUNT"}
    if len(counted)!=N_QUERY_TEXTS or any(v!=N_REPEATS for v in counted.values()):
        return basic|{"status":"MISSING_QUERY_OR_REPEAT"}
    predeclared=set(selection.get("chosen_text_hashes",[]))
    if set(counted)!=predeclared or len(predeclared)!=N_QUERY_TEXTS:
        return basic|{"status":"SAMPLE_CHANGED_AFTER_FREEZE"}
    by_query=[{"text_sha256":h,
        "mean_reduction":statistics.mean(1-r["pushdown_rdf_bytes"]/r["full_rdf_bytes"]
                                        for r in group),
        "mean_saved_ms":statistics.mean(r["saved_ms"] for r in group)}
        for h,group in groups.items()]
    byte_median=statistics.median(x["mean_reduction"] for x in by_query)
    lat_mean=statistics.mean(x["mean_saved_ms"] for x in by_query)
    before=p95([r["full_ms"] for r in rows])
    after=p95([r["pushdown_ms"] for r in rows])
    gate_a=byte_median>=0.25
    gate_b=lat_mean>0 and after<=before*1.01
    return basic|{
       "status":"EXPLORATORY_TRAIN_ONLY_MEASURED",
       "full_original_source_semantic_coverage":"48/48 pinned training paired evaluations",
       "n_frozen_unique_training_texts":N_QUERY_TEXTS,
       "median_fraction_RDF_response_bytes_saved_per_query":round(byte_median,6),
       "mean_saved_wallclock_ms_per_query":round(lat_mean,5),
       "full_rdf_bytes_all_repeats":sum(r["full_rdf_bytes"] for r in rows),
       "pushdown_rdf_bytes_all_repeats":sum(r["pushdown_rdf_bytes"] for r in rows),
       "p95_full_wall_ms":round(before,5),
       "p95_pushdown_wall_ms":round(after,5),
       "pass_predeclared_25pct_training_byte_reduction":gate_a,
       "pass_training_positive_latency_and_1pct_p95_guard":gate_b,
       "engineering_followup_if_both":bool(gate_a and gate_b),
       "worker_parsing_and_index_memory_may_not_be_costed":True,
       "not_a_valid_2014_heldout_or_production_economic_win":True,
       "not_a_new_semijoin_or_RDF_query_routing_algorithm":True,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("report",type=Path)
    args=parser.parse_args()
    data=json.loads(args.report.read_text(encoding="utf8"))
    print(json.dumps(interpret(data),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
