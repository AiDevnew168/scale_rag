# Candidate 3 — frozen chronological final PROXY gate (2026-11-21)

Workflow: https://github.com/AiDevnew168/scale_rag/actions/runs/44862500780
Commit under `research/candidate3-final-economic-gate-20261121`.
Scope: reproduced real 2018 Wikidata organic SPARQL predicate co-occurrence traces; **NOT** live RDF network/latency or demonstrated net profit.

## Methods
- Historical 14 June days, top 120 predicate IDs, four 30-ID shards.
- First present day in each evaluation month is observed. Frozen December-derived exact one-swap maximizes day0 whole-hyperedge locality over 5,400 capacity-preserving candidate swaps. Days after day0 are held out for scoring, never for decisions.
- Matched proxy controls: zero-migration static partition; frozen exact one-swap; day0 unique-only; day0 dual-risk with 90% and 50% of maximum observed request gain.
- Full query-log intervals January 1–28, January 29–February 25, and February 26–March 25, 2018. Original datasets and selection have already been inspected; this analysis is *post-hoc*, not a new independent preregistered validation.
- Additional metrics: sum(max(shards_touched-1,0)), unique novel pattern coverage, day-cluster bootstrap, threshold bytes given *hypothetical* serialized per-touch latency and bandwidth. Full JSON in action artifacts.

## Verified CI results

| Month | Future eligible requests | Frozen local % | One-swap local % | Frozen extra shard touches | One-swap extra shard touches | Saved | Relative reduction |
|---|---:|---:|---:|---:|---:|---:|---:|
| January | 324,273 | 87.3810 | 90.0951 | 44,515 | 35,827 | 8,688 | 19.517% |
| February | 369,366 | 86.6550 | 89.3482 | 51,497 | 42,599 | 8,898 | 17.279% |
| March | 369,538 | 85.0900 | 88.1327 | 57,485 | 47,170 | 10,315 | 17.944% |
| TOTAL | 1,063,177 | — | — | 153,497 | 125,596 | 27,901 | 18.177% |

## Honest negative control findings
- **Novel future request subset** extra shard touches: January 19,495→19,609 (+114); February 18,492→19,601 (+1,109); March 24,481→25,694 (+1,213); pooled +2,436. Thus a frequency-optimized swap hurts novelty locality even while improving the overall volume.
- Distinct novel pattern locality: January 27.1777→26.8293%, February 25.4452→23.6176%, March 26.4785→24.7760%.
- Equal-capacity day0 unique-only alternatives do **not** recover pooled volume gain. Day0 dual-risk 90% reproduces January/March head and beats February head for total saved touches (10,059 vs 8,898), but still does not preserve novel patterns vs static.
- No-migration routing can serve parallel shard requests; a lower shard count therefore has **no guaranteed latency advantage**. All cost tables in artifacts are conditional break-even envelopes, not real measured savings. At zero critical-path saving per avoided touch, any nonzero migration overhead yields negative net value.

## Decision
**PASS** for a frozen policy that reduces *observed shard-touch proxy* over three historical monthly windows.
**FAIL / NOT DEMONSTRATED** for no-harm novel-pattern coverage.
**NOT MEASURED** for real byte-balanced RDF migration, real distributed critical-path latency P50/P95, replication/caching under equal byte capacity, full SPARQL query semantics, and net operational cost.

**No paper-level algorithmic novelty or positive real net savings is claimed.**
For genuine final operational validation, materialize actual predicate-to-triple byte weights on a bounded RDF graph; hard-enforce per-node byte capacity; deploy fixed and one-swap variants, compare with cache/replicate at equal memory and no-migration parallel routing; measure migration bytes/time, queries P50/P95, throughput and queueing under identical chronological replay. Those experiments were not run by this CI workflow.
