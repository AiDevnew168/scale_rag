#!/usr/bin/env python3
"""Four independent RDF shard PROCESSES + Oxigraph coordinator execution.

Every worker runs actual SPARQL CONSTRUCT to retrieve predicate-local triples.
The coordinator unions returned triples and executes the ORIGINAL SELECT on a
fresh Oxigraph store, verifying its full multiset against the centralized
Oxigraph result on the identical data. Explicit no-query-during-swap barrier.
Physical movement: add to opposite worker, verify receipt, then DELETE WHERE
in the original worker (not transactionally atomic across a multi-host fleet).

NOT a native distributed SPARQL query optimizer, nor production latency proof.
Previously discovered exact duplicates in original 40-query file eliminated:
10 distinct training vs 10 disjoint test templates.
"""
import concurrent.futures, hashlib, json, multiprocessing as mp, random, statistics
import threading, time, urllib.request, zipfile
from collections import Counter,defaultdict
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_streamwatdiv_microshard as core

OUT=Path("results_candidate3_real_spql_shards");OUT.mkdir(exist_ok=True)
SEED=20261121
MAX_ROWS=20000
N_SHARDS=4

def payloads_by_shard(pred,sizes,cap):
    # Byte-exact reconstruction of the already-audited deterministic placement.
    buffers=[defaultdict(bytearray) for _ in range(4)]
    loads=[0]*4;locations=defaultdict(set)
    for p,n in sorted(sizes.items(),key=lambda z:(-z[1],z[0])):
        j=min(range(4),key=lambda i:(loads[i],i))
        if loads[j]+n<=cap:
            buffers[j][p].extend(b"".join(pred[p]));loads[j]+=n;locations[p].add(j)
        else:
            for line in pred[p]:
                j=min(range(4),key=lambda i:(loads[i],i))
                buffers[j][p].extend(line);loads[j]+=len(line);locations[p].add(j)
    assert sum(loads)==sum(sizes.values())
    assert max(loads)<=cap
    return [{p:bytes(b) for p,b in shard.items()} for shard in buffers],loads,dict(locations)

def evaluate(store,query):
    result=store.query(query)
    variables=[v.value for v in result.variables]
    rows=Counter()
    count=0
    for sol in result:
        count+=1
        if count>MAX_ROWS:raise RuntimeError("result exceeds audited row cap")
        rows[tuple(str(sol[var]) if sol[var] is not None else "" for var in variables)]+=1
    serial=json.dumps(sorted([(r,n) for r,n in rows.items()]),ensure_ascii=False,separators=(",",":"))
    return {"count":count,"hash":hashlib.sha256(serial.encode()).hexdigest()}

def serve(worker_id, data, ready):
    # Each independent process owns its own Oxigraph index and its own TCP server.
    db=Store()
    db.bulk_load(input=b"".join(chunk for chunk in data.values()),format=RdfFormat.N_TRIPLES)
    lock=threading.RLock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,code,payload,mime="application/octet-stream"):
            self.send_response(code);self.send_header("Content-Length",str(len(payload)))
            self.send_header("Content-Type",mime);self.end_headers();self.wfile.write(payload)
        def do_GET(self):
            if self.path!="/health":return self.reply(404,b"not found")
            with lock:
                payload=json.dumps({"worker":worker_id,"triples":len(db)}).encode()
            self.reply(200,payload,"application/json")
        def do_POST(self):
            size=int(self.headers.get("Content-Length","0"))
            if size>16*1024*1024:return self.reply(413,b"too large")
            body=self.rfile.read(size)
            if self.path=="/construct":
                req=json.loads(body)
                pieces=[]
                with lock:
                    for p in req["predicates"]:
                        # Actual Oxigraph distributed predicate-fragment SPARQL.
                        q=f"CONSTRUCT {{ ?s {p} ?o }} WHERE {{ ?s {p} ?o }}"
                        pieces.append(db.query(q).serialize(format=RdfFormat.N_TRIPLES))
                return self.reply(200,b"".join(pieces))
            if self.path=="/insert":
                p=self.headers["X-Predicate"]
                with lock:
                    db.bulk_load(input=body,format=RdfFormat.N_TRIPLES)
                return self.reply(200,json.dumps({"sha256":hashlib.sha256(body).hexdigest(),
                      "bytes":len(body),"predicate":p}).encode(),"application/json")
            if self.path=="/delete":
                p=json.loads(body)["predicate"]
                with lock:
                    db.update(f"DELETE WHERE {{ ?s {p} ?o }}")
                return self.reply(200,b'{"deleted":true}',"application/json")
            return self.reply(404,b"unknown path")
    s=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    ready.put({"worker":worker_id,"port":s.server_address[1],"triples":len(db)})
    s.serve_forever()

