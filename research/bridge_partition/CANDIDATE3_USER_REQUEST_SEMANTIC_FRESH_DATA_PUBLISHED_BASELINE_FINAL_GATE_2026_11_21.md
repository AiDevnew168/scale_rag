# Candidate 3 — Requested semantic SPARQL + fresh physical RDF + authentic published baseline gate

**Evidence cut 2026-11-21.** Research decision: **SPARQL semantic checker PASS on audited scope; physically deployed real RDF test PASS for engineering execution, FAIL positive net savings; original published baseline executable PASS but answer-count equivalence FAIL 1/3; full SOTA economic superiority NOT established.** Green Actions runs do NOT imply journal novelty or financial GO.

## 1. Separate original SPARQL SELECT semantic certifier

The source-locked contract `CANDIDATE3_FROZEN_SPARQL_SEMANTIC_VALIDITY_CONTRACT_2026_11_21.md` was written before this additional validator code, at commit `4fc0b983885c4cbef2af5724a082bbb19a29d084`. Independent new checker `candidate3_sparql_semantic_validity.py`, adversarial tests `test_candidate3_sparql_semantic_validity.py`, 15/15 pass:
https://github.com/AiDevnew168/scale_rag/actions/runs/44904410988

- Unordered original SELECT LIMIT/OFFSET: check valid cardinality and true submultiset of **unsliced full** authoritative answers; preserve unchanged original query for real execution.
- Plain full SELECT: unordered *bag* equality, not arbitrary row ordering. Literal lexical value, language and datatype, URI vs literal, unbound binding and variable names preserved.
- Global injective blank-node alpha-renaming across all response rows, not a per-row mapping. Fail closed under search resource cap.
- Ordered SELECT with ambiguous ties: original comparator declines certification without an externally proved deterministic order; no false PASS.
- The new validator uses a conservative lexical LIMIT/OFFSET tail check, and **must not replace the stronger algebra-checked W3C oracle** for article claims; e.g. string lexical edge cases may conservatively block valid queries.
- For article evidence use the earlier independently built algebra-aware `candidate3_sparql_semantic_oracle.py` + `candidate3_sparql_semantic_certifier.py` on branch `research/candidate3-same-source-published-baseline-20261121`. W3C-safe tests **19/19** https://github.com/AiDevnew168/scale_rag/actions/runs/44900322130; two independently authored certifiers agreed on **168/168 decisions** across real 4-Oxigraph TCP stores and 84 original SWDF calibration SELECTs in both fixed and moved layouts: https://github.com/AiDevnew168/scale_rag/actions/runs/44900210370 .
- Original bug root cause included worker `CONSTRUCT` reminting Blank Node identities and coordinator `Store.bulk_load` on partial source breaking a 3-BGP bnode join. Source-preserving raw N-Triples and `Store.load` resolved **84/84 SWDF calibration correctness**, in no-move, moved, replica and hybrid: https://github.com/AiDevnew168/scale_rag/actions/runs/44880920149 . This is previously opened CALIBRATION, not fresh unseen future.

## 2. Frozen fresh original real RDF datasets and measured physical economics

The 2026 LargeRDFBench original NYT and DrugBank complete graph test protocols were committed before original source evaluation; queries derived from graph structure are *synthetic*, **not real dated organic user SPARQL logs**.

| Third-party full original RDF | Physical 4 independent localhost TCP Oxigraph stores | Original SELECT full semantic checks | Actual migration bytes and index barrier | Measured new heldout paired net vs fixed, including move | Conservative admission |
|---|---|---|---|---|---|
| NYT 335,197 unique triples | YES | 81/81 | 1,683,926 bytes; 70.8354 ms | **-102.1695 ms**, CI95 [-165.2826,-38.3892] ms | old move loses |
| DrugBank 517,023 unique triples / 766,920 raw NTriples lines | YES | 78/78 | 3,432,609 bytes; 88.9393 ms | moved counterfactual **-114.3495 ms**, CI95 [-162.1873,-72.6477] ms | **NO MOVE was frozen before test**, selected net vs fixed 0 |

NYT run https://github.com/AiDevnew168/scale_rag/actions/runs/44880717063 .
DrugBank run https://github.com/AiDevnew168/scale_rag/actions/runs/44881297995 .

