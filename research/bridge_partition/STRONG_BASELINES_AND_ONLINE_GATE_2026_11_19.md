# Candidate 3 — Strong hypergraph and online-shift gates

**Date:** 2026-11-19
**Scope:** real TopoGraphRAG support-page trace proxy; NOT a full GraphRAG KG, actual latency, or publishable novelty claim.

## Key authoritative workflow runs

- Direct Mt-KaHyPar KM1/CUT vs METIS (three scenarios): https://github.com/AiDevnew168/scale_rag/actions/runs/44522610045
- Train-only robust six-weight hypergraph portfolio: https://github.com/AiDevnew168/scale_rag/actions/runs/44522639187
- Document-disjoint supervised coaccess prediction: https://github.com/AiDevnew168/scale_rag/actions/runs/44523460646
- Online observed shift, fixed migration versus full rebuild: https://github.com/AiDevnew168/scale_rag/actions/runs/44526858078

## Gate 1: direct strong hypergraph baselines

All conditions: four equal page-capacity blocks, no test-query gold used in construction.

| Fixed 600 query benchmark | Local (%) | Average activated partitions |
|---|---:|---:|
| Contiguous | 36.833 | 1.6817 |
| Structural METIS | 37.000 | 1.6833 |
| Workload clique-expanded METIS | **42.333** | **1.6283** |
| Direct Mt-KaHyPar KM1 | 40.500 | 1.6433 |
| Direct Mt-KaHyPar CUT | 40.000 | 1.6483 |

KM1 versus workload METIS: -1.833pp, document-bootstrap CI95 [-4.842, +1.033] pp. The direct hypergraph baseline did NOT dominate.

Cross-family shift: bridge→synthesis local 31.786% Mt-KaHyPar KM1 vs 33.393% workload METIS; synthesis→bridge 42.362% KM1 vs 40.472% METIS. Both paired differences have 95% CIs overlapping zero.

Robust six-weight train-only portfolio did not outperform fixed hypergraph weighting reliably; under synthesis→bridge it underperformed fixed hypergraph by -3.780pp, CI95 [-7.333, -0.151].

## Gate 2: document-disjoint prediction

99 source documents train; 43 entirely different source documents test; 497 questions.
- Structural page graph: 37.425% local.
- Semantically connected graph: 37.827%.
- Logistic learned coaccess graph: 38.229%.
- Learned vs structural: +0.805pp, CI95 [-5.556, +7.077] pp.

This does not support a claim of robust transfer to new documents.

## Gate 3: online shift with migration constraints

Code: `research/bridge_partition/online_adaptation.py`; CI `.github/workflows/bridge_online.yml`; fixed seed 310119. Phase 1 historical questions belong to one topology family. Phase 2 questions from the other family are split deterministically within each document into observed feedback and *future unseen* evaluation. No future labels are used for any placement.

Three methods:
1. Frozen phase-1 workload METIS.
2. Local balanced two-page swaps with fixed 10% maximum migration budget and a train-observation blended span objective; unchanged hard block capacities.
3. Full METIS repartition after phase-2 feedback (uncapped migration; a higher-cost comparator, not a matched budget contender).

| Future family | Docs | Future questions | Static local | Online local | Full rebuild local |
|---|---:|---:|---:|---:|---:|
| Synthesis | 60 | 219 | 36.530% | 35.160% | 42.009% |
| Bridge | 37 | 177 | 46.328% | 44.633% | 48.023% |

Document-bootstrap comparisons:
- Bridge→synthesis, online vs static -1.370pp, CI95 [-6.580,+3.620].
- Bridge→synthesis, full rebuild vs static +5.479pp, CI95 [-0.939,+11.067].
- Bridge→synthesis, online vs full rebuild -6.849pp, CI95 [-11.660,-2.218].
- Synthesis→bridge, online vs static -1.695pp, CI95 [-7.548,+5.238].
- Synthesis→bridge, full rebuild vs static +1.695pp, CI95 [-6.370,+9.678].

Migration page counts:
- Bridge→synthesis: online 142/4277 = 3.320% vs full rebuild 1113/4277 = 26.023%.
- Synthesis→bridge: online 96/1952 = 4.918% vs full rebuild 602/1952 = 30.840%.
- Costs are PAGE COUNTS, not bytes, network or milliseconds.

### Interpretation

The **measured positive signal** is workload-aware placement with known query-support traces in the same documents. Hypergraph partitioning, train-only minimax portfolio, and learned cross-document coaccess DID NOT demonstrate consistent superiority. Simple local-swap online adaptation also failed to improve held-out future-query localization.

This is not evidence that arbitrary budgeted online repartitioning is impossible. It DOES indicate that the current methods are insufficient and that a mere repackaging of robust hypergraph objectives is not a credible standalone novelty claim.

Related prior work must be treated as strong baselines: SWORD (query-span and replication), Mt-KaHyPar, Minimum Motif-Cut, SPLIT-RAG, LogosKG, MTGA 2026, and Replication in Graph Partitioning and Scheduling Problems (April 2026).

## Decision

**GO for problem characterization; NO-GO for paper/solver claims.** For a final strictly bounded next gate, test whether there is a feasible >3pp *budget-constrained* quality improvement over frozen partition on new unseen query families, using an ILP or provably bounded neighborhood optimum on a small held-out subset and equal migration cost. If not, stop candidate 3 rather than build a distributed service or repeatedly tune heuristics. A valid publication must additionally use actual graph edges, real byte capacities, strong query-span baselines, noisy log observations, and measured distributed routing cost; current tests cannot claim those outcomes.

All intervals are exploratory as the same benchmark has been inspected multiple times. These are not statistically independent confirmation experiments.
