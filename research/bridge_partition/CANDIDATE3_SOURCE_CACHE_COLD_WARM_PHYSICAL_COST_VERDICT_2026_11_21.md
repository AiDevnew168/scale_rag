# Original SWDF RDF worker cache cost: cold/warm physical probe and economic implications

## Evidence provenance

- Pre-result protocol: `CANDIDATE3_SOURCE_CACHE_COLD_COST_FROZEN_PROTOCOL_2026_11_21.md`.
- Pinned original SWDF RDF graph, no historical SPARQL query log: [completed four-worker physical CI 44920454357](https://github.com/AiDevnew168/scale_rag/actions/runs/44920454357); [artifact 14713232759](https://github.com/AiDevnew168/scale_rag/actions/runs/44920454357/artifacts/14713232759). Direct ZIP SHA256 `affe737d28e652c584d75e1f71f9a162acad73ed1b3bf1103bd27511f5765c9f`.
- Source selection: one deterministic largest original worker predicate fragment with an original NamedNode subject, before timing. Requests made to the same indexed localhost Oxigraph worker and optional Python source NTriples filter; all output matched original NTriples source bytes exactly. This is NOT one of the 2014 original public SELECT queries and is NOT a full-query latency experiment.

## Measured request-level results

| Physical measure | Value |
|---|---:|
| Full original fragment response bytes | 6,710,184 B |
| Filtered source response bytes | 162 B |
| Source response bytes removed | 99.9976% |
| First full-fetch HTTP request | 5.815 ms |
| Second full-fetch HTTP request | 4.009 ms |
| First cold filtered HTTP request | **258.374 ms** |
| Median of five subsequent warm filtered requests | **13.580 ms** |
| Cold-minus-warm filtered request excess | **244.795 ms** |
| Median of three full-fetch HTTP requests | **4.009 ms** |
| Selected worker Linux VmRSS before first filtered request | 326,752 KiB |
| Selected worker Linux VmRSS after first filtered request | 353,280 KiB |
| Worker VmRSS increase | **26,528 KiB (25.906 MiB)** |

## Economic and method conclusions

- The present Python implementation builds a lazy parsed list of exact original NTriples terms per predicate and then scans that parsed list for each filtered request. In this 6.71MB fragment case, warm filtered RPC is about 9.57ms **slower** than warm full fetch, although its RDF response body is far smaller. Thus per-shard RPC cost alone does **not** show an amortized positive benefit in this example.
- The positive original 24-query end-to-end training experiment ([run 44918517226](https://github.com/AiDevnew168/scale_rag/actions/runs/44918517226)) includes coordinator-side RDF parse and query execution, which benefit from smaller intermediate source data. **Do not conflate worker RPC latency with coordinator end-to-end query latency**. Depending on downstream parse, link bandwidth, cache and query shape, the total economics can still be positive.
- A one-time source-index/cache setup cost must be amortized across actual reuse on matching query shapes. For N future requests, an admissible strategy requires: `sum_i (T_full_i - T_filtered_warm_i) > C_cache_build + C_maintenance + C_recovery + C_switch`. Never substitute source bytes saved for wall time saved; all terms must use the same resource/economic units.
- One worker's Linux VmRSS delta does not quantify persistent four-worker RAM, memory peak, allocator fragmentation, total index maintenance or a general reproducible cache overhead. Cold vs warm on one predicate is not proof of root cause of the -222.826ms original training-pair outlier, only a mechanistically consistent independent source-only diagnostic.
- Before proposing an original method, evaluate a strong **always full** vs **always filtered** static control, a bounded resident-memory cache, and published original RDF-federation optimization baselines on an independent dataset. Indexing constant subject/object by hash can reduce repetitive scanning but is known prior art; algorithmic novelty must lie elsewhere and still needs to be demonstrated.

**Decision:** Real response-body savings CONFIRMED; cold setup and memory cost CONFIRMED; this specific warm worker endpoint slower than full-fetched RPC; end-to-end speed for first24 observed previously; prospective, fully costed economic controller benefit and novelty **NOT PROVEN**.