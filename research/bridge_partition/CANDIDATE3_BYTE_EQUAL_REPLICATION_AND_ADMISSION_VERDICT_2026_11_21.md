# Candidate 3 research verdict — PTCR vs. byte-equal replication, BEND economic action admission
**Date:** 2026-11-21  
**Branch:** `research/candidate3-compensated-swap-20261121`  
**Status:** strong retrospective locality candidate, **NO credible claim yet of outperforming WISE/WASP/AdPart or of net production profitability**.

## What is genuinely new in this research sequence

The previous exhaustive Jan/Feb/Mar 2018 single-swap risk frontier proved **empirical impossibility**, within that specific 5,400 one-swap action class, of keeping >=90% first-day burst gain while meeting two aggregate future June-novel nonregression metrics. Exhaustive anchored two-move ORACLE then constructed a feasible compensating action in **all three** months. These ORACLE moves may use future labels **ONLY to show existence**, not for online policy selection.

Our deployable *candidate* `PTCR-90` uses:
- June 2017 training to build four equal 30-predicate-ID shards;
- the preceding complete 28-day organic query traffic for estimating June-novel tail risk;
- **first day only** of the current month to maximize original frozen first-swap locality;
- exact second-swap enumeration with previous-period novel occurrence touch nonregression, previous-period novel distinct single-shard nonregression, and ≥90% current-first-day head gain; objective maximum previous novel request-touch savings;
- future days only for scoring; no future in decisions.

Code `candidate3_past_month_tail_compensation.py`, CI https://github.com/AiDevnew168/scale_rag/actions/runs/44870899418, with day-cluster uncertainty https://github.com/AiDevnew168/scale_rag/actions/runs/44871088691.

| Month | Frozen 1swap future touches saved | 2swap day0 greedy | PTCR-90 | PTCR novel request touch saving vs no-move | PTCR novel distinct single-local gain |
|---|---:|---:|---:|---:|---:|
| Jan | 8,688 | 8,531 | **8,783** | +926 | +14 |
| Feb | 8,898 | 8,935 | **9,250** | -444 | +12 |
| Mar | 10,315 | 7,964 | **12,694** | +299 | 0 |
| Total | 27,901 | 25,430 | **30,727** | +781 | +26 |

PTCR vs frozen +2,826 touches (+10.13%), but moves 4 predicate IDs instead of 2 and lacks actual Wikidata predicate byte sizes. Jan 95% paired daily CI for PTCR incremental gain **crosses zero**, Feb also **crosses zero**; only Mar is robust (+64.3777 extra touches saved / 10,000 future requests, day-cluster 95% CI [+30.6966,+103.7459]). All Jan-Mar historical periods were inspected during earlier algorithm design: these results are **retrospective exploratory**, not independent confirmation.

## External WatDiv10M: actual RDF sizes, strict pseudo-time patterns, 25MB same maximum action budget

Pinned original University of Waterloo WatDiv10M source:
- Graph NTriples archive SHA256 `1d0a8a4725c98974eb7347ce3e6d9cab44f9f40389589809674254151b745af6`: 10,916,457 actual triple lines, 1,542,624,409 serialized N-Triples bytes, 86 predicate types.
- Stress workload archive SHA256 `98796d4c8db67a1f68b3d1958d8f1334d5d38fe6da1c5e8eae72a8823ac7eed5`: 12,100 eligible questions in 121 distinct predicate combinations.
- Deterministic 5fold **disjoint predicate-pattern families**. Per fold, 2 folds historic, 1 'previous month', 1 current 'day0', 1 test, all mutually disjoint by family. Crucial: **these are ARTIFICIAL pseudo-time folds, not genuine chronological logs or five independent corpora**. The original official test.* files duplicate the warmup questions, so they are NOT used as independent tests.
- Four RDF raw-byte shard caps <=110% of average; two elephant predicates physically require fragmentation. Moving any predicate copies/repartitions exactly its measured raw N-Triples bytes. **These are analytically computed payload sizes, not executed physical migration or SPARQL**.
- Same maximum *per-fold* 25,000,000 raw bytes for all candidates, including the FIRST swap and any second move or replica.
- Earlier workflow failed because first swap violated budget; fixed first-swap admissibility and executed clean in https://github.com/AiDevnew168/scale_rag/actions/runs/44871251681.

