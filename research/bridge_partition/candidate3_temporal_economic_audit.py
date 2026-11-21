#!/usr/bin/env python3
"""Day-stratified, auditable exploratory economics for a frozen SWDF physical replay.

The input is de-identified paired query wall-time evidence, not a live A/B trace.
This is not a calibrated distribution-free profit guarantee or a novel theorem.
"""
import collections
import math
import random
import statistics

BLOCK_LENGTHS = (3, 7, 14)
N_BOOT = 2500


def _finite(x):
    return isinstance(x, (float, int)) and not isinstance(x, bool) and math.isfinite(x)


def _quantile(values, p):
    ordered = sorted(values)
    if not ordered:
        raise ValueError("empty bootstrap")
    return ordered[min(len(ordered)-1, max(0, math.floor(p*(len(ordered)-1))))]


def _p95(values):
    ordered = sorted(values)
    return ordered[math.ceil(0.95*len(ordered))-1]


def _block_boot(day_values, size, seed):
    """Circular moving-block resampling, for non-confirmatory sensitivity only."""
    rng = random.Random(seed)
    n = len(day_values)
    draws = []
    for _ in range(N_BOOT):
        path = []
        while len(path) < n:
            start = rng.randrange(n)
            path.extend(day_values[(start+j) % n] for j in range(size))
        draws.append(sum(path[:n]))
    return draws


def audit(records, eligible_by_day, heldout_days, *,
          migration_ms, semantics_pass, repeats=2, sample_per_day=12, seed=20261121):
    """Fail closed on missing timing, incorrect SPARQL, or sampled-day denominator.

    Each record contains day, anonymous occurrence_key, saving_ms,
    baseline_ms, alternative_ms, new_exact, new_family. Query text and IP
    addresses must never be supplied. Records represent execution repeats,
    not independent query occurrences.
    """
    if not semantics_pass:
        return {"status": "INVALID_SPARQL", "journal_GO": False}
    if not _finite(migration_ms) or migration_ms < 0:
        return {"status": "INVALID_MIGRATION_COST", "journal_GO": False}
    if not heldout_days or len(set(heldout_days)) != len(heldout_days):
        return {"status": "INVALID_CALENDAR", "journal_GO": False}
    if heldout_days != sorted(heldout_days):
        return {"status": "NONCHRONOLOGICAL_CALENDAR", "journal_GO": False}
    if repeats < 1 or sample_per_day < 1:
        return {"status": "INVALID_SAMPLE_DESIGN", "journal_GO": False}
    if set(eligible_by_day) - set(heldout_days):
        return {"status": "OUT_OF_PERIOD_COUNTS", "journal_GO": False}
    for n in eligible_by_day.values():
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            return {"status": "INVALID_ELIGIBLE_COUNT", "journal_GO": False}
    by_occurrence = collections.defaultdict(list)
    for row in records:
        if not isinstance(row, dict):
            return {"status": "MALFORMED_TIMING", "journal_GO": False}
        d = row.get("day")
        k = row.get("occurrence_key")
        if d not in heldout_days or not isinstance(k, str) or not k:
            return {"status": "INVALID_SAMPLE_KEY", "journal_GO": False}
        if not all(_finite(row.get(v)) for v in
                   ("saving_ms", "baseline_ms", "alternative_ms")):
            return {"status": "INVALID_WALLCLOCK", "journal_GO": False}
        if row["baseline_ms"] < 0 or row["alternative_ms"] < 0:
            return {"status": "NEGATIVE_RUNTIME", "journal_GO": False}
        if abs(row["baseline_ms"] - row["alternative_ms"] - row["saving_ms"]) > 0.00001:
            return {"status": "UNMATCHED_PAIR", "journal_GO": False}
        if type(row.get("new_exact")) is not bool or type(row.get("new_family")) is not bool:
            return {"status": "MISSING_NOVELTY_LABEL", "journal_GO": False}
        by_occurrence[(d, k)].append(row)
    if not records:
        return {"status": "NO_TIMINGS", "journal_GO": False}
    per_day = collections.defaultdict(list)
    for (day, key), rows in by_occurrence.items():
        if len(rows) != repeats:
            return {"status": "MISSING_OR_EXCESS_REPEATS", "journal_GO": False}
        if any(row["new_exact"] != rows[0]["new_exact"] or
               row["new_family"] != rows[0]["new_family"] for row in rows):
            return {"status": "INCONSISTENT_NOVELTY_LABEL", "journal_GO": False}
        per_day[day].append({"mean": statistics.mean(x["saving_ms"] for x in rows),
                             "new_exact": rows[0]["new_exact"],
                             "new_family": rows[0]["new_family"]})
    gains = []
    finite_population_variance = 0.0
    for day in heldout_days:
        n = eligible_by_day.get(day, 0)
        entries = per_day.get(day, [])
        m = len(entries)
        if m != min(n, sample_per_day):
            return {"status": "SAMPLE_COVERAGE_MISMATCH", "journal_GO": False,
                    "day": day, "expected": min(n, sample_per_day), "observed": m}
        if m == 0:
            gains.append(0.0)
            continue
        observed = [x["mean"] for x in entries]
        gains.append(n * statistics.mean(observed))
        if m > 1:
            finite_population_variance += (n*n) * (1-m/n) * statistics.variance(observed)/m
        elif n != 1:
            return {"status": "UNESTIMABLE_WITHIN_DAY_VARIANCE", "journal_GO": False}
    point = sum(gains) - migration_ms
    rng = random.Random(seed)
    naive = [sum(gains[rng.randrange(len(gains))] for _ in gains) - migration_ms
             for __ in range(N_BOOT)]
    moving = {}
    for length in BLOCK_LENGTHS:
        sims = [x - migration_ms for x in
                _block_boot(gains, length, seed + length)]
        moving[str(length)] = [_quantile(sims, 0.025), _quantile(sims, 0.975)]
    novelty = {}
    for flag in ("new_exact", "new_family"):
        matching = [r for r in per_day.values() for r in r if r[flag]]
        novelty[flag] = {
            "sampled_occurrences": len(matching),
            "sample_mean_saved_ms": (statistics.mean(x["mean"] for x in matching)
                                     if matching else None),
            "not_full_trace_extrapolation": True,
        }
    return {
        "status": "VALID_EXPLORATORY_ACCOUNTING",
        "calendar_days": len(heldout_days),
        "days_with_eligible_requests": sum(eligible_by_day.get(d,0)>0 for d in heldout_days),
        "eligible_occurrences": sum(eligible_by_day.get(d,0) for d in heldout_days),
        "sampled_independent_occurrences": len(by_occurrence),
        "paired_repetitions": len(records),
        "move_ms": migration_ms,
        "projected_unexecuted_net_ms": point,
        "within_day_design_se_ms": math.sqrt(max(0.0, finite_population_variance)),
        "naive_day_resampling_95_sensitivity_ms":
            [_quantile(naive, 0.025), _quantile(naive, 0.975)],
        "circular_moving_block_95_sensitivity_ms": moving,
        "sampled_p95_baseline_ms": _p95([r["baseline_ms"] for r in records]),
        "sampled_p95_action_ms": _p95([r["alternative_ms"] for r in records]),
        "sampled_p95_difference_ms": (_p95([r["baseline_ms"] for r in records]) -
                                       _p95([r["alternative_ms"] for r in records])),
        "novelty_slices": novelty,
        "statistical_claim": "DESCRIPTIVE_ONLY_NOT_VALIDATED_FUTURE_CI",
        "full_migration_rollback_shadow_and_production_costs_verified": False,
        "journal_GO": False,
    }
