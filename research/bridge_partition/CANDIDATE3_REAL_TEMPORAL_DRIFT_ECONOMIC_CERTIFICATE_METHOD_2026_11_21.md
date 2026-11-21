# Candidate 3 bounded-drift economic admission: exact theorem, impossibility result, non-novel controls

**Evidence and status:** 2026-11-21; source implementation `candidate3_bounded_drift_economic_certificate.py`; 13/13 fail-closed/adversarial tests at https://github.com/AiDevnew168/scale_rag/actions/runs/44906919628. **Formal conditional safety construction, NOT a novel SOTA algorithm and NOT verified future profit.**

## A. A necessary impossibility result

Suppose any migration controller observes finite fixed prior logs `h`, then decides whether to incur strictly positive migration cost `C`. With no restriction on future query distribution, construct two worlds that have **identical** history `h`: the first continues with queries helped by the migration, the other immediately switches to queries for which the new partition is worse. No decision function on `h` can distinguish them. Therefore no non-trivial history-only migration controller can guarantee strictly positive *realized future net* against no-migration over all possible future workloads. This counterexample does not rely on estimation error or a particular partition heuristic.

The `no_move` action guarantees zero incremental migration cost and zero incremental benefit relative to itself. Even a method with excellent historical retrospective gain cannot evade this no-free-lunch result. Conditional bounds require explicit, independently justified future-drift assumptions or realtime feedback with bounded loss.

## B. A valid simultaneous one-sided expected-net certificate under explicit assumptions

For each of a finite `M` candidate action set defined using a **disjoint training sample**, let per-query reward `g_a` equal measured *full original SPARQL end-to-end runtime saved* relative to the physical no-migration policy, with a **predeclared hard bound** `-B <= g_a <= B`. Let `X_{d,a}` be per-day block averages on `n` independent exchangeable calibration days (one query per day, or an explicitly justified scheme matching the future estimator). Assume these blocks share mean `mu_cal[a]`. Calibrated daily means should not be naively inflated to all individual requests when day traffic volumes vary enormously.

Let `P_cal` and `P_future` be **full joint distributions** over query identities *and realized latency rewards*, and let the future L1 shift satisfy a separately validated limit

```
SUM_x ABS(P_future(x) - P_cal(x)) <= rho_full[a],   0 <= rho <= 2.
```

Then for each fixed action,
```
E_future[g_a] >= E_cal[g_a] - B * rho_full[a].
```
Proof: `abs(sum_x (p-q)g(x)) <= sup|g| sum_x |p-q|`.

A one-sided Hoeffding+union confidence radius simultaneously for all `M` training-fixed action candidates, using `delta` in (0,1), is

```
epsilon = B * SQRT(2 * LOG(M/delta) / n).
E_cal[g_a] >= mean_cal[a] - epsilon  simultaneously with probability >=1-delta
```

given the explicitly required independent bounded calibration days. If an externally certified upper bound `C_a` on **entire** physical migration, index writes, communication, pause, and any cutover overhead is supplied and the future horizon `H` consists of `H` exchanges with the calibrated per-query population, the lower bound is

```
LCB_expected_net_a = H * (mean_cal[a] - epsilon - B*rho_full[a]) - C_a.
```

Admission requires `LCB_expected_net_a >0`, full original SPARQL semantic correctness for every tested action and original query, and verified cost/shift assumptions. The decision may choose the largest positive simultaneous LCB across candidates. If any required premise is unknown, **ABSTAIN**. Never use a single observed migration duration as a certified upper bound.

This is a **CONDITIONAL lower bound on expected future clipped economic benefit**, not a pathwise positive realized profit guarantee. A future observer can encounter bad day sequences even with these conditions. If latency is clipped to obtain `B`, the guarantee is ONLY on the clipped metric unless full physical unbounded latency is controlled by the implementation itself. Explicitly report losses from clipping and timeouts.

## C. Predicate witness theorem is only for routing, not real latency

A move of predicates `S` may change shard-contact routing only for queries whose predicate set intersects `S`, assuming deterministic fixed query routing and no other placement change. If `r_a(q)` is the number of contacted shards, `|r_before(q)-r_after(q)| <= 3` on four shards. Let `A={q:q predicates intersect S}`. Then

```
abs(E_new[delta_r] - E_old[delta_r]) <= 3 * SUM_{q in A} abs(P_new(q) - P_old(q)).
```

This is an exact triangle-inequality witness bound for **shard contacts only**. Do NOT substitute it into `g_a` for full SPARQL wall time. Even a query whose predicates were not moved can be delayed by changed cache, load, scheduling, network interference and index maintenance. A wallclock certificate requires a bound on FULL runtime reward drift, or separately proven bounds on all collateral effects. Otherwise the proof does not apply.

## D. Current research status and economic gate

- Previous physical NYT and DrugBank counterfactual migrations had negative net milliseconds and 95% intervals fully negative, while DrugBank's pre-test abstention avoided harm (incremental realized profit vs no move = **0**).
- The new 2014 original SWDF.log.gz source is immutable SHA `2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df`, **95,235,612 gzip bytes / 1,061,032,427 expanded bytes**, **5,499,797 HTTP records**, **176 actual UTC calendar days**, **1,416,681 dated query requests** and **99,995 distinct literal texts**. Source-only provenance CI https://github.com/AiDevnew168/scale_rag/actions/runs/44906760524.
- SWDF is from the same underlying publication family as FEASIBLE cleaned queries previously inspected; **not an independent external confirmation**, although its 176 genuine event timestamps were new to the prior synthetic query evaluations.
- The conservative control cannot claim guaranteed future profit from 176 observed days unless independently valid future distribution-shift and runtime/cost bounds exist. Prior days' empirical maximal drift does not certify an adversarially unrestricted future.
- A data/source-only 176-day strict SPARQL parser gate runs separately, with output hashes and aggregate statistics rather than sharing client IPs or raw query text.
- Unlike a paper-worthy outcome, the 13 green unit tests show correct fail-closed implementation **under asserted premises**, not actual economic advantage on a real SPARQL production cluster.

## E. Genuine next research requirement

Calibrate and evaluate a **loss-limited, feedback-driven, full-result-safe controller** that can stop/revert under actual unanticipated distribution shift with a rigorously bounded *realized loss budget*. Independent real current/future day blocks and matched original RDF snapshots are prerequisites for a journal claim. Strong prior art (author DIAERESIS, WISE, WASP, AdPart/PCM as available) must be run under properly matched budget and semantic correctness; reproducing DIAERESIS's three queries alone is insufficient. No claim of algorithmic novelty is made by Hoeffding, a TV inequality or stop-loss by themselves.
