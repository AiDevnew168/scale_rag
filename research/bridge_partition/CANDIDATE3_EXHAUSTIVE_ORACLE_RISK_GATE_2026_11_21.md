# Candidate 3 — exhaustive exact one-swap novelty-risk frontier, 21 November 2026

**VERIFIED CI:** https://github.com/AiDevnew168/scale_rag/actions/runs/44869028533

**Source:** June 2017 Wikidata organic training, Jan/Feb/Mar 2018 Wikidata organic temporal heldout. These 2018 intervals were ALREADY INSPECTED in previous work. **The oracle below intentionally uses future labels only to compute an optimistic, hindsight-dependent feasibility bound; none is a deployable policy, independent discovery, or causal result.**

## Why this experiment

Our frozen December-origin day0 one-swap yields strong `total extra shard touches` reductions on >1M historical requests but hurts newly occurring predicate patterns. We need to determine whether this is failure of our decision heuristic or a tradeoff intrinsic to the allowed *exact 5,400 balanced one-swap* action space.

Original model: June-selected top-120 predicates, original hypergraph KM1 partition with four exactly equal 30-ID shards, first populated evaluation day observed; subsequent days scored. Dataset is predicate co-occurrence proxy, not full RDF/SPARQL, physical bytes or network.

All 5,400 distinct swaps exhaustively evaluated against future labels, plus no-op. A future-oracle *admissible* swap has:
1. **`future_novel_distinct_local_gain >= 0`:** the *number* of June-unseen distinct query patterns that can be answered in one shard does not decrease relative to frozen.
2. **`future_novel_request_touches_saved >= 0`:** the total extra-shard touches for June-unseen *request occurrences* does not increase.

These are two aggregate metrics, **NOT** a per-query no-harm guarantee. All modeled predicates are equal-size IDs, NOT byte-balanced physical data.

| Month | Requests in future | Frozen day0 swap saved total touches | Frozen extra touches saved for novel requests | Frozen gain in distinct novel local patterns | Hindsight unrestricted best total touches saved | Best *joint novel safe* hindsight saved touches | Safe hindsight best with positive day0 gain | Safe swap at >=90% frozen best day0 gain? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| January | 324,273 | 8,688 | -114 | -6 | 8,924 | 4,264 | 4,083 | **NONE** |
| February | 369,366 | 8,898 | -1,109 | -39 | 10,696 | 1,806 | 1,806 | **NONE** |
| March | 369,538 | 10,315 | -1,213 | -38 | 12,245 | 7,014 | 2,582 | **NONE** |
| **Total** | **1,063,177** | **27,901** | **-2,436** | — | **31,865** | **13,084** | **8,471** | **NONE** |

Joint nonregression has **feasible physical ID swaps**: Jan 799 / 5,400; Feb 642 / 5,400; Mar 586 / 5,400. If additionally requiring a *positive observed day0 local gain*, feasible swaps are Jan 54, Feb 35, Mar 19. But **zero** one-swap candidates in any of the three months can meet joint future novel nonregression while also retaining >=90% of best day0 observed request gain. This includes hindsight oracle knowledge of the future.

The best joint-safe hindsight swap retains **46.89%** of the original frozen policy's aggregate future touch saving (13,084 / 27,901); if it must also show positive day0 observed benefit, it retains only **30.36%** (8,471 / 27,901). Note the best joint-safe hindsight choices in Jan and Mar have **negative day0 observed gain**; they would not rationally be chosen by a deployable day0-greedy optimizer.

## Formal impossibility of universal no-harm to all future query patterns

Let current partition have nonempty shard A with at least two nodes i,z, and shard B with node j. A balanced swap exchanges i in A and j in B. Construct a query consisting of predicates `{i,z}`. Before swap, `span({i,z}) = 1`; after swap `span({i,z}) = 2`. Therefore every nontrivial swap in this model admits *some possible query pattern* with strictly increased shard span; universal strict no-harm across **all possible unknown future queries** is mathematically impossible, regardless of policy. This theorem is simple, not standalone publishable algorithmic novelty. It does **not** imply all genuine observed future query distributions must degrade.

## Scientific interpretation

- A strong **quantitative feasibility characterization** now exists for the closed, fully enumerated 1-swap action space: with a 90% day0 head-gain requirement, **aggregate head-tail joint objective is infeasible**, even for an omniscient optimizer.
- A **different method/action space** is needed to maintain near-full head benefits while tightly bounding novel query risk: potentially multi-move under a higher migration budget, capacity-aware selective replication, or a distributional risk guarantee that knowingly allows a bound instead of zero degradation. Such alternatives must use **actual byte cost** and compare against known WISE/WASP/replication baselines before claiming novelty.
- It would be inappropriate to claim a new algorithm solely from this hindsight oracle audit. The 2018 months were repeatedly examined; no independent preregistration is possible on them.

## Missing from paper-quality cost evidence

1. Same real RDF triples, matching query sources and fresh held-out time period.
2. Hard per-shard **byte** capacity, actual migration bytes/time, cache and index costs.
3. True SPARQL executions and answer equality; no train/test leakage.
4. Strong WISE, WASP, no-migration and equal-memory replication comparators.
5. Positive paired *net* critical-path latency or monetary savings in realistic parallel routing, and tail-risk bound.
6. Independent domain or preregistered prospective workload.

**Decision:** retain candidate 3's strong real-user workload locality signal as a motivation. Reject universal zero-harm, and reject the 90%-head strict-novel nonregression requirement for one swap as **provably unachievable on all three inspected time windows in that action space**. Explore other feasible action spaces and stronger data without altering frozen historic results.

## Executable source

`research/bridge_partition/candidate3_exhaustive_oracle_risk.py`; CI `.github/workflows/candidate3_exhaustive_oracle_risk.yml`. Every Jan/Feb/Mar job passed, outputs attached to the GitHub Actions run above.
