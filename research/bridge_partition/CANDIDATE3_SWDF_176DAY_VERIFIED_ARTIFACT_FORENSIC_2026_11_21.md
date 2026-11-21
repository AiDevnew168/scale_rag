# Artifact-verified 176-day SWDF physical-run forensic verdict — 2026-11-21

**Evidence:** successful-completion workflow https://github.com/AiDevnew168/scale_rag/actions/runs/44908321838, SHA 411c7429919793f28d4c0cb6e10554a1798dca2e, artifact 14709959437. Zip SHA256 in job log 9dd79329e23c21c21ab05639b38525620b47f312a9b143eb4af8f195ea0074c5. Frozen decision pretest hash b99d27a0f01886e60fb3f386b6416389907449a80848561e874727065d95042c. The ZIP report.json and frozen decision JSON were read directly. Green CI denotes process completion, NOT passed scientific gates.

## Frozen sample and engine gate
- Original chronological split: 88 train days / 17 action construction / 18 admission calibration / 53 heldout.
- Source eligible occurrence counts: 4707 / 393 / 601 / 1441 respectively. Day-hash sampled occurrences: 1027 / 192 / 212 / 629.
- 629 heldout source occurrences with 2 repetitions => 1258 requested pair evaluations. All FIVE candidate layouts had 1256 valid PASS pairs, 2 exceptions from ONE identical original query text (SHA e8f4f6b9b2e90f89d4e5e80f68af8322751019f19324e7cee4c1cf2c08e95474) on 2014-09-26 UTC. Both repetitions: physical Oxigraph SyntaxError: Prefix not found (query line 4:46). All five candidates passed 424/424 calibration pairs.
- This is one distinct parser-vs-target-engine compatibility miss repeated twice, not two independent failing query families. The error occurs even in baseline no_move, and invalidates all economic comparisons under the frozen all-original-SELECT requirement.

## Direct artifact measurements — descriptive conditional timings, NOT valid net gain

| Action | Physical moved source bytes | Physical edit/index elapsed ms | Shard contacts saved over 1256 passing pairs | RDF TCP payload bytes saved | Mean saved ms per successful pair |
|---|---:|---:|---:|---:|---:|
| no_move | 0 | 0 | 0 | 0 | -0.29313 |
| one_swap | 16832 | 10.0401 | 332 | 0 | +0.29207 |
| two_swap_greedy | 5426967 | 199.4556 | 334 | 0 | -0.14688 |
| replica_only | 34569 | 5.3125 | 1124 | 0 | +0.38045 |
| swap_replica | 51401 | 12.0319 | 828 | 0 | -0.14616 |

None of these means can be converted into a valid full-period projected economic result because failed queries were omitted from the measured-pair denominator. No transport-RDF payload bytes were saved despite lower shard contacts, a key coordinator fragment-materialization bottleneck. The observation is only for this localhost coordinator, not a universal result about RDF joins or latency.

## Correct inference and next steps
1. Keep first failed semantic original trial intact. Do NOT delete the query, edit its prefix, or tune action policy to already-observed heldout answers.
2. Independently diagnose whether RDFlib source-only parser accepted a PREFIX use missing from the original query and whether Oxigraph rejects it on both centralized and distributed engines. Do not expose raw query strings or IPs in public artifacts.
3. Reconcile parser-admission versus target engine compatibility before a separately preregistered new validation cohort. Repeated reruns on these 53 revealed days are engineering regressions, not independent confirmatory evidence.
4. Monitor newer runs 44910678795 and 44911492637 (ongoing at this report-writing) for their actual completed artifacts; no success or positive economics should be preclaimed.
5. Any controller-level profit claim still requires actual chosen migration rather than actual selected no_move (zero incremental gain by definition), complete costs and independent prospective version-aligned natural data.

**Scientific verdict:** ENGINE SEMANTIC GATE FAIL; ECONOMIC ESTIMAND BLOCKED; JOURNAL POSITIVE SOTA NO-GO. Reproducible engineering lessons and negative diagnostics are useful but not method superiority.