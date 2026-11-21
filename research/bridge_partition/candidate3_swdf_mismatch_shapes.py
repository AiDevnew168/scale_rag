#!/usr/bin/env python3
"""Read-only mismatch explainability on frozen failed SWDF query-run artifact.

Does not alter, drop or re-score heldout queries. Re-fetches originally pinned
log only to classify whether LIMIT/OFFSET/nondeterministic row ordering could
explain mismatched full result multisets. Any study of these opened heldout
queries is diagnostic and precludes new confirmatory claims on same split.
"""
import collections,hashlib,json,re
from pathlib import Path
import candidate3_swdf_locked_audit as sd
r=list(Path("bundle").rglob("report.json"))
assert len(r)==1
data=json.loads(r[0].read_text())
src=sd.get_queries()
assert hashlib.sha256(src).hexdigest()=="7d239ff96296a321148d3da3d2ec80ad7c1e439afff2d6e2753c12b2da13c0c3"
records,_=sd.parse_records(src)
by_hash={x["text_sha256"]:x for x in records}
errors=set()
for method,detail in data["method_results"].items():
    errors.update(x["query_sha256"] for x in detail["error_examples"])
summary={}
for hash_ in sorted(errors):
    assert hash_ in by_hash
    q=by_hash[hash_]["query"]
    summary[hash_]={"limit":bool(re.search(r'\bLIMIT\b',q,re.I)),
     "offset":bool(re.search(r'\bOFFSET\b',q,re.I)),
     "order_by":bool(re.search(r'\bORDER\s+BY\b',q,re.I)),
     "distinct":bool(re.search(r'\bDISTINCT\b',q,re.I)),
     "n_predicates":len(by_hash[hash_]["predicates"]),
     "has_bnode":bool(re.search(r'\bBNODE\b|_:[A-Za-z0-9]+',q,re.I)),
     "has_service_graph":bool(re.search(r'\bGRAPH\b|\bSERVICE\b',q,re.I))}
stats={name:sum(int(x[name]) for x in summary.values()) for name in
       ("limit","offset","order_by","distinct","has_bnode","has_service_graph")}
print("FROZEN_SWDF_MISMATCH_SHAPES_START")
print(json.dumps({"failure_sha_count_visible":len(summary),
                  "shape_counts":stats,
                  "per_query":summary,
                  "nonmatching_results_must_not_be_discarded":True,
                  "source_frozen_run":44874462942},indent=2))
print("FROZEN_SWDF_MISMATCH_SHAPES_END")
