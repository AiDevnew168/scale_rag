# Candidate 3 — risk, independent RDF-byte and cost-evidence gate (2026-11-21)

**Branch:** `research/candidate3-risk-economics-20261121`  
**Status:** real workload locality replicated; **risk-controller improvement FAILS**; real byte-capacity feasible only after fragmenting elephant predicates; positive **measured TCP acknowledgement routing component** under controlled conditions; **end-to-end RDF economic profitability and algorithmic novelty NOT established**.

## Evidence provenance

1. Locked Wikidata organic query traffic on Jan/Feb/Mar 2018 from frozen policy:
   - https://github.com/AiDevnew168/scale_rag/actions/runs/44862500780
   - 1,063,177 future filtered real queries, 27,901 fewer extra shard touches (18.177%), at one capacity-preserving 2-ID swap per interval. This is a **predicate co-occurrence proxy**, *not* SPARQL execution.
2. Three-day risk admission versus simple controls:
   - https://github.com/AiDevnew168/scale_rag/actions/runs/44866989280
   - Outcomes common day4+ holdout Jan 297,479; Feb 315,575; Mar 336,320.
   - Locked one-swap saves Jan 7,650; Feb 8,020; Mar 9,319 extra touches (pooled 24,989).
   - Day0 candidate + canary days1-3 with observed novel-pattern nonregression gate accepts Jan only, preserves 7,650 (30.61% of locked gain), **yet novel distinct future locality deteriorates in Jan**. Feb/Mar rejected.
   - Greedy recent-observed alternative: Jan 7,650; Feb 9,471; Mar 31; no consistent improvement. Zero claim of algorithm novelty.
3. Official Wikimedia `sample.nt` physical preflight:
   - https://github.com/AiDevnew168/scale_rag/actions/runs/44867039886
   - Download succeeded but only **5,197 bytes**, **zero** matched top-120 selected predicates. **INCONCLUSIVE** as a physical cost input; no measured transfer for locked Wikidata swaps.
4. Independent Stream WatDiv 2026 synthetic RDF dataset:
   - Source: https://zenodo.org/records/23016810
   - SHA256 of downloaded ZIP: `b3f6f0447b9f78cc695953a0c1b5dd1144d5c400113493eecbb23f36d91d84b3`.
   - https://github.com/AiDevnew168/scale_rag/actions/runs/44867163282
   - 56,915 static triples (7,925,588 serialized bytes); one `friendOf` predicate holds 6,442,747 bytes = 81.3% total; no four-way <=+10% byte-balance possible without fragmenting predicate data.
   - Static+all stream-event triple payload: 115,470 serialized triples, 15,767,672 bytes, 84 predicates; aggregate is **not a chronological fully valid SPARQL store**.
5. Byte-balanced fragmentation and physically verified transfers:
   - https://github.com/AiDevnew168/scale_rag/actions/runs/44867477361
   - Split two elephant predicates (`friendOf`, `follows`) across all four shards. Result byte loads: [3,941,915; 3,941,937; 3,941,900; 3,941,920] (cap 4,336,109.8 each). **Actual byte cap PASSES**, not just ID count.
   - 40 synthetic SPARQL templates, first 20 train, last 20 test; one byte-feasible balanced whole-predicate swap chosen on train improves heldout extra shard touches 48 → 43 (**5 saved, 10.4167%**). Heavy predicate scans still touch 4 shards; this is a routing locality proxy.
   - Transferred **200,598 real serialized RDF bytes** over localhost TCP with SHA256 receipt; median 0.548 ms in that run. Receiver is an acknowledgement sink; it is **not** an atomic live shard migration.
   - Cost-per-byte greedy selects 191-byte swap, only 1 saved touch in test, demonstrating gain-per-byte optimization differs from volume-gain optimization (not a novelty claim).

## Paired TCP routing component measurement, stronger than bare activation counts

Final run with template-cluster bootstrap: https://github.com/AiDevnew168/scale_rag/actions/runs/44867642335

