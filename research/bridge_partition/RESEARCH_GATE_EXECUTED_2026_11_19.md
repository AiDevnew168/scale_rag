# Candidate 3: Workload-shift, direct hypergraph and oracle-vs-deployable gap
Date: 2026-11-19
Project: ScaleRAG candidate 3, Bridge-Preserving GraphRAG Placement
Conclusion: **Real operational placement proxy effect exists. Novel optimization algorithm has NOT been established. Future-knowledge gap is large; learning from observed historical traces did not close it.**

## Verified successful CI experiments (not prospective independent paper replications)
- Direct strong Mt-KaHyPar vs workload METIS: https://github.com/AiDevnew168/scale_rag/actions/runs/44522610045
- Six-weight train-only conservative hypergraph portfolio: https://github.com/AiDevnew168/scale_rag/actions/runs/44522639187
- Document-disjoint learned coaccess: https://github.com/AiDevnew168/scale_rag/actions/runs/44523460646
- Online limited migration vs full rebuild: https://github.com/AiDevnew168/scale_rag/actions/runs/44526858078
- Exact one-swap future oracle vs feedback-only choice: https://github.com/AiDevnew168/scale_rag/actions/runs/44527621095

## Strong hypergraph baseline on fixed 600 queries
Four equally capped page shards; all relevant splits held out by query ID but training/test share source docs:
- Contiguous 36.833% single-shard support.
- Structural METIS 37%.
- Workload METIS 42.333%.
- Real Mt-KaHyPar KM1 40.5%; CUT 40.0%.
- Direct KM1 - workload METIS = -1.833pp; 95% document-bootstrap interval [-4.842,1.033]pp.
- Train-only minimax portfolio did not achieve stable uplift over fixed hypergraph method. These are existing algorithms, not a new solution.

## Generalization to documents not used for learning
Train 99 distinct source documents and test 43 different documents (497 test questions), using only their page text features and a learned pairwise coaccess classifier:
- Structural baseline 37.425% local.
- Semantic graph 37.827%.
- Learned coaccess 38.229%.
- Learned - structural = +0.805pp, document-bootstrap CI [-5.556,7.077].
No credible positive transfer claim.

## Online adaptation to query-family changes
One topology family history, the other family split into observed new-query feedback and future query evaluation; identical hard shard page-count capacity. Two-pair balanced swap refinement capped at 10% page migration, compared against frozen structure and unlimited fresh METIS rebuild.

| History→Future | Docs | Future q | Frozen local | Online local | Uncapped rebuild local | Realized online page migrations | Rebuild page migrations |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bridge→Synthesis | 60 | 219 | 36.530% | 35.160% | 42.009% | 3.320% | 26.023% |
| Synthesis→Bridge | 37 | 177 | 46.328% | 44.633% | 48.023% | 4.918% | 30.840% |

Online failed to beat static. Rebuild uses many more moved pages and was not statistically conclusive vs frozen on these samples.

## Diagnostic one-swap future oracle, restricted to original pages 20–39
All variants start at identical frozen partition. One cross-shard two-page swap is feasible within a 10%-page cap. Exact enumeration of *all such swaps* yields the retrospective oracle of best local-complete support on future GOLD queries. This oracle violates deployability by design and must not be compared as an algorithmic improvement.

A new control uses the EXACT same enumeration but selects the swap exclusively from *observed* incoming-family feedback, then tests on future unseen questions.

| History→Future | Docs | Future q | Static local | Earlier online local | Feedback-only one-swap local | Retrospective FUTURE-GOLD oracle local |
|---|---:|---:|---:|---:|---:|---:|
| Bridge→Synthesis | 25 | 93 | 29.032% | 27.957% | 30.108% | 54.839% |
| Synthesis→Bridge | 20 | 114 | 41.228% | 39.474% | 42.105% | 67.544% |

Oracle vs static: +25.806pp and +26.316pp. Feedback-only one-swap vs static: +1.075pp CI [-5.435,7.448], and +0.877pp CI [-7.001,6.897]. The oracle can choose among swaps using the FUTURE itself; this is an extreme *selection-bias* ceiling and not evidence any method could predict that swap. The oracle is optimal only within one-swap neighborhood, NOT all allowable migration plans.

## Precise research judgment

**Validated issue:** Data placement has an important workload-dependent locality effect when historic page-support traces in the same document are available. Fixed workload optimization is sensitive to query family changes. Even a one-swap oracle can find substantial ex-post placements, but a same-budget feedback-only method does not identify them.

**Not validated:** A novel graph/flow solution, deployable large improvement, forecasting predictable from ordinary logs, GraphRAG QA accuracy, distributed latency, real byte memory, or generalization to new documents.

**Avoid common false claims:** One cannot claim that oracle+25pp implies +25pp realistic potential; nor that a Flow algorithm is needed. Use unseen future data exclusively for evaluation in real algorithm claims, and compare strong SWORD, Mt-KaHyPar, Minimum Motif-Cut, robust dynamic database partitioning, and incremental migration cost models.

**Next decisive scientific question:** Does structural information available before future questions (actual entity/relationship graph, update logs, current question text, richer semantics) meaningfully predict which future support-edge joins are demanded? If not, this is a fundamental forecasting limit and candidate 3 should stop. Any novel method must beat static, existing dynamic hypergraph partitioning, and equally constrained migration baselines on untouched documents and with real measured I/O or latency.

Files:
- research/bridge_partition/direct_hypergraph.py
- research/bridge_partition/robust_portfolio.py
- research/bridge_partition/document_transfer.py
- research/bridge_partition/online_adaptation.py
- research/bridge_partition/one_swap_oracle.py
