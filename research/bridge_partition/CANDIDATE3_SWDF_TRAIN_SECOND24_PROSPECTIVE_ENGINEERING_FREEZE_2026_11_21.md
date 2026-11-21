# Locked engineering replication — second, unseen-timing original SWDF TRAIN text cohort

**Frozen on 2026-11-21 after first 24 TRAIN cohort results were observed, but strictly BEFORE any measured latency/answers of the SECOND 24 query texts. This is NOT an untouched external or temporal confirmatory benchmark.**

## Fixed selection

- Original immutable natural 2014 SWDF access log SHA256 `2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df`; original RDF ZIP SHA256 `65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb`.
- Only first **88 natural UTC days** of the 176-day raw trace. All later 18 calibration and 53 prior exposed test dates forbidden for query selection or timings.
- Deduplicate full unmodified original eligible SELECT texts by SHA256. Restrict to exactly the prior frozen physical candidate eligibility: strict source original 2+ fixed predicates present in source graph, plain BGP supported by the conservative constant-filter compiler, original text valid in pyoxigraph empty store, at least one predicate has a constant subject/object, semantic certifier is either full_bag or unordered_slice.
- Sort eligible original texts by `sha256('20261121:'+text_sha256)` ascending. The first trial used ranks **1–24**. The second trial MUST use ranks **25–48**, not random search or queries selected for anticipated speedups. There were 269 eligible unique texts under the first trial's exact compiler.
- Freeze 24 texts, 2 repeated randomized-order paired executions, four indexed Oxigraph TCP worker processes on ONE runner, centralized full unchanged SPARQL SELECT. Source fragments are same original identity-preserving NTriples. Full-predicate raw fetch vs constant-only server-side RDF triple selection. No new optimizer parameters or runtime tuning.

## Hard gates defined BEFORE second timing outcomes

1. All **48/48** original query responses pass conservative central-vs-full and central-vs-selective semantic certifier; no missing/time-out/incorrect query is excluded.
2. Median per-query original NTriples response byte fraction reduction >= **25%**.
3. Paired average end-to-end original SELECT latency saving is > **0 ms**, measured across all 24 text clusters with both repetitions; paired action ordering randomized.
4. Observed selective-response sample p95 <= **1.01 x** full-fetch sample p95; report exact order statistic, not normal-approx p95 confidence guarantee.
5. Report 24 independent query-text-cluster average differences and a 10,000-replicate seeded bootstrap sensitivity (2.5%, 97.5%) as descriptive; a positive lower sensitivity quantile is required for a *stronger* internal replication signal, not an external confidence claim.
6. Explicitly report first/second-repetition effects to diagnose cold parse/index cache, and quantify source-bitmap/index maintenance CPU and resident memory *before* claiming true operational savings.

**Outcomes:** if any semantic or sample-coverage issue, FAIL CLOSED; if bytes improve but latency worsens, STOP contact-only optimism and quantify parse/cache overhead; if all metrics pass, advance to published baseline/independent real dataset. Even perfect secondary TRAIN result does not justify economic migration or novel methods claims.

**First study artifact was observed before this second-stage lock**: [run 44918517226](https://github.com/AiDevnew168/scale_rag/actions/runs/44918517226), first 24 original TRAIN texts: 48/48 PASS, median RDF byte reduction 58.341%, mean paired +61.45091 ms, p95 173.436 full vs 116.458 selective. This secondary design cannot be represented as a 2014 original preregistration or a new natural timestamped validation corpus.