| Controller | Pooled extra touches saved on disjoint 5fold | Sum migrated raw RDF bytes across five *separate hypothetical runs* | Positive / Negative / Zero heldout folds |
|---|---:|---:|---|
| one-swap max day0 | 500 | 32,371,836 | 3 / 1 / 1 |
| **two-swap day0 greedy** | **800** | **44,524,249** | 4 / 0 / 1 |
| PTCR-90 preceding tail | 600 | 66,275,176 | 4 / 1 / 0 |
| day0 two-swap per byte | 600 | 35,236,047 | 3 / 0 / 2 |

**External generalization finding NEGATIVE:** PTCR-90 does not dominate simple two-swap greedy in this stricter equal-byte-limit synthetic source, and it moves more data. Do NOT call PTCR a proven SOTA improvement.

## Stronger matched-capacity selectable-replica comparator

Full successful code/results: https://github.com/AiDevnew168/scale_rag/actions/runs/44871515750; source `candidate3_byte_matched_replication.py`. Real predicate payload raw bytes bound both the 25MB transfer/storage budget and each target shard’s byte ceiling. To evaluate routing with a replicated whole predicate, use **exact K=4 minimum shard set cover**. For fragmented elephant predicates the coordinator must still touch *all* shards holding fragments. Replication only adds data and cannot worsen the theoretical minimal shard contact span; this is a known property, not a new discovery.

| Strategy | Heldout pooled touches saved | Total raw move/replica bytes across 5 pseudo-folds |
|---|---:|---:|
| 2swap day0 greedy | 800 | 44,524,249 |
| PTCR-90 | 600 | 66,275,176 |
| **single selective replica chosen from prev+day0** | **700** | **41,129,589** |
| **one swap + one replica chosen from prev+day0** | **900** | **60,453,619** |
| cheap per-byte replica only | 200 | **825,218** |
| one swap+per-byte replica | 600 | 33,045,705 |

New **swapped+replicated hybrid** exceeds the best day0-only two-swap by 100 saved touches in this test, but costs 15,929,370 MORE raw bytes across 5 folds; no unqualified economic win. Cheap replica avoids 99% of this volume for lower saved locality; its performance is nonnegative in every fold, though unknown real network/index costs remain.

## Training-only action admission with robust controls

Source `candidate3_budgeted_action_admission.py`, executes from frozen immutable replica benchmark artifact `14693877818` (run 44871515750 SHA256 `5f67565e8e654aff0b521501c16062244de042f34c45d562463e3e194e4436fe`), no future labels in selection. GitHub CI: https://github.com/AiDevnew168/scale_rag/actions/runs/44871699646.

Actions no-migration/one-swap/two-swap/replicate-only/swap+replicate share 25MB maximum *per fold*. Select by predicted benefit from observed previous/day0, fixed horizon = observed test query count, and migration line-rate assumption, exploring `mean`, `minimum`, head-only, prior-only, risk-constrained minimum; use *heldout* only to evaluate. These economic scenarios are **defined after source benchmark was already seen** and are **explicitly sensitivity analysis, NOT preregistered future performance**.

| Hypothetical extra-shard critical-path saved time | Ideal bandwidth | Best fixed actual observed policy | Training-only mean-selected net benefit | Hindsight upper bound |
|---|---|---|---:|---:|
| 1 ms / touch | 100 Mbps | cheap replica, +133.98 ms | **+219.82 ms** | +286.83 ms |
| 1 ms / touch | 1 Gbps | 2swap day0 greedy, +443.81 ms | +422.84 ms | +893.85 ms |
| 5 ms / touch | 100 Mbps | cheap replica, +933.98 ms | **-116.74 ms** | +3438.54 ms |
| 5 ms / touch | 1 Gbps | hybrid swap+replica, +4016.37 ms | **+4421.19 ms** | +5293.85 ms |
| 20 ms / touch | 1 Gbps | hybrid swap+replica, +17516.37 ms | **+19421.19 ms** | +21793.85 ms |

**Conclusion: the action library broadens the Pareto frontier and a simple evidence-conditioned selector beats the strongest fixed comparator in some assumed-cost regimes, but fails in others.** In particular a training-selected rule LOSES versus no move in the 5ms/100Mbps profile while inexpensive replication is profitable in the same stylized model. A trustworthy profit/risk *admission mechanism* with an independently calibrated lower confidence bound is the **unsolved technical and scientific bottleneck**.

All ms numbers above are MODEL HYPOTHESES from per-touch serial critical-path and ideal wire bandwidth, NOT measured production SPARQL runtime, not currency and not a P95 service-level evaluation. No analytic model should be presented as a proven deployment saving.

