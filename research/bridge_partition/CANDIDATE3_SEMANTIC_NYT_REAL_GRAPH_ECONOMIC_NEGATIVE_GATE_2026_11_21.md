# Candidate 3 — Semantic SPARQL correctness and genuinely new physical NYT source: independent engineering result

Date 2026-11-21. Branch `research/candidate3-semantic-confirmation-20261121`.
No novel-algorithm or new economic superiority claim is warranted. All new code/reports committed to GitHub and exact Actions execution identifiers below.

## A. Conservative full SELECT semantic verifier: actual PASS

Files:
- `research/bridge_partition/candidate3_sparql_semantic_certifier.py`
- `research/bridge_partition/test_candidate3_sparql_semantics.py`
- GitHub Actions PASS 12/12: https://github.com/AiDevnew168/scale_rag/actions/runs/44879566108

The original SELECT (not a modified ORDER BY query) is run unchanged for measurements. Unordered LIMIT/OFFSET semantics are accepted iff both original answers have valid expected result multiplicity and bag inclusion under a separate unsliced full authoritative centralized RDF truth; a global injective bnode renaming is required across all result rows. Invalid rows, different literal language/datatype, duplicate multiplicity errors or broken blank-node coreference are FAIL. Where correctness cannot be proved (e.g. ORDER BY tie ambiguity, REDUCED or runaway search), the verifier reports INCONCLUSIVE rather than PASS. This is a *conservative proof of particular returned answers*, not a full SPARQL formal verification or claim of novel standards result.

## B. Exact root cause of four real SWDF multi-shard calibration misses

Earlier original full DICE SWDF source: 304,592 unique Oxigraph RDF triples, 84 eligible calibration queries; four original SELECT queries returned 1 answer against centralized full RDF but zero against the physically reconstructed query fragments. This happened identically with no-move, one-swap, one-replica, hybrid, so was NOT caused by migration. Initial new semantic verifier correctly accepted 80/84 and rejected 4/84 in every policy:
https://github.com/AiDevnew168/scale_rag/actions/runs/44879940048

The four were exact three-BGP joins using `rdf:type` and `ical:dtstart`, with a blank-node binding between the latter two triples. Source-level forensic result on a carefully preserved 30,250-triple 2-predicate subset:
https://github.com/AiDevnew168/scale_rag/actions/runs/44880474166

| Query class | Full SWDF | Identical source subset with Oxigraph `Store.bulk_load` | Identical subset with Oxigraph `Store.load` |
|---|---:|---:|---:|
| One BGP with LIMIT 20 | 20 | 20 | 20 |
| Two BGPs with LIMIT 20 | 20 | 20 | 20 |
| **Three-BGP join through source blank node** | **1** | **0** | **1** |

This controlled observation isolates a blank-node identity/join preservation failure specific to this tested bulk-loading reconstruction. The underlying root cause inside the library's bulk loader is not formally established. **Proof-backed operational repair:** use `Store.load(input=complete_source_fragments, format=N_TRIPLES)` for the coordinator's original SPARQL evaluation rather than `Store.bulk_load`. Preserve globally scoped original raw N-Triples bytes between source shards. A separately executed real four-worker semantic calibration CI is required to confirm 84/84; do NOT assume success from the isolated 3-BGP root-cause test.

## C. New authentic complete NYT RDF source and frozen independent semantic+economic physical test

The official 2026 LargeRDFBench Interoperable Edition (Zenodo 22140177) publishes authentic graphs and queries in separate ZIP files. Its 32 original federated SPARQL templates include only 9 fitting our strict constant-predicate BGP SELECT contract; **thus official original query bank FAILS 20-independent-family entry criterion**. Neither the 9 supported examples nor extrapolation from them constitutes organic traffic proof:
https://github.com/AiDev168/scale_rag/actions/runs/44880005504

Instead a specifically disclosed **engineering correctness regression** (NOT an original-user-log paper test) used the entire original `NYT.nt` RDF member, extracted with HTTP range from the official unmodified full 5.1GB ZIP. Precommitted protocol `research/bridge_partition/CANDIDATE3_FROZEN_NYT_NEW_REAL_GRAPH_ENGINEERING_GATE.md`, before any evaluation outputs. Original full N-Triples byte SHA256 `aac49186ab45899f8f467f9264367ddad76a8a08c6011cb618a5c2d6fe4aed85`, 51,498,878 original source bytes, 335,198 NTriples **lines**, **335,197 unique Oxigraph triples**, 36 predicates, 21,666 distinct subjects. The source yielded 1392 distinct subjects' pair/triple predicate combinations. Hash-frozen membership: 80 train, 18 calibration, 27 strictly unseen test query families; tests generated synthetically from the full real source structure, NOT natural users. Every test centrally returned a nonempty result.

