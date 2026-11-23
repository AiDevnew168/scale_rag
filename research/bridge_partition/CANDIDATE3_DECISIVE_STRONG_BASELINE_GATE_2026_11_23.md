# Candidate 3 — decisive strong-baseline scientific gate (23 November 2026)

**Decision scope:** Can a conservative adaptive physical partition / predicate-constant-pushdown mechanism justify a high-impact journal *method* paper on the original SWDF 2014 corpus? **NOT a promise of novelty**. This report is based on completed physical Github Actions and strict preservation of previously exposed holdout failures. The paired 48-text three-arm run is tracked separately; do not substitute its results until artifact validated.

## Existing executed facts (not projections)

| Evidence | Original source result | Logical implication |
|---|---|---|
| Frozen 176-day original access log | 88 training, 17 construction, 18 calibration, 53 historical test calendar days; strict eligible 4707 training occurrences / 1441 test | Original timestamps, but source RDF snapshot 2014 alignment unverified |
| Four-worker original heldout | 1256 / 1258 successful original query paired responses in each arm; two failures repeat an undeclared PREFIX query even in no_move | End-to-end economic profit **INVALID**, NOT '99.8% sufficient' |
| Original 88 training days structure | 2929 of 4707 eligible training occurrences have fixed BGP join anchor; 615 distinct texts | Query selection potentially helpful; not an algorithm |
| Frozen first24 training source query texts x2 | 48/48 SPARQL PASS; median RDF body reduction 58.341%; mean full->selective saved +61.45091ms; empirical p95 173.4361 -> 116.458ms | Feasibility against *bad full-fragment-fetch baseline*, not published SOTA |
| SHA ranks 25–48 original training text second cohort x2 | 48/48 SPARQL PASS; median RDF body reduction 58.341%; mean full->selective saved +53.0175ms | Within-source timing replication, NOT external 2014 original heldout; rank/sample strata conditional on syntax |
| First24 exact predicate families | 7 distinct exact predicate-set families; top two contain 14+5 = 19 of 24 texts | Treat text-based bootstrap as dependent; tiny independent family count |
| First24 constant-parse source fragments profile | 3 parsed fragments / 8,015,056 source bytes / 49,953 triples; 769.076ms one-time parse, 30,411,718 B traced live extra Python heap | Warm query comparisons cannot silently omit cache/RSS costs |
| Deterministic single-worker source fragment | 6,710,184 original bytes -> 162 selected bytes; first filtered RPC 258.374ms, warm filtered median 13.580ms, full RPC median 4.009ms; VmRSS +26,528 KiB | Byte reduction is not sufficient for worker-side latency or RAM benefit |
| Direct strong central indexed baseline, same first24 original texts x2 | 48/48 original SELECT executed. Mean 2.390744ms, empirical p95 17.302014ms. Source index build 638.296ms. | **Strong single-host disconfirmation** of four-worker approach for this 304,592-triple source graph, though comparison against prior runs is unpaired |

## Cross-artifact independent raw-row reconciliation

An independent offline extraction of the *two original action artifact JSONs*, rather than copying GitHub's short console summaries, recomputed the first cohort full 48 paired mean 155.08208958ms vs selective 93.63118333ms, second cohort 117.95104375ms vs selective 64.93353958ms, 47/48 positive per cohort, and **zero overlapping query-text SHA hashes** between cohorts. The second group had one negative outlier; no data deletion was made.

The central-indexed original first24 artifact has the **same exact set of 24 SHA query texts** as the first full/selective artifact. For each query text, comparing the separately executed two-repetition means, indexed central is faster in **24/24**, with the *smallest* central advantage >50.5ms. This is an unpaired, runner-session-different architecture diagnostic; no within-request randomized causal claim or independent population sign-test p-value is justified. First24 has only 7 predicate-set families, with 19/24 text examples concentrated in the first two families.

## The true fair control

The earlier 61.45ms is against four workers that ship complete predicate fragments into a fresh per-query coordinator store; it cannot be compared to a strong persistent SPARQL index as evidence of a better distributed engine. A direct centralized store does not pay cross-process TCP, fragment extraction, per-request graph rebuild, or separate worker cache. The 304,592-triple graph fits on one runner. Complexity of four workers is a LIABILITY without a demonstrated scalability or isolation requirement.

**Same-run physical experiment**: [run 45106146288](https://github.com/AiDevnew168/scale_rag/actions/runs/45106146288), exactly two SHA-locked cohorts 24+24 unique first88-day training texts, three method arms (`central_indexed`, `full_fragment_ship`, `constant_pushdown`) interleaved 3 balanced repeats, 144 complete triplets / 432 timed calls. Per-triplet original full SELECT central-vs-distributed certification, 4 worker VmRSS and CPU ticks, per-predicate family resampling. Engine invariants [run 45106304422](https://github.com/AiDevnew168/scale_rag/actions/runs/45106304422) succeeded on synthetic adversarial cases. **Do not give a final quantitative same-run verdict until completion and independent real artifact audit**.

## Conditions for a meaningful journal GO (NOT met)

1. Entirely independently dated query cohort with target engine syntax compatibility determined before test; exact original full SELECT SPARQL semantics, no silently omitted query or cache warm-only selection.
2. Version-matched and independent graph+queries corpus and full multi-host execution, not 4 loopback processes on one machine.
3. Strong matched published contemporaneous baselines (AdPart, WISE, CostFed/modern federation systems) plus strong indexed-central/no-move. Compare equivalent datasets, resource budgets, supported query semantics, cache policy, CPU/RSS, migration and rollback.
4. A defensibly **new** method beyond already-published local triple-pattern filters, semijoins, join-aware routing, adaptive pattern repartition, migration-cost controllers. Original algorithm specification, nontrivial mathematical property and independently measurable practical advantage.
5. A deployable past-only decision that chooses actual beneficial change and yields a *positive lower* uncertainty-adjusted net profit (not oracle-after-test or no_move=0 by definition).

## Current decision and scope

**FROZEN ORIGINAL 176-day economic migration novelty: NO-GO.** The alternative local source-filter baseline is an engineering improvement to a weak coordinator but **not established SOTA**. The central indexed result is a strong preliminary falsifier; final same-run three-arm check must be performed strictly before hard-closing the small single-host scenario. A negative result is NOT evidence all distributed RDF optimization is impossible at billion triples. No further investment in a new graph migration algorithm on *this toy single-host coordinator* until all conditions change.

Research-neighbor literature: AdPart adaptive distributed hash partition and local joins (VLDB Journal), WISE workload-aware migration and cost minimization, CostFed index-assisted source selection; all precede this implementation. A novel contribution cannot simply rebrand those mechanisms.