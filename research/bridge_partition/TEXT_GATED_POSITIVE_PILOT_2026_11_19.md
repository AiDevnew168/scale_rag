# Text-only incoming-workload gating: positive but exploratory gate

**Date:** 2026-11-19
**Research line:** Bridge-Preserving GraphRAG Placement, candidate 3
**Status:** Real page-placement proxy gain; NOT an independently confirmed new algorithm or demonstrated distributed RAG benefit.

## Reproduction links
- Ungated frozen query-text prefetch: https://github.com/AiDevnew168/scale_rag/actions/runs/44529076939
- Query-topology gated prefetch: https://github.com/AiDevnew168/scale_rag/actions/runs/44529482813
- Reproducible code: `research/bridge_partition/query_text_prefetch.py`
- GitHub Actions CI: `.github/workflows/bridge_text_prefetch.yml`
- Both runs publish per-question rows and summary report artifacts.

## What is actually being measured
A source document is physically represented as 4 equal page-capacity shards. For a batch of currently submitted questions from one source document, a query-text-only lexical retriever scores the original source page descriptions (no gold support used). One cross-shard pair of original pages may be swapped, preserving all hard capacities. In the query topology gating run, a TF-IDF+logistic classifier trained on question TEXT ONLY from other source documents predicts whether the incoming batch consists of bridge-chain questions. If yes, make the top-3 lexical page-set swap; if no, preserve the existing placement. Ground-truth future supports are scorer-only. The policy uses the TEXT of incoming queries, so this is request-batch prefetch, NOT prediction of questions which haven't been asked.

The gate policy itself was decided after examining the preceding results by query family. The same held-out items were then evaluated again, making this **exploratory**, not a new independent trial.

## Original real-data sample
In the 20–39 page document slice, after chronological-style synthetic split by question type:
- 25 documents, 93 test synthesis questions after bridge history.
- 20 documents, 114 test bridge questions after synthesis history.
- No test gold evidence provided to the page scoring, topology classification, swap selection.
- Topology classifier fit on documents completely disjoint from all eligible test documents (in two runs, 176 or 181 other docs), covering 1,305 or 1,351 training questions.
- The classifier chose the expected scenario at 23/25 and 20/20 document batches respectively. In the two mistaken first-direction batches, it did not modify the measured future locality.

## Real observations (full gold evidence pages all on ONE shard)

| Method | Bridge→Synthesis n=93 | Synthesis→Bridge n=114 |
|---|---:|---:|
| Frozen partition | 29.032% (27/93) | 41.228% (47/114) |
| Feedback-only best one swap | 30.108% | 42.105% |
| Incoming-text top-2 page swap | 26.882% | 48.246% |
| Incoming-text top-3 page swap | 25.806% | 50.877% |
| **Query-topology gated top-3 swap** | **29.032% (27/93)** | **50.877% (58/114)** |
| Future-gold oracle best one swap (DIAGNOSTIC ONLY) | 54.839% | 67.544% |

Together, the two groups give frozen 74/207=35.749%; query-gated 85/207=41.063%; difference +5.314 percentage points, or 11 complete-local query sets. The combined CI was not separately estimated. On the 114 bridge future queries, query-gated vs static delta +9.649pp and doc-cluster bootstrap CI95 [+1.998,+18.559]pp, 16 wins and 5 losses. In the synthesis future queries, exact prediction-gated difference is 0.0pp.

## Why this is not an established scientific breakthrough
- The incoming question TEXT is observed; it's an online routing/prefetch scenario rather than future unknown-workload prediction. A real distributed RAG service might not be willing to migrate a document's page partitions between batches due to high cost.
- Only 45 documents in a selected size band; no new external benchmark or prospective confirmation; topology-specific policy explicitly informed by prior exploratory analysis.
- Query labels are externally supervised during classifier training; deployment requires generalizing beyond these document-question families.
- Query support is ground-truth *page IDs* only for evaluation; the actual no-gold retriever is a low-cost TF-IDF page proxy using layout extracted/description text.
- No real memory-byte costs, document/graph hierarchy, incoming serving deadlines, node replication, actual routing, remote join latency, image-pixel retrieval, or end-to-end answer accuracy.
- The policy is a simple switch between existing baseline strategies, not a new optimization algorithm and not by itself patent/paper novelty. Prior art dynamic workload-aware graph/data partitioning and adaptive routing includes WASP, SWORD, MTGA 2026, SPLIT-RAG, and LogosKG.

## Decision
**GO for an independent, prospective replication of the query-topology-aware online placement policy with measured migration overhead and strong adaptive routing/replication baselines. NOT GO for a journal-paper novelty claim yet.**

A stricter next experiment should freeze this exact policy before selecting entirely new documents and a second benchmark, compare with no-migration adaptive routing and simple replication, and measure end-to-end wall-clock latency/byte movement, not only oracle minimum active shards. If the positivity vanishes under equal real overhead or stronger baselines, stop this formulation. Do not revert to repeating MCF-vs-Cross-Encoder top-k evidence selection.

## Final actual migration-cost audit (same workflow, fixed method)

Audited run: https://github.com/AiDevnew168/scale_rag/actions/runs/44529914877

The exact same gated policy moved two pages in one of the 25 bridge-to-synthesis documents (2 pages moved, zero aggregate shard activations saved) and moved two pages in each of the 20 synthesis-to-bridge documents (40 pages moved, 11 shard activations saved over 114 queries). Across the 207 evaluated queries, total page moves = **42**, net saved activated shards = **11**, or **3.818 page moves per saved shard activation** in this limited batch. A bare activation-count benefit does NOT demonstrate wall-clock cost savings: net usefulness depends on the byte-size of pages, migration traffic, routing setup costs, batch recurrence, concurrent queries and whether copying can replace moving. A real break-even test must compare the measured cost of 42 page moves with 11 saved shard activations and consider static request routing without moving data. Reported move ratio has no assumed bytes/latency units.
