#!/usr/bin/env python3
"""Candidate 3: non-vacuous only-when-evidence-matches bounded-drift admission.

This is a conservative SCIENTIFIC CONTROL, not a new proven SOTA algorithm.

Theoretical contract (each fixed candidate j):
For fixed predeclared action j with rewards in [-B_j,B_j], n independent
calibration *day blocks*, a known upper bound rho_j on total L1 drift in the
future query outcome distribution, and a certified upper bound on *complete*
physical migration/index/cutover cost C_j:
  E_future[g_j] >= mean_cal[j]
      - B_j*sqrt(2*log(M/delta)/n)
      - B_j*rho_j.
A future horizon H therefore has a positive net expectation lower bound when
  H*LCB - C_j > 0.
The finite-candidate union bound makes the statement simultaneous for all
M training-frozen actions and does not invalidate it when one is selected
by calibration.

CRITICAL LIMITS:
- "Independent day blocks", bounded reward, and independently justified
  future drift rho are ASSUMPTIONS, not verified by temporal parsing.
- L1 drift of full-query runtime outcomes is NOT identifiable from past alone,
  and no prior empirical drift maximum gives a distribution-free future bound.
- Predicate witness locality restricts SHARD TOUCH deltas, NOT full walltime:
  a source disjoint from moved predicates may still have different latency
  due to cache, scheduling, contention, noise, or index changes.
- This is expected clipped objective, NOT a pathwise positive profit guarantee.
- A measured single cutover time is NOT an upper confidence bound.
- Without genuine premises, refuse; "no move" is the only certified decision.
"""
from __future__ import annotations
import math
from collections import Counter
from typing import Any

