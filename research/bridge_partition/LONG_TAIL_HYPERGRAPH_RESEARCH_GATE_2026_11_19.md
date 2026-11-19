# ScaleRAG Candidate 3 — Observed evidence, novelty-risk boundary, and frozen next gate

**Date:** 2026-11-19  
**Decision:** **GO for ONE tightly scoped multi-objective novel-pattern robustness research problem; NO CLAIM of a novel algorithm yet.**

## Empirical provenance

The following are real CI runs in this GitHub branch:

1. Layout page-shard benchmark 600 test questions (source TopoGraphRAG): https://github.com/AiDevnew168/scale_rag/actions/runs/44515079238
2. Direct Mt-KaHyPar strong baseline: https://github.com/AiDevnew168/scale_rag/actions/runs/44522610045
3. Document-disjoint dense page coaccess 43 document test: https://github.com/AiDevnew168/scale_rag/actions/runs/44529364201
4. Threefold document-disjoint dense page coaccess 142 docs, 1,491 test questions: https://github.com/AiDevnew168/scale_rag/actions/runs/44530707740
5. Wikidata real organic query log first-month test: https://github.com/AiDevnew168/scale_rag/actions/runs/44530068673
6. Mt-KaHyPar direct temporal baseline: https://github.com/AiDevnew168/scale_rag/actions/runs/44530427288
7. **Separate following-month** 100,198 organic multi-property requests: https://github.com/AiDevnew168/scale_rag/actions/runs/44530747392
8. **Third-month** August 2017 held-out hyperedge+pair-net smoothing: https://github.com/AiDevnew168/scale_rag/actions/runs/44531934029
9. Separate **December** 2017 held-out novel-combination-focused objective selection: https://github.com/AiDevnew168/scale_rag/actions/runs/44532418101
10. **December unique-pattern distribution / repetition / paired error audit**: https://github.com/AiDevnew168/scale_rag/actions/runs/44533269125

These outputs are *not* full RAG answer accuracy, true memory-byte graph partitioning, measured network joins, or distributed serving latency.

## Results that survived a stronger check

**Real timestamped workload:** From real Wikidata SPARQL organic 2017 query logs, select 120 property IDs using ONLY June 12–25 training. Map IDs to 4 equal-count shards. Evaluate a whole *different* July 10–Aug 6 file of 100,198 eligible user queries:
- Popularity-based fixed placement: 66.020% complete same-shard predicate sets.
- Historical coaccess METIS: 69.208%.
- Established Mt-KaHyPar KM1 hypergraph: **73.278%**.
- Direct KM1 vs clique METIS +4.070pp, 28-day block-bootstrap interval [+2.322,+6.071]pp.
These gains validate a real, reproducible placement *task*, **not** novelty for Mt-KaHyPar.

**One other independent August 7–Sep 3 file (158,620 eligible):**
- Conventional direct KM1 85.687%.
- Full-hyperedge plus historical pair-net regularization, beta=1 chosen on July development **86.408%**, +0.721pp, day-block interval [+0.514,+0.994].
- On 16,395 **new combinations** unseen in June history, regularized 51.107% vs direct 51.302% (-0.195pp). The mean gain came from familiar patterns, not the research target.

**Dense page coaccess FAILED the strong reliability check:**
An initial 43-document result showed semantic+structural 41.247% vs sparse 38.229%, +3.018pp with CI crossing zero. Threefold document-disjoint CV covering all 142 documents and 1,491 questions showed semantic+structural **35.547%**, sparse **36.620%**, basic structural **37.022%**. Thus the initial positive point estimate was not generalizable. Do not claim a semantic text-model advance.

## Critical heavy-tail finding from genuinely later December organic logs

Train June 12–25, tune candidate beta from July novel June-unseen patterns, test untouched Dec 3–30 on the same fixed June-selected 120 predicates.

