# Candidate 3: genuine physical SWDF benchmark, independent source eligibility and prior-art build audit

**Date:** 2026-11-21  
**Scope:** This is an executed methods/economic *FAIL-or-PASS* report, not a draft asserting novelty.  
**Source-locked preregistration:** `research/bridge_partition/CANDIDATE3_PROSPECTIVE_3RD_PARTY_SPARQL_PRECOMMIT.md` (committed before the FEASIBLE original SWDF query outcomes were examined).

## 1. Genuine independent RDF+SPARQL workload source

DICE FEASIBLE's complete `SWDF-CleanQueries.txt` (real endpoint-log-derived queries, but query timestamps not provided) was fetched and SHA-pinned. Corresponding **complete**, original FEASIBLE SWDF `swdf.nt` RDF source was fetched from the authors' Google Drive archive and validated by SHA256.

- Original SWDF RDF ZIP SHA256: `65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb`
- Original uncompressed RDF SHA256: `97575d036db4e55fa89f25231d3afb2c427555bce4a60fc429f902ddf7c45400`
- Query file SHA256: `7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3`
- Source-encoding caveat: 4,188 lines in 61MB graph were invalid UTF-8 and re-decoded as Latin-1 for Oxigraph input. Full transformed graph audit written in CI. No silent data omission was allowed.
- Central Oxigraph loaded **304,592 distinct triples**, fully indexed in a separate full-graph control store.
- Four independent Oxigraph TCP worker processes physically loaded the original triple fragments, each capped at **16,806,061 raw bytes**, before moving or copying data.
- Holdout has **102 exact-text-unique SPARQL SELECT queries** in **34 distinct predicate-pattern families**, completely disjoint by family from training and calibration, with 101 centrally nonempty query results. Original query strings are evaluated unchanged.
- Only BGP-like subset with static predicates, no SERVICE or named graph/OPTIONAL/FILTER/UNION etc., was admitted by the earlier fixed `rdflib==7.5.0` algebra contract.
- The historical SWDF graph dump version's exact match to the original query event timestamps is **NOT verified**, so no causal temporal-drift effectiveness is claimed.

Pinned source audit: https://github.com/AiDevnew168/scale_rag/actions/runs/44874154118

## 2. Actual physical four-worker migration, replication and query execution — FAIL correctness

Four stored placements were physically materialized with Oxigraph index updates, TCP traffic, and a query barrier (no concurrent user queries). Their original RDF move cost and wall time are measured, not assumed:

| Action | Actual migrated / replicated raw bytes | Measured local barrier + index milliseconds | Pairwise original SELECT exactness | Raw net economic claim |
|---|---:|---:|---|---|
| 1-swap | 670,057 | 25.721 | **FAIL** 42/202 query-run errors | NOT VALID |
| 2-swap greedy | 2,003,790 | 76.584 | **FAIL** 44/202 query-run errors | NOT VALID |
| 1 replica | 314,196 | 11.130 | **FAIL** 44/202 query-run errors | NOT VALID |
| 1 swap + 1 replica | 984,253 | 36.365 | **FAIL** 42/202 query-run errors | NOT VALID |

The initial implementation used per-worker SPARQL `CONSTRUCT` of requested predicate fragments, then the coordinator fully executed unchanged original SELECT against those fragments. Source-correctness failures affected many `LIMIT` without `ORDER BY` queries; we do NOT silently discard their failed exactness even though some differing `LIMIT` outputs are allowed by unordered SPARQL semantics. One source query exceeded the fixed 20,000 result-row verification cap and remains a documented failure.

The measured-only calibration admission controller correctly chose **no migration**, because all candidates had query mismatch/errors; a successful abstention is NOT a proof of deployment profit.

Runs:
- https://github.com/AiDevnew168/scale_rag/actions/runs/44874462942 (physical execution, detailed payload/latency/exactness)
- https://github.com/AiDevnew168/scale_rag/actions/runs/44874739992 (calibration-only admission, rejected all)
- https://github.com/AiDevnew168/scale_rag/actions/runs/44874924307 (failure-shape audit)
- https://github.com/AiDevnew168/scale_rag/actions/runs/44875050080 (unordered LIMIT diagnostic on calibration only).

## 3. Isolated physical data-level failure: blank nodes

