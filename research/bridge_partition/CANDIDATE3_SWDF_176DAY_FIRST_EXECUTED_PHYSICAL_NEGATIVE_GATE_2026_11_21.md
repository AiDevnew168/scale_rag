# SWDF 176-day first executed physical benchmark — semantic gate FAIL

Date: 2026-11-21. Source evidence: https://github.com/AiDevnew168/scale_rag/actions/runs/44908321838
Original run SHA 411c7429919793f28d4c0cb6e10554a1798dca2e. Artifact ID 14709959437; artifact zip SHA256 9dd79329e23c21c21ab05639b38525620b47f312a9b143eb4af8f195ea0074c5.

**The GitHub workflow passed as a software process, but ALL FIVE POLICIES FAIL scientific full-SPARQL semantic and economic admissibility. No profitability proven.**

## Frozen sample

Original gzip SHA256 2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df. True UTC calendar split: 88 train days (4707 eligible occurrences), 17 construction days (393), 18 calibration days (601), 53 test days (1441). Test 629 sampled original eligible request occurrences, each tested twice = 1258 pairs per method. Test 253 unique query texts, 80 new exact texts, 11 new predicate families. Four independently indexed localhost Oxigraph TCP processes, NOT multiple independent hosts; RDF-as-of-2014 snapshot alignment not verified.

## Complete observed diagnostic table

| Physical policy | Fully successful pairs | Exceptions | Change in RDF payload bytes | Contacts saved among successful pairs | Move/index barrier ms | p50 baseline / alternate ms (successful pairs only) |
|---|---:|---:|---:|---:|---:|---|
| no_move | 1256/1258 | 2 | 0 | 0 | 0 | 150.923 / 150.870 |
| one_swap | 1256/1258 | 2 | 0 | 332 | 10.0401 | 151.1282 / 151.1409 |
| two_swap_greedy | 1256/1258 | 2 | 0 | 334 | 199.4556 | 151.3436 / 151.6038 |
| replica_only | 1256/1258 | 2 | 0 | 1124 | 5.3125 | 151.0895 / 151.2652 |
| swap_replica | 1256/1258 | 2 | 0 | 828 | 12.0319 | 151.3714 / 151.3562 |

These are conditional diagnostics after errors were omitted; they are NOT legitimate positive economic estimates. In original report all five actions have economic.valid=false and reason ORIGINAL_FULL_SPARQL_SEMANTIC_CORRECTNESS_FAIL. Full rollback/shadow/cross-host costs are unverified.

## The two physical exceptions

Both repeats of one sampled original query from 2014-09-26 failed. Query SHA256 e8f4f6b9b2e90f89d4e5e80f68af8322751019f19324e7cee4c1cf2c08e95474. Underlying error is Oxigraph SyntaxError at 4:46, Prefix not found. Preliminary rdflib algebra accepted the query, showing source-parser versus physical engine compatibility mismatch. This is not established as a wrong SPARQL result, but fails the original end-to-end contract. Do not remove or modify the exposed query to claim confirmatory success. For a new later independent benchmark, prequalify source syntax with both parsers using source-only gates, then freeze an entirely new cohort.

## Elementary conditional transport conservation

Actual code paths: candidate3_source_identity_worker.py /raw-fragments, candidate3_swdf_real_full_sparql_economics.py shards_for_query, candidate3_nyt_full_real_e2e.py run_query.

For predicate witness P and disjoint original source partitions S_p, when every source partition is fetched exactly once (choose one copy of an unchanged full-predicate replica), serialized RDF response payload equals the sum over p in P and fragment s in S_p of length(s). The sum does not depend on predicate ownership/shard placement. Therefore pure whole-predicate swapping or full fragment replication in this eager shipping architecture cannot reduce serialized RDF response payload bytes, assuming no pruning, compression, caching or server-side joins. The theorem does NOT cover packet/header costs or wall-time behavior, where changes may be measurable. No novelty claim: this is direct conservation of bytes.

Actual router regression: https://github.com/AiDevnew168/scale_rag/actions/runs/44913514206 (7/7 PASS). The measured zero RDF payload savings under all five policies match this invariant. This is why optimizing shard touch counts alone is scientifically weak.

## Publication decision

The actual conservative risk controller chose no_move, whose incremental realized gain against no_move is exactly zero. A hypothetical future-selected winning placement would be post-hoc diagnostic, not a deployed advantage. The run lacks a complete semantic pass, positive full net, 2014 graph snapshot alignment, multi-host system and matching published strong competitor. It does not clear any full SOTA journal superiority gate.

Stop tuning whole-predicate swap/replica touch proxies on the exposed SWDF test. The existing negative NYT and DrugBank evidence further lowers this candidate's priority. Pending further corrected physical runs 44910678795 and 44911492637 must be reported faithfully when completed, including any failures. Keep the original experiment intact.

Future candidate is ONLY an unproven research direction: a query-execution strategy that breaks eager full-predicate fetch by certified selective predicate filtering/joins and economically justified switching. However semijoins, SPARQL pushdown, and partition shipping are old ideas; compare with smart-KG+ (https://journals.sagepub.com/doi/full/10.3233/SW-243571), FedX (https://rdf4j.org/documentation/programming/federation/), WISE, AdPart before any new implementation or novelty assertion.
