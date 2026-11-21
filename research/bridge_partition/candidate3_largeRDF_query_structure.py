#!/usr/bin/env python3
"""Only original SPARQL QUERY STRUCTURE of 2026 LargeRDFBench.

Never downloads/opens RDF graph or expected answer values.
Choose candidate published single-graph coverage before further test work.
"""
import hashlib,io,json,re,urllib.request,zipfile,collections
from pathlib import Path
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.term import URIRef

SOURCE="https://zenodo.org/api/records/22140177/files/queries.zip/content"
SHA="10a2e5fb7a69ff9da66d9d5bf977a77e"
OUT=Path("results_candidate3_external_largeRDF_query_contract");OUT.mkdir(exist_ok=True)
ALLOWED={"SelectQuery","Project","BGP","Slice","Distinct","OrderBy","OrderCondition"}
def source_text():
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"ScaleRAG-2026-frozen-structure-only/1.0"})
    with urllib.request.urlopen(req,timeout=40) as resp:data=resp.read(200000)
    assert hashlib.md5(data).hexdigest()==SHA
    return data

def inspect(name,q):
    try:
        a=prepareQuery(q).algebra
        nodes=[];triples=[]
        def scan(x):
            if isinstance(x,CompValue):
                nodes.append(x.name)
                if x.name=="BGP":triples.extend(x["triples"])
                for k,v in x.items():
                    if k not in ("triples","_vars"):scan(v)
            elif isinstance(x,(tuple,list)):
                for v in x:scan(v)
        scan(a)
        preds=[str(p) for _,p,_ in triples if isinstance(p,URIRef)]
        hosts=sorted(set(re.search(r"https?://([^/]+)",x).group(1)
           for x in preds if re.search(r"https?://([^/]+)",x)))
        return {"name":name,"sha256":hashlib.sha256(q.encode()).hexdigest(),
           "kind":"SELECT" if "SelectQuery" in nodes else "not_SELECT",
           "triple_patterns":len(triples),"distinct_predicate_IRIs":len(set(preds)),
           "predicate_domains":hosts,
           "service_or_graph_or_path_or_aggregate":any(x in nodes for x in
              ("ServiceGraphPattern","Graph","Path","AggregateJoin","Group","ToMultiSet")),
           "algebra_names":sorted(set(nodes)),
           "strict_2to6_constant_BGP_eligible":(
              set(nodes).issubset(ALLOWED) and 2<=len(triples)<=6
              and len(set(preds))>=2 and len(preds)==len(triples))}
    except Exception as e:return {"name":name,"parse_failure":type(e).__name__+":"+str(e)[:160]}

def main():
    q=source_text()
    with zipfile.ZipFile(io.BytesIO(q)) as z:
        rows=[inspect(n,z.read(n).decode("utf8",errors="strict")) for n in sorted(z.namelist()) if n.endswith(".sparql")]
    summary=collections.Counter("strict_supported" if r.get("strict_2to6_constant_BGP_eligible")
      else ("parse_failure" if "parse_failure" in r else "strict_rejected") for r in rows)
    result={"schema":"candidate3-LargeRDFBench-2026-original-SPARQL-source-only-eligibility-v1",
      "frozen_protocol_commit":"6a7de564f5de21fa4124a1de0846ca3ad6bc7fd7",
      "query_zip_original_md5":SHA,"n_query_templates":len(rows),
      "strict_eligibility_counts":dict(summary),
      "original_source_query_shapes":rows,
      "rdf_source_dataset_triples_unopened":True,
      "expected_answers_unopened":True,
      "hard_stop_gate":"BLOCKED_FOR_INDEPENDENT_20_FAMILY_PROOF" if summary["strict_supported"]<20 else "PROCEED_TO_EXACT_GRAPH_COVERAGE_CHECK",
      "limitations":[
        "This is only structural query eligibility, does not verify that any query is single-graph executable",
        "Original LargeRDFBench benchmark is federated and may require more than one original dataset",
        "Actual original query outputs and all published expected results remain sealed"]}
    (OUT/"report.json").write_text(json.dumps(result,indent=2))
    print("LARGERDF_QUERY_CONTRACT_START",flush=True);print(json.dumps(result,indent=2),flush=True)
    print("LARGERDF_QUERY_CONTRACT_END",flush=True)
if __name__=="__main__":main()