Independent **calibration-only** source-predicate checks were run against original source bytes and actual queried fragments from all four policies. **33/37 predicates matched** exactly at normalized RDF-term level, but the same four failed under *every* placement. Exactly those four contained **RDF blank nodes**. This strongly implicates loss/freshening of globally scoped blank-node identity across separately indexed worker stores; it is not evidence that the swap itself caused these errors.

https://github.com/AiDevnew168/scale_rag/actions/runs/44876142868

A different worker materializer now serves **unchanged original RDF N-Triples bytes per indexed predicate**, while retaining real 4-process Oxigraph indexes for inserts/deletions. This preserves the source's blank-node labels at the network boundary; the original full SELECT still runs in the coordinator. The correction, by definition, changes from worker-side `CONSTRUCT` to direct raw-fragment access; it is still a genuine physical distributed storage and central full-SPARQL query engine, **not a native distributed join optimizer**.

Source code: `candidate3_source_identity_worker.py`, `candidate3_swdf_source_identity_economics.py`. Corresponding workflow: `.github/workflows/candidate3_swdf_source_identity_economics.yml`.

**Important:** this repair is a methodological regression on **previously opened** holdout queries, so even 100% success after the repair would NOT constitute a new prospective confirmatory novelty result. Do not update the historical frozen failure report to claim it passed.

## 4. Independent 2014 log with genuine timestamps: strict eligibility STOP

The independent AKSW/LSQ repository's `combined.swdf.log` is an actual dated May 16 2014 server HTTP-log test fixture, but is NOT the full historical log (2,007 lines total). Original file SHA256: `063805ee1d1d80ead68fc1c7d369fadf5a5810b9a61e0d2ac49a70b8db52b3de`.

Under the predeclared static-predicate BGP SELECT 2–6-triple eligibility filter, only **4 occurrences, 3 unique texts and 3 predicate-pattern families** survive. Thus it **FAILS** the >=20 unique heldout and >=5 nonempty tests required for credible economic study. Furthermore no verified matching 2014 RDF snapshot exists.

https://github.com/AiDevnew168/scale_rag/actions/runs/44876014244

Other initial public SWDF RDF listing sources had expired SSL certificates from a Github runner; the actual DICE/FEASIBLE full original graph was already separately and successfully acquired. Do not present expired certificates as a permanent absence of SWDF RDF.

## 5. Faithful published baseline source and its actual build

Found official independent 2024 DIAERESIS implementation from the author's repository https://github.com/isl/DIAERESIS at commit `22dfe190078973f644f5d6279181e54ec116f6e3`. A GitHub Actions job checked out this exact commit and ran its original Maven build using Java 8. **BUILD SUCCESS**, produced `DIAERESIS-1.0-SNAPSHOT.jar` (366,237 bytes). Source includes real SWDF benchmark queries and RDF graph references, and runs on Spark/Hadoop.

https://github.com/AiDevnew168/scale_rag/actions/runs/44876436118

**Crucial boundary:** A Maven build is not an execution. DIAERESIS requires a Spark/HDFS topology and its own query translation and RDF partitioning. Its published paper uses a completely different distributed execution architecture and mixed vertical/schema partitioning, so comparing its published numbers to Oxigraph localhost timings is **scientifically invalid**. No faithful same-machine original WISE/WASP/DIAERESIS runtime has yet been run. The strong-prior-art superiority gate is **BLOCKED**, not passed. The original authors' code is now documented and buildable.

## 6. Exact final scientific verdict

- **PASS as physical testbed:** complete RDF source, four independent genuine Oxigraph stores on TCP, physically moved data with byte and wall-time measurement; 102 true query texts and source hashes pin the evidence.
- **FAIL as original full query exactness:** prior eager `CONSTRUCT` worker version had nonmatching or oversized results. Raw identity repair is being tested separately and must be evaluated without claiming new independent test status.
- **PASS on fail-safe policy behavior:** all action candidates were rejected on calibration query errors and real controller correctly abstained. This is not novel or a positive economic performance result.
- **FAIL independent temporal traffic gate:** AKSW LSQ software 2014 sample provides only 3 eligible distinct texts; DICE FEASIBLE SWDF cleansed query source has no reliable event timestamps.
- **PASS upstream baseline build / BLOCKED runtime comparison:** DIAERESIS author source builds, but its real Spark/Hadoop execution has not been run against our system under matched resources, result and budget constraints.
- **NO-GO for claimed top-journal novel algorithm or positive real-world economic superiority** based on currently completed evidence.