def call(port,path,data=b"",headers=None,timeout=25):
    req=urllib.request.Request(f"http://127.0.0.1:{port}{path}",data=data,headers=headers or {})
    t=time.perf_counter()
    with urllib.request.urlopen(req,timeout=timeout) as resp:body=resp.read()
    return body,(time.perf_counter()-t)*1000

def fetch_query(query,route,ports,parallel=True):
    grouped=defaultdict(list)
    for p in sorted(set(core.TRIP.findall(query))):
        if p not in route:raise ValueError("unknown predicate "+p)
        for j in route[p]:grouped[j].append(p)
    assert grouped
    t=time.perf_counter()
    tasks=[(j,json.dumps({"predicates":ps}).encode()) for j,ps in sorted(grouped.items())]
    def request(tup):
        shard,body=tup
        returned,ms=call(ports[shard],"/construct",body,{"Content-Type":"application/json"})
        return shard,returned,ms
    if parallel:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            replies=list(pool.map(request,tasks))
    else:replies=list(map(request,tasks))
    net_ms=(time.perf_counter()-t)*1000
    payload=b"".join(b for j,b,ms in replies)
    load=Store()
    load.bulk_load(input=payload,format=RdfFormat.N_TRIPLES)
    res=evaluate(load,query)
    total_ms=(time.perf_counter()-t)*1000
    return {"correctness":res,"shards":len(grouped),
      "network_bytes":sum(len(b) for _,b,_ in replies),
      "fetched_ntriples":len(load),"network_ms":round(net_ms,4),
      "total_query_ms":round(total_ms,4)}

def transfer_pair(pair,pred,route,ports):
    p,q=pair
    assert len(route[p])==len(route[q])==1
    left=next(iter(route[p]));right=next(iter(route[q]))
    assert left!=right
    t=time.perf_counter()
    records=[]
    # The coordinator's read barrier is active; no other query executes here.
    for key,target in ((p,right),(q,left)):
        data=b"".join(pred[key]);sha=hashlib.sha256(data).hexdigest()
        response,ms=call(ports[target],"/insert",data,{"X-Predicate":key},timeout=60)
        received=json.loads(response)
        assert received["sha256"]==sha
        records.append({"predicate":key,"bytes":len(data),"target":target,
                        "sha256":sha,"insert_ms":round(ms,4)})
    for key,old in ((p,left),(q,right)):
        ret,ms=call(ports[old],"/delete",json.dumps({"predicate":key}).encode(),
                    {"Content-Type":"application/json"},timeout=60)
        assert json.loads(ret)["deleted"]
    route=route.copy()
    route[p]={right};route[q]={left}
    return route,{"records":records,"moved_bytes":sum(x["bytes"] for x in records),
        "coordinator_barrier_ms":round((time.perf_counter()-t)*1000,4),
        "is_multi_host_transaction":False}

def percentile(x,p):
    y=sorted(x)
    return round(y[min(len(y)-1,max(0,int((len(y)-1)*p)))],4)