Real completed 4x TCP Oxigraph-worker experiment, original unchanged SELECT, actual physically transmitted/indexed RDF and strict byte capacity:
https://github.com/AiDevnew168/scale_rag/actions/runs/44880717063

| Measure | Frozen static | Training/calibration-only one balanced swap |
|---|---|---|
| Original semantic SELECT responses proven valid | **81 / 81** | **81 / 81** |
| Three replications of 27 untouched query families | YES | YES |
| Raw RDF bytes moved | 0 | **1,683,926** |
| Measured single-VM migration/index barrier | 0 | **70.8354 ms** |
| Initial 4-shard raw bytes | 12.86MB each (max 12,886,747 bytes) | post-load under cap 14,162,192 bytes |
| Shard contacts saved vs static during 81 test runs | 0 | **-3** (three extra contacts!) |
| Parallel TCP materialization wall-clock p95 | ~106ms | ~104ms (paired timings varied) |
| **Measured paired NET after migration** | 0 by definition | **-102.1695 ms** (loss) |
| Cluster bootstrap 95% net, 27 family units | baseline should center near zero | **[-165.2826, -38.3892] ms** |

This is a **genuine negative economic finding** on a completely untouched real RDF graph with a frozen, graph-derived synthetic query selection. It does NOT establish prospective organic performance, real cross-machine financial costs or top-paper novelty. A successful safety controller would have to ABSTAIN from this move given trustworthy calibration of its actual future critical-path gain; that controller has NOT been proven on truly fresh chronological traffic.

## D. Published original contender: DIAERESIS

Found and pinned exact original author source `isl/DIAERESIS` commit `22dfe190078973f644f5d6279181e54ec116f6e3`; original Maven build produced `DIAERESIS-1.0-SNAPSHOT.jar` 366,237 bytes under Java 8, not a proxy heuristic:
https://github.com/AiDevnew168/scale_rag/actions/runs/44876436118

Located ORIGINAL published SWDF data and schema from author URL `https://users.ics.forth.gr/~kondylak/SWJ/swdf.zip`, ZIP SHA256 `c1787940fbffab1b92e61bb338707bc11d2575931fefd15cabc78f88c00654de` with complete 51,587,578-byte `clean_swdf.nt` and 100,612-byte `schemaSWDF.txt`. Source proof:
https://github.com/AiDevnew168/scale_rag/actions/runs/44880049061

Faithful original unmodified Scala Spark/DAP → QueryTranslator → QueryProcessor is attempted in `candidate3_diaeresis_full_author_runtime.py` and its workflow. Required Spark 3.1.1, Java 8, Hadoop `FsShell` with local filesystem, no actual multi-host HDFS. Initial env bootstrap failures: corrupt Temurin Java artifact, missing Python 3.9 from Ubuntu 26.04 runner, then `core-site.xml not found`; these are environment issues, NOT demonstrated errors in the author's DAP algorithm. **Do not claim baseline executed** until all original 3 stages actually PASS on the original source, and even then no equal-resource or actual matched workload superiority claim until actual original answer equivalence and same conditions are verified.

## E. Exact final scientific gates

- **PASS**: independently runnable W3C-conservative original SELECT semantic certifier (12/12 tests).
- **PASS**: isolated original real SWDF blank-node join root cause and verified `Store.load` corrected same original three-BGP query (bulk_load 0 vs load 1), independent of migration.
- **PASS**: complete NYT RDF source with 27 fresh original real-graph test families, four indexed workers, **81/81 legal original SELECT outputs**, measured data moves, paired latency and dependence-aware uncertainty.
- **FAIL**: NYT source-derived synthetic workload with one swap yields **significantly negative** measured short-horizon net timing after migration; cannot claim economic savings.
- **BLOCKED**: LargeRDFBench original external query set has only 9/32 strict eligible (and is federated), not 20+ real organic new query families.
- **BLOCKED**: matched faithful DIAERESIS actual complete author pipeline and head-to-head original query result/latency comparable environment until verified.
- **BLOCKED**: independent real-user, timestamped, source-aligned RDF/SPARQL time-series drift and real cross-machine economics.

The high-quality journal method still requires a formal and empirically well-calibrated positive-net action admission (no-move, migration, replica, hybrid) evaluated without test leakage in **actual new real traffic**, and an authentic published baseline runtime using equivalent original data and budget. This stage advanced system correctness/measurement but did not prove novelty or profit.

## Verified final SWDF semantic root-cause correction: PASS 84/84 x 4

After the physically isolated three-BGP comparison proved identical source fragments yield `rdf:type` to `ical:dtstart` blank-node join 0 under `Store.bulk_load` and 1 under `Store.load`, the full four-independent-Oxigraph-worker coordinator switched to **`Store.load`** on the combined raw N-Triples predicate fragments. All original queries were preserved unchanged; the W3C-conservative separate unsliced truth was used only for legality proof.

