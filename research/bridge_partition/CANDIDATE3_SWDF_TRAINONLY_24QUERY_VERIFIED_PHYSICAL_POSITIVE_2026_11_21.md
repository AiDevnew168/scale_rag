# Candidate 3 — first genuine positive TRAIN-only physical selective-fetch evidence, 2026-11-21

## Source and immutable experiment evidence

- GitHub Actions completed SUCCESS: https://github.com/AiDevnew168/scale_rag/actions/runs/44918517226
- Artifact ID: 14713341448, https://github.com/AiDevnew168/scale_rag/actions/runs/44918517226/artifacts/14713341448
- Executed source SHA: `1fcbed5174c7925b7af17ccec88aabf03eaea7bf`; original raw dated-log SHA: `2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df`; graph archive SHA: `65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb`.
- The complete artifact `report.json` and `selection_frozen_before_training_answers.json` were checked to be EXACTLY identical on the frozen selection object; no 53-day historical heldout source request was reused.
- Original train-only source cohort: 4,707 eligible occurrences, 973 unique eligible texts, 2,929 constant-anchored occurrences and 615 anchored unique texts. More conservative physical query compiler + target parser found 269 training-only original anchored texts eligible; selected 24 by a frozen SHA(seed:text_SHA256) ranking, independently of RDF answers and latency.

## Actual measured paired physical result (4 localhost indexed Oxigraph TCP workers, original NTriples)

| Frozen measure | Real observed value |
|---|---:|
| Selected original distinct training SELECT texts | 24 |
| Randomized-order repeated full/constant-filtered paired comparisons | 48 / 48 complete and SPARQL PASS |
| Original source RDF triples | 304,592 |
| Total baseline original RDF TCP response bodies, 48 runs | 565,956,588 bytes |
| Total filtered original RDF TCP response bodies, 48 runs | 236,504,624 bytes |
| Aggregate body-byte reduction | 58.2115% |
| Median per-query byte reduction | **58.3407%** |
| Baseline total request wall ms | 7,443.9403 |
| Filtered total request wall ms | 4,494.2968 |
| Mean saved wall ms per original selected query-repeat pair | **+61.4509** |
| Median saved wall ms per pair | +70.5533 |
| Baseline query wall p95 | 173.4361 ms |
| Filtered query wall p95 | 116.4580 ms |
| Queries with negative mean paired time | **1 of 24** |
| Pairs with negative observed benefit | **1 of 48** |
| Exceptionally slow first filtered cold query | 326.7436 ms versus 103.9175 ms baseline; same query second filtered repeat 42.6688 ms |

**Frozen local development gate passes**: 48/48 SPARQL correctness; median RDF bytes reduction >=25%; paired wall-clock gain positive; p95 filtered at most 1.01x baseline (here strictly lower). This is a positive **conditional TRAIN-only 24-query physical feasibility result**, not a deployable temporal migration outcome.

## Query-cluster rather than repetition-level uncertainty

Independent Python recalculation of the exact uploaded 48 deidentified rows grouped repetitions by 24 query text SHA labels. 5,000 seeded query-cluster bootstrap resamples (seed 20261121), with descriptive order-statistic 2.5%-97.5% quantiles:

- Mean paired latency saving: **+45.7093 to +72.3270 ms**.
- Median fraction of raw RDF response bytes reduced: **0.582325 to 0.583409**.
- These are DESCRIPTIVE sensitivity quantiles, **not a 95% coverage guarantee** under natural temporal autocorrelation, query selection, caching, or unseen workloads. The source selection is deliberately restricted to anchored eligible training texts and is not representative of the whole original service.
- The newly tested independent query-cluster audit has 7/7 tests passing: https://github.com/AiDevnew168/scale_rag/actions/runs/44919572182.

## Why the result is promising but NOT a publishable original solution

1. It changes the physical query execution model by filtering source-original NTriples triple patterns before TCP transport (a known basic optimization). Previous predicate-location swaps/replicas cannot reduce raw response bytes under the full-fragment fetch invariant.
2. The method is standard constant-bound BGP predicate pushdown, NOT invented semijoin / distributed join / a novel drift-adaptive controller. Comparison only to naive full-fragment fetching is weak; AdPart, FedX/CostFed, WISE, pushdown and semijoin-aware alternatives must be evaluated fairly.
3. Original 2014 FEASIBLE SWDF source graphite RDF snapshot as-of-2014 is not certified. Four worker processes share one physical runner, not four networked independent hosts. Query sample is 24 selected supported texts from train only, not prospective future time.
4. Filtered worker lazily builds cached parsed NTriples fragment lists; cold first request outlier shows it can impose large setup latency. The **full cost of indexing, memory, warmup, eviction, source updates, source-format conversion, and rollback is not accounted for**. Runtime means cannot be converted to deployment profit.
5. No online policy selected a migrate or filter-or-full action from genuinely prospective past data. No original AdPart/WISE/FedX executable or true network inter-host CPU/economic comparison. No source/version-matched independent repeat of this gain.

## Next defensible gate (frozen before *new* external measurements)

- Measure cold/warm source cache and parsed-filter index creation time and peak resident memory; test under source updates and eviction. Account for each one-time cost against observed per-query body/time gains in a full amortization horizon; require a positive conservative post-index adjusted net. Preserve the observed cold 326.7ms outlier, do not remove it from primary.
- Compare to strong `always_full`, `always_constant_filter`, and a pre-trained, cross-fitted feature-based runtime choice with full monitoring overhead, plus native published engine baselines if equivalence possible. The basic filter must remain a strong baseline, never labeled the new contribution.
- Independently validate SPARQL semantics, bnode global identity, bags and unordered LIMIT on version-pinned 2026 interoperable LargeRDFBench public source where feasible; this benchmark has no natural chronology and cannot replace a drift benchmark.
- Only after these pass, seek an actual previously untested natural chronological workload with version-matched graph; no reuse of the already-opened 53-day 2014 holdout for a confirmatory advantage.

**Scientific verdict:** positive low-level distributed-data-fetch feasibility; full economic admission and novelty still NO-GO/UNPROVEN. Continue to cost-complete engine baseline, not further naive predicate swap optimization.