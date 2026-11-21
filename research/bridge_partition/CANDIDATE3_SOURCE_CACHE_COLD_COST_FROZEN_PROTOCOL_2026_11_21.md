# Frozen cold-versus-warm worker cache and memory accounting, before execution

**Engineering microbenchmark protocol registered 2026-11-21 after positive first24 training workload wall-time observation. NOT a profit study, not a 53-day heldout retry.**

Problem: first24 original TRAIN SELECT pair shows one cold-looking pushdown response of 326.74ms vs 103.92ms full despite large byte pruning. Worker caches parsed NTriples triples lazily in Python. Without measuring parse startup and resident memory, an online profit/cost policy cannot be trusted.

## Independent, original graph only (no SWDF query-log read)

- SHA-pin original graph ZIP 65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb; instantiate same original four indexed localhost TCP Oxigraph workers.
- Preselection: choose lexicographically stable largest per-worker source predicate fragment that has an original NamedNode subject; choose first NTriples triple's NamedNode as a filter constant. This is a deterministic synthetic *source-derived* query, not an original historical SPARQL query. Do not browse query log.
- Fixed sequence of HTTP requests to same worker: full raw predicate fetch twice, then first uncached constant subject filter once, then 5 identical warm filtered requests, then full once. Record all JSON-independent HTTP end-to-end ms and returned raw RDF payload bytes. Confirm selective output is exactly a subsequence of source original NTriples lines; check no blank node identity rewriting.
- Record Python worker process RSS before and after first cached filter (Linux /proc/PID/status), cache retained while process alive; expose raw and reconstructed response sizes, number of original NTriples records and exact source fingerprint. Do not present 1 RSS change as total cluster RAM or full memory profile.
- Real network TCP localhost and worker graph loading/indexing are physically exercised; no multi-host, production trace, temporal drift or published original baseline.

**Interpretation predeclared:** if first selective request takes materially longer than warm median or RSS rises, it is evidence of a cold-path/cache cost that must enter an admission/amortization model. Do not subtract that cost from first24 end-to-end timings or retrofit a positive claim. If cold/warm difference is zero, investigate other causes of the observed -222.8ms outlier. Any missing/failed source coverage => invalid microbenchmark.

Safety: no source query literals or user IP. Any action on 53 exposed days is prohibited.