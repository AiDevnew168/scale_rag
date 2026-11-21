#!/usr/bin/env python3
"""Locked source+strict SPARQL metadata/eligibility audit; NO result evaluations.

Original FEASIBLE SWDF graph zip + real logged query text. SHA source pin.
Policy family split: 20% test, 20% calibration, 60% training, frozen SHA
order. Query parser from rdflib 7.5.0 SPARQL algebra, no regex-only
reconstruction. Supports only SELECT whose algebra consists of
SelectQuery, Project, BGP, Slice, Distinct, Reduced, OrderBy, OrderCondition
and has 2-6 constant-URI predicates all in graph. No SERVICE, FILTER,
OPTIONAL, UNION, GROUP, paths, FROM, values, aggregate, property vars.
No source-provided Results Size or Query Execution Time used for selection.
"""
import collections,hashlib,io,json,re,urllib.request,urllib.parse,zipfile
from pathlib import Path
import gdown
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.term import URIRef

ROOT=Path("results_candidate3_SWDF_locked_audit");ROOT.mkdir(exist_ok=True)
GRAPH_ID="0B1tUDhWNTjO-cjBqUG1BZF9RTnM"
GRAPH_SHA="65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb"
QUERY_SOURCE="https://raw.githubusercontent.com/dice-group/feasible/master/SWDF-CleanQueries.txt"
SEED=20261121
ALLOW={"SelectQuery","Project","BGP","Slice","Distinct","Reduced","OrderBy","OrderCondition"}
def downloaded():
    target=ROOT/"swdf.zip"
    if target.exists():return target
    r=gdown.download(id=GRAPH_ID,output=str(target),quiet=True,fuzzy=True)
    if not r or not target.exists():raise RuntimeError("Source SWDF graph unavailable")
    if hashlib.sha256(target.read_bytes()).hexdigest()!=GRAPH_SHA:
        raise RuntimeError("SWDF original ZIP SHA256 source PIN mismatch")
    return target
def get_queries():
    req=urllib.request.Request(QUERY_SOURCE,headers={"User-Agent":"ScaleRAG-independent-real-SWDF-lock/1.0"})
    with urllib.request.urlopen(req,timeout=90) as r:
        b=r.read(90*1024*1024+1)
    if len(b)>90*1024*1024:raise RuntimeError("Query file source exceeds cap")
    return b
def parse_records(query_bytes):
    # Every field is one line, query URL-encoded on a single Query String line.
    text=query_bytes.decode("utf8",errors="replace")
    blocks=re.split(r"(?m)^#-+\s*$",text)
    records=[];fails=collections.Counter()
    for block in blocks:
        fields={}
        for line in block.splitlines():
            if ": " not in line:continue
            k,v=line.split(": ",1)
            fields[k.strip()]=v.strip()
        if "Query String" not in fields:continue
        if fields.get("Query Type","").upper()!="SELECT":
            fails["not_SELECT"]+=1;continue
        if any(fields.get(x,"").lower()=="yes" for x in ("UNION","OPTIONAL","FILTER",
                    "GROUP BY","REGEX")):
            fails["unsupported_construct"]+=1;continue
        try:
            n=int(fields.get("Triple Patterns","0"))
            if not 2<=n<=6:
                fails["triple_count_outside_contract"]+=1;continue
            query=urllib.parse.unquote_plus(fields["Query String"])
            parsed=prepareQuery(query)
            nodes=[];triples=[]
            def walk(x):
                if isinstance(x,CompValue):
                    nodes.append(x.name)
                    if x.name=="BGP":
                        triples.extend(x["triples"])
                    for k,v in x.items():
                        if k not in ("triples","_vars"):walk(v)
                elif isinstance(x,(tuple,list,set)):
                    for y in x:walk(y)
            walk(parsed.algebra)
            if not nodes or not set(nodes).issubset(ALLOW):
                fails["unsupported_algebra"]+=1;continue
            if parsed.algebra.get("datasetClause"):
                fails["named_graph_clause"]+=1;continue
            if not 2<=len(triples)<=6 or not all(isinstance(p,URIRef) for s,p,o in triples):
                fails["unexpected_or_dynamic_triples"]+=1;continue
            preds=tuple(sorted(set(str(p) for _,p,_ in triples)))
            if len(preds)<2:
                fails["single_predicate_family"]+=1;continue
            records.append({"query":query,
                 "text_sha256":hashlib.sha256(query.encode()).hexdigest(),
                 "predicates":preds,
                 "metadata_query_no":fields.get("Query No")})
        except Exception as e:
            fails["SPARQL_parse_error_"+type(e).__name__]+=1
    return records,dict(fails)
