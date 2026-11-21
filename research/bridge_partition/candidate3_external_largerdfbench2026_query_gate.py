#!/usr/bin/env python3
"""Independent 2026 LargeRDFBench QUERY-ONLY conformance/readiness audit.

Pinned public archive: Zenodo record 22140177, queries.zip MD5 published.
No bulk RDF datasets or expected result downloads, no benchmark answers/timing.
This is an external syntax/structural-coverage probe and not a federation result.
"""
import collections
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

from pyoxigraph import Store
from rdflib.plugins.sparql.processor import prepareQuery
import candidate3_selective_fetch_transport as selective

RECORD="https://zenodo.org/records/22140177"
URL=RECORD+"/files/queries.zip?download=1"
MD5="10a2e5fb7a69ff9da66d9d5bf977a77e"
MAX_DOWNLOAD=250_000
MAX_MEMBER=100_000
MAX_TOTAL=2_000_000
OUT=Path("results_candidate3_external_LargeRDFBench2026_query_gate")
OUT.mkdir(exist_ok=True)


def query_archive_entries(data):
    if not isinstance(data,bytes) or len(data)>MAX_DOWNLOAD:
        raise ValueError("Invalid or oversized public ZIP")
    if hashlib.md5(data).hexdigest()!=MD5:
        raise ValueError("Published 2026 benchmark archive MD5 mismatch")
    return inspect_zip(data)


def inspect_zip(data):
    texts={}
    total=0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.infolist():
            if member.is_dir():
                continue
            path=member.filename.replace("\\","/")
            if path.startswith("/") or ".." in path.split("/"):
                raise ValueError("Unsafe ZIP member path")
            if member.file_size>MAX_MEMBER:
                raise ValueError("Oversized original SPARQL query")
            total+=member.file_size
            if total>MAX_TOTAL:
                raise ValueError("ZIP decompression size cap")
            if not path.lower().endswith((".rq",".sparql",".txt",".query")):
                continue
            if path.lower().endswith(("/readme.txt","/license.txt")):
                continue
            raw=z.read(member)
            try:
                text=raw.decode("utf8")
            except UnicodeDecodeError:
                raise ValueError("Non-UTF8 original benchmark query")
            if not re.search(r"\b(SELECT|ASK|CONSTRUCT|DESCRIBE)\b",text,re.I):
                continue
            texts[path]=text
    if not texts:
        raise ValueError("No SPARQL original queries found")
    return texts


def audit_public_queries(texts):
    counter=collections.Counter()
    rows=[]
    empty=Store()
    for name,query in sorted(texts.items()):
        digest=hashlib.sha256(query.encode()).hexdigest()
        status={"archive_member":name,"sha256":digest,"original_query_not_modified":True}
        try:
            algebra=prepareQuery(query).algebra
            status["rdflib_parse"]="PASS"
            counter["rdflib_parse_pass"]+=1
            status["rdflib_root"]=algebra.name
        except Exception as e:
            status["rdflib_parse"]="FAIL"
            status["rdflib_failure_type"]=type(e).__name__
            counter["rdflib_parse_fail"]+=1
        try:
            empty.query(query)
            status["oxigraph_syntax"]="PASS"
            counter["oxigraph_syntax_pass"]+=1
        except Exception as e:
            status["oxigraph_syntax"]="FAIL"
            status["oxigraph_failure_type"]=type(e).__name__
            counter["oxigraph_syntax_fail"]+=1
        try:
            clauses=selective.compile_filters(query)
            status["plain_BGP_supported"]=True
            status["constant_anchor_predicate_count"]=sum(x is not None for x in clauses.values())
            counter["plain_BGP_supported"]+=1
            if status["constant_anchor_predicate_count"]>0:
                counter["plain_BGP_constant_anchor_supported"]+=1
        except Exception:
            status["plain_BGP_supported"]=False
            status["constant_anchor_predicate_count"]=0
            counter["plain_BGP_unsupported_or_non_SELECT"]+=1
        rows.append(status)
    return {
        "schema":"candidate3-2026-interoperable-LargeRDFBench-queries-only-gate-v1",
        "public_dataset_record":RECORD,
        "queries_zip_md5":MD5,
        "n_extracted_query_files":len(texts),
        "published_query_suite_expected":40,
        "n_queries_match_published_40":len(texts)==40,
        "engine_and_constant_BGP_features":dict(counter),
        "query_sha256_and_syntactic_flags":rows,
        "RDF_source_graph_evaluated":False,
        "federated_expected_answers_verified":False,
        "network_distributed_runtime_or_migration_tested":False,
        "natural_workload_timestamps_present":False,
        "original_2014_SWDF_heldout_reused":False,
        "novel_or_journal_method_claim":False,
    }


def main():
    with urllib.request.urlopen(URL,timeout=50) as resp:
        data=resp.read(MAX_DOWNLOAD+1)
    texts=query_archive_entries(data)
    result=audit_public_queries(texts)
    (OUT/"report.json").write_text(json.dumps(result,indent=2))
    print("EXTERNAL_LARGERDFBENCH2026_QUERY_GATE_START",flush=True)
    print(json.dumps({k:v for k,v in result.items()
        if k!="query_sha256_and_syntactic_flags"},indent=2),flush=True)
    print("EXTERNAL_LARGERDFBENCH2026_QUERY_GATE_END",flush=True)
    if not result["n_queries_match_published_40"]:
        raise RuntimeError("Unexpected public query archive inventory (not 40); do not publish result")


if __name__=="__main__":
    main()
