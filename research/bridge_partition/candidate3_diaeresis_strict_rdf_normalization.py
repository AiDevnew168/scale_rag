#!/usr/bin/env python3
"""Deterministic, explicitly audited author SWDF RDF strict-IRI normalization.

The original DIAERESIS ZIP is pinned and NEVER replaced in-place in GitHub.
Only a generated testbench COPY is used for *both* original author Spark DAP
and four-index Oxigraph. Original source is NOT valid strict N-Triples when
certain replacement glyphs occur in IRI brackets. Percent-encoding that
glyph preserves an explicit lexical representation but NOT proof of original
author RDF semantic identity. Exact same normalized bytes permit a fairer
same-graph interoperability check; it is NOT exact original raw-source test.
"""
import hashlib,io,json,re,urllib.request,zipfile
from pathlib import Path
from pyoxigraph import Store,RdfFormat
SOURCE="https://users.ics.forth.gr/~kondylak/SWJ/swdf.zip"
ZIP_SHA="c1787940fbffab1b92e61bb338707bc11d2575931fefd15cabc78f88c00654de"
IRI=re.compile(r"<([^<>]*)>")
OUT=Path("results_candidate3_diaeresis_normalization")
OUT.mkdir(exist_ok=True)
def normalize(raw):
    bad_utf8=0; modified_lines=0; modified_iris=0; samples=[]
    output=[]
    for number,line in enumerate(raw.splitlines(keepends=True),start=1):
        try:text=line.decode("utf8")
        except UnicodeDecodeError:
            bad_utf8+=1
            text=line.decode("utf8",errors="replace")
        changes=[0]
        def fix(m):
            iri=m.group(1)
            if "\ufffd" not in iri:return m.group(0)
            changes[0]+=1
            return "<"+iri.replace("\ufffd","%EF%BF%BD")+">"
        result=IRI.sub(fix,text)
        modified_iris+=changes[0]
        if result!=text or "\ufffd" in text and bad_utf8:
            modified_lines+=1
            if len(samples)<8:samples.append({"line":number,"replaced_iri_count":changes[0],
                "contains_replacement": "\ufffd" in text})
        output.append(result.encode("utf8"))
    return b"".join(output),{
        "source_raw_sha256":hashlib.sha256(raw).hexdigest(),
        "source_raw_bytes":len(raw),"source_line_count":len(output),
        "invalid_utf8_source_lines":bad_utf8,
        "modified_line_count":modified_lines,
        "IRI_replacement_character_percent_encoded_count":modified_iris,
        "audit_lines_without_raw_private_text":samples,
        "normalization":"Decode source UTF-8 lines, replacement for undecodable octets, U+FFFD within <IRI> encoded as %EF%BF%BD, preserve all lines and no silent row filtering"}
def certify(raw):
    normalized,meta=normalize(raw)
    meta.update({"normalized_sha256":hashlib.sha256(normalized).hexdigest(),
                "normalized_bytes":len(normalized)})
    store=Store()
    store.load(input=normalized,format=RdfFormat.N_TRIPLES)
    meta["strict_oxigraph_unique_triples"]=len(store)
    meta["parser_gate"]="PASS_STRICT_NTRIPLES"
    return normalized,meta
def main():
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"ScaleRAG-comparability-raw-source-audit/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r:compressed=r.read(9_000_000)
    assert hashlib.sha256(compressed).hexdigest()==ZIP_SHA
    with zipfile.ZipFile(io.BytesIO(compressed)) as z:
        assert "swdf/data/clean_swdf.nt" in z.namelist(),z.namelist()
        raw=z.read("swdf/data/clean_swdf.nt")
    report={"schema":"candidate3-DIAERESIS-raw-vs-strict-NTriples-audit-v1",
        "source":SOURCE,"zip_sha256":ZIP_SHA}
    try:
        normalized,meta=certify(raw)
        report.update(meta)
        report["status"]="PASS_NORMALIZED_SAME_BYTES_FOR_BOTH_ENGINES"
    except Exception as exc:
        report["status"]="BLOCKED_NORMALIZATION_NOT_SUFFICIENT"
        report["exception"]=type(exc).__name__+":"+str(exc)[:800]
        # Always preserve deterministic full audit even if strict parser fails.
        _,meta=normalize(raw)
        report.update(meta)
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("DIAERESIS_STRICT_GRAPH_PREFLIGHT_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("DIAERESIS_STRICT_GRAPH_PREFLIGHT_END",flush=True)
    if report["status"].startswith("BLOCKED"):raise RuntimeError("source_NTriples_strict_compatibility_gate_BLOCKED")
if __name__=="__main__":main()