def main():
    zpath=downloaded()
    with zipfile.ZipFile(zpath) as z:
        assert z.namelist()==["swdf.nt"],z.namelist()
        graph=z.read("swdf.nt")
    predsize=collections.Counter()
    for line in graph.splitlines(keepends=True):
        if not line.strip():continue
        tokens=line.split(None,2)
        if len(tokens)<3 or not tokens[1].startswith(b"<"):
            raise ValueError("Invalid RDF NTriples predicate line")
        predsize[tokens[1].decode()[1:-1]]+=len(line)
    qraw=get_queries()
    records,excl=parse_records(qraw)
    found=len(records)
    rows=[r for r in records if all(p in predsize for p in r["predicates"])]
    excl["predicate_absent_from_graph"]=found-len(rows)
    uniq={}
    for r in rows:
        uniq.setdefault(r["text_sha256"],r)
    patterns=sorted({r["predicates"] for r in uniq.values()})
    order=sorted(patterns,key=lambda p:hashlib.sha256(
        ("candidate3-swdf-prelocked-v1:"+str(SEED)+":"+json.dumps(p)).encode()).hexdigest())
    fold={p:k%5 for k,p in enumerate(order)}
    divisions={"training":[],"calibration":[],"holdout":[]}
    for r in uniq.values():
        k=fold[r["predicates"]]
        role="holdout" if k==0 else ("calibration" if k==1 else "training")
        divisions[role].append(r)
    for i in divisions:
        divisions[i].sort(key=lambda r:r["text_sha256"])
    assert len({r["text_sha256"] for r in divisions["holdout"]}&
              {r["text_sha256"] for r in divisions["training"]+divisions["calibration"]})==0
    report={"schema":"candidate3-original-FEASIBLE-SWDF-graph-and-real-log-locked-eligibility-v1",
      "source_archive_url":"https://drive.google.com/file/d/"+GRAPH_ID+"/view",
      "source_archive_sha256":GRAPH_SHA,
      "graph_uncompressed_sha256":hashlib.sha256(graph).hexdigest(),
      "graph_NTriples_raw_bytes":len(graph),
      "graph_predicate_count":len(predsize),
      "graph_predicate_bytes":sum(predsize.values()),
      "query_url":QUERY_SOURCE,"query_source_bytes":len(qraw),
      "query_file_sha256":hashlib.sha256(qraw).hexdigest(),
      "query_contract":sorted(ALLOW),
      "parse_exclusions":excl,"strict_pre_graph_valid":found,
      "graph_compatible_eligible_occurrences":len(rows),
      "graph_compatible_unique_texts":len(uniq),
      "unique_predicate_families":len(patterns),
      "deterministic_5fold_assignments":{"training":3,"calibration":1,"holdout":1},
      "heldout_pattern_families":len({r["predicates"] for r in divisions["holdout"]}),
      "selected_queries_per_role":{k:len(v) for k,v in divisions.items()},
      "exact_text_overlap":0,
      "test_results_unopened":True,
      "limitation":"Query log 'clean queries' lacks original chronological traffic; family-disjoint, not temporal validation. Source RDF zip may not match recording-time graph."}
    (ROOT/"audit.json").write_text(json.dumps(report,indent=2))
    # Query strings only in local runner; only hashes+family labels saved
    (ROOT/"locked_manifest.json").write_text(json.dumps({
        "source_sha":report["query_file_sha256"],
        "selected_sha256_by_role":{k:[r["text_sha256"] for r in rows] for k,rows in divisions.items()},
        "family_count_by_role":{k:len({r["predicates"] for r in rows}) for k,rows in divisions.items()}},
       indent=2))
    print("SWDF_LOCKED_AUDIT_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("SWDF_LOCKED_AUDIT_END",flush=True)
if __name__=="__main__":main()
