# Candidate 3: exact novelty-risk frontier + new official WatDiv10M byte-weighted stress benchmark
**Date:** 2026-11-21  
**Repo/branch:** `AiDevnew168/scale_rag`, `research/candidate3-oracle-risk-feasibility-20261121`  
**Scope and decision:** Preserve successful chronological Wikidata touch-locality findings; construct a second structurally-disjoint workload feasibility test with **real N-Triples byte weights**; do NOT claim novel algorithms or production economic profitability.

## A. Complete 5,400-swap oracle frontier on previously opened genuine Wikidata query logs

Verified: https://github.com/AiDevnew168/scale_rag/actions/runs/44869028533

Train June 2017, evaluate January/February/March 2018; exactly four partitions of 30 predicate IDs each. Every balanced two-predicate swap exhaustively scored (5,400). An oracle may read future *only to compute the maximum achievable score for the declared action class*: it is NOT a deployable policy or independent paper test. "Novel" = predicate combination absent from June training.

| Month | Frozen day0 policy future extra touches saved | Best hindsight with both future novel aggregate metrics nondecreasing | Best hindsight also with positive day0 observed local gain | Feasible joint-safe alternative with >=90% best day0 gain |
|---|---:|---:|---:|---|
| Jan 2018 | 8,688 | 4,264 | 4,083 | **none** |
| Feb 2018 | 8,898 | 1,806 | 1,806 | **none** |
| Mar 2018 | 10,315 | 7,014 | 2,582 | **none** |
| **Pooled** | **27,901** | **13,084 (46.89%)** | **8,471 (30.36%)** | **none** |

"Joint safe" requires **future novel distinct patterns with one-shard locality count >= unchanged baseline** AND **future novel request occurrences with total extra-shard touches <= unchanged baseline**; it does not imply every individual query improves. The absence of >=90% day0 head preservation is an exhaustive empirical INFEASIBILITY CERTIFICATE only for that fixed 1-swap, four equal-ID-shards search space and these three inspected workloads. It does not imply no 2-swap, replication or byte-aware solution exists.

A general trivial witness rules out *universal* no-harm for arbitrary possible future queries under any nontrivial 1-swap: exchange predicate `i` in shard A with `j` in B, choose `z` still in A; pair query `{i,z}` increases shard count 1->2. This is not a publishable new theorem by itself.

## B. Authentic third-family benchmark: University of Waterloo WatDiv original data

Official sources: https://dsg.uwaterloo.ca/watdiv/ , https://dsg.uwaterloo.ca/watdiv/watdiv.10M.tar.bz2 , https://dsg.uwaterloo.ca/watdiv/stress-workloads.tar.gz
Source SHA256:
- graph BZip2: `1d0a8a4725c98974eb7347ce3e6d9cab44f9f40389589809674254151b745af6`
- stress workloads GZip: `98796d4c8db67a1f68b3d1958d8f1334d5d38fe6da1c5e8eae72a8823ac7eed5`

Source preflight: https://github.com/AiDevnew168/scale_rag/actions/runs/44869313918  
Full original byte scan: https://github.com/AiDevnew168/scale_rag/actions/runs/44869433164

We streamed the entire genuine official WatDiv 10M RDF N-Triples dump (10,916,457 triple lines, 1,542,624,409 uncompressed bytes, 86 predicates), not a 5KB toy sample. Largest predicates `friendOf` ≈650,207,861 bytes and `follows` ≈472,918,766 bytes require fragmentation if there are 4 byte-capped shards. An analytical greedy fragmentation model with 10% capacity ceiling gives per-shard raw bytes [424,221,713; 347,087,200; 424,221,713; 347,093,783], cap 424,221,713, and 2 fragmented predicates. **Actual RDF triple fragments were NOT materialized on four servers**. Thus byte weights and theoretical cap are grounded but real index sizes / physical migration remain unknown.

Official `watdiv-stress-100` workloads contain 12,400 one-line SELECT queries per named file; 12,100 qualify for the strict >=2 known-predicate structural trace filter. Crucial identity audit: **all 12,100 eligible queries in each of nominal test.1..test.5 files are exact text duplicates of warmup eligible queries**. The intended "five separate test files" therefore yield ZERO independent exact-text holdout queries. We rejected this invalid evaluation, recorded it, and built a different cross-pattern test. Do not cite the zero-size test files as independent validation.

## C. Five strict pattern-family disjoint folds with real official graph bytes

Verified successful execution: https://github.com/AiDevnew168/scale_rag/actions/runs/44869561656
Source: `research/bridge_partition/candidate3_official_watdiv_pattern_folds.py`. The 12,100 eligible warmup question occurrences contain 4,076 distinct exact query texts and **121 distinct predicate-set combinations**. A deterministic SHA256-hashed grouping by *complete predicate-set identity* creates 5 folds: in each, 4/5 pattern families are train-only, 1/5 test-only. **No exact text OR predicate-set family appears on both sides**. Each of the 121 distinct families is held out exactly once across folds; however these are synthetic generated variations from *the same corpus*, NOT five independent domains or chronological workloads.

Frozen work: four byte-weighted shards, proposed 1-swap must preserve raw-byte upper capacity; training-only objectives max observed local, max observed extra-touch savings, or gain-per-byte. The baseline is a simple workload-free byte placement, NOT full WISE or WASP.

| Heldout fold | Test occurrences | Locality/touch-maximizing swap touches saved | Gain-per-byte swap touches saved | Cross-family overlap |
|---|---:|---:|---:|---|
| 0 | 2,500 | 0 | 100 | 0 |
| 1 | 2,400 | 100 | 100 | 0 |
| 2 | 2,400 | 200 | 0 | 0 |
| 3 | 2,400 | 400 | 0 | 0 |
| 4 | 2,400 | 100 | 0 | 0 |
| **Total** | **12,100** | **800** | **200** | **0** |