The paper-worthy open problem is still accurate positive-net migration/replication admission **under genuinely unpredictable tail/drift**, full correctness, true byte and index costs, matched incumbent code and independently heldout source. We have not proved a general economic improvement.

**Do not retrospectively repurpose any WatDiv, Wikidata 2018 or already-opened SWDF test labels as independent confirmation.**

## 7. Completed raw-source fragment identity correction — 2026-11-21

The physical bugfix **finished** (CI success for execution, **NOT** paper criteria):
https://github.com/AiDevnew168/scale_rag/actions/runs/44876361186

Using the original unmodified `swdf.nt` N-Triples fragment bytes at the TCP worker boundary, every one of the **37/37 calibration-relevant predicate source fragments matched byte-for-byte** for each of the five policies. This includes the four blank-node-bearing predicates that previously mismatched with independently reminted SPARQL `CONSTRUCT` output.

All four workers still owned real separate Oxigraph indexes and served via HTTP TCP; inserts and deletes altered both indexed data and raw fragment inventory. The coordinator still ran each **original unmodified full SELECT** with Oxigraph. A method-local replica identity check was corrected so duplicate full copies are individually compared, not concatenated.

**Original full-query exact multiset correctness still FAILS** in the already-opened heldout (102 textual queries ×2 repeats, with one central query above 20k row guard, so 202 evaluated pairs). Per-policy equality of **both** baseline and action responses with centralized original full SELECT was:

| Method | Exact full-answer paired observations / 202 | Exactness gate | Actual moved N-Triples bytes | Real move+index wall time (ms) | Total N-Triples bytes saved (in tested requests) | Extra shard contacts saved |
|---|---:|---|---:|---:|---:|---:|
| no move | 182 | FAIL | 0 | 0 | 0 | 0 |
| one swap | 180 | FAIL | 670,057 | 27.1582 | 0 | 0 |
| two-swap greedy | 178 | FAIL | 2,003,790 | 82.9694 | 0 | -42 |
| one replica | 185 | FAIL | 314,196 | 16.9808 | 0 | 0 |
| swap+replica | 183 | FAIL | 984,253 | 41.5713 | 0 | 0 |

These remaining exact-multiset divergences may include **legally nondeterministic SPARQL `LIMIT` without `ORDER BY`**, not necessarily false answers; a calibration-only diagnostic previously showed some such divergences disappear with a *modified ordered query*. It would be improper to use an ORDER BY rewriting as proof of original-query equivalence. Other causes cannot yet be excluded. The previously opened SWDF heldout cannot become an independent confirmatory test by rerunning after this correction.

**Net realized positive economic benefit is NOT CERTIFIED for any policy** because the original full-output strict correctness gate failed, and even physical source-fragment identity success does not establish distributed query correctness. No correct-answer economic superiority over actual WISE/WASP/DIAERESIS was established. The strongest incumbent source (DIAERESIS) was **successfully built** in run 44876436118, but has not been faithfully executed against matched source under Spark/HDFS.

The *independent chronological* AKSW/LSQ 2014 SWDF sample was also separately audited: its 2,007 HTTP records yielded only **4 strict-eligible original SELECT occurrences / 3 unique query texts**. It is a test fixture, not a sufficient independent time-series cohort. Run: https://github.com/AiDevnew168/scale_rag/actions/runs/44876014244.

**Final decision for this gate: SYSTEM ENGINEERING PARTIAL PASS (full source, four physical indexed workers, migration measurement, 37/37 calibration fragment fidelity); CONFIRMATORY PAPER/PROFIT GATE FAIL/BLOCKED (strict full original SELECT exactness, matched published runtime, independent temporal sample, and net real economic superiority).**

The next scientifically necessary change is a SPARQL-semantic-validity evaluator for unordered `LIMIT` and proper blank-node isomorphism on full answers **fixed before accessing a genuinely new heldout**, plus strong equal-resource Spark/Hadoop counterpart or an equivalently faithful runnable contemporary baseline and true cross-host measurements. No source re-labeling, score-based exclusion, or test-driven tuning may be presented as fresh confirmation.
