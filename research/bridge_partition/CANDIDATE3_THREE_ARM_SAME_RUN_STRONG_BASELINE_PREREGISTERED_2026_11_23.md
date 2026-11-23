# Same-run strong-baseline falsification lock — original SWDF TRAIN-only, 2026-11-23

**Registered BEFORE the new 3-arm experiment starts.** Previous cross-run first24, second24 and central indexed answers/timings are already known. Hence this is a **post-discovery, exploratory matched engineering falsification**, never a fresh temporal validation or independent confirmatory journal benchmark.

## Immutable original data, frozen sample and three methods

- Original FEASIBLE SWDF source HTTP query log gzip SHA256 `2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df`.
- Original RDF ZIP SHA256 `65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb` (304,592 triples after graph normalization; as-of-2014 graph snapshot alignment remains unproven).
- Only the first 88 real UTC training dates; 48 DISTINCT original SHA-sorted fixed-compiler eligible SELECT texts, drawn as previous first24 SHA ranks 1–24 and second24 ranks 25–48. Complete query SHA fingerprints: first `108a618ab725e291d05967c1d81e58a1c5e8365804f88f7602bbe7370f26e09c`, second `3e2fd328952e2ddc1c0ea913af49db15bfe4f867a30d1a1db492ffb4e80eaed5`. No later queries or changed cohort.
- Three arms for **exact same source query text**: A direct full indexed centralized Oxigraph `Store.query` with solution-row materialization; B four indexed localhost TCP shard workers transporting full immutable predicate NTriples to a new temporary Oxigraph store per query; C same workers transporting only constant-selected source-original NTriples to a new temporary store per query. B/C never rewrite the original SELECT text; source Blank Node labels preserved.
- EXACTLY 3 repetitions per original text, 144 matched 3-arm blocks = **432 timed full SELECT calls**. Deterministic query-group shuffle from seed `20261123`, each query gets 3 cyclically rotated A/B/C orders after an independently shuffled initial order. All three methods appear once per ordinal position in every 3-repetition query group; no adaptive time-based query selection. Report first-vs-subsequent repetitions, plus order positions.

## Correctness gate: absolute

Every original SELECT must execute and the conservative independent centralized-vs-full and centralized-vs-selective semantic certifier must report PASS; no timeout, exceptions, mismatched variables, dropped pair, silently repaired prefix or missing repetition. Run always writes the errors and returns **FAIL CLOSED** on any disagreement; a green workflow step alone is never evidence of correctness. Original unordered LIMIT semantics, duplicate bags, bnode global bijection and ambiguous ties must be handled conservatively.

## Fairness and honest interpretation

- Within-run same runner, same materialized original RDF graph, pinned pyoxigraph 0.5.13 and rdflib 7.5.0, same 48 queries and randomized block position. This removes the main historical cross-run confound.
- Store-first engine versus source-line-serving four-worker coordinator **have different capabilities/resource assumptions**. Direct central index persists, whereas shard coordinator builds a new indexed temp store per query. Exactly that architectural cost is the practical falsification: do not describe B/C as comparable distributed RDF join engines like AdPart, S2RDF, CostFed, DIAERESIS.
- Measure `mean`, `median`, *sample* p95, sample maximum, total bytes transferred, per-query cluster summaries and per-predicate-set family; report cold request outliers, workers' Linux RSS and CPU ticks pre/post where measurable. The main CPU/memory for temporary query stores is not a complete production TCO benchmark; cache build, eviction and source changes need prospective measurement.
- The previous study's first24 7 predicate families (14+5+five singletons) invalidate treating each text as an independent workload family. Bootstrap by query and by family (when >=4 families) is descriptive, not prospective 95% CI. Also perform equal-text and raw original 2014 occurrence count-weighted TRAIN-only sensitivity if available without looking at later text.

## Gate decision

1. If A (strong indexed central) has substantially lower mean and p95 than B/C, classify *this original 304k-triple / single-host / source-fragment-shipping architecture* as **NO-GO for competitive systems speed and method novelty**; B→C improvement cannot serve as evidence of a novel faster distributed RDF algorithm.
2. This does NOT prove that all truly distributed RDF engines are inferior, nor disprove a benefit at a predeclared larger graph capacity (>single-host RAM) with real cross-host optimized joins. Such claims require a **new independent original data set** and actual published baseline implementations, matched capacity and full lifecycle costs.
3. Even if B/C improve vs A, this internal 48-text study would establish engineering potential only. With source parser/future 2014 heldout already exposed, 2026 independent benchmark query inventory mismatch and no original published baseline, no journal GO is permitted.

**No positive result has been inspected for the 3-arm same-run experiment at lock time.**