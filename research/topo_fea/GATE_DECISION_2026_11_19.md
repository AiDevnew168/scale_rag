# Real TopoGraphRAG Gate Decision — 2026-11-19

**Research question:** Does topology-/role-constrained evidence assembly materially improve recovery of the *complete* evidence set compared with strong simple alternatives, when the question and real document layouts are held fixed?

**Decision:** **NO-GO for immediate investment in a new Flow/graph solver on the evidence tested.** The broader hypothesis of *verified semantic relation-compatibility constraints* remains untested rather than disproven.

## Provenance and successful workflows

- Official dataset: https://huggingface.co/datasets/diandianone123/topographrag-bench
- Original annotation SHA256: `3bd203243a5c50a664f719e686608f9e4bfb0b9b31f0ea9514b324b2986247ff`
- Original layout source SHA256: `bbf21b76355ba3c2e3d2d53f183bd52a21b39b6f118bcf75754dad234ef87633`
- Selection: seed 261119; 300 questions spanning 191 documents (180 bridge-chain, 120 synthesis)
- Gold cardinality control: https://github.com/AiDevnew168/scale_rag/actions/runs/44500691453
- Baselines and graph proxy: https://github.com/AiDevnew168/scale_rag/actions/runs/44482419973
- Independent BM25 and union pools: https://github.com/AiDevnew168/scale_rag/actions/runs/44501655663
- Real pretrained cross-encoder: https://github.com/AiDevnew168/scale_rag/actions/runs/44501115217
- Frozen CE structural controls: https://github.com/AiDevnew168/scale_rag/actions/runs/44503429070
- Exact same-query paired cross-run comparisons: https://github.com/AiDevnew168/scale_rag/actions/runs/44503996967

No gold evidence, bridge entities, golden traces or answers enter retrievers or cross-encoder model calls. They enter *only* the final scorer. Data are real layout texts/OCR/VLM-provided descriptions; **pixels are not read directly**.

## Gold cardinality and feasibility

All 180 sampled bridge-chain questions have exactly 2 gold evidence nodes. All 120 synthesis questions have 3–6 gold nodes. Thus **all** complete evidence sets are theoretically representable with a budget of 6. There were no duplicate query IDs.

Top-50 TF-IDF candidate pool contains complete gold for 242/300 = 80.667%. TF-IDF Top-6 succeeds in 99/300 = 33.0%; 143 cases have all evidence in the pool but not in the naive Top-6. This is a retrieval *selection* gap, not evidence of repairable link incompatibility. The source document is known and the pool is drawn from that single document—this is NOT whole-corpus document discovery.

## Aggregated complete evidence set retrieval

| Method | Full@2 | Full@6 | Full@12 |
|---|---:|---:|---:|
| TF-IDF | 14.33% | 33.00% | 52.33% |
| BM25 | 16.00% | **38.33%** | **53.67%** |
| Cross-Encoder MiniLM-L6 | 10.00% | 33.33% | 51.67% |
| CE + MMR | 11.00% | 34.00% | n/a |
| CE + greedy two-role assignment | 17.33% | 37.67% | n/a |
| CE + exact two-role assignment | 17.00% | 37.00% | n/a |

At @6, mean evidence recall is: TF-IDF 55.606%; BM25 **63.033%**; CE **60.144%**.

Cross-Encoder ID: `cross-encoder/ms-marco-MiniLM-L6-v2`. Hugging Face model revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`; 384-token truncation; 15,000 query–evidence pairs; CPU inference. This is a legitimate pretrained text cross-encoder, not a 2026 multimodal state-of-the-art reranker.

## Matched comparisons and uncertainty

CI: 2,000 whole-document bootstrap replicates (191 document clusters). All comparisons are exploratory because the same sample was investigated repeatedly.

| New method vs baseline | Delta Full@6 (percentage points) | Wins | Losses | Cluster bootstrap CI95 pp |
|---|---:|---:|---:|---|
| BM25 vs TF-IDF | +5.333 | 36 | 20 | [+1.020, +9.967] |
| CE vs TF-IDF | +0.333 | 37 | 36 | [-5.034, +5.883] |
| CE + greedy vs CE | +4.333 | 15 | 2 | [+1.650, +7.516] |
| CE + exact vs CE | +3.667 | 13 | 2 | [+1.253, +6.712] |
| CE + greedy vs BM25 | -0.667 | 29 | 31 | [-5.923, +4.276] |
| CE + exact vs BM25 | -1.333 | 29 | 33 | [-6.774, +3.631] |

At @6, CE with all 50 original candidate scores recovers 100/300 full evidence sets and leaves 142/300 cases with gold in Top-50 but not all in CE Top-6. Importantly, that **does not** prove these 142 cases can be repaired with graph constraints.

## Topology-specific breakdown: Full@6

| Method | Bridge-chain n=180 | Synthesis n=120 |
|---|---:|---:|
| TF-IDF | 47.778% | 10.833% |
| BM25 | 55.000% | 13.333% |
| CE | 46.111% | 14.167% |
| CE+MMR | 48.333% | 12.500% |
| CE+greedy roles | 53.333% | 14.167% |
| CE+exact roles | 52.778% | 13.333% |

Exact two-role matching was **not** better than the greedy two-role approach or BM25. This does not assess a genuine role-and-relation consistency constrained global optimizer, since no independently verified positive/negative relation constraints were available.

## Interpretation and stop decision

1. A selection gap exists under lexical candidate generation and a text-surrogate layout representation.
2. BM25, a simple classic baseline, beats all tested graph/role selection proxies on total full@6 by point estimate.
3. The CE improved average evidence recall over TF-IDF but did not improve full-set @6, and BM25's recall exceeds CE's in this setting.
4. Role-aware query splitting can improve CE's full@6 on this exploratory dataset. But **greedy slightly outperforms exact matching** and neither beats BM25. Thus no demonstrated need for a novel flow/ILP solver.
5. On Synthesis, all methods remain low. That could reflect missing joint-relation reasoning, but also weak source representations, model truncation, query paraphrases, and candidate quality.

**Decision: NO-GO for new algorithm development or journal-paper claims now.** A narrow continuation requires simultaneously: (a) an appropriate stronger reranker with identical pool and budget; (b) labels for real relation compatibility on held-out documents; (c) per-query separation of missing evidence vs incorrect role assignment vs erroneous evidence joins; and (d) exact CP-SAT/ILP compared with greedy under identical semantic scores and constraints. If those conditions cannot be met, stop this line rather than building another large architecture.

**Limitations:** not direct multimodal inference, not official end-to-end RAG, not a faithful FlowReader/G²-Reader reproduction, no question-wise formal prospective hypothesis lock, and no independent document-held-out confirmation. All results should be presented as exploratory feasibility and failure attribution only.


## Independent execution-sharding reproducibility check

A separate five-shard parallel rerun on the same original 300 questions, using five clean CI workers, completed successfully:
https://github.com/AiDevnew168/scale_rag/actions/runs/44503581998

Its aggregate independent fingerprint/same-question checks reproduced TF-IDF Full@6 = **33.000%**, CE Full@6 = **33.333%**, CE mean evidence Recall@6 = **60.144%**, and paired CE vs TF-IDF Delta = **+0.333 pp** with the same document-cluster CI **[-5.034,+5.883] pp**. This establishes computational reproducibility across job sharding. It is NOT a statistically independent replication, because all 300 queries and model weights were unchanged.
