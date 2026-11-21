#!/usr/bin/env python3
"""Calibration-only proof-of-cause: unordered LIMIT nondeterministic outputs.

Do not use heldout errors to choose query selection. Execute original full
SPARQL SELECT and a separate deterministically ORDERed diagnostic variant
on identical central graph and four TCP shard stores. The original query
is not rewritten for economic timing. ORDER BY is only a diagnostic query;
if central vs sharded ordered answers align, original LIMIT mismatch is
consistent with legal unordered LIMIT semantics, not an execution bug.
"""
import json,re
from pathlib import Path
from pyoxigraph import Store,RdfFormat
from rdflib.plugins.sparql.processor import prepareQuery
import candidate3_swdf_real_full_sparql_economics as core
import candidate3_paired_full_sparql as paired
import candidate3_real_sparql_shards as eng
OUT=Path("results_candidate3_SWDF_limit_semantics");OUT.mkdir(exist_ok=True)
def deterministic(q):
    if not re.search(r'\bLIMIT\s+\d+\b',q,re.I):return None
    if re.search(r'\bORDER\s+BY\b',q,re.I):return None
    alg=prepareQuery(q).algebra
    pvs=alg.get("PV") or []
    vars_=sorted(set(str(x) for x in pvs))
    if not vars_:return None
    m=re.search(r'\bLIMIT\s+\d+\b',q,re.I)
    if not m:return None
    return q[:m.start()]+" ORDER BY "+ " ".join("?"+v for v in vars_)+" "+q[m.start():]
def main():
    graph,pred,size,roles,packs,loads,route,cap=core.prepare_source()
    chosen=[x for x in roles["calibration"] if deterministic(x["query"]) is not None]
    chosen=chosen[:12]
    assert len(chosen)>=3
    central=Store()
    central.bulk_load(input=graph,format=RdfFormat.N_TRIPLES)
    frag={p for p,s in route.items() if len(s)>1}
    ports,workers=paired.start_group(packs)
    comparisons=[]
    try:
        for r in chosen:
            h=r["text_hash"]
            result={"text_sha256":h}
            try:
                original_truth=eng.evaluate(central,r["query"])
                original_dist=core.query_four_workers(r["query"],r["pattern"],route,ports,frag)
                canon=deterministic(r["query"])
                assert canon
                ordered_truth=eng.evaluate(central,canon)
                ordered_dist=core.query_four_workers(canon,r["pattern"],route,ports,frag)
                result.update({"original_exact_match":original_truth==original_dist["answer"],
                    "ordered_diagnostic_exact_match":ordered_truth==ordered_dist["answer"],
                    "original_count":original_truth["count"],
                    "distributed_original_count":original_dist["answer"]["count"],
                    "diagnostic_ordered_count":ordered_truth["count"]})
            except Exception as exc:
                result["error"]=type(exc).__name__+": "+str(exc)[:250]
            comparisons.append(result)
    finally:paired.shutdown(workers)
    final={"schema":"candidate3-SWDF-calibration-only-unordered-LIMIT-diagnostic-v1",
      "n":len(comparisons),
      "original_mismatch":sum(x.get("original_exact_match") is False for x in comparisons),
      "ordered_diagnostic_match":sum(x.get("ordered_diagnostic_exact_match") is True for x in comparisons),
      "errors":sum("error" in x for x in comparisons),
      "rows":comparisons,
      "future_heldout_queries_read":0,
      "limitation":"Adding ORDER BY changes the diagnostic SPARQL query; do NOT use it to replace original query timings or claim exact-original-result equivalence."}
    OUT.joinpath("report.json").write_text(json.dumps(final,indent=2))
    print("SWDF_LIMIT_DIAGNOSTIC_START",flush=True)
    print(json.dumps(final,indent=2),flush=True)
    print("SWDF_LIMIT_DIAGNOSTIC_END",flush=True)
if __name__=="__main__":main()
