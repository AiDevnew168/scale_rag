#!/usr/bin/env python3
"""Fail-closed interpretation of a *completed* candidate3 temporal benchmark.

This program NEVER chooses a deployable migration using heldout information.
An oracle computed from heldout action scores is strictly diagnostic.
"""
import argparse
import json
import math
from pathlib import Path

ALTERNATIVES = ("one_swap", "two_swap_greedy", "replica_only", "swap_replica")
EXPECTED = ("no_move",) + ALTERNATIVES
SCHEMA = "candidate3-original-authentic-176day-four-process-semantic-economic-v1"


def finite_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def interpret(data):
    """Interpret the physically measured report without reselecting any action.

    Returns aggregate metadata only; query strings and identifiers are not read.
    """
    if data.get("schema") != SCHEMA:
        raise ValueError("Unsupported physical experiment schema")
    if data.get("selected_real_policy") != "no_move":
        raise ValueError("Only preregistered no_move policy is admissible")
    audit = data.get("initial_training_source_audit", {})
    counts = audit.get("observed_exact_eligible_occurrences_by_split", {})
    if (counts.get("train") != 4707 or counts.get("test") != 1441 or
            counts.get("construction", 0) + counts.get("calibration", 0) != 994):
        raise ValueError("Frozen 176-day eligibility totals were not reproduced")
    methods = data.get("methods", {})
    if set(methods) != set(EXPECTED):
        raise ValueError("Missing or unexpected action in frozen comparison set")
    if not all(methods["no_move"].get("full_query_correctness_gate", False)
               for _ in [0]):
        return {"status": "INVALID_BASELINE_SEMANTICS",
                "real_controller_action": "no_move", "journal_GO": False}
    summary = {}
    all_valid = True
    for name in ALTERNATIVES:
        method = methods[name]
        econ = method.get("economic", {})
        if not method.get("full_query_correctness_gate", False):
            summary[name] = {"status": "INVALID_SEMANTICS"}
            all_valid = False
            continue
        if not econ.get("valid", False):
            summary[name] = {"status": "INVALID_ESTIMATOR",
                             "reason": econ.get("reason", "not reported")}
            all_valid = False
            continue
        gain = econ.get("projected_unexecuted_original_full_period_net_point_ms")
        ci = econ.get("day_cluster_bootstrap_95_projected_net_ms")
        if (not finite_number(gain) or not isinstance(ci, (list, tuple))
                or len(ci) != 2 or not all(finite_number(x) for x in ci)
                or ci[0] > ci[1]):
            summary[name] = {"status": "INVALID_FINITE_ECONOMIC_OUTPUT"}
            all_valid = False
            continue
        summary[name] = {"status": "VALID_EXPLORATORY_COUNTERFACTUAL",
                         "net_projected_ms": gain,
                         "naive_day_bootstrap95_net_ms": ci,
                         "nominal_positive_lower_bound": ci[0] > 0}
    valid = {key: value for key, value in summary.items()
             if value["status"] == "VALID_EXPLORATORY_COUNTERFACTUAL"}
    output = {
        "schema": "candidate3-176day-no-hindsight-oracle-gap-verdict-v1",
        "physical_benchmark_schema": SCHEMA,
        "real_controller_action": "no_move",
        "real_controller_incremental_gain_vs_static_ms": 0.0,
        "real_controller_gain_is_zero_by_policy_definition": True,
        "comparison_arms_all_valid": all_valid,
        "action_results": summary,
        "journal_GO": False,
        "comparison_to_published_SOTA_achieved": False,
        "live_production_causal_trial": False,
        "historical_RDF_snapshot_as_of_2014_verified": False,
        "inference_limit": ("Day-cluster intervals are conditional and may fail "
                            "under serial correlation; physical trace projection "
                            "is not real deployed full-horizon profit."),
    }
    if not all_valid:
        output["diagnostic_oracle"] = "BLOCKED_NOT_ALL_ARMS_VALID"
        return output
    best_name, best = max(valid.items(), key=lambda item: item[1]["net_projected_ms"])
    best_gain = best["net_projected_ms"]
    output["diagnostic_oracle"] = "POST_HOC_HELDOUT_ORACLE_NOT_DEPLOYABLE"
    output["best_hypothetical_action"] = best_name if best_gain > 0 else "no_move"
    output["best_hypothetical_gain_ms"] = max(0.0, best_gain)
    output["posthoc_oracle_gap_vs_safe_controller_ms"] = max(0.0, best_gain)
    output["positive_lower_bound_in_any_alternative"] = any(
        row["nominal_positive_lower_bound"] for row in valid.values())
    output["hypothetical_placement_signal"] = (
        "EXPLORATORY_POSITIVE_POINT_ESTIMATE" if best_gain > 0
        else "NO_POSITIVE_PLACEMENT_ESTIMATE_IN_FROZEN_ACTION_SET")
    output["multiple_comparisons_adjusted"] = False
    return output


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report", type=Path)
    args = ap.parse_args()
    data = json.loads(args.report.read_text(encoding="utf-8"))
    print(json.dumps(interpret(data), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
