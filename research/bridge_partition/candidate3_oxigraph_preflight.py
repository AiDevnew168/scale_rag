#!/usr/bin/env python3
"""Actual Oxigraph query preflight on pinned independent Stream WatDiv data.

All 40 original SELECT templates are attempted against the complete UNION of
static triples + all streamed insertion triples (NOT chronological snapshots).
Each query executes in a child process with a firm timeout. Counts and
nonempty outcomes preflight an end-to-end sharded query correctness test.
"""
import hashlib, json, os, pathlib, subprocess, sys, time
from collections import Counter
from pyoxigraph import Store,RdfFormat
import candidate3_streamwatdiv_microshard as core

OUT=pathlib.Path("results_candidate3_oxigraph_preflight")
OUT.mkdir(exist_ok=True)
QFILE=OUT/"queries.json"
DB=OUT/"central_store"
QUERY_TIMEOUT_SEC=12
ROW_CAP=20000

def load_data():
    with core.read_archive() as zipfile:
        lines=zipfile.read("static.nt").splitlines(keepends=True)
        static=len(lines)
        for raw in zipfile.read("stream-events.jsonl").splitlines():
            e=json.loads(raw)
            for triple in e["triples"]:
                lines.append(triple.encode("utf8")+b"\n")
        queries=[ln.strip() for ln in zipfile.read("queries.sparql").decode("utf8").splitlines()
                 if ln.strip().startswith("SELECT")]
    assert len(queries)==40
    all_bytes=b"".join(lines)
    return static,len(lines),all_bytes,queries

def child(qid):
    queries=json.loads(QFILE.read_text())
    q=queries[qid]
    store=Store.read_only(str(DB))
    t=time.perf_counter()
    sols=store.query(q)
    count=0
    hash_sum=0
    hash_xor=0
    for solution in sols:
        count+=1
        if count>ROW_CAP:
            print(json.dumps({"qid":qid,"status":"row_cap","rows_at_least":count,"seconds":time.perf_counter()-t}),flush=True)
            return
        row="\x1f".join(str(x) if x is not None else "" for x in solution)
        h=int.from_bytes(hashlib.blake2b(row.encode(),digest_size=16).digest(),"big")
        hash_sum=(hash_sum+h)%(1<<128)
        hash_xor^=h
    print(json.dumps({"qid":qid,"status":"complete","rows":count,"seconds":round(time.perf_counter()-t,4),
          "multiset_sum_128":f"{hash_sum:032x}","xor_128":f"{hash_xor:032x}"}),flush=True)

def main():
    start=time.perf_counter()
    static,ntrips,data,queries=load_data()
    QFILE.write_text(json.dumps(queries))
    store=Store(str(DB))
    store.bulk_load(input=data,format=RdfFormat.N_TRIPLES)
    exact_count=len(store)
    del store
    reports=[]
    for qid in range(len(queries)):
        try:
            cmd=[sys.executable,str(pathlib.Path(__file__).resolve()),"--query",str(qid)]
            proc=subprocess.run(cmd,text=True,capture_output=True,timeout=QUERY_TIMEOUT_SEC)
            if proc.returncode!=0:
                result={"qid":qid,"status":"error","returncode":proc.returncode,
                        "stderr":proc.stderr[-450:]}
            else:
                result=json.loads(proc.stdout.strip().splitlines()[-1])
        except subprocess.TimeoutExpired:
            result={"qid":qid,"status":"timeout","timeout_sec":QUERY_TIMEOUT_SEC}
        reports.append(result)
        print("QUERY_PREFLIGHT_PROGRESS",json.dumps(result),flush=True)
    s=Counter(d["status"] for d in reports)
    query_hashes=[hashlib.sha256(q.encode("utf8")).hexdigest() for q in queries]
    split_overlap=set(query_hashes[:20]) & set(query_hashes[20:])
    repeat_groups={h:[i for i,x in enumerate(query_hashes) if x==h] for h in set(query_hashes)}
    nonempty=[x["qid"] for x in reports if x["status"]=="complete" and x["rows"]>0]
    summary={"schema":"candidate3-real-oxigraph-central-query-preflight-v1",
      "source_archive_sha256":core.EXPECTED_SHA,"static_triples_raw":static,
      "static_plus_stream_triples_raw":ntrips,
      "unique_triples_in_oxigraph":exact_count,
      "ntriples_serialized_bytes":len(data),
      "query_templates":len(queries),
      "query_identity_audit":{"unique_exact_templates":len(set(query_hashes)),
         "train_first20_vs_test_last20_exact_hash_overlap":len(split_overlap),
         "duplicate_groups":[v for v in repeat_groups.values() if len(v)>1]},
      "query_timeout_sec":QUERY_TIMEOUT_SEC,
      "row_cap":ROW_CAP,"status_counts":dict(s),"nonempty_complete_query_ids":nonempty,
      "query_results":reports,"elapsed_sec":round(time.perf_counter()-start,2),
      "limitations":[
       "Real SPARQL 1.1 engine query execution; not just shard-contact acknowledgement",
       "Full union of historical stream insertions, not temporal per-event evaluation",
       "Original synthetic generated query templates (not independent organic workload)",
       "No actual distributed shard execution in this preflight",
       "Timeout and row-cap results may NOT be counted as correctness passes",
       "No WISE or matched-memory replication baseline"] }
    (OUT/"report.json").write_text(json.dumps(summary,indent=2))
    print("OXIGRAPH_PREFLIGHT_START",flush=True);print(json.dumps(summary,indent=2),flush=True);print("OXIGRAPH_PREFLIGHT_END",flush=True)
if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--query":child(int(sys.argv[2]))
    else:main()
