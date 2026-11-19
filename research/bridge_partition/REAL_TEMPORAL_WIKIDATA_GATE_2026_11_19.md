# Candidate 3 — Genuine timestamped real KG-query workload gate

**Date:** 2026-11-19
**Research status:** Positive, reproducible *query-span proxy* signal under genuine chronological holdouts; NOT yet a novel algorithm and NOT measured end-to-end GraphRAG latency or answer accuracy.

## Critical source change (methodological fix)

Prior TopoGraphRAG-Bench questions have no organic timestamp sequence. Random train/test assignment cannot substantiate future-workload forecasting. We therefore moved to real organic Wikidata SPARQL request logs (2017, anonymized and timestamped, published by TU Dresden/Wikimedia, CC-0).

Source files:
- June 12–July 9 2017, 192,330 organic queries: `https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/2017-06-12_2017-07-09/2017-06-12_2017-07-09_organic.tsv.gz`
  SHA-256 `1cf943c70530264d599d66a1fe15ea8eb670c548112e65bfa0702fc2db1cc5cf`
- July 10–Aug 6 2017, 200,726 organic queries: `https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/2017-07-10_2017-08-06/2017-07-10_2017-08-06_organic.tsv.gz`
  SHA-256 `1a14b938cb532289270b0ca4fb9fbabc240f73573a07a1268f0527580b07c3e9`
- Dataset documentation: https://iccl.inf.tu-dresden.de/web/Wikidata_SPARQL_Logs/en
- Natural-language alignment (potential separate study, NOT used here): https://github.com/ad-freiburg/wikidata-query-logs ; WDQL 2026.

Only training query text/SPARQL property IDs used for building placement, never future data. Frozen top 120 direct property IDs chosen from June12–June25 train by observed property frequency. Four blocks, 30 equal-ID capacity each, no replica, no dynamic migrations. Each qualifying query uses 2–12 of these IDs. This models predicate-level query coaccess, **not actual triple storage or byte-sized hardware placement**.

**Comparison methods:** (a) train popularity order and contiguous 30-ID blocks, (b) weighted coaccess graph / clique METIS, and (c) native direct Mt-KaHyPar hypergraph partition KM1, with each unique *train* predicate coaccess set an original weighted hyperedge. All are mature baseline techniques, NOT our proposed novelty.

## Main time-ordered same-file test

Train June 12–June 25, dev June 26–July 2, untouched scoring July 3–July 9. Of 48,311 original final-week queries, 26,485 meet the 2–12 selected-property restriction.

| Method | Fully one-shard queries | Mean shards needed |
|---|---:|---:|
| Train popularity contiguous | 67.529% | 1.40053 |
| Historical coaccess graph METIS | 71.218% | 1.31999 |
| Direct hypergraph KM1 | 73.215% | 1.28956 |
| Direct hypergraph CUT | 72.505% | 1.35439 |

METIS vs popularity: +3.689 percentage points, seven-day block bootstrap CI95 [2.577,4.835].
KM1 vs METIS: +1.997pp, day-block CI95 [-0.282,4.634]. KM1 promising but not significant with only seven day blocks.

Predictive coaccess value on 7,140 possible unordered pairs of 120 training-selected properties, forecasting test pair presence:
- Past **actual pair coaccess count**: AP 0.78214, ROC-AUC 0.91923.
- Product of past independent property counts: AP 0.48221, ROC-AUC 0.79742.

This is a real positive historical-relationship predictive signal above popularity alone.

## Independent *later file / future month* evaluation

**All partition layouts frozen using only the same June12–June25 training.** No retraining or tuning against this newer file. Test July10–Aug6: 200,726 organic queries, 100,198 in-scope.

| Method | Local % | Mean activated shards |
|---|---:|---:|
| Train popularity | 66.020% | 1.43040 |
| Historical coaccess METIS | 69.208% | 1.34207 |
| Native Mt-KaHyPar KM1 | **73.278%** | **1.28258** |

Paired day-block bootstrap:
- KM1 vs METIS: **+4.070pp**, CI95 **[+2.322,+6.071]pp**.
- KM1 vs popularity: **+7.258pp**, CI95 **[+5.716,+9.157]pp**.
- METIS vs popularity: +3.188pp, CI95 [+2.258,+4.150]pp.

The source file and period are temporally later than the first audit, providing stronger separation than question-random shuffling. The current test is still exploratory overall because algorithm choices and the first week were inspected beforehand.

## Most important reviewer control: completely unseen combinations

Of 100,198 eligible future-month queries:
- 88,110 requests have a property-ID set already seen in initial train.
- 12,088 requests use a property-ID set NOT seen during the initial 14-day training.
- 2,470 unique property-ID-set combinations appear in the future month.
- 1,605 of those unique combinations were never seen in train.

| Evaluation subgroup | n | Popularity % | METIS % | KM1 % |
|---|---:|---:|---:|---:|
| All future requests | 100,198 | 66.020 | 69.208 | **73.278** |
| Novel (previously unseen) property sets, query-weighted | 12,088 | 27.598 | 28.863 | **31.411** |
| All deduplicated future property sets | 2,470 | 30.000 | 32.186 | **34.332** |
| Deduplicated novel future sets | 1,605 | 23.614 | 26.293 | **27.975** |

Thus KM1 advantage over METIS on deduplicated *novel sets* is +1.682pp, and over popularity +4.361pp. All such subgroup inspections were performed AFTER the primary future-month report, so are **descriptive/exploratory**, not confirmatory. Improvement is smaller on genuine novel patterns, and most query traffic still repeats historically common patterns.

## Executable scripts and successful GitHub Actions

- `research/bridge_partition/temporal_wikidata.py`: initial real chronological test and relationship prediction, action https://github.com/AiDevnew168/scale_rag/actions/runs/44530068673
- `research/bridge_partition/temporal_hypergraph.py`: real strong hypergraph baseline, action https://github.com/AiDevnew168/scale_rag/actions/runs/44530427288
- `research/bridge_partition/month_ahead_wikidata.py`: independent future-month test, action https://github.com/AiDevnew168/scale_rag/actions/runs/44530747392
- `research/bridge_partition/temporal_novel_patterns.py`: deduplicated/novel-pattern robustness analysis, action https://github.com/AiDevnew168/scale_rag/actions/runs/44531065203

All runs successfully completed and uploaded JSON artifacts. Code includes fixed seeds, exact source hashes, deterministic parser, and restricted train-only feature selection.

## Research decision

**GO for a new data- and cost-grounded algorithmic hypothesis; no journal novelty claim yet.** We now have meaningful positive evidence that query *hyperedge* coaccess and group structure are predictive of future real workload even a month later, including on novel predicate combinations. This is a better signal than the artificially shifted TopoGraphRAG question subsets.

We must NOT conflate this with novel optimization: direct Mt-KaHyPar, SWORD 2014, WISE 2020 and 2026 robust dynamic partitioning cover major parts of this algorithmic space. The next true novelty gap must be in a sharply defined cold-start and tail-risk objective under **actual predicate/triple byte weights**, long-tail multi-hop query templates and routing latency. Strong prior art and sequential held-out later intervals required.

**Not established:** a graph-theoretic novelty, measured GraphRAG answer improvement, measured networking cost, or dominance over advanced SWORD/WISE/robust partitioner implementations. Avoid starting a large graph service or a manuscript before those gates.
