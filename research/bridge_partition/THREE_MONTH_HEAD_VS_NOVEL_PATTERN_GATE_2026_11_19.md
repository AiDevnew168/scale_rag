# Candidate 3 — Three-Month Frozen Hot/Tail Tradeoff Audit
**Date:** 2026-11-19
**Research repo:** AiDevnew168/scale_rag
**Status:** Real reproducible operational query-span signal, strong evidence of HEAD-vs-NOVEL-PATTERN conflict; NOT a proved new algorithm.

## Reproducibility
- Frozen day0 policy independent January & February: https://github.com/AiDevnew168/scale_rag/actions/runs/44534663360
- Frozen exact same policy on March: https://github.com/AiDevnew168/scale_rag/actions/runs/44535289318
- Exploratory alternative dual-risk same-day0 swap decisions, three months: https://github.com/AiDevnew168/scale_rag/actions/runs/44536018374
- Scripts: `research/bridge_partition/independent_month_burst.py`, `research/bridge_partition/dual_risk_swap_audit.py`; corresponding Actions workflows.
- Frozen placement from June 12-25, 2017, first-day-only feedback in the respective new month; tests contain only later days in that month. Exactly 120 June-selected top property IDs, 4 balanced 30-ID shards, no replicas, at most one balanced two-predicate swap. No future queries enter adaptation decisions.

## Completely later chronological windows, fixed intervention

| Month | Future eligible request count | Fixed strong KM1 complete same-shard % | Day0 max-count-gain one-swap % | Delta pp | Day-block bootstrap CI95 pp |
|---|---:|---:|---:|---:|---|
| 2018 Jan 1–28 | 324,273 | 87.381 | 90.095 | +2.714 | [2.242,3.225] |
| 2018 Jan 29–Feb 25 | 369,366 | 86.655 | 89.348 | +2.693 | [2.279,3.247] |
| 2018 Feb 26–Mar 25 | 369,538 | 85.090 | 88.133 | +3.043 | [2.728,3.403] |

The March code extends the MONTHS list and adds evaluation metrics; it uses unchanged `december_burst_swap.optimizer_one_swap`. The two early 2018 windows were used in previous exploratory analysis, then the March check added a later file. This is independent *chronological* verification in one log family, NOT unseen benchmark-family confirmation or guaranteed non-overlap between agents working on the same repository.

## Novel *unique* future coaccess-set behavior

Each distinct 2–12-property combination gets ONE vote, rather than its raw request frequency.

| Month | # distinct novel future combinations | Frozen strong coverage % | Head-optimizing day0 swap coverage % | Distinct-pattern-optimizing day0 swap coverage % |
|---|---:|---:|---:|---:|
| January | 1,722 | 27.178 | 26.829 | 28.920 |
| February | 2,134 | 25.445 | 23.618 | 25.679 |
| March | 2,232 | 26.478 | 24.776 | 26.165 |

**Critical:** The method improving demand-weighted locality across 3 months HURTS novel distinct-pattern coverage every month. Distinct-pattern-only day0 optimization can rescue the low-frequency tail at the cost of the head, but did not consistently surpass frozen for March.

## New train-only two-risk candidate test (AFTER looking at previous data: exploratory)

Enumerate zero or 5,400 capacity-preserving balanced two-predicate swaps using ONLY first-day observed request-pattern counts and unique pattern counts; choose maximum day0 unique-pattern gain subject to retaining >=90% (or 50%) of the BEST day0 observed-request count-gain. Test later days only.

- January: >=90% chooses same head swap [20,57], so no novel unique improvement: head 90.095%, novel distinct 26.829%.
- February: >=90% chooses [20,57] rather than head-only [25,57]. Head locality improves slightly from 89.348 to 89.454%; novel distinct improves from 23.618 to 24.742%, still below unchanged baseline 25.445%.
- March: >=90% chooses the same head swap [27,57]; head 88.133%, novel distinct 24.776%. >=50% chooses [8,59], but head drops to 84.666% (below frozen 85.090%) and novel distinct 26.165% (below frozen 26.478%). This is a concrete generalization failure for the naive two-risk selector.

This does NOT prove a Pareto improvement is impossible with other available information. It demonstrates that simply adding observed-day unique-pattern counting to the head objective does not reliably preserve *future* unseen structures.

## Scientific interpretation
1. **Strong positive:** a single historic-day adaptation reliably improves traffic-weighted locality over frozen strong hypergraph baseline on three later genuine chronological workload periods (>1.06 million eligible future requests).
2. **Important negative:** the same policy degrades average future novel structure coverage (one vote per distinct unseen combination) across all three periods.
3. **Simplistic tradeoff solution fails:** hard safeguards on day0 unique gains cannot reliably protect truly future novel patterns; tail-unique prediction is not equivalent to recovering popular traffic.
4. **Potential research opening:** *online constrained hypergraph placement that simultaneously preserves a quantified uncertain-distinct-pattern risk and demand-weighted SLO under byte-weighted capacity/migration*. Prior art on partitioning, SWORD, WISE, MTGA, learned tail-aware placement must be reviewed; do not claim novelty from scalarization or max-min alone.
5. **Critical missing gates:** physical predicate-byte weights and migration cost; real distributed join/routing latency; comparison to cheap routing, caching, replication and incremental partitioners; more independent temporal log families; statistically defensible cluster uncertainty for distinct patterns (not iid patterns).
6. **Not RAG accuracy:** a query's co-mentioned predicate IDs being placed together is a cost proxy, not guaranteed SPARQL execution speed or scientific RAG response accuracy.

## Go/no-go judgment
**GO for a limited workload-diversity-constrained physical cost study. NO-GO for announcing a breakthrough, a new graph algorithm or a paper yet.** The opportunity is empirically real, but hard: one must improve the tail WITHOUT sacrificing the demonstrated head benefit, under actual bytes and hard memory limits. If this cannot be done over two new independent log sources, stop this candidate rather than repeatedly optimizing against already-viewed 2018 periods.
