# Artifact-verified first real SWDF TRAIN-only constant-pushdown physical result (2026-11-21)

**Evidence artifact:** [GitHub Actions run 44918517226](https://github.com/AiDevnew168/scale_rag/actions/runs/44918517226), commit `1fcbed5174c7925b7af17ccec88aabf03eaea7bf`, [artifact 14713341448](https://github.com/AiDevnew168/scale_rag/actions/runs/44918517226/artifacts/14713341448), artifact ZIP SHA256 `59ce0eab84a6e702d86d533dd4376ac20c44eb63783348bd297532c8ad4e9b7f`. Source query-log SHA256 `2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df`; RDF archive SHA256 `65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb`. Directly inspected `report.json` and `selection_frozen_before_training_answers.json`. No raw SPARQL texts or user IPs copied here.

**Status:** engineering feasibility passes the *previously fixed* first-stage benchmark thresholds. **NOT** an original journal innovation, prospective heldout validation, real multi-host economic migration, or full RDF federation result.

## Original data and immutable selection

- Source: the original natural 2014 SWDF access log, **first 88 calendar dates only**, not the known-exposed 53-day heldout.
- Original strict training source 4,707 eligible occurrences; separate structural eligibility was 615 distinct source-query texts and 2,929 occurrences with constant term and shared join variable. Source shape CI 44915287023.
- Physical runner found 269 unique training texts compatible with its narrower plain BGP, constant-fetch compiler, exact target query execution and slice rules; selected 24 unique source texts by SHA256(seed:text hash) before reading their source graph answers and timing. This is conditional on compatibility; do NOT generalize to the remaining source requests or SPARQL language.
- Each of 24 selected texts ran two paired randomized-order baseline/filtered executions on four indexed Oxigraph worker processes, **all on one host**, original graph 304,592 triples.

## Direct measurements, 48 paired executions

| Metric | Full predicate fragment transfer | Constant-filtered predicate transfer |
|---|---:|---:|
| Correct certified original full SELECT answers | 48/48 | 48/48 |
| Mean end-to-end wall time (ms) | 155.0821 | 93.6312 |
| Median end-to-end wall time (ms) | 162.9948 | 89.0957 |
| Empirical p95 wall time (ms) | 173.4361 | 116.4580 |
| Total RDF response payload (decimal MB) | 565.956588 | 236.504624 |

- Median per-query RDF byte fraction reduced **58.341%** (reported 0.58341). Aggregate payload-body byte reduction **58.212%**. Positive RDF byte saving occurred in all 48 measurements; the request selects source-original N-Triples lines retaining blank-node identity.
- Mean paired end-to-end saving **+61.45091 ms per original training query**, median paired saving +70.5533 ms; **47/48 individual pairs** were positive. Per-unique-text mean was positive for **23/24** distinct texts.
- First chosen query repetition 0 incurred a **-222.8261 ms** timing loss (103.9175 ms full vs 326.7436 ms selective), even though it reduced RDF bytes 6,915,894 to 1,439,588. The first trial may include lazy worker cache/index initialization; this causal explanation is **hypothetical, not yet physically separated**.
- Repetition 0: across 24 distinct texts mean +55.64285 ms, 23/24 positive; repetition 1: mean +67.25896 ms, 24/24 positive. Worker startup/index memory and cold/warm amortization costs have not been separately metered.
- Exploratory query-cluster bootstrap over the 24 distinct text-means (10,000 resamples, seed 20261121) gave **[46.32,72.26] ms** 2.5–97.5% quantiles. This is a *sample-conditional sensitivity interval*, NOT a prospective temporal 95% confidence interval, and not independent of source/query-family clusters.
- Operational: source predicate bytes, full coordinator graph construction and per-query store building are charged inside the paired wall path; the materialization/worker parsed cache warm-up and resident memory are not comprehensively accounted as an online amortized objective. No cross-host network jitter or multi-tenant load.

## Pre-frozen two-condition local engineering gate

1. **Semantic 48/48 PASS**: yes; no excluded original selected query.
2. **Median per-query RDF-byte reduction >=25%**: PASS, 58.341%.
3. **Mean paired latency saving >0 ms**: PASS, +61.45091 ms.
4. **Sample p95 action no worse than baseline by >1%**: PASS, 116.458 vs 173.436 ms.

**Decision:** **GO to a harder ENGINEERING experiment**, NOT journal methods GO. Preserve the exact report hash; do not choose different 24 queries to inflate results.

## Important limitations and scientific next experiment

- Fixed 24 unique original **training** texts are not the naturally weighted 4,707-query traffic mixture. A uniform query-text sample is not equal to frequency-weighted workload economics.
- The current algorithm is simple triple-pattern constant selection, a classical pushdown technique; related prior art such as CostFed and AdPart already optimize federation and distributed joins. This is an implementation feasibility baseline, **not a new algorithmic theorem**.
- New head-to-head must meter **cold start and worker cache residency** under bounded memory, CPU, parse/index creation time, p95, and full source/response bytes; add *always-full*, *always-constant-pushdown*, and a declared cost-aware adaptive policy as separate controls.
- Validation must use **untimed/unused training-compatible query texts** chosen before result inspection, or a genuinely independent dataset. The first 53 known 2014 SWDF test days are no longer untouched; using them as a claimed external validation is forbidden.
- An independently verified published benchmark is needed. Query-only LargeRDFBench 2026 CI 44919826851 **failed** expected inventory count: source ZIP contained **32** original `.sparql` files while the publication describes a **40**-query full suite; the pinned 32 parsed in both engines, only 9 matched narrow constant BGP. Do NOT silently reduce the expected suite to 32 or claim external conformance; reconcile the missing 8 at source first.
- A positive journal claim still requires an independently version-aligned RDF dataset, real original published baselines and genuine economic online selection under changing workload; none of that is established here.