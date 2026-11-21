# SWDF original 176-day replay: forensic timing sensitivity and publication verdict

**Historical reported observation, NOT an executable selected policy win.** This report uses the original artifact from [run 44911492637](https://github.com/AiDevnew168/scale_rag/actions/runs/44911492637), [artifact 14711280912](https://github.com/AiDevnew168/scale_rag/actions/runs/44911492637/artifacts/14711280912), exact ZIP SHA256 `33fcb2e169ffaccfa1e6b88b0e0e14bc399aca9e6230f97fb220f054da72486b`, commit `f175be388c89cf7167013404de78f1265360dd40`. This is a POST-HOC qualitative diagnostic and is forbidden as a confirmatory economic net estimate.

## Fatal gate — every original cohort method invalid

All 5 physical placements and static control have 1,256 / 1,258 semantically certified paired runs, exactly 1 distinct original SHA-bearing query with undeclared prefix reoccurring in 2 repeats at 2014-09-26. A separate strictly pinned original-access-log diagnostic ([run 44914773712](https://github.com/AiDevnew168/scale_rag/actions/runs/44914773712)) found the same text 7 times in the original raw trace. RDFlib 7.5.0 source algebra accepted it by one undeclared default namespace mapping, whereas pyoxigraph 0.5.13 rejects the original query with `Prefix not found`; adding a single explicit namespace declaration **only in a separate diagnostic** makes empty Oxigraph parse succeed. The original query text was never repaired in the measured trial.

Even if we condition on the 1,256 successfully certified pairs and ignore the two failed ones for **diagnosis only**, the timing signal remains weak. Every method is invalid for pre-registered full original original-query inference.

## Descriptive timings on already-cherry-incomplete 628 distinct sampled occurrences

| Frozen arm | Conditional raw mean paired saved ms | Equal-day mean ms | Circular 7-day moving-block 2.5–97.5% descriptive quantiles of equal-day mean ms | Paired observed p95 base -> alt ms |
|---|---:|---:|---:|---:|
| no_move | -0.1338 | -0.1461 | [-0.5968,+0.2036] | 120.15 -> 118.09 |
| one_swap | +0.2324 | +0.2119 | [-0.3157,+0.7722] | 116.86 -> 116.75 |
| two_swap_greedy | -0.2245 | -0.2230 | [-0.7125,+0.2070] | 126.97 -> 127.11 |
| replica_only | +0.3146 | +0.3116 | [-0.0595,+0.6641] | 128.31 -> 127.93 |
| swap_replica | -0.1000 | -0.0960 | [-0.7760,+0.5329] | 123.62 -> 123.59 |

These intervals are **sensitivity quantiles, NOT calibrated frequentist confidence intervals**. The bootstrap computed 2,500 circular 7-day moving-block resamples over 53 ordered day averages, seed 20261121; each day average uses each of its successful paired repetition differences. Quantiles use sorted draws at positions 62 and 2437 (0-indexed; descriptive). They do not account for day-dependent finite-sample population inference, four-arm multiplicity, actual production contention, post-hoc missing pair or costs. Equal-day means do NOT reproduce eligible-query-volume-weighted entire trace net. This entire analysis is inadmissible as a journal profit claim.

**Crucial conditional observation:** each alternate's descriptive sensitivity interval includes zero. Even forgiving the failed SPARQL and missing cost limitations, the existing 53-day sample does not establish a robust positive latency signal.

## Invariant mechanism: no original RDF-body byte savings from placement-only actions

Under the actual source-routing protocol, for every queried predicate p there are disjoint immutable source byte fragments F(p,i); swaps only move them and replication creates copies of existing fragments. Correct routing fetches exactly one copy of every original fragment, so for original SELECT query q:

    RDF_response_bytes(q,placement) = sum_{p in distinct_predicates(q)} sum_{i in original_fragments(p)} size(F(p,i)).

This is independent of worker assignment. Shard contact counts may decrease but raw response RDF payload bytes cannot. This is a deterministic property of the implemented full-predicate-fetch coordinator, **not a universal SPARQL or server-side join-processing theorem**. A different query execution architecture allowing selective pushdown, join filtering, or cached fragments can break the premise. Synthetic actual-router proof checks passed under [CI 44913514206](https://github.com/AiDevnew168/scale_rag/actions/runs/44913514206). The physically measured saved RDF response bytes for all four alternative methods were 0.

## Research decision

1. The original historical 53-day benchmark is **blocked**; reusing its known failing sample after prefix repair as 'unseen' would be data leakage.
2. Primary resource objective 'save network RDF payload with predicate-only swaps/replicas + full-fragment fetch' is **structurally impossible**. Do not invest in another contact-count-only placement optimizer.
3. The observed small apparent timing deltas are not robust after serial-correlation sensitivity and have no positive deployed-controller profit. Current selected actual policy remains `no_move` => incremental static benefit **0**.
4. Novel publishable work would require changing the query execution model AND proving actual novel advantage beyond existing AdPart/WISE and RDF join-pushdown literature, with an untouched temporally prospective workload. Query-dependent remote filtering is established prior art; it cannot be described as new just for being implemented.
5. A negative-result empirical systems paper is still possible only after at least an independent dataset, matched original published baselines, external validity of an RDF graph snapshot and complete costing; top-journal methods-SOTA remains **NO-GO**.

**No positive economic claim is made in this file.**