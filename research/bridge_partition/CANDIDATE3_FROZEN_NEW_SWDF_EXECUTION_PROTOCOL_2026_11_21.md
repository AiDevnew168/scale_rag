# FROZEN BEFORE NEW DATA INSPECTION: External SWDF real-log, four-process SPARQL economic gate

Date: 2026-11-21. Source domain **SWDF**, never used in candidate3's prior WatDiv or Wikidata dataset experiments. This is an *engineering held-out benchmark*, not prospective production traffic or an independent controlled user trial.

## Predeclared source and fail-closed hierarchy

1. Source real SPARQL query log: `https://raw.githubusercontent.com/AKSW/LSQ/develop/lsq-core/src/test/resources/logs/combined.swdf.log` (AKSW LSQ test fixtures). This is a small sample of organic SWDF logs, NOT a representative entire LSQ historical traffic stream; inspect actual log syntax only after this file is committed.
2. Matching SWDF RDF snapshot: first try `https://hobbitdata.informatik.uni-leipzig.de/benchmarks-data/datasets-dumps/` official HOBBIT SWDF dump listing; next `https://www.rdfhdt.org/datasets/` SWDF2012 242k triple HDT, requiring a **documented HDT->NTriples conversion tool** (not guessed SPARQL query output); third a pinned accessible full SWDF dump from FEASIBLE authoritative project.
3. An RDF dataset from a *different domain* and queries unrelated to SWDF MUST NOT silently replace the match. If unavailable, label this benchmark **BLOCKED**, do not fabricate a source.
4. Raw bytes, SHA256, source URLs, RDF triple counts, syntax and query text hashes must be recorded. If no real usable complete RDF and >=20 unique valid query templates including >=5 with nonempty results, fail this gate.

## Before seeing query outcomes: sampling, partitions, baselines

- Do not tune model on the new SWDF corpus: **frozen candidate** is PTCR-90 with exact 4-shard previous-tail and day0 acceptance, plus a predeclared alternative BEND selectors under real measured costs; no threshold chosen based on new test labels.
- Only if actual timestamped real log exists: split by real timestamps into first 50% chronological *training*, next 20% validation, final 30% test; if no credible timestamps, the objective is an exact-hash disjoint **engineering** test, not chronological economic drift proof.
- Train/test EXACT textual identity overlap MUST be zero, with separate predicate-set structural family-disjoint audit. Do NOT refer to hash disjointness as full distributional independence. Feature parse via SPARQL-aware parser; unsupported graph, SERVICE, property paths, variable-predicate branches are rejected and counted; no unsupported query can count as a correctness PASS.
- Four independent `pyoxigraph==0.5.13` worker processes connected by TCP on runner localhost; all stores physically loaded with their own RDF triples and indexes. Central Oxigraph uses full graph as exact answer oracle. Coordinator materializes required predicate triples and executes original complete SELECT. This is naive distributed storage (and needs explicit correctness), not a production federated query optimizer.
- Exact identity of complete answer multisets (normalized binding tuples, with RDF term semantics preserved), **including nonempty answer queries**, before/after migration, is a mandatory hard gate; no partial examples substituted for full validity.
- Per-shard physical bytes <=1.10*average graph bytes; migration measured actual transmitted bytes, acknowledged and removed during query barrier. Include loading/index maintenance and downtime, not just raw network theoretical line rate. Distinguish buffered localhost loopback from real multi-host Ethernet.
- Controls: static balanced, static duplicate-aware selective replication, observed-only 1swap, head-only 2swap, PTCR90, safe no-op, and hybrid 1swap+replica, all with same storage caps and <=25MB total moved/replicated serialization. When faithful WISE/WASP implementation is not available, state **NOT IMPLEMENTED**; do not label loosely similar methods as actual WISE/WASP.
- 5 repeated paired, randomized query orders in both serial & parallel fragment retrieval. Genuine measured critical-path p50/p95 on distinct test templates; 95% cluster bootstrap at distinct-query-pattern or day units, with correct dependence, not individual repeat count.
- Net economic: `sum(real paired query wall-clock savings) - measured barrier and storage/index update time`. Do not claim money savings without independently priced hardware, power and network.
- Required GO: full correctness, ≥20 independent exact heldout templates with ≥5 nonempty, positive net paired latency CI after migration and no material p95 harm vs **the strongest** complete same-budget baseline, robustness in at least two independent real workload shifts, comparison to faithful published prior art. Otherwise gate **NO-GO or BLOCKED**. No tuning on test outcomes.

## Independent verification

Freezing this document precedes fetching or analyzing SWDF log and corresponding graph in the new workflow. All data and future experiment output remain branch-local and archived in GitHub Actions logs/artifacts, with immutable SHA references. Existing 2018 organic Wikidata and synthetic WatDiv outcomes may motivate algorithm but NOT be rebranded independent holdout results.