Max-total policy: positive in 4/5 folds, 1 zero, no negative. Pattern-cluster bootstrap 95% *descriptive* interval for total touch savings [300,1400]; **NOT** cross-domain or causally guaranteed confidence. Moved serialized predicate bytes over five *separate hypothetical* fold deployments: 46,146,651; for byte-normalized policy 225,555 bytes. Thus per-byte efficiency is ≈51.15 times larger for the cheaper policy, despite lower total saved touches. These are predicted payload bytes from physically read predicate counts, not confirmed moved indexed RDF payloads.

## D. Training-only, no-migration-admitting **conditional** economic analysis

Code `research/bridge_partition/candidate3_byte_economic_envelope.py`
CI: https://github.com/AiDevnew168/scale_rag/actions/runs/44869742312
Consumes the **frozen** 5fold JSON artifact from run 44869561656 / artifact 14693710835; no new heldout-prompt tuning or relabeling. Pre-assumed fixed forecast horizon H=2,400 future queries/fold. Training-only admission chooses best *predicted net* among no migration, head, or small-gain-per-byte:

`predicted_net_ms = (training_touches_saved/training_query_count)*2400 * assumed_serial_ms_per_saved_touch - migrated_raw_bytes*8/(1000*bandwidth_Mbps)`.

No network RTT, sync, index or disk overhead. This is **conditional ideal transport**, not measured SPARQL or money. Scenario grid was generated AFTER inspecting the benchmark; exploratory sensitivity not preregistration.

| Assumed critical path saved / touch | Assumed bandwidth | Training-only admission across 5 folds | Conditional realized aggregate net ms | Pattern-family bootstrap 95% conditional net, ms |
|---|---|---|---:|---|
| 1 ms | 100 Mbps | 5 cheap moves | +181.9556 | **[-18.0444, +481.9556]** |
| 1 ms | 1000 Mbps | 4 head + 1 cheap | +108.0266 | **[-191.9734, +508.0266]** |
| 5 ms | 100 Mbps | mixed head / cheap | **-1147.7358** | **[-2147.7358, +352.2642]** |
| 5 ms | 1000 Mbps | 5 head moves | +3630.8268 | **[+1130.8268, +6630.8268]** |
| 20 ms | 100 Mbps | 5 head moves | +12308.2679 | **[+2308.2679, +24308.2679]** |

The conditional sign flips across scenario assumptions; a pre-trained admission policy can LOSE money versus no migration at 5 ms and 100 Mbps, even though it predicted net positive from training. Hence a universal economic claim would be unjustified.

For a single 100Mbps one-shot run across all 5 hypothetical fold deployments, 46,146,651 moved bytes take >=3691.73 ms at ideal line rate. With 800 heldout touches saved, amortization requires >=4.615 **serial critical-path milliseconds** per avoided touch, even before storage/index and synchronization overhead. For the cheap policy, 225,555 bytes cost ideal 18.0444 ms / 200 saved touches => >=0.09022 ms/touch; but 3 of the 5 disjoint folds had zero savings, demonstrating risk.

## E. What the evidence proves / does not prove

**Supported:** (1) prior historical Wikidata >1M query trace shows repeatable single-swap locality benefit; (2) full 5,400-swap oracle establishes strict head/tail tradeoff in one-swap space; (3) true independent WatDiv 10M predicate-byte measurements and 121 heldout distinct pattern-family CV show modest positive locality transfer with zero exact pattern leakage; (4) there is a large observed tradeoff between absolute touch gain and physical-byte migration burden.

**NOT supported:** unique new algorithm; strict novel query protection; net economic gain in a real production RDF graph, QA or RAG system; true SPARQL performance on full WatDiv10M; equal-memory replication/WASP/WISE dominance; universal throughput/P95 benefit; confidence across independently collected user workload distributions.

**Research decision:** the candidate is still an attractive *concrete* systems research problem, not yet a validated journal invention. A credible next step must use source-matched RDF, true query execution and measured migration-index costs, compare against strong existing partitioning/replication baselines at equal byte capacity, use a new preregistered workload, and show positive net benefit *in realistic parallel mode*. Avoid further post-hoc tuning of already inspected Jan-Mar and WatDiv folds without an independent test.

## Reproducibility references

- `research/bridge_partition/candidate3_exhaustive_oracle_risk.py`, GitHub run 44869028533
- `research/bridge_partition/candidate3_external_watdiv_preflight.py`, GitHub runs 44869115162, 44869244939, 44869313918
- `research/bridge_partition/candidate3_official_watdiv_byte_transfer.py`, GitHub run 44869433164
- `research/bridge_partition/candidate3_official_watdiv_pattern_folds.py`, GitHub run 44869561656
- `research/bridge_partition/candidate3_byte_economic_envelope.py`, GitHub run 44869742312

Original data rights and benchmark methodology: G. Aluç, O. Hartig, M. T. Özsu, K. Daudjee, *Diversified Stress Testing of RDF Data Management Systems*, ISWC 2014 (https://dsg.uwaterloo.ca/watdiv/).
Relevant prior art: WISE (2020, https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290), WASP (2021, https://link.springer.com/article/10.1007/s41019-021-00156-2), AdPart (https://vldb.org/vldb_journal/index.php/component/article_manager/article/1370), and 2026 replication-vs-partitioning ILP results (https://arxiv.org/abs/2605.00209). Generic cost-aware migration and replication are known; neither alone constitutes novelty here.