These are **new authentic graph sources**, though not authenticated aligned original real-user time series. No actual cross-host network or monetized operational savings. Two negative counterfactuals are preserved as failures, not tuned away. The DrugBank no-move avoids harm but does not outperform no-move control.

## 3. Executed original PUBLISHED baseline — not just compiled

Author `isl/DIAERESIS` SHA `22dfe190078973f644f5d6279181e54ec116f6e3`, unmodified code, genuine original DAP partition, original QueryTranslator and original Spark/Hadoop QueryProcessor. Builds and executes all three stages, with Spark 3.1.1 Java8 on local two-core runtime and Hadoop FsShell over file URI; it is **not** a 4-host HDFS cluster.

- Original full author pipeline execution https://github.com/AiDevnew168/scale_rag/actions/runs/44881159983 .
- Full author original stage execution and central plus physical 4-TCP-shard Oxigraph on the **SAME transparent normalized original 304,583 NTriples lines** and **same three unchanged author-original queries**, successful CI https://github.com/AiDevnew168/scale_rag/actions/runs/44900610242 .
- Common original graph normalization fixed 28 illegal replacement glyphs in RDF IRIs across 27 lines in both engines; it changes raw source bytes and is clearly disclosed. Common normalized source SHA256 `ea2b8ac2e06bdf6f6d8aa2f64178dfb02fe9fb6a32343e2bde63f133c74bf034`. Did NOT delete any input assertion.
- 279 original query files, four met strict predeclared URI-predicate static-BGP common execution contract. The lexical first THREE were executed unchanged. The original author Spark query outputs expose row count, not full RDF binding multisets, limiting interop correctness guarantee.
- Author `query101.txt` output count=1, central Oxigraph count=1, 4-worker original SELECT answer semantic PASS.
- Author `query118.txt` output count=11,112, central Oxigraph count=11,114, 4-worker semantic PASS for central 11,114. **COUNT MISMATCH, no LIMIT, NOT legally arbitrary LIMIT behavior.**
- Author `query35.txt` output count=1092, central count=1092, 4-worker semantic PASS.
- Original query118 source forensic https://github.com/AiDevnew168/scale_rag/actions/runs/44900984321 established full original input contains 11,114 distinct subject `rdf:type foaf:Person` assertions with ZERO duplicate subjects; only one corresponding line was affected by normalization. No deletion or query rewriting was done to force equivalence. The missing two inside author pipeline remain unexplained.
- Original author reported query stage times [142,77,1742]ms vs physical 4-worker Oxigraph means [21.0595,53.1768,51.7502]ms on 3 queries; **not meaningfully comparable** as query engines and partition strategies do not share optimizer, performance measurement definitions or replication/migration objective. No credible ratio is stated.
- The source WISE/WASP/AdPart matching runtime remains unavailable; **DIAERESIS is one legitimate published implementation, not SOTA exhaustive coverage**.

## 4. Final exact GO/NO-GO

- Correct W3C conservative solution-bag and blank-node semantics on supported original SELECT: **PASS 19 adversarial tests; 84/84 two physical placements × independent evaluator**.
- Physical source preserving correction and four real independent indexed TCP Oxigraph workers: **PASS engineering, not multi-host cluster**.
- Authentic previously unseen RDF graphs with original full SPARQL query correctness: **PASS for synthetic graph-derived query families on NYT and DrugBank**.
- Positive net economic advantage after real migration: **FAIL observed moved counterfactuals**, safe abstention successful once on DrugBank but no positive gain vs no-move.
- Original published competitor genuine DAP->translator->processor same-source execution: **PASS**; author exact count correctness vs central: **FAIL 1 of 3 queries**.
- Statistically powered independent natural chronological workload+match exact RDF snapshot: **BLOCKED**.
- Strongest paper-worthy WISE/WASP multi-host apples-to-apples runtime superiority and genuine paid/economic savings: **NOT ESTABLISHED**.

**Scientific conclusion: no honest evidence yet that the proposed method is a novel stronger-than-published algorithm with positive monetary net benefit.** Stop tuning known 2018 or WatDiv test labels. Any further full-paper GO must use precommitted new genuine real time series, aligned RDF, exact semantic gate for all queries and a faithful incumbent at matched resources.
