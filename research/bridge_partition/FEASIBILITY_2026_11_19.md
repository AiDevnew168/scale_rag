# Candidate 3 feasibility: Bridge-Preserving GraphRAG Partitioning
Date: 2026-11-19
Status: **Positive operating-cost proxy, no original algorithm demonstrated. Focused GO for novelty check; no paper claim.**

## Research question and motivation
This is NOT another MCF-vs-Cross-Encoder evidence Top-k test. It measures a *physical placement proxy* for multi-source RAG: how many document shards must be activated to contain all ground-truth evidence units when a document is split into 4 parts. Query-stage routing is idealized and the gold evidence is never used to design a test-time placement. The statistic is an oracle *cost proxy*, not retrieved recall, answer accuracy or measured latency.

## Prior art that constrains novelty
- Yang et al., SPLIT-RAG, EMNLP 2026: question-driven graph partitioning and selected partition-agents; https://aclanthology.org/2026.emnlp-main.2110/
- Cheng et al., LogosKG, ACL 2026: degree-aware partitioning, cross-graph routing, on-demand caching; https://aclanthology.org/2026.acl-long.1966/
- Minimum Motif-Cut, VLDB Journal 2024: workload-aware RDF partitioning to co-locate motif queries and reduce joins; https://doi.org/10.1007/s00778-024-00860-1
- SWORD, VLDB Journal (older): workload-hypergraph partitioning, query span, data replication and incremental repartition; https://www.vldb.org/vldb_journal/index.php/component/article_manager/article/1311
- Mt-KaHyPar-MC, ESA 2026: strong multi-constraint hypergraph partitioning; https://drops.dagstuhl.de/storage/00lipics/lipics-vol388-esa2026/html/LIPIcs.ESA.2026.12/LIPIcs.ESA.2026.12.html

Thus naive workload-aware METIS and greedy replication shown below are **not innovations**.

## Real-data setup, leakage control and replicability
Official TopoGraphRAG-Bench annotations and manifest, using public source URLs in script. Same seed 261119, document-level workloads.
- 2,024 original questions, 201 original source documents
- In-scope: bridge-chain + multi-source synthesis with >=2 *distinct source pages*.
- Fixed page-placement problem: 4 equally page-weighted shards per source document, shard capacity <= ceil(number_pages/4), including METIS post-balance repair.
- Historic-workload proxy: 891 **training** questions; 600 disjoint **test** questions, 142 shared source documents. Support-page labels in training questions are treated as oracle historical query traces. Test question supports DO NOT enter placement, replication, graph construction or hyperparameter selection.
- Partitions compared: contiguous pages; randomly balanced pages; page-adjacency graph METIS; page-adjacency plus training-query coaccess weighted graph METIS; base METIS plus train-only selected replicas. Query coaccess uses clique expansion of all training evidence-page sets. Weights were set heuristically (adjacent=100; each coaccess hyperedge total~400) and were NOT tuned on a separate study.
- Replica budgets: <= max(1, floor(5% pages)) per doc; actual realized 221 extra page copies of 7,632 originals, **2.896% total**; maximum per document may be >5% because of minimum one-copy allowance.
- The tested decoder always computes the *minimum number of activated shards needed to cover all gold evidence pages* (for evaluation ONLY); actual RAG router and load latency were not measured.
- Baselines and proposed ideas are on page nodes, NOT an extracted entity-relation KG, and page count is not actual RAM or I/O bytes.

Code in `research/bridge_partition/pilot.py`; GitHub workflow in `.github/workflows/bridge_partition.yml`.
Primary successful fully balanced rerun: https://github.com/AiDevnew168/scale_rag/actions/runs/44515079238
Two-way query-family transfer: https://github.com/AiDevnew168/scale_rag/actions/runs/44515368909
Each workflow attaches deterministic per-question and train/test split manifests in downloadable run artifacts.

## Main real observed results (600 unseen questions, all shard capacities valid)

| Method | Test queries fully on ONE shard | Mean oracle activated shards |
|---|---:|---:|
| Random balanced | 16.167% | 2.0033 |
| Contiguous page partition | 36.833% | 1.6817 |
| Standard adjacency-only METIS | 37.000% | 1.6833 |
| Historic-query-coaccess METIS | **42.333%** | **1.6283** |
| Adjacency METIS + train-only greedy replication | **44.833%** | **1.5850** |
| Adjacency METIS + train-only frequency replication, equal 221 copies | 44.000% | 1.5983 |

