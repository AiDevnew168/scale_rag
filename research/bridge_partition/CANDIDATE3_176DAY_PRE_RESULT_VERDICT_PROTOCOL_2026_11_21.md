# Frozen interpretation protocol — 176-day SWDF physical replay

**Status:** documented on 2026-11-21 after physical workflow launch, **before reading any heldout performance results**. This is a post-source/pre-result interpretation addendum; **NOT an original pre-registration before the SWDF log was seen**. Applies to source `research/candidate3-raw-swdf-temporal-drift-20261121` and fixed physical test commit `e5470d4383dcd5fc26c151d913dbb0385a86b27b` or later bugfixes explicitly labeled. Do not tune the action chooser after viewing heldout performance.

## What is and is not learned

- Actual conservative economic controller selects `no_move` because complete future full-runtime drift upper bounds and certified full switching/recovery costs are unknown. Its **incremental realized benefit over no_move is exactly zero by policy definition**, not the measured random difference between twice running the same query on a static cluster.
- `one_swap`, `two_swap_greedy`, `replica_only`, and `swap_replica` are **pre-frozen hypothetical placements scored by paired *benchmark* execution**. They are not realized profit for the deployed conservative controller.
- 4 independent indexed localhost TCP Oxigraph workers, not multiple hosts nor a distributed join planner. Matching original centralized SELECT semantic answers is a hard eligibility gate.
- 2014 original query-log timestamps and source graph ZIP are SHA-pinned, but the full RDF graph's **as-of-2014 snapshot match is unverified**. The FEASIBLE cleaned query publication family was inspected in earlier work, so this is not a totally fresh external domain.
- Eligible subset: **7,142 / 1,416,681** dated queries with text, ~0.504%, not all public SWDF endpoint traffic. Do not generalize a benefit to unsupported query forms or report EUR/USD savings without real pricing.
- The current physical benchmark is not an experimentally randomized live production migration trial: run-order randomization is not sufficient to eliminate time-of-day/cache/contention drift in an online service.

## Primary metric for exploratory *placement* counterfactuals

Per genuinely eligible day `d`, let `N_d` be the full count of eligible original request occurrences and `m_d=min(12,N_d)` uniform SHA-priority sampled occurrences (the source ordinal distinguishes identical repeated query texts). Each sampled occurrence has R=2 paired benchmark timing repeats in randomized order. Let `delta_{d,i,r}=T_static - T_action` denote **full coordinator+TCP+RDF load+original SPARQL SELECT wall time**, not shard contacts.

A stratified full trace **projection**, NOT an actual deployed timing realization, is:

```
Ghat_a = sum_(all 53 UTC heldout days d with N_d>0)
           N_d * mean_(sampled original occurrences i and timing repeats r)(delta_d,i,r)
         - C_a
```

Here `C_a` must include the measured physically executed transfer+index+cutover; separately disclose any unmeasured downtime, monitoring, shadow, networking or rollback, and never call a partial cost complete. An actual sampled benchmark balance `sum(delta)-C_a` is not a real 53-day serving balance. Unequal `N_d` must not be averaged as one request per day without explicitly redefining the estimand.

Within-day source hash-priority sampling does not make repeated timing probes independent production requests. Estimate and expose within-day finite population sampling error if per-occurrence observations are available; day-cluster/bootstrap and contiguous moving-block sensitivity should explicitly discuss temporal dependence and concentrated volume bursts. A nominal 95% interval from naive independent-day resampling is NOT a guaranteed 95% CI under arbitrary temporal autocorrelation or distribution shift.

## Mandatory fail-closed conditions

- Full original SELECT legality against central reference before **and** after physical action for every sampled query; any unsupported/timed-out/incorrect execution makes that action **INVALID**, not a zero delta to omit from the denominator.
- Use legally supported unordered LIMIT subbags and one global bijective Blank Node mapping; preserve RDF datatype, language, lexical identity and multiplicity. Missing/stale source ID: BLOCKED.
- A candidate with no meaningful physical move should be reported as equivalent to static, not an algorithmic victory.
- Quantify *measured query wall time*, source byte movement, indexing, pause, and all counted resource limits separately.
- Stratify **new exact test texts** and **new predicate families** as separate exploratory slices; disclose small effective sample sizes and no post-hoc selective wins.
- Report paired p50 and p95 and bounded-timeout semantics, not only mean net.
- Freeze comparison hypotheses to no_move, one_swap, two_swap_greedy, replica_only, and hybrid under the same 110% per-shard raw byte cap and 25MB move/replica budget. If selecting the winning candidate based on heldout results, that is an **oracle diagnostic**, not a valid policy score; adjust statistical multiplicity for comparisons.

## Journal gates and prior art

Existing methods already address adaptation and relocation:
- **WISE** workload-aware RDF partitioning with monitoring/migration cost model: https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290
- **AdPart** distributed SPARQL with incremental redistribution: https://vldb.org/vldb_journal/index.php/component/article_manager/article/1370
- **WASP** workload-adaptive streaming *property graph* partitioner, evaluated also in RDF-like graph stores; do not silently call it an exact SPARQL/RDF policy competitor: https://link.springer.com/article/10.1007/s41019-021-00156-2
- **2026 dynamic replication with storage/transfer costs** is directly relevant to risk/budget novelty: https://www.sciencedirect.com/science/article/abs/pii/S0304397526002471
- **2025 online balanced partitioning bounds** underline the complexity of online switching claims: https://doi.org/10.1145/3694906.3743327

**Gate 1 — engineering:** corrected full 176-day physical run completes; exact source counts reproduced; original SELECT validity all PASS; complete physically metered costs, reproducibility hashes, no missing queries. Any FAILED subgate => NO-GO for economic inference.

**Gate 2 — exploratory conditional placement benefit:** one pre-frozen *non-oracle* alternate has positive matched net after complete cost and an uncertainty interval strictly >0 with no significant p95 regression. If not, report negative/abstention result; no further tuning against those 53 days.

**Gate 3 — deployable controller:** the actual **decision algorithm** must migrate sometimes on genuine training/calibration-based feasible certification, and must beat static no_move and a competitively calibrated threshold/migration-controller baseline on temporally prospective data. If actual selected `no_move`, realized incremental benefit =0 and Gate 3 = FAIL even when a hypothetical placement was positive.

**Gate 4 — journal superiority:** at least one independent realistic timestamped original-query + version-matched RDF graph benchmark; matched strong published partition/replica/switching-policy competitor, cross-host accounting, statistical uncertainty; original theoretical novelty assessed separately from Hoeffding/TV/stop-loss alone. Until then, a methods-SOTA paper is **NO-GO**.

## Current external evidence at authoring
- Original strict eligibility source audit: https://github.com/AiDevnew168/scale_rag/actions/runs/44907125997
- Previous physical failure due double-escaped SELECT token (no benchmark outcomes): https://github.com/AiDevnew168/scale_rag/actions/runs/44908346611
- Corrected physical CI run launched: https://github.com/AiDevnew168/scale_rag/actions/runs/44910678795
- The 13/13 economic-control and 15/15 stop-loss CI tests certify logic under premises, not future economic savings.
