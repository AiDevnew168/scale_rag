#!/usr/bin/env python3
"""Forensic-only original SWDF engine-prefix compatibility on a KNOWN failed query.

Do not print original SPARQL text, IP addresses, full namespace declarations,
or repair any benchmark queries. Synthetic prefix repair is DIAGNOSTIC ONLY.
The frozen 176-day test remains INVALID regardless of the result.
"""
import gzip
import hashlib
import json
import re
from pathlib import Path

import gdown
from pyoxigraph import Store
from rdflib import Graph
from rdflib.plugins.sparql.processor import prepareQuery

import candidate3_feasible_raw_swdf_dated_source as raw
import candidate3_feasible_raw_swdf_strict_temporal as eligibility

SOURCE_SHA = "2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df"
FAILED_TEXT_SHA = "e8f4f6b9b2e90f89d4e5e80f68af8322751019f19324e7cee4c1cf2c08e95474"
OUT = Path("results_candidate3_SWDF_176day_prefix_forensics")
OUT.mkdir(exist_ok=True)
DECLARED = re.compile(r"\bPREFIX\s+([A-Za-z][\w.-]*):\s*<", re.I)
PREFIX_USE = re.compile(r"(?<![\w-])([A-Za-z][\w.-]*):[A-Za-z_]")
IRI = re.compile(r"<[^>]*>")
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)


def candidate_undeclared_defaults(query):
    """Heuristic to form syntactic repair trials; not a SPARQL validity proof."""
    declared = set(x.lower() for x in DECLARED.findall(query))
    builtin = {k.lower(): str(v) for k, v in Graph().namespaces()}
    no_iris_or_strings = QUOTED.sub(" ", IRI.sub(" ", query))
    used = set(x.lower() for x in PREFIX_USE.findall(no_iris_or_strings))
    return {p: builtin[p] for p in sorted(used - declared) if p in builtin}


def engine_syntax(query):
    """Empty store allows parser diagnostics without any original query answers."""
    try:
        Store().query(query)
        return {"accepted": True, "exception_type": None, "missing_prefix_error": False}
    except Exception as exc:
        return {"accepted": False, "exception_type": type(exc).__name__,
                "missing_prefix_error": "prefix not found" in str(exc).lower()}


def diagnose(query):
    digest = hashlib.sha256(query.encode()).hexdigest()
    if digest != FAILED_TEXT_SHA:
        raise ValueError("Unexpected query text; refuse unpinned diagnosis")
    try:
        prepareQuery(query)
        accepted_rdflib = True
    except Exception:
        accepted_rdflib = False
    original = engine_syntax(query)
    predicates, error = eligibility.select_predicates(query)
    defaults = candidate_undeclared_defaults(query)
    if defaults:
        extra = "".join("PREFIX " + k + ": <" + u + ">\n" for k,u in defaults.items())
        altered = engine_syntax(extra + query)
    else:
        altered = {"accepted": False, "exception_type": None, "missing_prefix_error": False}
    return {
        "schema": "candidate3-FEASIBLE-original-source-prefix-forensic-v1",
        "original_query_sha256": digest,
        "target_engine": "pyoxigraph 0.5.13",
        "source_eligibility_rdflib_accepts": accepted_rdflib,
        "source_eligibility_predicates_accepted": error is None and len(predicates or ()) >= 2,
        "original_target_syntax": original,
        "undeclared_rdflib_default_prefix_count_heuristic": len(defaults),
        "only_diagnostic_added_default_prefixes_target_syntax": altered,
        "original_query_unchanged_in_any_physical_benchmark": True,
        "forbidden_to_reuse_repaired_text_for_53day_inference": True,
        "existing_53day_economic_gate_valid": False,
        "any_query_literal_or_ip_emitted": False,
    }


def main():
    path = OUT / "SWDF.log.gz"
    downloaded = gdown.download(id=raw.SOURCE_ID, output=str(path),
                                quiet=True, fuzzy=True)
    if not downloaded or not path.is_file() or raw.sha_file(path) != SOURCE_SHA:
        raise RuntimeError("Source compressed SHA mismatch / download unavailable")
    hits = 0
    query = None
    with gzip.open(path, "rb") as handle:
        for line in handle:
            text = line.decode("utf8", errors="replace")
            match = raw.APACHE.search(text)
            if not match or match.group(2).upper() != "GET":
                continue
            candidate = raw.parse_query(match.group(3))
            if candidate is None:
                continue
            if hashlib.sha256(candidate.encode()).hexdigest() == FAILED_TEXT_SHA:
                hits += 1
                query = candidate
    if hits < 1:
        raise RuntimeError("Frozen error hash not found in immutable original source")
    output = diagnose(query)
    output["original_source_SHA256"] = SOURCE_SHA
    output["original_access_log_occurrences_with_failed_text"] = hits
    # Never emit query, inline PREFIX text, user IPs, or unverified error excerpts.
    (OUT / "report.json").write_text(json.dumps(output, indent=2))
    print("CANDIDATE3_PREFIX_FORENSIC_START", flush=True)
    print(json.dumps(output, indent=2), flush=True)
    print("CANDIDATE3_PREFIX_FORENSIC_END", flush=True)


if __name__ == "__main__":
    main()