## Formal, conservative potential novelty path (HYPOTHESIS ONLY)

**Working concept: Witness-Calibrated Budgeted Action Admission (WCBAA).** A single decision can choose no-op, balanced moves, selective replicas, and a hybrid. Use a *counterfactual, action-specific locality witness* consisting of predicate combinations whose route can change, and quantify separate previous-tail and day0-head benefits. The admission threshold must compare a confidence-adjusted **lower bound of future critical-path time saved** to full measured move/replica bytes, write-index cache overhead and downtime; if it cannot certify positive net, abstain.

**Rigorous supporting lemma, NOT novelty alone:** Let four-shard partition P be changed by migrating a predicate set S. For any query q disjoint from S, its sharded predicate-local span is unchanged. Let `g(q)=span_P(q)-span_P'(q)`, then `|g(q)|<=3`, and `g(q)=0` outside witness set `A={q : q intersects S}`. For past/query distributions p,q on the same pattern universe,

`E_q[g] >= E_p[g] - 3 * Σ_{x in A}|q(x)-p(x)|`.

This is a direct triangle-inequality sensitivity bound; a genuine **operational guarantee requires a valid, precommitted bound on future witness-distribution drift**, not merely assuming it. An uncertainty ball so wide that all futures are allowed yields vacuous/no-migration certificates. This lemma is textbook-level and by itself cannot establish scientific originality; an efficient, non-vacuous method that learns a valid uncertainty radius from independent earlier time-series and beats published prior-art could be new.

**Immediate fail-fast criteria for journal work:**
1. A new truly unread heldout workload with time stamps and matching RDF source graph, no repeated pattern leakage, physical data migration and query correctness;
2. Matched 4-shard storage and bytes across no-op, 1swap, 2swap, cheap replica, hybrid, WISE/WASP/AdPart-appropriate stronger baselines;
3. Measured serial and parallel SPARQL latency, network bytes, P95/P99, query output equality and migration/recovery overhead in a real service;
4. At least one *pre-registered* controller with lower-bound net improvement over the strongest available baseline and honest novel-pattern risk tradeoff;
5. Reproducible independent confirmation, with multiple workload shifts and dependence-aware uncertainty. Otherwise **NO-GO** for a top-journal algorithm novelty claim.

## External source discovery and blocker
Verified LSQ 2.0 provides query logs from 27 SPARQL endpoints including DBpedia and SWDF (https://lsq.aksw.org/, literature `LSQ 2.0: A linked dataset of SPARQL query logs`, Semantic Web 15, 2024). Bounded read-only preflight GitHub CI https://github.com/AiDevnew168/scale_rag/actions/runs/44871806041 attempted 200-query samples from DBpedia and timestamped SWDF but **both returned connection refused from runner**, despite CI itself completing; no data accessed, no test labels inspected, source availability BLOCKED. Published RDF dumps are a promising alternative subject to ensuring corresponding KG snapshots, timestamps, and legal access; no substitute was silently invented.

## Prior art that must NOT be misrepresented
- WISE: workload-aware RDF triple movement, query-span, cost balance (2020), https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290
- WASP: workload-adaptive streaming RDF graph partitioner (2021), https://link.springer.com/article/10.1007/s41019-021-00156-2
- AdPart: hash locality + adaptive RDF partition/replication https://vldb.org/vldb_journal/index.php/component/article_manager/article/1370
- `Analyzing workload trends for boosting triple stores performance` (2024) already combines **indexing, cache and selective replication under shared storage**, https://www.sciencedirect.com/science/article/pii/S0306437924000784
- MTGA (Sep 2026) explicitly models long-tail queries via feedback, multi-task GNN and incremental partitioning https://www.sciencedirect.com/science/article/pii/S0957417426016192
- gRouting (2016) even shows alternative decoupled storage/query routing can outperform heavy repartition, https://arxiv.org/abs/1611.03959
- DICE source-available baseline PCM, https://github.com/dice-group/workload-aware-rdf-partitioning

**Bottom line:** PTCR is the best time-retrospective two-step candidate so far on real Wikidata logs, but not the best external byte-weighted generalization. Selective replication is a serious strong baseline; the action-library hybrid appears stronger on touch locality but more expensive. The next method must be a *well-calibrated, abstaining, budgeted and risk-certified admission mechanism*, not more fixed heuristic moves. No SOTA or economic-proof claim is currently scientifically defensible.
