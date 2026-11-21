#!/usr/bin/env python3
"""SAME-RUN, SAME original author RDF+query baseline interoperability check.

Consumes UNMODIFIED original DIAERESIS DAP/Translator/Processor output files
created earlier in this exact GitHub Actions runner, then evaluates the same
three source queries and 51MB complete RDF graph on original Oxigraph and
four independent TCP Oxigraph worker indexes (source-identity preserving).
Equality of actual exact SELECT solution MULTISETS is proven within Oxigraph.
DIAERESIS author returns *row counts* only; compare counts, not pretend
its SQL output is a JSON-SPARQL term binding multiset. No fair CPU/storage
standardized direct speed advantage is claimed across engines.
"""
import collections,hashlib,json,math,os,re,statistics,time
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_real_sparql_shards as engine
import candidate3_source_identity_worker as workers
import candidate3_swdf_real_full_sparql_economics as core
from candidate3_sparql_semantic_certifier import certify,solution_rows

ROOT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"candidate3-DIAERESIS-author"
RAW=ROOT/"swdf"/"data"/"clean_swdf.nt"
QDIR=ROOT/"published_queries"
RESULTS=Path("results/SWDF_Author/4_bal")
OUT=Path("results_candidate3_diaeresis_same_source_comparison")
OUT.mkdir(exist_ok=True)
N=3
def parse_spark_results():
    by_query={}
    files=sorted(RESULTS.glob("results_*_bal.txt"))
    for path in files:
        lines=path.read_text(encoding="utf8",errors="replace")
        blocks=re.split(r"(?=Query:\s+query_\d+\.txt)",lines)
        for block in blocks:
            n=re.search(r"Query:\s+(query_\d+\.txt)",block)
            if not n:continue
            def field(k):
                t=re.search(r"(?m)^"+re.escape(k)+r":\s*(\d+)",block)
                return int(t.group(1)) if t else None
            key=n.group(1)
            row={"author_spark_result_count":field("Result_count"),
                 "author_spark_query_time_ms":field("Time"),
                 "author_spark_load_time_ms":field("Time_load"),
                 "author_spark_loaded_rows":field("Load_data")}
            assert all(v is not None for v in row.values()),(key,row)
            by_query[key]=row
    return by_query

