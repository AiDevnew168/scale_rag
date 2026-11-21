# Candidate 3 final external semantic-certification and authentic-baseline reproducibility gate

**Date:** 2026-11-21  
**Release branch:** `research/candidate3-same-source-published-baseline-20261121`  
**Decision discipline:** successful GitHub CI != paper-level superiority. No frozen future oracle result is a deployable policy. Previously examined SWDF calibration queries are engineering regression, NOT independent new scientific data.

## A. SPARQL validity oracle fixed without altering timed original query

New independent implementation `candidate3_sparql_semantic_oracle.py`, adversarial tests `test_candidate3_sparql_semantic_oracle.py`. The W3C-conservative policy:
- Preserves RDF URI vs literal datatype/language/lexical identity and solution **BAG multiplicity**.
- Preserves one **global injective Blank Node mapping** across all SELECT result rows and variables using RDF graph isomorphism for full bags and exact budgeted matching for limited subbags; 19 adversarial tests.
- For `LIMIT` without `ORDER BY`, a candidate original SELECT result must have proper cardinality and be a legal *subbag of the separately evaluated full unsliced centralized query*, with consistent Blank Node mapping. The original timed query remains unchanged.
- Nested LIMIT, ambiguous ordered LIMIT, REDUCED and unsupported query forms are BLOCKED, never falsely PASS. Large combinatorial searches are also BLOCKED rather than guessed.
- Original underlying materialization must use `Store.load` for cross-predicate source Blank Node joins; an old use of `Store.bulk_load` on a partial graph was observed to break a 3-BGP join despite identical graph lines.

Completed adversarial CI:
https://github.com/AiDevnew168/scale_rag/actions/runs/44900322130 (19/19 PASS).

Independent REAL physical four-Oxigraph-TCP-worker same-original-SPARQL validation:
https://github.com/AiDevnew168/scale_rag/actions/runs/44900210370

| SWDF calibration placement | Earlier separately implemented certifier | Independent RDF-isomorphism certifier | Disagreements |
|---|---:|---:|---:|
| Physical original no move | 84/84 PASS | 84/84 PASS | 0 |
| Physical balanced single migration (670,057 original bytes) | 84/84 PASS | 84/84 PASS | 0 |

**168/168 paired verdicts agree**. These are 84 previously inspected SWDF calibration queries in 2 physical placements, not 168 independent organic requests or a conformance test of all SPARQL constructs. No paper economic SOTA claim follows.

## B. Truly new original RDF sources: prospective safety and negative economics, NOT positive dominance

The earlier frozen protocols and original CI reports on separate 2026 real RDF datasets:
- Official LargeRDFBench NYT: 335,197 distinct Oxigraph triples, 27 original-RDF graph-derived test query families, 81/81 original SPARQL response checks, physically moved 1,683,926 raw bytes in four actual indexed TCP stores. Measured paired economic *loss* after migration **-102.1695 ms**, family bootstrap CI95 **[-165.2826,-38.3892] ms**. CI https://github.com/AiDevnew168/scale_rag/actions/runs/44880717063.
- Official LargeRDFBench DrugBank: 766,920 original asserted N-Triples **lines** but 517,023 **unique** indexed triples; 26 heldout query families, 78/78 original SELECT checks. Calibration-only 95% LCB was nonpositive and p95 harmed, so frozen decision was **NO MOVE before test**. After freezing, physical counterfactual migration 3,432,609 raw bytes at 88.9393ms was evaluated and lost **-114.3495ms** on heldout with 95% family-bootstrap **[-162.1873,-72.6477] ms**. Successful abstention avoided a harmful move; actual selected savings vs no-move is **zero**, NOT +114ms profit. CI https://github.com/AiDevnew168/scale_rag/actions/runs/44881297995.

Both are authentic **complete third-party RDF graphs** but their experimental query families are generated from those graphs, not independently observed original human/SPARQL organic time series. There is still no valid separate real-world workload-shift guarantee, cross-host economic measurement, or direct superiority over WISE/WASP/DIAERESIS.

## C. Faithful published source baseline and source compatibility preflight

Published author repository: https://github.com/isl/DIAERESIS (SHA `22dfe190078973f644f5d6279181e54ec116f6e3`), complete unmodified DAP partitioning → original QueryTranslator → original Spark QueryProcessor already demonstrated real execution (not merely compile):
https://github.com/AiDevnew168/scale_rag/actions/runs/44881159983