def compute_bound(
    samples_by_action:dict[str,list[float]], *,
    training_fixed_actions:list[str],
    reward_abs_bound_ms:float,
    tail_delta:float,
    future_request_horizon:int,
    future_l1_drift_bound:float|None,
    l1_bound_is_externally_justified:bool,
    migration_upper_ms_by_action:dict[str,float],
    migration_upper_is_certified:bool,
    calibration_is_independent_blocks:bool,
    same_query_population_contract:bool,
    full_sparql_correctness_gate:bool,
)->dict[str,Any]:
    """Return a fail-closed conditional admission decision and evidence.

    samples_by_action contains one independent block mean per calendar day,
    not per-query repetitions. If blocks are correlated, this function
    cannot certify expected future performance. The action must have been
    frozen on a DISJOINT training period.
    """
    actions=list(training_fixed_actions)
    assert len(actions)==len(set(actions)), "duplicate actions in library"
    bad=[]
    if not actions:bad.append("no_predeclared_candidates")
    if any(a=="no_move" for a in actions):bad.append("no_move_cannot_be_candidate")
    if not (0<tail_delta<1):bad.append("bad_tail_delta")
    if not (math.isfinite(reward_abs_bound_ms) and reward_abs_bound_ms>0):
        bad.append("invalid_reward_absolute_bound")
    if future_request_horizon<1:bad.append("unknown_future_horizon")
    if future_l1_drift_bound is None or not (0<=future_l1_drift_bound<=2):
        bad.append("no_valid_full_runtime_future_L1_drift_upper")
    if not l1_bound_is_externally_justified:bad.append("future_drift_not_verified")
    if not migration_upper_is_certified:bad.append("full_migration_cost_upper_not_certified")
    if not calibration_is_independent_blocks:bad.append("independent_block_assumption_unmet")
    if not same_query_population_contract:bad.append("query_distribution_contract_unmet")
    if not full_sparql_correctness_gate:bad.append("original_SPARQL_semantic_answer_gate_failed")
    lengths=[]
    for a in actions:
        if a not in samples_by_action or not samples_by_action[a]:
            bad.append(f"no_calibration_samples_{a}")
            continue
        seq=samples_by_action[a]
        lengths.append(len(seq))
        if not all(isinstance(v,(int,float)) and math.isfinite(v)
                   and abs(v)<=reward_abs_bound_ms for v in seq):
            bad.append(f"unbounded_or_nonfinite_calibration_reward_{a}")
        cost=migration_upper_ms_by_action.get(a)
        if cost is None or not math.isfinite(cost) or cost<0:
            bad.append(f"missing_migration_upper_bound_{a}")
    if lengths and (min(lengths)!=max(lengths) or min(lengths)<2):
        bad.append("unequal_or_insufficient_independent_days")
    if bad:
        return {"schema":"candidate3-bounded-drift-economic-admission-v1",
            "selected":"no_move","status":"ABSTAIN_UNCERTIFIED",
            "reasons":sorted(set(bad)),"full_expected_profit_certificate":False,
            "statement":"No economically admissible migration without the explicitly required evidence."}
    m=len(actions)
    n=lengths[0]
    alpha=reward_abs_bound_ms*math.sqrt(2*math.log(m/tail_delta)/n)
    shift=reward_abs_bound_ms*future_l1_drift_bound
    records={}
    for a in actions:
        mu=sum(samples_by_action[a])/n
        lcb=mu-alpha-shift
        move=migration_upper_ms_by_action[a]
        net=lcb*future_request_horizon-move
        records[a]={"calibration_day_mean_saved_ms":round(mu,6),
            "simultaneous_Hoeffding_penalty_ms":round(alpha,6),
            "drift_penalty_ms":round(shift,6),
            "LCB_expected_future_saved_ms_per_query":round(lcb,6),
            "certified_full_migration_upper_ms":round(move,6),
            "LCB_expected_net_ms_for_frozen_horizon":round(net,6),
            "eligible":net>0}
    eligible=[(v["LCB_expected_net_ms_for_frozen_horizon"],a)
                 for a,v in records.items() if v["eligible"]]
    pick=max(eligible,key=lambda x:(x[0],x[1]))[1] if eligible else "no_move"
    return {"schema":"candidate3-bounded-drift-economic-admission-v1",
      "selected":pick,
      "status":"CONDITIONALLY_ADMISSIBLE" if pick!="no_move" else "ABSTAIN_NONPOSITIVE_NET_LOWER_BOUND",
      "full_expected_profit_certificate":pick!="no_move",
      "is_distribution_free_under_arbitrary_future_shift":False,
      "guarantee_is_expected_clipped_per_query_gain_only":True,
      "n_assumed_independent_calendar_day_blocks":n,
      "candidate_library_size_M":m,
      "simultaneous_one_sided_delta":tail_delta,
      "calibration_reward_abs_bound_ms":reward_abs_bound_ms,
      "future_L1_drift_upper":future_l1_drift_bound,
      "predeclared_future_n_queries":future_request_horizon,
      "actions":records,
      "strict_conditions":[
        "All candidate actions frozen before calibration; days independent and within bounded reward assumption",
        "Full runtime reward L1 shift upper valid for future and independently justified, not fit on future",
        "Full migration including transfer, index, barrier and recovery charged by certified upper bound",
        "All original SPARQL responses semantically validated and no missing incorrect queries",
        "One-sided expected lower bound is not realized positive net guarantee"]}

def locality_witness_l1_difference(old:dict[str,int],new:dict[str,int],
                                   witness:set[str])->int:
    """Witness set supports routing change; never use as walltime bound."""
    return sum(abs(old.get(k,0)-new.get(k,0)) for k in witness)

def adversarial_impossibility_example()->dict[str,Any]:
    """Counterexample: matching prefixes cannot distinguish future flips."""
    prefix=[{"observed_gain_ms":6.0,"query":"old_hot"}]*10
    futures={
      "continuation_good":[{"gain_ms":6.0}]*10,
      "continuation_bad":[{"gain_ms":-6.0}]*10}
    return {"same_observed_history":True,
      "prefix_len":len(prefix),
      "future_world_net_savings_ms":{k:sum(r["gain_ms"] for r in v)
                                    for k,v in futures.items()},
      "conclusion":"No history-only controller guarantees positive future net gain under unconstrained adversarial drift."}

if __name__=="__main__":
    print(adversarial_impossibility_example())
