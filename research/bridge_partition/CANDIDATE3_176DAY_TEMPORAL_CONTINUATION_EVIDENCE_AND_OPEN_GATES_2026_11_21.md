# Candidate 3 continuation — genuine 176-day original organic SWDF trace and risk-limited economic controls

**Date:** 2026-11-21. **Branch:** `research/candidate3-raw-swdf-temporal-drift-20261121`.  
**Scientific status:** new natural-time observational source acquired; no journal-positive-net proof. This report is a factual execution log, NOT a novelty announcement.

## Baseline before continuation

- Previously verified W3C-conservative full original SELECT semantic validity: 19 adversarial tests and 168 paired reviewer agreements over 84 earlier physical SWDF calibration queries ×2 policies. Original SPARQL LIMIT may legally return different subsets and blank nodes must preserve consistent identity; unsupported cases are BLOCKED.
- Full author-published DIAERESIS original DAP → Spark SQL translation → execution completed; same normalized graph counts matched central Oxigraph for two of three unmodified author queries. One query118 mismatch 11112 vs 11114 remained unsolved. This is not enough for a fair same-budget statistics claim.
- Independent new original NYT and DrugBank RDF engineering tests showed after-migration **negative** measured net time. DrugBank pretest chose no move; avoided harm but achieved zero incremental economic savings vs static.
- Source-of-truth report: `CANDIDATE3_USER_REQUEST_SEMANTIC_FRESH_DATA_PUBLISHED_BASELINE_FINAL_GATE_2026_11_21.md` on branch `research/candidate3-sparql-semantic-validator-20261121`.

## New and fully executed: original author raw SWDF dated log

The original DICE/FEASIBLE `SWDF.log.gz` archive **not** the previously opened cleaned query file. A frozen protocol was committed **before download/read**:
`CANDIDATE3_FROZEN_RAW_SWDF_REAL_TEMPORAL_LOG_PROTOCOL_2026_11_21.md`, commit `b70f5a1da34f263e7a31dbbff9923aa0d684cd47`.

Source: `https://drive.google.com/file/d/0B1tUDhWNTjO-T3BweE9YeE1rUGM/view` as linked from `https://github.com/dice-group/feasible`.
- Original untouched gzip SHA256: `2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df`.
- Compressed bytes **95,235,612**; uncompressed bytes **1,061,032,427**.
- HTTP access-log lines **5,499,797**; with parsed timestamps **5,401,530**.
- **176 distinct actual UTC dates**, earliest 2014-05-15 UTC (offset-aware May 16 00:29+01 local) through 2014-11-12 UTC.
- Original SPARQL query requests with date: **1,416,681**, literal query texts SHA256 unique **99,995**. Original lexical SELECT indicator **128,839 occurrences**, NOT an SPARQL algebra-valid query count.
- Median original dated-query requests/day **3,732**, mean ~8,049, maximum **231,296 on 2014-09-23**, and top four days **36.09% of all dated original query requests**. This verifies major VOLUME bursts but does NOT prove predicate-family shift or workload mix.
- No client IP addresses, raw request payloads or literal query strings exported in GitHub reports. All request texts stay within ephemeral runner memory.
- Genuine source-provenance and UTC days gate **PASS**. Original semantic SPARQL eligibility, full 2014 RDF snapshot alignment, exact source query results, and net economics are SEPARATE unproven gates.
- Source audit successful CI: https://github.com/AiDevnew168/scale_rag/actions/runs/44906760524.
- The previous 2014 2007-line LSQ fixture with 3 eligible unique texts was insufficient; this independent original FEASIBLE raw artifact is the correct FULL source. It remains within the same broader SWDF publication family as past cleaned queries and **must not** be called a fully untouched domain.

A fully strict `rdflib==7.5.0` static-predicate SELECT and pinned original RDF predicate compatibility source audit (no query answer/time exposure) was separately queued in workflow:
https://github.com/AiDevnew168/scale_rag/actions/runs/44907125997
Do NOT call this second gate PASS until its report is read and audited. Training 50% / calibration 20% / heldout 30% of the **actual sorted UTC calendar days**, not a shuffle of repeated query strings.

## Two genuinely different economic control components implemented and tested

### 1) Bounded drift conditional admission — formal only under explicit premises

`candidate3_bounded_drift_economic_certificate.py`.
For M training-frozen actions, independent bounded calibration day-block rewards `X_{a,d} in [-B,B]`, valid future complete-runtime distribution L1 shift ≤rho, 95% simultaneous Hoeffding radius, future sample horizon H and independently certified total migration+index upper cost C:

```
LCB_expected_net_a = H * (mean_cal_a
   - B*sqrt(2*log(M/delta)/n)
   - B*rho) - C.
```

Requires positive lower bound, entire original SPARQL correctness, independently verified future drift, certified migration cost upper, true independent calibration days, correctly matched per-day vs per-query weights. If any premise missing, **ABSTAIN**. This is a bound on EXPECTED clipped net under explicit assumptions, NOT a guarantee of positive realized earnings. Full query wall time can change outside predicate witnesses via cache/contention, so witness-locality L1 bounds cannot replace full-runtime drift bounds. Previous one-barrier actual observed cost is NOT a certified upper cost.

**13/13 tests** including nonstationary adversary, unbounded reward and absent correct SPARQL veto:
https://github.com/AiDevnew168/scale_rag/actions/runs/44906919628

### 2) Distribution-free active trial maximum realized loss — only with full reliable metering