Only 4 of the 279 author query files met the predeclared constant-URI-BGP source-compatibility filter without unsupported dynamic predicates, so the lexically first 3 were executed; their 3 original SQL-stage timing fields are **not a statistically adequate head-to-head benchmark**.

Original author SWDF ZIP: https://users.ics.forth.gr/~kondylak/SWJ/swdf.zip
SHA256 `c1787940fbffab1b92e61bb338707bc11d2575931fefd15cabc78f88c00654de`.

An earlier attempt to execute Oxigraph directly on original author unnormalized `clean_swdf.nt` failed strictly at line 29,974 because the original graph includes invalid replacement glyph inside RDF IRIs, while author's Spark loader tolerated it. We did **NOT** silently drop these triples or pretend direct source bytes are valid SPARQL graph.

To make an exactly **same normalized source** compare possible, the deterministic documented conversion encoded replacement glyph U+FFFD in IRI brackets as `%EF%BF%BD` on precisely **27 lines / 28 glyphs**, leaving all source N-Triples line records. Original raw SHA256 `662e93b311eb93f91741b910bd427bf6179e3c66706f41e20bf46b4b620733cb`, 51,587,578 bytes, 304,583 original NTriples lines. Normalized SHA256 `ea2b8ac2e06bdf6f6d8aa2f64178dfb02fe9fb6a32343e2bde63f133c74bf034`, 51,587,758 bytes, all **304,583 strict Oxigraph triples** loaded. Source eligibility CI success:
https://github.com/AiDevnew168/scale_rag/actions/runs/44900442274

The **original published Scala source is not modified**; both Spark DAP and Oxigraph must consume the exact same normalized generated file in the next full pipeline. The normalization is a transparent **testbench transformation**, NOT a claim of original raw-source semantic identity.

Our comparison script `candidate3_diaeresis_same_source_oxigraph_check.py` is scoped to full original SELECT on author source; DIAERESIS author emits **row counts**, so equality can only be established for counts, not its entire solution binding multiset. It is an engineering interoperability check, not full paper-level equivalent benchmark.

Prior original author comparison failed twice on mundane startup issues (missing gdown then strict N-Triples-invalid RDF), retained as failures. Pre-normalized full published pipeline itself passed. The normalized same-source run is required to establish any actual same-source overlap; do not cite source-normalization preflight as author baseline success.

## D. Prior-art inspection and scientific GO

Original AdPart author source https://github.com/razen-alharbi/AdPart exists and is a genuinely relevant workload-adaptive RDF competitor, but needs legacy MPI/Qt multiworker environment and has NOT been executed in an equivalent source/hardware setup. The GitHub repository `GraphPartitioning/WISE` concerns vertex-cut graph partitioning, NOT the RDF WISE paper; do not mislabel it as that baseline. WISE RDF (2020) and WASP RDF (2021) are not executable in our current matched testbed. DIAERESIS only constitutes one original published contender, not comprehensive SOTA coverage.

| Gate | Current status |
|---|---|
| Conservative W3C original SELECT semantic oracle with bnode global identity, LIMIT legal subbags | **PASS (19 tests, 84/84 real queries ×2)** |
| Correct RDF source fragment assembly on 4 independent indexed TCP workers | **PASS within audited supported subset** |
| At least two new real third-party RDF datasets with measured physical movement and correctness | **PASS**, but graph-generated synthetic request families |
| Pretest admission avoids harmful migration on unseen DrugBank | **PASS conditional to given 1 scenario**; realized economic improvement vs zero-move is zero |
| Matched published implementation same input, same original queries and source | **BLOCKED until exact full common-graph test completes** |
| Fair matched published baseline net economic superiority on statistically powered real chronological user traffic | **NOT ESTABLISHED** |
| Cross-host full distributed E2E, crash-consistent migration, realistic network and dollars | **NOT ESTABLISHED** |
| Top-journal novelty and economic superiority | **NO-GO ON CURRENT EVIDENCE** |

Do not use future labels to tune any threshold, rebrand already opened samples as prospective, or claim original DIAERESIS raw RDF is byte-identical after normalization. Any actual future confirmed result must preserve all source identifiers, refusal counts and journal gate blockers.
