#!/usr/bin/env python3
"""Candidate3 robust active trial: deterministic (pathwise) economic loss cap.

Separate from the forecast-only certificate; no assumption on future traffic
distribution. The result is a WORST-CASE LOSS bound, NOT a positive-profit
guarantee. Requires 100% paired counterfactual timing from a correct shadow
baseline, inclusive metering costs, bounded per-request harm and a certified
revert upper bound. If any required capability is unavailable, never migrate.

A risk budget L and per-request harm bound B and revert upper C_back yield
threshold T=L-B-C_back. If initial migration C_move<=T and every subsequent
net saving d_i >=-B, then stop at the first observed balance<=-T and revert
immediately. Final net relative static stays >= -L, even if future workload
shifts adversarially. Revert is charged at actual cost <=C_back. No unattended
unmetered requests allowed during a trial.

This stop-loss is standard risk management; not on its own new research.
"""
from dataclasses import dataclass
from math import isfinite

class UncertifiableTrial(RuntimeError):
    pass

@dataclass
class LossCappedTrial:
    total_loss_budget_ms:float
    hard_max_single_request_regret_ms:float
    certified_max_revert_ms:float
    actually_paid_migration_ms:float
    full_shadow_pairing_available:bool
    semantic_correctness_verified:bool
    physically_enforced_regret_ceiling:bool
    revert_upper_is_certified:bool

    def __post_init__(self):
        nums=(self.total_loss_budget_ms,self.hard_max_single_request_regret_ms,
              self.certified_max_revert_ms,self.actually_paid_migration_ms)
        if any(not isfinite(n) for n in nums):
            raise UncertifiableTrial("nonfinite_cost_or_risk_bound")
        if self.total_loss_budget_ms<=0 or min(nums[1:])<0:
            raise UncertifiableTrial("invalid_bounded_control_budget")
        if not self.full_shadow_pairing_available:
            raise UncertifiableTrial("unmetered_queries_forbidden")
        if not self.semantic_correctness_verified:
            raise UncertifiableTrial("unverified_full_SPARQL_response")
        if not self.physically_enforced_regret_ceiling:
            raise UncertifiableTrial("unbounded_single_request_harm")
        if not self.revert_upper_is_certified:
            raise UncertifiableTrial("revert_cost_upper_not_proven")
        self.trigger_threshold=self.total_loss_budget_ms-(
            self.hard_max_single_request_regret_ms+self.certified_max_revert_ms)
        if self.actually_paid_migration_ms>self.trigger_threshold:
            raise UncertifiableTrial("migration_spend_too_large_for_loss_budget")
        self.net_ms=-self.actually_paid_migration_ms
        self.n_paired_queries=0
        self.reverted=False
        self.revert_charged_ms=0.0

    def observe_real_paired_query(self,*,static_full_ms:float,
             migrated_full_ms:float,additional_shadow_metering_ms:float):
        if self.reverted:
            raise UncertifiableTrial("trial_already_reverted")
        vals=(static_full_ms,migrated_full_ms,additional_shadow_metering_ms)
        if not all(isfinite(v) and v>=0 for v in vals):
            raise UncertifiableTrial("missing_or_invalid_paired_metering")
        reward=static_full_ms-migrated_full_ms-additional_shadow_metering_ms
        if reward<-self.hard_max_single_request_regret_ms:
            # This can happen if the claimed physical single-request cap was
            # not actually enforceable. Never make a false bounded-loss claim.
            raise UncertifiableTrial("hard_single_request_loss_cap_breached")
        self.net_ms+=reward
        self.n_paired_queries+=1
        must_revert=(self.net_ms<=-self.trigger_threshold)
        return {"net_before_revert_ms":round(self.net_ms,6),
            "must_revert_now_before_next_request":must_revert,
            "queries_must_continue_fully_paired":not must_revert,
            "is_pathwise_profitable_at_present":self.net_ms>0}

    def revert(self,actual_revert_ms:float):
        if self.reverted:raise UncertifiableTrial("double_revert")
        if not isfinite(actual_revert_ms) or not 0<=actual_revert_ms<=self.certified_max_revert_ms:
            raise UncertifiableTrial("revert_above_certified_hard_cost_bound")
        self.net_ms-=actual_revert_ms
        self.revert_charged_ms=actual_revert_ms
        self.reverted=True
        if self.net_ms< -self.total_loss_budget_ms-1e-8:
            raise AssertionError("PATHWISE_LOSS_INVARIANT_BROKEN")
        return {"final_realized_net_relative_no_move_ms":round(self.net_ms,6),
          "worst_case_floor_ms":-self.total_loss_budget_ms,
          "loss_budget_respected":True,
          "observed_paired_request_count":self.n_paired_queries,
          "guarantee_is_pathwise_not_positive_profit":True}
