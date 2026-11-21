# Frozen SPARQL acceptance contract, before semantic validator implementation (2026-11-21)

The *previously inspected* FEASIBLE SWDF exact-hash/family holdout is reopened only for ENGINEERING REGRESSION. Passing it after a repair MUST NOT be called independent scientific confirmation.

## Full SELECT result equivalence

- Evaluate complete original SELECT without rewriting it for latency. Preserve RDF term type (IRI, plain/typed/language-tagged literal, blank node, unbound), duplicates (bag semantics), variable names, and blank-node identity consistency across all bindings.
- SELECT with no ORDER BY: results are a **multiset** (row sequence irrelevant). Preserve original LIMIT/OFFSET in the timed query. With a tail-level LIMIT/OFFSET but NO ORDER BY: compare each returned multiset as a **valid sample** of a reference *unsliced* full-result multiset (projected DISTINCT and all other authorized algebra preserved); expected sample size `min(limit, max(0, full_count-offset))`. Candidate must be a sub-multiset of the original unsliced result, with one global injective blank-node renaming over the response's bindings. For `OFFSET` with no LIMIT, expected count is `max(0, full_count-offset)`. This validates legal unordered response selection, not exact selection equality with a centralized limited query. No partial count-only acceptance.
- SELECT with ORDER BY, LIMIT or OFFSET: ordered bindings must agree *in sequence* with the reference engine modulo globally consistent blank-node renaming. Ties in ORDER BY not uniquely defined may yield legitimate alternative sequences; without a proven tie-aware comparator, fail closed with `ORDER_BY_NONDETERMINISM_UNRESOLVED`, not a false PASS.
- Only authorize top-level LIMIT/OFFSET syntactic removal for this simple algebra class. Never remove nested subquery LIMIT, or use regex to truncate arbitrary SPARQL text and call it safe. Strictly fail closed on unrecognized tail modifiers.
- For full unsliced reference queries with row count >20,000, outcome is `RESOURCE_BLOCKED` — do not drop or quietly count as passing.
- Graph-level matching for blank nodes uses true RDF graph isomorphism or canonicalization **when testing graph fragments**. For SELECT result bags use a global blank-node alpha renaming constrained by all rows and literal/IRI bindings.
- Calibration-only semantic acceptance evaluation may locate engineering bugs, but cannot be used to alter the frozen 34-family prior test split and call it a new independent test.

## Comparator regression tests to run

1. Unordered LIMIT supports any valid kth element, rejects answers outside full solution set, rejects duplicate overuse, enforces exact answer count and OFFSET.
2. Full unordered bag respects duplicates, result binding variable order independence, literal language and datatype differences.
3. Full ordered answers do not accept row swaps and fail closed on LIMIT ties without an implemented formal tie test.
4. Blank-node alpha equivalence accepts consistent global renamings, rejects inconsistent aliasing, enforces multiple related rows and permits unused reference blank nodes under subbag.
5. Tests for false positives from independent per-row blank-node renamings, result row truncation, type conflation and binding dropping.
6. Real pyoxigraph result conversion + unchanged query integration and run on four separate source-preserving SWDF shards, with error accounting across *all* originally frozen calibration and heldout queries.

## Publication comparison

The upstream DIAERESIS author code at commit `22dfe190078973f644f5d6279181e54ec116f6e3` has been built. To claim full baseline comparison, execute original DAP partition + translator + query runner in real Spark+HDFS with identical graph and queries and separate central correctness oracle. If source runtime cannot be set up, report **BLOCKED**, not a similarly named approximation.

## New corpus

Actual independently unseen timestamped logs plus matching RDF graph are mandatory for economic confirmation. The AKSW/LSQ 2014 SWDF small fixture is NOT adequate (only 3 strict-eligible unique templates). DICE FEASIBLE SWDF has no trustworthy timestamps. Distinct newly generated synthetic queries do NOT qualify as unseen organic workload. Freeze SHA source before accessing outcome labels.

## Verdict policy

A GitHub Actions green CI indicates the experiment ran, NOT a paper PASS. Fail closed on comparator unsupported semantics, unanswered queries, mismatched multiset, deficient statistical power, missing genuine full prior-art executable baseline, or unverified snapshot alignment.
