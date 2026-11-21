# Candidate 3 — full SPARQL four-shard validation and economic verdict
**Date:** 2026-11-21  
**Repo:** AiDevnew168/scale_rag  
**Branch:** `research/candidate3-real-sparql-execution-20261121`  
**Evidence class:** Executed, auditable engineering feasibility; NOT an independent paper-quality algorithm claim.

## Bottom line
- **PASS:** Four real Oxigraph shard processes expose predicate-local `CONSTRUCT` queries; coordinator merges actual returned N-Triples and evaluates the original `SELECT`. On 10 *exact-template-disjoint* heldout queries (4 nonempty), the complete result multiset hash matches the independently loaded central Oxigraph engine in all runs.
- **PASS:** One *training-only chosen* two-predicate swap physically copies 292,495 serialized RDF bytes between shards, verifies SHA256 receipts, and deletes the old predicate triples from the two original stores while queries are stopped.
- **FAIL:** The real SPARQL query transfer/contact workload on these 10 test templates is **unchanged** by that swap. The paired measured net benefit is negative in both serial and parallel execution, including a one-time 15.7273ms migration barrier.
- **NOT PROVEN:** Novel algorithm, economic benefit in a production distributed RDF/Semantic-RAG system, performance on truly new benchmark families, guarantee of no novel-pattern degradation, or dominance of WISE/WASP.

## Source and safety barriers
- Source independent Stream WatDiv archive: https://zenodo.org/records/23016810
- Archive SHA256 `b3f6f0447b9f78cc695953a0c1b5dd1144d5c400113493eecbb23f36d91d84b3`.
- Physical union: 56,915 initial triples plus 58,555 streamed insertion triple **records**, yielding 115,470 raw N-Triples lines and 107,099 unique RDF triples in the central Oxigraph store. This *union of all events* is an engineering static snapshot, **not chronological stream replay**.
- Four shard physical raw bytes: [3,941,915; 3,941,937; 3,941,900; 3,941,920]; explicit <= 4,336,109.8 byte ceiling in each. Two elephant predicates physically split for feasibility; no future queries used in placement, split, or swap selection.
- From the 40 SPARQL query lines there are **only 20 unique exact texts**. The original "train first 20 / test last 20" was FULL 20/20 train-test leakage. See exact hash audit: https://github.com/AiDevnew168/scale_rag/actions/runs/44868009594.
- Corrected seeded exact-hash-disjoint split: 10 unique train / 10 unique test; no overlapping query text or query IDs. Exact-disjoint locality comparison: https://github.com/AiDevnew168/scale_rag/actions/runs/44868051022. Original claimed 5 saved touches /20-query heldout vanishes: now **0 saved /10-query distinct heldout** for both candidate swap objectives. Previous 10.42% heldout-gain claim **withdrawn** as generalization evidence.

## Genuine four-shard engine and migration
CI: https://github.com/AiDevnew168/scale_rag/actions/runs/44868163925  
Code: `research/bridge_partition/candidate3_real_sparql_shards.py`.

- Workers each own an independent in-memory `pyoxigraph==0.5.13` RDF store and TCP HTTP service. The service evaluates real `CONSTRUCT` queries per selected predicate on shard-local data.
- Coordinator fetches all relevant predicate fragments from 1–4 services and evaluates unmodified original full SPARQL SELECT on the union of those fragments with Oxigraph. This is a **naive coordinator materialization** distributed storage system, *not* federated distributed join optimization.
- All 10 heldout answer multisets (including 4 nonempty) equal the centralized results, both sequential and parallel, before and after the physical move.
- Swap is `<http://ogp.me/ns#tag>` <-> `<http://xmlns.com/foaf/age>`. Transferred 230,556 + 61,939 = 292,495 N-Triples raw bytes. SHA256 checked at receiving workers; sending workers delete their predicate triples. Query admission is paused for a controlled, *non-atomic across servers* barrier; not a production transactional migration.
- On 10 heldout queries the serial and parallel executions both contact **35 shards** and fetch **19,250,844** RDF bytes, unchanged before/after swap. This is the basic economic obstacle in this dataset.

## Randomized paired test and bootstrap (more defensible latency estimate)
CI: https://github.com/AiDevnew168/scale_rag/actions/runs/44868241077  
Code: `research/bridge_partition/candidate3_paired_full_sparql.py`.

Two separate four-shard worker clusters run concurrently (each policy still uses four byte-balanced shards), one fixed and one physically migrated, on the same machine. Tests interleave randomly. Each of the 10 distinct heldout queries is evaluated five times per policy/mode (50 paired observations), with every full SPARQL answer multiset checked. **Uncertainty resamples 10 distinct query templates, not 50 observations.**

| Metric | Serial | Parallel |
|---|---:|---:|
| Fixed mean per query | 34.9311 ms | 26.8664 ms |
| Migrated mean per query | 35.0435 ms | 27.2081 ms |
| Mean saved per 10 distinct queries, before migration | **-1.1241 ms** | **-3.4167 ms** |
| 95% template-cluster bootstrap interval, before migration | [-3.6824, +1.2136] | [-7.0668, -0.1240] ms |
| Physical migration barrier (once) | 15.7273 ms | 15.7273 ms |
| Mean net saved per 10 queries after cost | **-16.8514 ms** | **-19.1440 ms** |
| 95% template-cluster bootstrap interval, after cost | **[-19.4097, -14.5137] ms** | **[-22.7941, -15.8513] ms** |
| Shard contacts (50 requests) fixed/migrated | 175 / 175 | 175 / 175 |
| RDF bytes fetched (50 requests) fixed/migrated | 96,254,220 / 96,254,220 | 96,254,220 / 96,254,220 |

This *refutes positive economic savings in this tested setting*; it does not imply all data layouts or traffic patterns have zero benefit. P50 and P95 after the swap are also not convincingly improved. No monetary pricing or energy was measured, so time differences must not be presented as currency savings.

## Preserve independent genuine positive evidence
Earlier real Wikidata organic query-log test is **not invalidated** by the Stream WatDiv exact-text leakage: https://github.com/AiDevnew168/scale_rag/actions/runs/44862500780
- 1,063,177 *filtered chronological future queries* across three 2018 windows.
- Frozen one balanced swap per window reduced extra-shard-touch proxy by 27,901 / 153,497 = **18.177%**, with novel distinct-pattern degradation.
- This is a different workload family and unit of placement (120 equal-size predicate IDs). These logs do **not** contain RDF triple physical bytes, distributed SPARQL results or network latency. Do not fuse numeric outcomes across those incompatible benchmarks.

## Comparison to existing literature and admission gate
Workload-aware RDF repartitioning and migration-aware cost models already occur in:
- WISE: https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290
- WASP: https://link.springer.com/article/10.1007/s41019-021-00156-2
- AWAPart: https://arxiv.org/abs/2203.14884

The simple one-swap, risk-canary, and elephant predicate split mechanisms have no proven algorithmic novelty above these baselines. In this corrected small independent-template test, there is no economic improvement at all. A standalone high-impact method paper is **NO-GO** at this time.

Future `GO` requires **new, unopened realistic data and queries; query disjointness audited before experiments; full distributed query correctness; true byte-equal replication/cache and faithful WISE/WASP comparisons; physical indexed migration with recovery; positive paired net cost in realistic parallel mode**. Work on the original Wikidata workload remains a *separate, still-untested implementation candidate*, not a validated general algorithm. Do not repeatedly tune on the now-opened 20-template Stream WatDiv suite.