- Same independent 20 heldout query templates, 5 interleaved paired repeats each (100 pairs).
- TCP handler **only acknowledges** each shard activation: DOES NOT execute SPARQL joins, look up triple indices or return answers.
- Three profiles with `0ms`, `1ms`, `5ms` *injected* per-shard server delay; two modes: serial and parallel fanout. All results below are measured end-to-end **ACK-ONLY TCP route-overhead** and measured *separate* TCP transfer.
- Same verified migration: 200,598 bytes, median 0.5436 ms, P95-nearest 0.7552 ms (7 repetitions).
- Bootstrap samples whole query templates, not all 100 repeated observations as independent points. The CI for net batch saving subtracts **P95 migration** from bootstrap route-saving quantiles; this is conservative about transfer time but not a full migration model.

| Mode (injected per-shard delay) | Mean saved ms per 20-query batch | Mean minus median transfer, ms | 95% bootstrap interval after P95 transfer, ms | P95 before → after, ms |
|---|---:|---:|---:|---|
| Serial, 0 ms | 1.1360 | +0.5924 | [-0.4346, +1.2624] | 0.9313 → 0.9212 |
| Parallel, 0 ms | 1.6848 | +1.1412 | [-0.1417, +2.1139] | 1.3576 → 1.3191 |
| Serial, +1 ms | 6.4372 | +5.8936 | **[+0.6724, +10.8424]** | 5.2248 → 5.2277 |
| Parallel, +1 ms | 1.3545 | +0.8109 | [-0.5916, +1.8900] | 2.3128 → 2.2670 |
| Serial, +5 ms | 26.6139 | +26.0703 | **[+4.6765, +47.2137]** | 21.3738 → 21.3624 |
| Parallel, +5 ms | 1.0741 | +0.5305 | [-0.7749, +1.5127] | 6.3241 → 6.3283 |

**Outcome:** on this component, only **serial 1 ms / 5 ms injected-delay regimes** have a positive 95% query-template-cluster bootstrap lower bound **after** P95 sampled migration. Parallel and zero-injected-delay 95% intervals cross zero. Some P95 query latencies are no better or slightly worse. Any statement of system-wide positive economic savings or robust P95 improvement would therefore be false.

## Prior-work/novelty gate

Relevant strong methods overlap the generic objective:
- WISE (2020), workload-aware query-span and migration-cost guided RDF triple relocation: https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290
- WASP (2021), workload-adaptive streaming partitioner for distributed RDF graph stores: https://link.springer.com/article/10.1007/s41019-021-00156-2
- AWAPart (2022), adaptive KG partitioning: https://arxiv.org/abs/2203.14884
- A repartitioning hypergraph model for dynamic load balancing (2009), already integrates cut+movement cost: https://www.sciencedirect.com/science/article/pii/S0743731509000847

**Neither risk-based canary admission, query-span swaps, nor elephant predicate splitting is established as algorithmically new.** This work has a measurable characterization and a physically feasible small pilot, not enough for a high-impact paper novelty claim.

## Formal claim boundary

For *the measured controlled component only*, let `T_fixed(q)` and `T_swap(q)` be TCP acknowledgement routing times, and `M` sampled transfer time. A batch has measured component-level net benefit iff

`sum_{q in batch} [T_fixed(q)-T_swap(q)] > M`.

No confidence guarantee carries over to production until migration includes atomic placement updates, disk, indices, routing consistency and cache/replication costs and TCP handlers execute real queries. Actual SLA objective should be paired P50/P95/P99 with queueing and equal-byte capacities.

## Next genuine journal gate (not yet passed)

1. Same physical RDF source **and** query workload on a live, verifiable multi-shard SPARQL engine, with end-to-end answer equality, measured actual bytes (including index pages), atomic migrations and no test-period labels in decisions.
2. Equal-byte replication/cache alternative and faithful WISE/WASP/strong static partitions; test serial **and** realistic parallel routing, with real load and queuing.
3. Fresh previously unopened/registered chronological dataset with many more distinct queries and shifts; train/tune only on pre-period.
4. The proposed new method must beat the strongest prior-art implementation by a reliable margin and control **future** novel-pattern risk without sacrificing all total benefit. The three-day risk gate tested here failed this criterion.
5. Only after those criteria pass is a journal novelty + real net economic profitability claim defensible.

**Decision:** retain the original candidate-3 positive workload signal and the new byte-feasible RDF prototype. Reject the simple risk admission as a paper innovation. Further development conditional on a genuine distributed SPARQL integration and strong baselines; do not write a high-impact acceptance claim from the current data.
