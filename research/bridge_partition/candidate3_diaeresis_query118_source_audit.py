#!/usr/bin/env python3
"""Diagnostic of the exact 2-row original DIAERESIS Spark SELECT count mismatch.

Published author query118: SELECT * WHERE { ?person rdf:type foaf:Person }.
Source normalized RDF graph and unmodified author query checked already on
identical bytes. This is an independent source-line integrity audit; it does
NOT alter source, remove outliers or revise the author's published result.
"""
import hashlib,io,json,urllib.request,zipfile,collections
from pathlib import Path
from candidate3_diaeresis_strict_rdf_normalization import normalize,ZIP_SHA,SOURCE
OUT=Path("results_candidate3_diaeresis_query118_integrity");OUT.mkdir(exist_ok=True)
P=b"<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
O=b"<http://xmlns.com/foaf/0.1/Person>"
def count(raw):
    rows=[];modified=[];subjects=collections.Counter()
    for i,line in enumerate(raw.splitlines(),start=1):
        parts=line.strip().split(None,3)
        if len(parts)<4 or parts[1]!=P or parts[2]!=O:continue
        subjects[parts[0]]+=1
        rows.append(i)
        if b"\xef\xbf\xbd" in line or b"%EF%BF%BD" in line:
            modified.append(i)
    return {"all_matching_assertion_lines":len(rows),
      "distinct_matching_lexical_subjects":len(subjects),
      "duplicate_subject_assertion_occurrences":sum(c-1 for c in subjects.values()),
      "matching_rows_affected_by_28_invalid_IRI_glyphs":len(modified),
      "matching_line_numbers_with_invalid_or_encoded_iri":modified[:25],
      "matching_assertion_line_count_sha256":hashlib.sha256(
        str(len(rows)).encode()).hexdigest()}
def main():
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"ScaleRAG-source-count-integrity/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r:compressed=r.read(9_000_000)
    assert hashlib.sha256(compressed).hexdigest()==ZIP_SHA
    with zipfile.ZipFile(io.BytesIO(compressed)) as z:raw=z.read("swdf/data/clean_swdf.nt")
    normalized,metadata=normalize(raw)
    results={"schema":"candidate3-author-query118-two-count-difference-source-line-audit-v1",
      "full_original_graph_sha256":metadata["source_raw_sha256"],
      "full_common_normalized_sha256":hashlib.sha256(normalized).hexdigest(),
      "author_original_QUERY118_SELECT_text":"SELECT * WHERE { ?person rdf:type foaf:Person }",
      "known_author_spark_reported_result_count":11112,
      "known_strict_complete_oxigraph_reported_count":11114,
      "original_author_RDF_assertions":count(raw),
      "same_normalized_RDF_assertions":count(normalized),
      "transformation_modified_IRIs":metadata["IRI_replacement_character_percent_encoded_count"],
      "still_not_same_engine_semantics":True,
      "no_author_source_query_or_data_filtering":True}
    OUT.joinpath("report.json").write_text(json.dumps(results,indent=2))
    print("DIAERESIS_QUERY118_INTEGRITY_START",flush=True)
    print(json.dumps(results,indent=2),flush=True)
    print("DIAERESIS_QUERY118_INTEGRITY_END",flush=True)
if __name__=="__main__":main()
