#!/usr/bin/env python3
"""Physical RDF preflight + measured loopback transfer, NEVER a distributed net-benefit claim.

Read capped bytes of the official Wikimedia sample.nt *as real N-Triples*.
Group by June top120 predicates, measure exact serialized sample payload bytes
for previously frozen swaps, and report completeness limits.
Loopback transfer measures only moving the sampled payload in a test TCP server:
no full RDF join/query, disk durability, production latency or byte-balanced graph.
"""
import datetime, hashlib, json, os, re, socket, socketserver, struct, statistics, threading, time, urllib.request
from collections import Counter,defaultdict
from pathlib import Path
import temporal_wikidata as base

SOURCE="https://people.wikimedia.org/~gmodena/wikidata/data/sample.nt"
MAX_BYTES=32*1024*1024
OUT=Path("results_candidate3_physical_rdf");OUT.mkdir(exist_ok=True)
MATCH=re.compile(br"<http://www.wikidata.org/prop/direct/(P[0-9]+)>")
SWAPS={"january":(20,57),"february":(25,57),"march":(27,57)}
FUTURE_SAVINGS={"january":8688,"february":8898,"march":10315}
class Sink(socketserver.BaseRequestHandler):
    def handle(self):
        conn=self.request
        data=b""
        while len(data)<8:
            more=conn.recv(8-len(data))
            if not more:raise IOError("missing header")
            data+=more
        length=struct.unpack("!Q",data)[0]
        h=hashlib.sha256()
        while length:
            chunk=conn.recv(min(length,65536))
            if not chunk:raise IOError("truncated transfer")
            h.update(chunk);length-=len(chunk)
        conn.sendall(h.digest())
class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
    daemon_threads=True
def transfer(payload):
    with Server(("127.0.0.1",0),Sink) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        latencies=[]
        for _ in range(9):
            tic=time.perf_counter_ns()
            with socket.create_connection(server.server_address,timeout=10) as s:
                s.settimeout(10)
                s.sendall(struct.pack("!Q",len(payload)))
                s.sendall(payload)
                received=b""
                while len(received)<32:
                    buf=s.recv(32-len(received))
                    if not buf:raise IOError("missing receipt")
                    received+=buf
            elapsed=(time.perf_counter_ns()-tic)/1e6
            assert received==hashlib.sha256(payload).digest()
            latencies.append(elapsed)
        server.shutdown()
    latencies=sorted(latencies)
    return {"repetitions":len(latencies),"min_ms":round(latencies[0],4),
      "median_ms":round(statistics.median(latencies),4),
      "p95_nearest_ms":round(latencies[8],4),
      "all_ms":[round(x,4) for x in latencies]}

def load_source():
    digest=hashlib.sha256()
    collected=bytearray()
    meta={}
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"Academic-RDF-Economics-Preflight/1.0"})
    with urllib.request.urlopen(req,timeout=40) as r:
        meta={"response_status":r.status,"declared_content_length":r.headers.get("Content-Length"),
              "last_modified":r.headers.get("Last-Modified"),"content_type":r.headers.get("Content-Type")}
        while len(collected)<MAX_BYTES:
            c=r.read(min(1024*1024,MAX_BYTES-len(collected)))
            if not c:break
            collected.extend(c);digest.update(c)
    reached_cap=len(collected)>=MAX_BYTES
    # Do not parse incomplete trailing RDF triple line.
    content=bytes(collected)
    if content and not content.endswith(b"\n"):content=content[:content.rfind(b"\n")+1]
    return content,{"url":SOURCE,"downloaded_prefix_bytes":len(collected),
        "parsed_complete_line_prefix_bytes":len(content),"sample_prefix_sha256":digest.hexdigest(),
        "max_bytes":MAX_BYTES,"reached_cap":reached_cap,**meta}

def run():
    june,jsha=base.load()
    rows=[(d,q) for d,q in june if d<14]
    freq=Counter()
    for d,q in rows:freq.update(set(q))
    selected=tuple(x for x,_ in sorted(freq.items(),key=lambda v:(-v[1],v[0]))[:120])
    result={"schema":"candidate3-real-rdf-prefix-byte-migration-preflight-v1",
       "training_sha":jsha,"source":SOURCE,"swaps":SWAPS,
       "limitations":["Wikidata physical sample snapshot may not correspond in time to 2018 traffic",
       "Real N-Triples raw bytes from only a bounded download prefix, NOT complete predicate weights",
       "Not a byte-balanced global partition; no feasibility guarantee",
       "Loopback localhost TCP is an actual local transfer but NOT production distributed network",
       "Serialized raw text transfer only: no disk writes, triple-index rebuilding, cache invalidation, query waiting or join execution",
       "Extra-shard touches saved from query logs are not equivalent to RTT savings, so no economic proof"]}
    try:
        data,meta=load_source()
        result["sample"]=meta
        rec=defaultdict(bytearray);counts=Counter();total=0
        for line in data.splitlines(keepends=True):
            m=MATCH.search(line)
            if not m:continue
            prop=m.group(1).decode()
            if prop not in set(selected):continue
            rec[prop].extend(line);counts[prop]+=1;total+=len(line)
        result["ntriples_selected_matching_lines"]=sum(counts.values())
        result["ntriples_selected_matching_bytes"]=total
        result["selected_predicates_covered"]=len(counts)
        result["selected_predicates_total"]=120
        result["bytes_by_selected_predicate"]={p:len(rec[p]) for p in selected}
        result["sampled_predicate_sizes"]={p:counts[p] for p in selected}
        results={}
        for name,(a,b) in SWAPS.items():
            p,q=selected[a],selected[b]
            payload=bytes(rec[p])+bytes(rec[q])
            item={"predicate_names":[p,q],"ntriples_bytes_in_sample":len(payload),
                  "individual_bytes":[len(rec[p]),len(rec[q])],
                  "source_coverage_both_nonzero":bool(rec[p] and rec[q]),
                  "future_shard_touches_saved_on_historical_logs":FUTURE_SAVINGS[name]}
            if payload:item["local_loopback_transfer"]=transfer(payload)
            results[name]=item
        result["sampled_swaps"]=results
        result["preflight_status"]="sampled_bytes_only"
    except Exception as exc:
        result["preflight_status"]="unavailable_source_or_network_error"
        result["error"]=type(exc).__name__+": "+str(exc)[:350]
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("PHYSICAL_RDF_PREFLIGHT_START",flush=True)
    print(json.dumps({k:v for k,v in result.items() if k not in ("bytes_by_selected_predicate","sampled_predicate_sizes")},indent=2),flush=True)
    print("PHYSICAL_RDF_PREFLIGHT_END",flush=True)
if __name__=="__main__":run()