**Successful CI, no excluded failures:** https://github.com/AiDevnew168/scale_rag/actions/runs/44880920149. On all 84 original calibration queries:
- no_move **84 PASS, 0 FAIL**
- one_swap **84 PASS, 0 FAIL**, actual physical RDF transfer+index barrier **24.7101ms**
- replica_only **84 PASS, 0 FAIL**, actual barrier **10.9699ms**
- swap_replica **84 PASS, 0 FAIL**, actual barrier **35.6527ms**.

Previous intermediate CI 44880816020 incorrectly reported zero passing after a Python comment introduced literal backslash-n escapes that commented out the intended `Store.load` call. That coding defect was corrected in commit `026e09aa0cae74e0660a51ed095c5648c0c8239a`; prior failure is preserved, not hidden. 44880920149 is the successful retest.

This proves **semantic correctness on the fully specified SWDF calibration subset** at unchanged SPARQL query semantics, with actual TCP workers and unmodified total RDF source byte membership. It does **NOT** independently confirm SWDF heldout (already previously opened), actual multi-host operation, nor a newly successful economic controller. The NYT fresh external engineering A/B continues to show negative real net savings, preserving the paper-level economic NO-GO.

## F. Second independent complete original real RDF corpus: preregistered DrugBank economic *abstention*

Protocol `research/bridge_partition/CANDIDATE3_FROZEN_NEW_DRUGBANK_ECONOMIC_ABSTENTION_PROTOCOL.md` was committed at `bcf47876d6b3e401224b7f5d51a4cdd2735dc7ef` **BEFORE** original `DrugBank.nt` source from the official 2026 LargeRDFBench ZIP or any query output was inspected.

Source ZIP fixed official archive MD5 `d3b1dcedf94af4114d7a75f8f0fa141b`; original full `DrugBank.nt` uncompressed **150,431,510 bytes**, SHA256 `5be1e9091bcb51d27124047aaa3facfc089973904a9496d160bdd44d2448c056`. The original archive contains **766,920 RDF N-Triples input lines**, but Oxigraph stores **517,023 unique RDF triples** due duplicate original source assertions; these numbers must **NOT** be conflated in claims about cost or capacity. Actual migration transfers original raw asserted line bytes including duplicates, a physical protocol overhead (deduplicated optimized movement could be cheaper).

Precommitted 125 deterministic original-subject predicate cooccurrence query families, split **78 train / 21 calibration / 26 test**, with zero identical pattern/test overlaps. The original SPARQL SELECT query strings were not altered during evaluation. Test query workload is **synthetic derived from a fully original real RDF graph**, NOT organic user/SPARQL dated logs.

**Verified live full four-TCP-Oxigraph-worker CI:** https://github.com/AiDevnew168/scale_rag/actions/runs/44881297995

The single bounded balanced move was picked from training ONLY (swap `chemicalIupacName` and `interactionDrug1` predicates); originally proposed **3,432,609 bytes**, actual physical/index migration wall barrier **88.9393ms**. Calibration was 42 paired observations from 21 independent query families with all original SPARQL answers semantically valid; observed p95 was **156.9998ms (static) vs 166.4187ms (candidate)**. Bootstrap 95% calibration NET prospective interval was **[-198.2034,+112.3073]ms**, lower bound NOT positive. Under the FROZEN admission rule (95% LCB>0, 100% semantic legal, p95 action <=1.01*static), **decision = NO_MOVE**, written to `DECISION_LOCKED_BEFORE_TEST.json` before test. No future query labels used for policy.

After this immutably frozen decision, the physically built moved candidate was evaluated **counterfactually**, on 26 disjoint unseen query families with 3 repetitions each. All **78/78 original full SPARQL outputs were semantically valid** both fixed and moved, with family-bootstrap net moved **-114.3495ms**, CI95 **[-162.1873,-72.6477]ms** after full real index barrier. Hence the **previously frozen no-move gate avoided a confidently negative speculative move** on a new real RDF corpus. Actual selected policy net vs no-move = 0 by definition; do not misreport the counterfactual loss as realized profit. Existing no-move baseline ties the selected policy economically.

**Limitation:** this is a *single* new synthetic query distribution derived from a genuine source graph; bootstrap intervals assume family exchangeability and do not certify natural workload drift or monetary profitability. No true cross-host execution, faithful published prior art method comparison on same original graph/storage/engine, nor actual independent chronological user queries. Does not prove journal novelty or SOTA superiority.

Together with NYT, these two complete-original-real-RDF tests show **the naive move frequently loses economic net benefit**, while a conservative pretest calibrated no-move admission can correctly reject the loss on the unseen DrugBank corpus. This is useful limited empirical evidence for abstention, not a universal risk guarantee.
