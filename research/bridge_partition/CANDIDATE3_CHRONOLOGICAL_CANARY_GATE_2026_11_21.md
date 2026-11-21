# Candidate 3: chronological canary and dominant-pattern exclusion (2026-11-21)

**Execution:** https://github.com/AiDevnew168/scale_rag/actions/runs/44864233900
**Method:** frozen December-origin single balanced swap proposed using day 0. Day 1 *only* is an advance warning canary; all later days withheld from all decisions. No changes to prior successful frozen algorithm. Train on June 2017 120 predicates, four 30-ID shards. All 2018 months were already inspected before this follow-up: **EXPLORATORY, NOT independent confirmatory validation**.

## Strong frozen one-swap: re-tested on days 2+ (after both observation days)

| Month | Day2+ eligible future requests | Extra shard touches saved vs static | Change in single-shard pp | Improvement after excluding dominant day0 query pattern (pp) | Distinct novel-pattern delta (pp) |
|---|---:|---:|---:|---:|---:|
| January | 314,840 | +8,364 | +2.6922 | +6.8764 | -0.3563 |
| February | 353,099 | +8,569 | +2.7012 | +7.0556 | -1.8877 |
| March | 353,493 | +10,107 | +3.0561 | +7.1564 | -1.7154 |
| **Pooled** | **1,021,432** | **+27,040** | — | — | — |

**Important**: the day0 dominant pattern is *already invariant under the swap* in all three months. Removing it does not remove any measured saved extra touches. This is a strong counter to the simplistic claim that a *single* dominant recurring pattern explains the benefit. It does **not** rule out concentration across other recurring patterns.

## Only day1 canary observations and chronological future outcomes

| Month | Day1 novel distinct-pattern delta (pp) | Strict canary accepted? | Allowed -1pp canary accepted? | Future novel distinct-pattern delta of frozen swap (pp) |
|---|---:|---|---|---:|
| January | 0.0000 | Yes | Yes | -0.3563 |
| February | +0.6756 | Yes | Yes | -1.8877 |
| March | -0.4976 | No | Yes | -1.7154 |

Strict canary rule fixed *before these executions*: accept frozen day0 swap only if it saves extra shard touches on day1, day1 has >=20 novel distinct patterns, and novel distinct-pattern locality does not decrease on day1.

Strict canary saves 8,364 + 8,569 + 0 = **16,933** extra touches across the three days2+ heldouts. This preserves 62.62% of the frozen-head savings (27,040), while avoiding March deterioration entirely by doing no swap. However it still fails in January and February to protect future novel patterns: the canary looks harmless, then the later-month heldout patterns suffer. This **is not a successful guarantee** and may or may not generalize.

## Why publication remains conditional

Prior art makes hot-pattern relocation **not novel by itself**:
- WISE (2020): adaptive workload-aware RDF triple migration with query-span monitoring and cost models: https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290
- SWORD: workload-aware placement and replication, incremental repartitioning: https://www.vldb.org/vldb_journal/index.php/component/article_manager/article/1311
- DICE group (2021): RDF predicate co-occurrence based graph partitioning: https://github.com/dice-group/workload-aware-rdf-partitioning
- MTGA (2026): long-tail aware dynamic DB partitioning: https://www.sciencedirect.com/science/article/pii/S0957417426016192
- 2026 replication/partition ILP: https://arxiv.org/abs/2605.00209

### A defensible *new* paper hypothesis (UNPROVEN)

Does a **risk-calibrated migration admission controller** under an equal-byte storage and migration budget, accounting for novel-pattern risk and queueing/concurrency, deliver *net* lower cost than no migration, WISE-style repartitioning, and matched-capacity replication under previously unseen workload shifts? The risk model must be specified **before** a never-inspected test dataset, and must be compared with simpler canary and no-migration controls.

### Next actual measurement gate (not completed by this workflow)

1. Select actual RDF dataset with full graph triples and provenance; report triple/predicate physical bytes and query semantics, not just June top-120 IDs.
2. Construct four real partitions with equal **bytes** (not just 30 predicate IDs), version safe replica cache comparator with the **same** aggregate byte budget.
3. Implement measured query routing (serial and parallel), P50/P95/P99, inter-shard bytes, migration byte count/duration, CPU, end-to-end query validity.
4. Frozen replay where decisions use past observed windows only, matched no-migration and WISE/SWORD/MTGA/METIS/MMC strong baselines, plus both simple canary variants.
5. Confirm *positive paired net benefit after migration*, nontrivial gain beyond strongest baseline, and precommitted novel-pattern risk bound on newly held-out workload. Without all three, don't submit a novelty paper.

**Gate judgment:** PROXY POSITIVE; canary safety INSUFFICIENT; physical net economics UNKNOWN. No author should claim paper-level novelty or actual distributed latency savings based on these logs.
