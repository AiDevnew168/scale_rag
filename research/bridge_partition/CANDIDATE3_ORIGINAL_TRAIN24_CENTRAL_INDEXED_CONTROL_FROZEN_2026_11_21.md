# Frozen strong centralized Oxigraph baseline: original first24 SWDF training SELECTs

**Registered on 2026-11-21 BEFORE any direct centralized query timing was measured for this new benchmark.** Earlier first24 full/constant-pushdown timings ARE KNOWN, so the present control is post-result and not a blind journal test. It is a necessary falsification test for single-host architectural overhead.

## Source and selection

- Original immutable SWDF source graph ZIP SHA256 `65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb`, original 2014 HTTP log SHA256 `2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df`.
- Only first 88 natural UTC training dates; same frozen 24 distinct original SELECT texts selected by SHA256(seed20261121:text SHA). Verify ordered 24 query text hash fingerprint SHA256 of pipe-separated 24 SHA strings is `108a618ab725e291d05967c1d81e58a1c5e8365804f88f7602bbe7370f26e09c`.
- Load the whole original RDF graph into one fully indexed Oxigraph store, pyoxigraph==0.5.13. Run the unchanged original SELECT through the actual central Oxigraph engine, fully materialize returned solution rows, twice each. No distributed worker, local TCP fetch or per-query temporary graph construction. Freeze all 48 original query executions, no excluding query/unsupported error. Record p50, p95, mean, total, cardinality and full source graph memory footprint before and after.

## Fair interpretation

1. Centralized indexed execution on one machine is a **strong practical no-federation baseline** for the 304,592-triple original SWDF graph. It is NOT a resource-budget-matched stand-in for multi-host AdPart, WISE, CostFed or billion-triple federation.
2. Published first24 full-fragment coordinator mean 155.0821ms, constant-filtered coordinator mean 93.6312ms on a different Github Actions run. Their comparison to *new* central-only means is an **unpaired architecture diagnostic**; do not report the difference as a causal paired benchmark or prospective CI.
3. If central indexed is substantially faster, the previous 61.45ms gain merely repairs a bad original four-worker coordinator baseline; never call it distributed-system superiority.
4. No new algorithmic novelty is proven by this experiment, even if central is slower; independent multi-host, version-aligned external dataset and strong original published baselines still required.

**Stop criterion:** no new partition optimization should be called a journal-grade distributed contribution if the central indexed baseline dominates and the target graph fits one host, absent an explicit distributed scalability advantage at larger graph sizes.