December test: 339,300 eligible requests, 246,552 requests on a new June-unseen predicate-set combination, but only **1,940 unique such combinations**.
- One specific previously unseen 4-property pattern ([P31,P625,P279,P238]) occurs **223,186 times**, i.e. **90.523% of novel requests**.
- Top 10 unseen combinations together are **94.814% of novel requests**.
- Standard KM1 has **94.832%** one-shard coverage among new-pattern **requests**; beta=0.25 chosen on July novelty has **4.332%** because it splits that single dominant pattern.
- If every new combination receives **one vote**, KM1 coverage is **22.577%** and beta=0.25 coverage is **24.175%**.
- Among 1,940 distinct patterns, beta=.25 has 53 wins vs KM1 and 22 losses, absolute difference **+1.598pp**; naive pattern-level bootstrap CI [+0.722,+2.526]pp. **This bootstrap assumes patterns independent and is optimistic** because they share properties and query origins. Not statistically definitive.
- A method optimizing average frequency and a method favoring diversity of query structures can point in **opposite directions**. Do not hide their Pareto conflict behind a single score.

December logs source SHA256: 00e4bd4631dbf83962d193b4367e09c0d2a4570b705518883fb07338dc0a7a67.
August logs source SHA256: fc4633815702f140f6c7f15b21927d93117199347dc0240dca068f2f0e2e640d.

## The correct open scientific question

**Given an evolving historical workload, can a constrained hypergraph placement protect the long tail of never-before-seen relational query *structures* while keeping frequent known queries affordable, under actual per-shard byte memory and update/migration budgets?**

A candidate explicitly two-risk constrained objective is

    minimize_P  E_historical_traffic[span(q,P)-1] +
                lambda * CVaR_tau_over_estimated_unseen_patterns[span(q,P)-1] +
                mu * migration_bytes(P,P_old)
    subject to:
      max_shard_bytes <= B
      E_historical_traffic[span(q,P)-1] <= C_baseline + epsilon
      total_migrated_bytes <= M

Any future-pattern estimator must be constructed solely from past semantic/structural coaccess and dev data, NEVER unseen test patterns. This optimization objective is **hypothetical and NOT new merely by being written down**.

## Existing work that must be beaten or differentiated

- SWORD: https://www.vldb.org/vldb_journal/index.php/component/article_manager/article/1311
- WISE workload-aware partitioning with decay: https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290
- Minimum Motif-Cut: https://doi.org/10.1007/S00778-024-00860-1
- Mt-KaHyPar: established very strong hypergraph baseline
- MTGA 2026: https://www.sciencedirect.com/science/article/pii/S0957417426016192 (explicit long-tail handling and dynamic updates)
- WASP streaming partitioning: https://link.springer.com/article/10.1007/s41019-021-00156-2

Therefore a novelty claim requires nontrivial *mathematical or empirical* improvement beyond known robust/fair partitioning, dynamic coaccess and replication, and must include explicit memory/byte physics. A simple weighted average of known objectives is not sufficient novelty.

## Frozen experimental next gate (not yet executed)

1. **Stop model and hyperparameter fishing on 2017 December**: all December test stats are now exploratory.
2. Design a properly risk-constrained algorithm with exact or bounded surrogate for the unseen-pattern tail, compare direct KM1, WISE/SWORD-style recency and replication, and hypergraph mix beta=.25/1.
3. Pre-register the algorithm and tuning procedure *before* opening another untouched interval: **2018-01-01 to 2018-01-28** organic Wikidata logfile (official, accessible, not used yet by this line).
4. Evaluate **both** demand-weighted (including peak/tail cost) and distinct-novel-pattern-uniform (with cluster-aware uncertainty), and enforce a hard, test-independent constraint on demand-weighted degradation.
5. Replace simplistic predicate equal weights with actual data bytes / grouped RDF triple loads; simulate/measure join and migration cost instead of assuming number of active shards equals latency.
6. Only if the new algorithm beats known baselines on novel patterns WITHOUT unacceptable head-workload degradation may a serious research paper project start.

**Interpretation:** This line now has reproducible real historical workloads, multiple truly later file-level tests, strong baselines, a concrete and measurable long-tail failure, and a falsifiable two-risk objective. It still lacks proven novelty or end-to-end RAG benefit.