Paired, document-cluster bootstraps (2,000 exploratory replicates):
- Historic-workload METIS vs topology-only METIS: +**5.333 percentage points** single-shard questions, CI95 [+0.492,+10.397], 98 wins, 66 losses.
- Historic-workload METIS vs contiguous pages: +5.5 pp, CI95 [+0.647,+10.527].
- Base METIS + historical greedy replication vs Base METIS: +7.833 pp, CI95 [+5.700,+10.035].
- Greedy replica choice vs frequency replica choice with the SAME number of copies: only +0.833 pp, CI95 [-0.957,+2.735]. **No convincing algorithmic superiority from the greedy replication scorer**.
- Exactly 0 documents exceeded the enforced capacity ceil(npages/4) in either METIS method.
- No real latency speedups can be claimed from activated shard count alone.

## Distribution shift controls — a negative but useful structural clue

Train on bridge-chain only; test on unseen synthesis questions (560 queries, 111 documents): adjacency-only METIS local 34.643%, query-workload METIS local **33.393%**, diff **-1.25pp** with CI [-7.132,+4.487]. Replication on structural METIS 38.750% vs 38.571% for equal-copy frequency control, no meaningful greedy edge.
Train on synthesis only; test on unseen bridge-chain questions (635, 116 docs): structure METIS local 38.110%, workload METIS local **40.472%**, diff **+2.362pp** with CI [-1.952,+6.584]. Structural METIS + replication local 45.039%.
All shift trials preserve the same source documents (not held-out documents); query types are disjoint by train/test, and gold test pages are used ONLY for scoring. Confidence intervals include zero for query-aware METIS in both cross-family shifts.

## Factual conclusions and limitations
1. There is an empirical cross-shard evidence co-location challenge in a **real, non-synthetic evidence-annotation workload** under four page shards.
2. Training-question coaccess yields a positive *in-distribution* query-span proxy gain at exactly fixed page-count shard capacity. This is a genuine, reproducible effect but **not new theory** and not a demonstrated improvement in RAG QA or wall-clock latency.
3. When the query family changes, the coaccess advantage does not convincingly transfer. Thus a specific, observed generalization challenge exists.
4. Low-cost replication improves localization, but almost the same benefit comes from a far simpler frequency heuristic. This mirrors earlier complexity-vs-greedy concerns.
5. Multiple baselines are untested: strong **direct hypergraph Mt-KaHyPar**, Minimum Motif-Cut, SWORD, SPLIT-RAG and LogosKG. No claims of superiority over them.
6. Synthetic gold historical traces are optimistic compared to real noisy user-query logs. Evaluation queries share documents with the training workload. Page-number balancing is not memory/byte balancing. Four shards and ideal route simulation are not real distributed measurements.
7. This sample has been inspected repeatedly; bootstraps are exploratory, not confirmatory on untouched holdout.

## Concrete nontrivial research direction (hypothesis, not result)
**Workload-Shift-Resilient, Bridge-Safe, Budgeted GraphRAG Placement**:
jointly select balanced partitions and selective replicas to minimize expected and upper-tail activated-shard or real remote-join costs across an uncertainty set of shifting query-pattern distributions, while guaranteeing per-shard memory and update constraints.
Mathematical *candidate* objective: min_{P,R} max_{Q in U(historical traces)} E_Q[span(q,P,R)-1] + alpha*CVaR_{0.9,Q}(span) + beta*replica_bytes, subject to hard per-shard RAM budgets. This objective alone is NOT known to be novel; formal prior-art work is required (SWORD, MMC, LogosKG, 2022 tail-latency replication, SPLIT-RAG, MTGA 2026).

**Next yes/no gate:** replace page-path toy graph with an extracted authentic multi-document entity/relation graph; use noisy retrieval traces (not gold supports); implement direct Mt-KaHyPar/SWORD/MMC comparisons under equal real byte-memory, replica and route budgets; test family-shift and held-out documents; measure actual p95 routing latency and complete support coverage, not just oracle minimum shard-span. Only then contemplate a new graph algorithm or journal claim.

## Decision
**GO for a bounded, systems-aware robustness feasibility study; NOT a GO for writing a novelty paper and NOT a claim that our algorithms beat state-of-the-art.** The positive physical-placement proxy and measured workload-shift fragility provide a better-defined starting point than repeating top-k reranking; leave this report frozen and avoid relabeling exploratory results as confirmatory.