def main():
    with core.read_archive() as z:
        lines=z.read("static.nt").splitlines(keepends=True)
        events=z.read("stream-events.jsonl").splitlines()
        for item in events:
            obj=json.loads(item)
            for triple in obj["triples"]:lines.append(triple.encode()+b"\n")
        raw=[q.strip() for q in z.read("queries.sparql").decode().splitlines()
             if q.strip().startswith("SELECT")]
    hashes={hashlib.sha256(q.encode()).hexdigest():q for q in raw}
    assert len(raw)==40 and len(hashes)==20
    rng=random.Random(SEED);order=sorted(hashes);rng.shuffle(order)
    cut=len(order)//2
    train=[hashes[h] for h in order[:cut]]
    test=[hashes[h] for h in order[cut:]]
    assert not(set(order[:cut])&set(order[cut:]))
    pred,sizes,heavy,split,part,expected_loads,cap,_=core.disk_layout(lines)
    payloads,loads,route=payloads_by_shard(pred,sizes,cap)
    assert loads==expected_loads
    train_ps=[tuple(sorted(set(core.TRIP.findall(q)))) for q in train]
    pair,meta,_=core.optimize(train_ps,part,sizes,split,loads,cap,"maximize_observed")
    assert pair
    # Genuine *complete* reference query engine.
    central=Store()
    central.bulk_load(input=b"".join(lines),format=RdfFormat.N_TRIPLES)
    central_n=len(central)
    truth={hashlib.sha256(q.encode()).hexdigest():evaluate(central,q) for q in test}
    nonempty=sum(1 for r in truth.values() if r["count"]>0)
    assert nonempty>=1, "No nonempty heldout queries; cannot claim meaningful QA equality"
    ready=mp.Queue();workers=[]
    try:
        for i,data in enumerate(payloads):
            proc=mp.Process(target=serve,args=(i,data,ready),daemon=True)
            proc.start();workers.append(proc)
        init=[ready.get(timeout=100) for _ in range(4)]
        ports={x["worker"]:x["port"] for x in init}
        assert len(ports)==4
        checks={}
        for phase in ("fixed","swapped"):
            methods={}
            for mode in ("serial","parallel"):
                rows=[]
                for query in test:
                    h=hashlib.sha256(query.encode()).hexdigest()
                    res=fetch_query(query,route,ports,parallel=(mode=="parallel"))
                    if res["correctness"]!=truth[h]:
                        raise AssertionError(f"FULL ANSWER MISMATCH phase={phase} mode={mode} query={h}")
                    rows.append(res)
                times=[r["total_query_ms"] for r in rows]
                methods[mode]={"n":len(rows),"nonempty_ground_truth_queries":nonempty,
                  "passed_full_multiset_exactness":len(rows),
                  "p50_ms":round(statistics.median(times),4),
                  "p95_ms":percentile(times,.95),
                  "mean_ms":round(statistics.mean(times),4),
                  "total_ms":round(sum(times),4),
                  "network_bytes":sum(r["network_bytes"] for r in rows),
                  "total_shard_calls":sum(r["shards"] for r in rows),
                  "query_trace":rows}
            checks[phase]=methods
            if phase=="fixed":
                route,migration=transfer_pair(pair,pred,route,ports)
        report={"schema":"candidate3-real-four-shard-oxigraph-query-and-migration-v1",
          "source_sha256":core.EXPECTED_SHA,
          "data_model":"static plus all stream insertion triples as a static union",
          "raw_triples":len(lines),"unique_central_rdf_triples":central_n,
          "physical_shard_bytes":loads,"byte_capacity_limit":cap,
          "exact_unique_query_texts":len(hashes),"n_unique_train":len(train),
          "n_unique_test":len(test),"train_test_hash_overlap":0,
          "nonempty_test_queries":nonempty,"query_result_limit":MAX_ROWS,
          "migration_proposed_on_train_only":pair,
          "migration_train_gain":meta,
          "migration":migration,"results":checks,
          "limitations":[
            "Four independent TCP shard processes and actual Oxigraph per-shard CONSTRUCT queries",
            "Coordinator retrieves needed predicate triples and runs full original SPARQL SELECT",
            "This is naive coordinator fragment materialization, NOT a native federated SPARQL query optimizer",
            "All stream events merged into a static graph, NOT a temporal stream replay",
            "No concurrent queries during migrations; not distributed atomic multi-host transaction",
            "Ten distinct heldout query templates, synthetic and previously inspected",
            "No actual across-machine network, no WISE/WASP replication baseline, no economic proof",
            "End-to-end latency includes all predicate fragments, materialization and query engine but not production queueing"] }
        OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
        summary={k:v for k,v in report.items() if k!="results"}
        summary["results"]={phase:{mode:{k:v for k,v in detail.items() if k!="query_trace"}
                  for mode,detail in methods.items()} for phase,methods in checks.items()}
        print("REAL_SPARQL_SHARDS_START",flush=True)
        print(json.dumps(summary,indent=2),flush=True)
        print("REAL_SPARQL_SHARDS_END",flush=True)
    finally:
        for p in workers:
            if p.is_alive():p.terminate()
            p.join(timeout=3)
if __name__=="__main__":main()