def main():
    assert RAW.is_file() and RAW.stat().st_size==51587578,(RAW,RAW.exists())
    author_results=parse_spark_results()
    names=["query_0.txt","query_1.txt","query_2.txt"]
    assert sorted(author_results)==names,(author_results.keys(),names)
    raw=RAW.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    central=Store()
    central.load(input=raw,format=RdfFormat.N_TRIPLES)
    pred=collections.defaultdict(list);sizes=collections.Counter()
    for line in raw.splitlines(keepends=True):
        if not line.strip():continue
        pieces=line.split(None,2)
        assert len(pieces)==3 and pieces[1].startswith(b"<")
        p=pieces[1].decode("utf8")
        pred[p].append(line);sizes[p]+=len(line)
    assert sum(sizes.values())==len(raw)
    cap=math.ceil(len(raw)*1.1/4)
    packs,loads,route=engine.payloads_by_shard(pred,sizes,cap)
    fragmented={p for p in route if len(route[p])>1}
    ports,processes=workers.start_group(packs)
    result={"schema":"candidate3-real-author-DIAERESIS-vs-Oxigraph-same-source-query-check-v1",
      "author_original_commit":"22dfe190078973f644f5d6279181e54ec116f6e3",
      "author_full_original_three_stages_already_completed":True,
      "source_author_RDF_unmodified_sha256":sha,
      "source_author_original_triple_lines":len(raw.splitlines()),
      "source_author_oxigraph_unique_triples":len(central),
      "per_shard_raw_byte_cap":cap,
      "actual_shard_raw_bytes":loads,
      "frozen_3_unmodified_author_query_filenames":names,
      "query_checks":{},
      "conclusion":"DIAGNOSTIC_ONLY_NO_MATCHED_RUNTIME_SOTA",
      "limits":[
        "Original DIAERESIS returned only result counts; cannot verify original author SQL solution term multiset identity, only count equivalence.",
        "DIAERESIS Spark original DAP vertical/schema partitions vs Oxigraph original predicate-based 4 TCP stores, different physical planners.",
        "Same GitHub host, raw graph and original query strings, but sequential Spark vs Oxigraph runs, distinct cache/hot-path and resource allocations: wall times cannot prove algorithmic superiority.",
        "Only three original source queries are supported by original translator without uninitialized variable-predicate subPartIndex; insufficient statistical families.",
        "No migrations allowed on author DAP baseline, so no dynamic migration economic SOTA comparison.",
        "Same original author's source not future temporal user traffic, and no cross-host network or production billing."]}
    try:
        for name in names:
            q=(QDIR/name).read_text(encoding="utf8")
            # Original author 3 static predicate BGP SELECTs; rdflib-validated
            # source chosen BEFORE query performance in original pipeline.
            from rdflib.plugins.sparql.processor import prepareQuery
            from rdflib.plugins.sparql.parserutils import CompValue
            from rdflib.term import URIRef
            alg=prepareQuery(q).algebra
            triples=[]
            def walk(obj):
                if isinstance(obj,CompValue):
                    if obj.name=="BGP":triples.extend(obj["triples"])
                    for k,v in obj.items():
                        if k not in ("triples","_vars"):walk(v)
                elif isinstance(obj,(tuple,list)):
                    for t in obj:walk(t)
            walk(alg)
            pat=tuple(sorted(set("<"+str(p)+">" for _,p,_ in triples)))
            assert len(pat)>=1 and all(isinstance(p,URIRef) for _,p,_ in triples)
            group=core.shards_for_query(pat,route,fragmented)
            def get_fragment(item):
                j,ps=item
                payload=json.dumps({"predicates":sorted(ps)}).encode()
                content,ms=engine.call(ports[j],"/raw-fragments",payload,
                      {"Content-Type":"application/json"},timeout=90)
                return content
            via_shards=b"".join(get_fragment(item) for item in sorted(group.items()))
            reference_variables,refrows=solution_rows(central,q)
            physical=Store();physical.load(input=via_shards,format=RdfFormat.N_TRIPLES)
            semantic=certify(central,physical,q)
            t=[]
            for _ in range(N):
                tick=time.perf_counter()
                # source-predicate TCP fetch and query graph ingestion included
                parts=b"".join(get_fragment(item) for item in sorted(group.items()))
                store=Store()
                store.load(input=parts,format=RdfFormat.N_TRIPLES)
                solution_rows(store,q)
                t.append((time.perf_counter()-tick)*1000)
            author=author_results[name]
            result["query_checks"][name]={
                "hash":hashlib.sha256(q.encode()).hexdigest(),
                "original_author_spark":author,
                "central_reference_select_count":len(refrows),
                "oxigraph_four_worker_select_semantic_status":semantic["status"],
                "author_row_count_matches_central":author["author_spark_result_count"]==len(refrows),
                "source_total_fragment_bytes_loaded":len(via_shards),
                "n_predicates":len(pat),
                "n_physical_shard_contacts":len(group),
                "oxigraph_eager_TCPCoordinator_load_and_original_SELECT_mean_ms":round(statistics.mean(t),4),
                "oxigraph_eager_TCPCoordinator_load_and_original_SELECT_runs":N}
    finally:
        workers.stop_group(processes)
    result["all_three_author_counts_match_oxigraph_reference"]=all(
        x["author_row_count_matches_central"] for x in result["query_checks"].values())
    result["all_three_fourworker_original_select_legally_correct"]=all(
        x["oxigraph_four_worker_select_semantic_status"]=="PASS" for x in result["query_checks"].values())
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("DIAERESIS_MATCHED_SOURCE_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("DIAERESIS_MATCHED_SOURCE_END",flush=True)

if __name__=="__main__":main()
