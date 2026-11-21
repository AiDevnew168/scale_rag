# Prospective decision rules for a TRAIN-ONLY selective-fetch architecture probe

**Status:** explicitly set before reading workflow 44915287023 source feature counts. This is an exploratory stop/go for engineering, not a 2014 confirmatory journal preregistration. Original prior test cohort has already been exposed and invalidated by target-engine PREFIX mismatch; it is not permitted for independent method-selection evaluation.

## Why architectural change, not more partition swaps

The current full-predicate fragment-fetch coordinator sends the same raw RDF response payload bytes per BGP query independently of where complete predicate fragments reside. True savings require partial data shipped, reuse of physically cached data, or join processing at the workers. This is NOT a new discovery in RDF literature: [AdPart](https://vldb.org/vldb_journal/index.php/component/article_manager/article/1370) performs actual distributed joins and adaptive replication; [WISE](https://www.sciencedirect.com/science/article/abs/pii/S2214579620300290) explicitly optimizes communication and migration; [DIAERESIS](https://journals.sagepub.com/doi/10.3233/SW-243554) uses semijoin reduction.

## Gate A (structural evidence, first 88 genuine dates ONLY)

The script candidate3_trainonly_selective_fetch_feasibility.py must find:
- At least **50 distinct eligible TRAIN-only original query texts** with one constant subject/object term in a triple pattern that also binds a shared BGP variable.
- At least **250 TRAIN-only original query occurrences** of those anchored join shapes among the immutable 4,707 eligible training requests.
- All source SHA, strict 176-day chronology and graph-predicate compatibility checks PASS. The permitted calculation reads none of calibration or heldout original SPARQL texts, answers or timings.

If either size requirement fails, do not build a costly selective-fetch implementation for this original training workload. These thresholds are engineering go/no-go heuristics, not power calculations or evidence of generalization.

## Gate B (real physical feasibility on the same TRAIN-ONLY texts; not innovation)

If A passes, implement a version-correct RDF triple-pattern selection/predicate routing and semijoin-reduced worker response with a strict *all original SELECT* semantic certifier. Run unmodified queries. Compare original full-fragment coordinator, explicit constant-filter-only pushdown, semijoin pushdown, strong published-system methodology where compatible; measure RDF bytes, CPU, memory, p50/p95 end-to-end wall time, source fragment edit/index/recovery. Report per-query paired results and exclude no errors. Require **zero semantic errors**, at least **25% median RDF response-byte reduction over anchored training queries**, and positive physically measured mean latency saving with sensitivity across independent training days, no p95 regression. A local synthetic or positive-byte-only result is insufficient.

## Gate C (journal novelty and economic policy, entirely NEW data)

Do not tune a new method using the known 53 heldout days. Before claiming scientific novelty, evaluate on an independent natural-query dataset with version-matched RDF data and genuine clock timestamps. Require a real deployable economic controller that sometimes changes strategy based only on past data and beats no_move and published AdPart/WISE-style controls under matched capacity/network/cost. Demonstrate theoretical innovation not already covered by classical semijoin reduction, online repartitioning, adaptive query routing, confidence-bound admission, or stop-loss. Multi-host costs and production rollback remain mandatory.

**All three gates separate:** structural availability is not byte benefit; byte benefit is not speed benefit; speed benefit is not a novel economic controller nor a journal-worthy original algorithm.