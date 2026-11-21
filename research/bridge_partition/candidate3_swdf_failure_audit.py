#!/usr/bin/env python3
"""Read-only error audit of frozen completed full-SWDF run artifact."""
import collections,json
from pathlib import Path
p=list(Path("bundle").rglob("report.json"))
assert len(p)==1,p
r=json.loads(p[0].read_text())
summaries={}
for method,record in r["method_results"].items():
    errs=record["error_examples"]
    count=collections.Counter(x["error"].split(":",1)[0] for x in errs)
    summaries[method]={"n_failed":record["n_failed_query_execution"],
        "visible_error_types_from_sample":dict(count),
        "first_10_examples":errs[:10],
        "n_exact_correct_pairs":record["n_correct_paired_executions"],
        "all_queries_exact":record["all_eligible_heldout_answers_exact"]}
print("FROZEN_SWDF_ERRORS_START")
print(json.dumps({"source_run":44874462942,
    "central_errors":r["central_error_examples"],
    "central_errors_total":r["central_query_errors"],
    "method_failure_illustrations":summaries},indent=2))
print("FROZEN_SWDF_ERRORS_END")
