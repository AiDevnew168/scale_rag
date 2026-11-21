#!/usr/bin/env python3
"""Exact predicate-family diversity audit of already measured 24 TRAIN-only queries.

Uses original SHA-locked 2014 graph+raw 88 training days and original unchanged
query structure. Emits ONLY query SHA / predicate-family SHA / source body bytes,
not literals, original SPARQL, private IPs or later heldout answers.
This post-result diagnostic does not reselect or improve the original sample.
"""
import collections
import hashlib
import json
from pathlib import Path

import candidate3_swdf_176day_physical_economic as physical
import candidate3_trainonly_selective_fetch_physical as first
import candidate3_feasible_raw_swdf_dated_source as raw

OUT=Path("results_candidate3_train24_exact_predicate_family_audit")
OUT.mkdir(exist_ok=True)
EXPECTED_24="028afc6b5634bf596c11ccb481ce2ed778ae572ae22502f2bdf16264851ca384"
EXPECTED_24_PAIR_FULL_BYTES=565_956_588


def summarize(chosen, weights):
    family_rows=collections.defaultdict(list)
    mapping=[]
    for row in chosen:
        preds=tuple(sorted(set(row["pattern"])))
        if any(p not in weights for p in preds):
            raise RuntimeError("Unmatched original source predicate")
        # The exact source fetch routing transfers each original fragment once.
        theoretical_full_bytes=sum(weights[p] for p in preds)
        digest=hashlib.sha256(json.dumps(preds).encode()).hexdigest()
        family_rows[digest].append(row["hash"])
        mapping.append({"original_query_text_sha256":row["hash"],
                        "predicate_set_family_sha256":digest,
                        "n_unique_predicates":len(preds),
                        "theoretical_full_original_RDF_TCP_body_bytes":theoretical_full_bytes})
    counts=sorted([len(v) for v in family_rows.values()],reverse=True)
    return {
        "n_distinct_original_query_texts":len(chosen),
        "n_exact_predicate_set_families":len(family_rows),
        "query_texts_per_family_descending":counts,
        "n_texts_in_top_two_predicate_families":sum(counts[:2]),
        "n_unique_full_response_byte_values":len(set(
            x["theoretical_full_original_RDF_TCP_body_bytes"] for x in mapping)),
        "exact_source_full_bytes_two_repeats":2*sum(
            x["theoretical_full_original_RDF_TCP_body_bytes"] for x in mapping),
        "anonymous_text_to_family_membership":mapping,
        "source_query_tokens_or_IP_logged":False,
        "source_train_88_days_only":True,
        "performance_causal_significance_from_this_audit":False,
        "journals_SOTA_GO":False,
    }


def main():
    _graph,_bypred,weights,_packs,_loads,_route,_cap=physical.load_real_source()
    rawpath=OUT/"SWDF.log.gz"
    got=physical.graphsource.gdown.download(id=raw.SOURCE_ID,
      output=str(rawpath),quiet=True,fuzzy=True)
    if not got or not rawpath.is_file() or raw.sha_file(rawpath)!=physical.SOURCE_SHA:
        raise RuntimeError("Original immutable raw access log not reproduced")
    queries,_meta=first.choose_train_only(rawpath,{p[1:-1] for p in weights})
    joined=hashlib.sha256("\n".join(x["hash"] for x in queries).encode()).hexdigest()
    if joined!=EXPECTED_24:raise RuntimeError("Original 24-query ranking mismatch")
    result=summarize(queries,weights)
    result.update({
        "schema":"candidate3-train24-exact-source-predicate-family-diversity-v1",
        "source_sample_hash":joined,
        "original_24train_query_pair_report_artifact_id":14713341448,
        "original_source_log_SHA256":physical.SOURCE_SHA,
        "original_graph_ZIP_SHA256":physical.GRAPH_SHA})
    (OUT/"report.json").write_text(json.dumps(result,indent=2))
    print("EXACT_TRAIN24_PREDICATE_FAMILY_AUDIT_START",flush=True)
    print(json.dumps({k:v for k,v in result.items()
          if k!="anonymous_text_to_family_membership"},indent=2),flush=True)
    print("EXACT_TRAIN24_PREDICATE_FAMILY_AUDIT_END",flush=True)
    if result["exact_source_full_bytes_two_repeats"]!=EXPECTED_24_PAIR_FULL_BYTES:
        raise RuntimeError("Full response payload mismatches verified frozen physical artifact")


if __name__=="__main__":main()
