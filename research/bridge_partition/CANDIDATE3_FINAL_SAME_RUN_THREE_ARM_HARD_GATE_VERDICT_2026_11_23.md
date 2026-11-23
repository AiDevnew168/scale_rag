# FINAL DECISIVE THREE-ARM SAME-RUN HARD GATE — 2026-11-23

**Decision: NO-GO for a new high-impact journal method built on the current single-host 304,592-triple predicate-fragment-shipping coordinator or its constant-filter pushdown.** This is an empirically strong *scope-limited* conclusion, NOT a universal disproof of large-scale distributed RDF optimization.

## Immutable executed evidence

- **Actual original three-arm physical CI:** https://github.com/AiDevnew168/scale_rag/actions/runs/45106146288, commit `6a9ab43f5fe2ee779a06dd044b399de09d4c3b21`, GitHub artifact ID `14788740361`, ZIP SHA256 `ae47c7b18a6c388df09173a9d612f1c45460458b2a3e4b7cb9c92dd0e32cfe0f`. Exact `report.json` and pre-timing freeze are stored in artifact. All results were recomputed independently from the raw artifact, not just accepted from a green CI action or rounded console lines.
- **Pinned original source:** FEASIBLE SWDF historical log SHA256 `2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df`, RDF ZIP SHA256 `65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb`. Graph has **304,592 original RDF triples**. The original RDF graph is NOT verified as-of the 2014 query timestamps.
- Original 88-day TRAIN-only trace; 48 full original query texts, SHA-frozen as two nonoverlapping 24-text cohorts from the earlier source-only ranking. Both frozen sets matched SHA text IDs in the two prior completed original training artifacts 14713341448 and 14713990727. **The exposed, semantically invalid 53-day historical test was not recycled.**
- Physical controls all on ONE GitHub runner: direct persistent indexed pyoxigraph central store; four separately indexed localhost TCP shard processes + raw full-predicate fragment transfer + per-request central temporary graph; same workers + conservative source-original NTriples constant-only predicate filtering + per-request central temporary graph. Fixed 3 balanced method-order permutations per text, 3 repeats each.
- **144 complete triple-arm blocks, 432 original query calls, 288 independent central-versus-worker original SPARQL semantic certifications all PASS; zero censored requests or exceptions.** Both 24-text cohorts cover all 48 distinct source text hashes; each text has all three repetitions and all arms at all three balanced positions.

## Direct same-run performance, recomputed

| Arm | Mean complete SELECT wall ms | Median ms | Empirical p95 ms | Max ms | Total TCP original RDF payload bytes |
|---|---:|---:|---:|---:|---:|
| Persistent full-index centralized Oxigraph | **1.802419** | **0.096430** | **12.269261** | 45.573366 | 0 (no worker-to-coordinator transfer) |
| Full predicate fragment shipping | 127.643503 | 132.661561 | 152.913906 | 171.142241 | 1,747,083,228 |
| Constant-filter pushdown to workers | 70.455225 | 71.351342 | 80.520621 | **333.654725** | 730,309,749 |

- Source-body saving from full fragment transfer to selective: `1 - 730309749/1747083228 = 58.198%`; within the weak four-worker design, mean SELECT wall saving **57.188278ms**, or **44.8%** lower relative to full fragment shipping. Hence the classic constant-filter optimization DOES have a real, repeatable implementation benefit against the designated weak control.
- **Direct indexed central versus selective**: `70.455225 / 1.802419 = 39.09x` faster in mean wall time. Indexed central faster in **144/144 individual matched execution blocks**; also in **48/48** distinct query-text mean deltas and **7/7** exact predicate-family mean deltas. Minimum per-original-text mean central advantage **20.487ms**. This is a same-run physical defeat, not an unpaired estimator.
- Family dependence: exact family sizes **[34, 8, 2, 1, 1, 1, 1]** of 48 texts, not 48 independent families; the descriptive 3,000-replicate predicate-family resampling interval for selective-minus-central mean latency is **[41.049, 71.416]ms**. This is *not* an independent timestamp-based confidence interval or production tail-risk guarantee.
- Startup, source-only same-run: central indexed graph build 607.834ms; four worker indexed group startup 326.122ms. These are different startup operations and do NOT provide total production operating cost or a long-horizon economic net. Persistent worker cache RSS and CPU ticks recorded in raw report, but no full eviction/rollback/maintenance budget is certified.
- Previous single-worker original source cache cold RPC had 258.374ms latency and +25.906 MiB VmRSS, and three source fragments required 769.076ms parser-cache setup and 30.412MB traced Python allocations. Same-run selective single-request maximum was **333.655ms**; p95 improvement does not imply a production p99/worst-case SLA.

## Validity boundaries

1. All results are about 48 source-compatible original first88-day *TRAIN-only* texts (chosen by restricted compiler eligibility), four workers on **one host**, and one RDF graph fitting centrally in memory. They do not show the centralized solution would dominate an actually too-large-to-fit graph, network-separated multi-host workload, or remote federated endpoints.
2. This is *not* a real native distributed SPARQL join engine. All interworker data remain fully or selectively retrieved and rebuilt into a fresh per-request coordinator store, unlike more competitive published distributed RDF systems.
3. No original WISE, AdPart, CostFed or newer 2026 executable has been run on a matched data/control; even a positive selective-over-full margin cannot be called a stronger state-of-the-art outcome. Classic triple-pattern pushdown and semijoin filtering precede this work.
4. The previous 53-day original heldout economic benchmark is **invalid**: 1256/1258 correct paired SPARQL with two failures (one repeated text missing explicit PREFIX), the selected actual economic policy `no_move` had **zero incremental gain**, no convincing uncertainty-adjusted positive prospective net.
5. Original source graph not aligned to original logs as-of date; Query-only published 2026 external 40-vs-32 benchmark inventory is unresolved. No second independent full corpus or truly cross-host execution exists.

## Final research admission verdict

| Gate | Verdict |
|---|---|
| Reproducible natural original training source and source hash | PASS within source |
| Correct original 48-query triple-arm semantic evaluation | PASS (432 calls / 288 pairs) |
| Full-to-selective transfer byte and same-run wall reduction | PASS against naive full-fragment coordinator |
| Strong indexed same-run central baseline competitiveness for this small graph | **FAIL (central 39.09x faster)** |
| Independent temporally untouched test with all SELECT semantics | FAIL / consumed historical holdout |
| Real distributed multi-host / memory capacity & complete cold maintenance costs | NOT DEMONSTRATED |
| Matched published SOTA and genuinely novel algorithm | NOT DEMONSTRATED |
| Prospective economic net gain from an actually selected migration | **NO: no_move chosen; zero incremental** |
| High-impact journal methods novelty for current approach | **NO-GO** |

**Action:** Freeze source-level training positive results as an engineering benchmark; STOP spending resources inventing more migration heuristics on this four-worker temporary-graph coordinator. A fresh research hypothesis must target a fundamental failure genuinely unaddressed by AdPart/WISE/CostFed, use a version-aligned INDEPENDENT temporal corpus, strong published multi-host baselines, and predeclared net resource evidence. Do not claim an article submission chance from the current implementation alone. The older source and all negative outcomes remain fully preserved for reproducibility.