`candidate3_pathwise_loss_capped_repartition.py`.
Under hard single query regret ceiling B, known complete rollback upper R, real migration cost C, and committed TOTAL realized risk allowance L, only start if `C <= L - B - R`. For every live request, charge genuine paired end-to-end timing difference and mandatory shadow measurement cost. Switch back to original placement immediately when cumulative net balance reaches `-(L-B-R)`. Then regardless of any adversarial future distribution, final realized net ≥`-L`. This is a simple deterministic stop-loss bound, NOT a positive-profit guarantee. It only applies if the ceiling is physically enforced and shadow/static counterfactual is accurately metered for **all** intervening queries; sampled probes or missing updates invalidate it.

**15/15 tests**, including **75 adversarial synthetic traffic sequences**, all passing:
https://github.com/AiDevnew168/scale_rag/actions/runs/44907748771

This bounded-loss controller must NOT be described as an original theorem or SOTA algorithm; stop loss and online switching-cost control already have literature. Original academic alternatives include dynamic balanced graph repartitioning (SIAM Journal on Computing 2020), online balanced repartitioning ESA 2022, and dynamic regret with switching costs (Sep 2026); precise prior-art evaluation still needed.

## Formal impossibility boundary

Two future worlds can share the exact same observed query history and then immediately diverge to all-helped vs all-harmed query workloads. A nontrivial history-only migration with positive switching cost cannot guarantee positive realized future net under unrestricted adversarial drift. This is a simple no-free-lunch observation, not novel. Genuine risk policy must either assume bounded drift, pay full feedback monitoring, budget controlled downside, or abstain.

## SCIENTIFIC GO/NO-GO as of completed evidence

- Full author raw organic date trace acquired: **PASS**.
- Algebra-checked eligible query volume and predicate compatibility: **PENDING separate reported CI result**.
- Future event graph snapshot aligned with original 2014 source: **NOT VERIFIED**.
- All-original-SPARQL answer semantics on genuinely new time blocks: **NOT YET EVALUATED**.
- Positive net full 4-shard migration after full cost against no move on natural temporal heldout: **NOT YET ESTABLISHED**.
- Matched original published WISE/WASP/DIAERESIS end-to-end SOTA economic gain: **NOT ESTABLISHED**.
- Mathematically valid admission under supplied assumptions and deterministic bounded active loss: **PASS for unit tests only**, real serving runtime assumptions not validated.
- Full top-journal novelty and economic win: **NO-GO on current evidence**.

### Next exact gate

Do not use future labels to tune the method. Complete already started original raw-log STRICT algebra and graph predicate audit. If eligible, freeze policy before any original future query answers, select no-move vs matched byte-cap candidates, measure genuine four-indexed-TCP-worker complete original SPARQL correctness plus migration and day-cluster paired net including rollback/shadow; run the original author baseline on matched hardware/query set where its algorithm supports them. If raw log source becomes ineligible or RDF snapshot mismatch undermines causal claims, report BLOCKED and do not substitute simulated natural dates.

## Completed official original 176-day STRICT algebra and graph-presence gate (after initial report)

**SUCCESS, source-only** CI https://github.com/AiDevnew168/scale_rag/actions/runs/44907125997; frozen protocol commit `b70f5a1da34f263e7a31dbbff9923aa0d684cd47`. Full author raw 2014 SWDF archive and complete FEASIBLE RDF graph SHA verification passed.

| Split on authentic UTC calendar days | Distinct days | Strict eligible original SELECT occurrences | Distinct exact query texts | Distinct predicate families |
|---|---:|---:|---:|---:|
| Training 2014-05-15 through 2014-08-10 | 88 | 4,707 | 973 | 188 |
| Calibration 2014-08-11 through 2014-09-20 | 35 | 994 | 211 | 134 |
| Heldout 2014-09-21 through 2014-11-12 | 53 | 1,441 | 253 | 145 |
| Total occurrence pool | 176 | **7,142** | **1,082 unique overall** | not summed; shared families across periods |

There are **80 test exact query texts absent from all pre-test** and **11 test predicate families absent from all pre-test**, besides 173 previously seen exact test texts. These are authentic original real dated requests, not queries synthesized from graph structure. `rdflib==7.5.0` strict original SELECT algebra includes static URI predicate BGP, 2–6 patterns, 2+ distinct source-graph predicates; all excluded unsupported queries are audited. No original future test *answer or timing* observed in source-eligibility.

**Gate: PASS for pursuing a physically measured exploratory real-timestamp benchmark.** Original as-of-2014 RDF dataset snapshot compatibility remains **NOT VERIFIED**, so full causal paper-level source validity is still blocked.

**Frozen plan before physical original test answer execution:** `CANDIDATE3_LOCKED_DATED_SWDF_PHYSICAL_SAMPLING_ADDENDUM_2026_11_21.md`, commit `d966551684f7d18eca4fab631c6706b97d5d1465`. Training 88 days; first 17 calibration days action-construction; final 18 calibration days admission evaluation; last53 days intact test. Deterministic ≤12 eligible original occurrences per day with source ordinal hashes, matched 4-indexed-worker SPARQL truth and semantic original SELECT contract, measured migration/replica cost, no move and equal-byte controls.

Executable physical source: `candidate3_swdf_176day_physical_economic.py`; CI workflow `.github/workflows/candidate3_swdf_176day_physical_economic.yml`. **At this report write-time the full physical CI is in progress; do not call success or use its results until complete:** https://github.com/AiDevnew168/scale_rag/actions/runs/44908346611

This full physical benchmark still is not a multi-host distributed optimizer, and the original published baseline DIAERESIS does not offer this identical migration action/policy. Neither economic nor paper superiority is established by passing eligibility.
