#!/usr/bin/env python3
"""Identity-preserving four-process RDF fragment endpoint.

Oxigraph CONSTRUCT may freshen blank-node labels across independent stores;
return the original source NTriples bytes for indexed predicates instead.
The worker STILL owns and mutates a real Oxigraph index for every insert and
delete; the coordinator runs the complete unchanged original SPARQL SELECT.
This is a physical *fragment store*, not a native federated query planner.
"""
import hashlib,json,threading,multiprocessing as mp,urllib.request
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pyoxigraph import Store,RdfFormat
import candidate3_selective_fetch_transport as selective

def serve(worker_id, data, ready):
    fragments={p:bytes(raw) for p,raw in data.items()}
    store=Store()
    store.bulk_load(input=b"".join(fragments.values()),format=RdfFormat.N_TRIPLES)
    lock=threading.RLock()
    parsed_source_cache={}  # lazy keyed by original predicate; immutable byte-identity
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,value):
            self.send_response(status)
            self.send_header("Content-Length",str(len(value)))
            self.send_header("Content-Type","application/octet-stream")
            self.end_headers()
            self.wfile.write(value)
        def do_GET(self):
            if self.path!="/health":return self.reply(404,b"missing")
            with lock:body=json.dumps({"worker":worker_id,"indexed_triples":len(store)}).encode()
            self.reply(200,body)
        def do_POST(self):
            n=int(self.headers.get("Content-Length","0"))
            if n>16*1024*1024:return self.reply(413,b"request-too-large")
            body=self.rfile.read(n)
            if self.path=="/raw-fragments":
                req=json.loads(body)
                if not isinstance(req.get("predicates"),list):
                    return self.reply(400,b"missing-predicates")
                with lock:
                    try:
                        # Preserve source blank-node lexical identity exactly.
                        parts=[fragments[p] for p in req["predicates"]]
                    except KeyError:return self.reply(409,b"predicate-not-here")
                return self.reply(200,b"".join(parts))
            if self.path=="/selective-fragments":
                # This endpoint is an optional TRAIN-only architectural control,
                # never a mutation or rewrite of the original SWDF requests.
                try:
                    req=json.loads(body)
                    filters=req["filters"]
                    if not isinstance(filters,dict) or not filters:
                        return self.reply(400,b"missing-filters")
                    with lock:
                        if not all(p in fragments for p in filters):
                            return self.reply(409,b"predicate-not-here")
                        response=b"".join(
                            selective.filter_fragment(fragments[p],clauses,
                                cache=parsed_source_cache,cache_key=p)
                            for p,clauses in sorted(filters.items()))
                except (ValueError,TypeError,KeyError,RuntimeError):
                    return self.reply(400,b"invalid-selective-request")
                return self.reply(200,response)
            if self.path=="/insert":
                p=self.headers["X-Predicate"]
                with lock:
                    if p in fragments:return self.reply(409,b"duplicate-fragment")
                    store.bulk_load(input=body,format=RdfFormat.N_TRIPLES)
                    fragments[p]=body
                    parsed_source_cache.pop(p,None)
                return self.reply(200,json.dumps({"sha256":hashlib.sha256(body).hexdigest(),
                     "bytes":len(body),"predicate":p}).encode())
            if self.path=="/delete":
                p=json.loads(body)["predicate"]
                with lock:
                    if p not in fragments:return self.reply(409,b"fragment-missing")
                    store.update(f"DELETE WHERE {{ ?s {p} ?o }}")
                    del fragments[p]
                    parsed_source_cache.pop(p,None)
                return self.reply(200,b'{"deleted":true}')
            return self.reply(404,b"unknown")
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    ready.put({"worker":worker_id,"port":server.server_address[1],"n_indexed":len(store)})
    server.serve_forever()

def start_group(packs):
    ready=mp.Queue()
    processes=[]
    for i,shard in enumerate(packs):
        p=mp.Process(target=serve,args=(i,shard,ready),daemon=True)
        p.start()
        processes.append(p)
    metadata=[ready.get(timeout=120) for _ in range(4)]
    assert len({x["worker"] for x in metadata})==4
    return {x["worker"]:x["port"] for x in metadata},processes

def stop_group(workers):
    for w in workers:
        if w.is_alive():w.terminate()
        w.join(timeout=4)
