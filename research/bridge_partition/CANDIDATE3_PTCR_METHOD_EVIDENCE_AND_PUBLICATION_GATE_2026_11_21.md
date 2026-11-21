# PTCR-90 (Past-month Tail-Compensated Repartitioning): precise candidate method
**Date:** 2026-11-21  
**Status:** exploratory evidence of a potentially useful new *research approach*, not yet an accepted publication-grade algorithm or production economic proof.

## Motivation and prior art

- **WISE (2020)** moves triples of frequent RDF query patterns under workload and movement costs. This means "move a hot pattern" is already known.
- **WASP (2021)** monitors dynamic active vertices/edges and partitions RDF stores adaptively, including handling high-degree vertices. "Streaming adaptation" is already known.
- **MTGA (2026)** explicitly addresses long-tail queries with online feedback.
- **Replication in Graph Partitioning and Scheduling Problems (2026)** investigates communication-cost gains from data replication.
- **A Repartitioning Hypergraph Model for Dynamic Load Balancing (2009)** integrates communication and migration cost.
- **Online Graph Partition for Distributed Dynamic GNN Training (2025)** provides adaptive decisions and online competitive analysis.
- **LRP (2025)** learns robust partitions for dynamic query shifts.

The prospective differentiator of PTCR is *using temporally staggered, separate evidence pools* to select a **two-stage compensated migration** and to enforce quantitative head/tail constraints over the **previously observed novel-pattern group**, not ordinary one-swap burst tuning. This combination is a *hypothesis of contextual novelty*, not a claim of priority over all related works.

## Formal definitions

Initial June-trained placement `P0`. Workloads:
- `H`: historic June training used only to build `P0` and define the old-pattern identity set;
- `R_{t-1}`: **all** eligible requests from the complete preceding 28-day interval, available before the new period starts;
- `O_t`: *only the first observed 24-hour day of current period t*;
- `F_t`: all later days of current period, strictly held out until the end.

Let `s_P(q)` be the number of active shards of query predicate-set q under P, and `L_P(q)=1[s_P(q)=1]`.

1. Frozen first move `P1`: enumerate all 5,400 distinct balanced one-swaps, maximize `H_t(P)=sum_{q in O_t} f_t(q)[L_P(q)-L_{P0}(q)]`. No future labels.
2. Prior novel tail `N_{t-1}={q in R_{t-1}:q not in H}`, including query occurrence weights.
3. Enumerate all balanced second swaps `P2` anchored at `P1`, plus the no-second-swap option.
4. Admit only `P2` with all:
   - `H_t(P2)>=0.9*H_t(P1)`
   - `T_{t-1}(P2)=sum_{q in N_{t-1}} f(q)[s_{P0}(q)-s_{P2}(q)]>=0`
   - `U_{t-1}(P2)=sum_{distinct q in N_{t-1}}[L_{P2}(q)-L_{P0}(q)]>=0`
5. **PTCR-90 selected policy:** maximize `T_{t-1}(P2)`, ties by `H_t(P2)`, then stable lexicographic pair. If feasible set empty, abstain with `P0` (zero migrations).
6. This first exploratory version enforces four equal **predicate-ID** shard sizes of exactly 30. It does **NOT** enforce real RDF bytes; that is a major open paper gate.

Candidate search is exact within its **anchored two-swap** class (5,400 candidates) because all legal pairs are enumerated and the exact objective/constraints are computed. Incremental incidence indexing restricts evaluation to hyperedges containing a moved predicate. This is not a proof of globally optimal partitioning, an approximation guarantee or a future tail nonregression guarantee.

## Exact anchored two-swap ORACLE feasibility

GitHub CI 44870629536: https://github.com/AiDevnew168/scale_rag/actions/runs/44870629536

The first swap is fixed to the frozen day0 original. The second swap's future risks/costs are tested exhaustively as a **future-aware bound**, not as an executable policy. Within 5,400 second-swap choices for each month, there exists an action with >=90% first observed head gain AND no future degradation in two aggregate June-novel tail metrics:

| Month | Locked first-swap future touches saved | Best hindsight joint-safe second-swap future touches saved | Safe oracle second swap |
|---|---:|---:|---|
| Jan | 8,688 | 12,258 | [30,72] |
| Feb | 8,898 | 10,276 | [30,47] |
| Mar | 10,315 | 12,694 | [30,47] |

This breaks the earlier *empirical infeasibility within the ONE-swap action space*, which has **zero** candidates satisfying all constraints in all three months. It is a concrete feasibility breakthrough, not an online algorithm proof.

