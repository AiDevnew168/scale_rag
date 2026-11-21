# Candidate 3 — prior art, novelty boundary, and publication gate (2026-11-21)

**Evidence class:** literature audit with falsifiable claims, not demonstrated superiority. Author status before completed physical SWDF outcome.

## Prior art constraining novelty

| Work | Relevant established capabilities | Claim that is NOT new |
|---|---|---|
| [WISE (2020)](https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290) | RDF workload monitoring, cost-aware partition redistribution and replication | Workload-aware RDF migration |
| [AdPart, The VLDB Journal](https://www.vldb.org/vldb_journal/index.php/component/article_manager/article/1370) | Real distributed RDF/SPARQL, adaptive redistribution and replication, eviction of redundant frequent patterns | Online adaptive redistribution and replication |
| [WASP (2021)](https://link.springer.com/article/10.1007/s41019-021-00156-2) | Workload-aware streaming graph partitioning | Generic workload-driven graph partition adaptation |
| [Analyzing workload trends for boosting triple stores performance (2024)](https://www.sciencedirect.com/science/article/pii/S0306437924000784) | Workload trend and triple-store cost adaptation | Pattern tracking and general RDF workload-based cost models |
| [UniPart (2024)](https://journals.sagepub.com/doi/abs/10.3233/SSW240024) | Streaming RDF partitioning and workload-aware adaptation | Streaming RDF partition adaptation |
| [Stall-Free Asynchronous State Repartitioning with a Proactive Workload Tracking Window (2026)](https://onlinelibrary.wiley.com/doi/full/10.1002/cpe.70581) | Asynchronous state repartitioning and forward-looking tracking window | Repartitioning without foreground scheduling stalls |
| [Replication in Graph Partitioning and Scheduling Problems (2026)](https://arxiv.org/abs/2605.00209) | Formal replication in hypergraph/graph placement, cost-aware ILP comparison | Replication as a novel graph communication reduction primitive |

**Comparator caveat:** WASP and the asynchronous-state work do not run the exact original SPARQL/RDF engine; they are related work and cannot silently be called head-to-head SOTA baselines. Original WISE and AdPart are directly relevant but require faithful execution or an explicit compatible common-subsystem comparison.

## What current results do and do not show

- The conditional expected-gain Hoeffding and distribution-shift tests and deterministic stop-loss tests passed on synthetic premises. These elementary mathematical constructions are not new theorems and do not establish positive production net.
- FEASIBLE raw log 2014: 176 genuine UTC dates; only 7,142 predicate-compatible eligible original query occurrences, about 0.504% of 1,416,681 requests with dated query text. Source-only eligibility is not a whole-service traffic benchmark.
- The full RDF graph is SHA-pinned but its actual snapshot identity as of each 2014 date is unverified. The four workers are independent indexed localhost TCP processes on one VM, not a four-host federated join planner.
- Under the conservative certified-drift gate, the actual chosen policy is **no_move**, whose incremental benefit against static no_move is zero by definition. A heldout-optimal placement is a post-hoc oracle, not an executable improvement.
- Past NYT and DrugBank counterfactual migration performance was negative. Their abstention success is a safety result, not positive profits.
- The first full 176-day source physical run failed in the sampler before economic scoring. A corrected run is needed; no successful physical net was available at authoring.

## Testable target for a novel contribution

Possible scientific question: **Can a semantics-safe, risk-budgeted adaptive RDF migration controller actually make better deployable decisions than calibrated existing migration/replication controllers under authentic chronological drift, after measuring migration, index update, downtime, shadow and rollback?**

Candidate paper framing: *When Not to Repartition RDF: Risk-Budgeted Semantic-Safe Migration Under Natural Workload Drift*. This is a research title, not an accepted novelty statement.

A robust positive paper must demonstrate that the real controller sometimes migrates based entirely on past information and obtains positive **realized** incremental net vs static and strongly tuned online threshold/replication competitors. A controller that always refuses migration provides no incremental deployed savings.

A narrower negative-results or benchmarking systems article may be possible if we obtain independent replication, full query conformance and comprehensive economic measurement. Such a paper should not claim an original SOTA migration theorem.

## Hard scientific gates

1. **SPARQL:** original SELECT answer legality matches independent centralized graph for every sampled query under both placements. Respect global Blank Node identity and unordered LIMIT legal subbags. Semantic errors, unsupported cases and timeouts are failures, not discardable observations.
2. **Trace/accounting:** preserve aggregate original request-day counts, anonymous sampled occurrence IDs, genuine paired wall times, repetitions, novelty categories, and exact measured physical migration bytes and time. Report day inclusion probabilities.
3. **Cost:** include index writes, pause, recovery, actual rollback and monitoring costs; otherwise label a result as partial-cost exploratory only, not profitable migration.
4. **Uncertainty:** days are chronological and may be autocorrelated. Report within-day finite population uncertainty, moving-block sensitivity, burst concentration, sampled p95, and multiplicity for four speculative actions. No test-selected best placement may be called a predeclared selected policy.
5. **Policy:** prospective past-only decision algorithm must migrate sometimes and outperform true static no-move and a tuned admissible online baseline; merely labeling a post-hoc oracle as a control is not allowed.
6. **Generalization:** independent natural original-query workload, version-aligned RDF graph, actual multi-host network where relevant, and faithful published baseline under matched resource budgets.

As of writing: 13/13, 15/15 and new 11/11 tests establish only implementation invariants; positive net economics, novelty and journal superiority remain UNPROVEN.