## PTCR-90 CAUSAL retro-replay (June + past month + day0 selection only)

GitHub CI https://github.com/AiDevnew168/scale_rag/actions/runs/44870899418; uncertainty re-run https://github.com/AiDevnew168/scale_rag/actions/runs/44871088691

| Month | No move saved | Frozen first-swap saved | Same 2-swap budget day0-greedy saved | PTCR-90 saved | PTCR-90 June-novel request touches saved | PTCR-90 June-novel distinct local gain |
|---|---:|---:|---:|---:|---:|---:|
| Jan | 0 | 8,688 | 8,531 | **8,783** | **+926** | **+14** |
| Feb | 0 | 8,898 | 8,935 | **9,250** | -444 | **+12** |
| Mar | 0 | 10,315 | 7,964 | **12,694** | **+299** | **0** |
| **Total** | 0 | **27,901** | **25,430** | **30,727** | **+781** | +26 (not independent) |

- PTCR-90 has 2,826 extra touches saved vs frozen (10.13%) and 5,297 vs two-swap day0 greedy (20.83%) on 1,063,177 future requests.
- **March PTCR-90 spontaneously selects [30,47], the full future-aware oracle-safe second move, without seeing March future labels.**
- February still has **444 more June-novel extra touches than static**, despite recovering the distinct novel-locality count. It is **NOT** universally tail-safe.
- A separate June-only historical pair-shadow compensation heuristic failed to consistently solve the problem: https://github.com/AiDevnew168/scale_rag/actions/runs/44870734274. This negative comparator must remain included.

## Paired day-cluster uncertainty on PTCR improvements (3000 deterministic resamples)

Units = extra-shard touches saved by PTCR per 10,000 future queries; compared against the named baseline:

| Month | PTCR minus frozen, point / 95% interval | PTCR minus 2-swap day0 greedy, point / 95% interval |
|---|---|---|
| Jan | +2.9296 / **[-12.7994, +20.1106]** | +7.7712 / [-14.6592, +29.9522] |
| Feb | +9.5298 / **[-0.2054, +21.1674]** | +8.5281 / [-51.2758, +81.1978] |
| Mar | **+64.3777 / [+30.6966, +103.7459]** | **+127.9977 / [+70.9036, +196.6669]** |

**March** improvement is robust to this descriptive 27-day resampling. **Jan and Feb** incremental differences are **not** robust at 95% individually (their CIs cross zero). There is strong temporal dependence and only 3 periods. The three months were already open and analyzed when PTCR was conceived, so NO independent pre-registration claim can be made.

## Byte-price/operational economics and baseline gates

The first implementation has 2 swaps, while original method has 1, and no actual Wikidata 2018 predicate byte sizes. It is **not** legitimate to call +2,826 extra touches an economic gain until incremental migration cost is measured.

For any total extra physical-migration bytes `B_extra`, amortization requires approximately:

`B_extra * 8 / bandwidth_bps + extra_index_rebuild_sec + extra_barrier_sec < 2826 * critical_path_seconds_saved_per_avoided_touch`.

For example, at **100 Mbps** ideal transport and *assumed* 5 milliseconds per avoided serial touch, the combined three-month second-swap bytes must be **less than 17,662,500 bytes** even **before** any storage/index/caching costs. This is an assumption-derived threshold, NOT a measured property size, not a guarantee, and cannot be conflated with actual parallel SPARQL latency.

Strong next comparisons must include WISE/WASP / MTGA when objective-compatible, equal-byte-limit 1swap and 2swap greedy, memory-matched selective replication, cache controls, no migration, real critical-path parallel query runtime, correctness and P95/P99. Any "winner" statement before that point would be premature.

## Assessment
**Research-continuation GO:** one-swap head/tail infeasibility has been constructively overcome by a 2-move oracle, and a *fully causal* heuristic achieved stronger than simple 1/2-swap controls in three historic logs.  
**Paper novelty/economic deployment GO:** NOT YET. Must test new genuinely uninspected workload, byte-based migration at fixed storage, effective parallel latency, and reproducible prior-art comparisons. No new benchmark may be chosen/tuned after viewing its future labels and called independent.

## Exact artifacts
- `research/bridge_partition/candidate3_two_swap_compensation_oracle.py`
- `research/bridge_partition/candidate3_shadow_compensation.py`
- `research/bridge_partition/candidate3_past_month_tail_compensation.py`
- `.github/workflows/candidate3_two_swap_compensation_oracle.yml`
- `.github/workflows/candidate3_shadow_compensation.yml`
- `.github/workflows/candidate3_past_month_tail_compensation.yml`
