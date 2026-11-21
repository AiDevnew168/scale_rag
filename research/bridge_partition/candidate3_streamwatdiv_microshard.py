#!/usr/bin/env python3
"""Independent synthetic benchmark: real RDF byte-balanced microsharding.

A heavy predicate is split physically among four shards so no unit exceeds a
10% byte-imbalance budget. Query routing is a CONSERVATIVE predicate fanout
proxy, NOT SPARQL join execution. First half generated templates train,
second half test. This does not validate production economics or novelty.
"""
import hashlib, io, itertools, json, re, socket, socketserver, statistics, struct, threading, time, urllib.request, zipfile
from collections import Counter, defaultdict
from pathlib import Path
SRC=("https://zenodo.org/records/23016810/files/"
 "stream-watdiv-static-1-stream-1-seed-42-q10-m6-c1.zip?download=1")
EXPECTED_SHA="b3f6f0447b9f78cc695953a0c1b5dd1144d5c400113493eecbb23f36d91d84b3"
OUT=Path("results_candidate3_streamwatdiv_microshard");OUT.mkdir(exist_ok=True)
# This is a simplified SPARQL triple-pattern parser for the generated benchmark only.
TRIP=re.compile(r'(?:\?\w+|<[^>]+>)\s+(<[^>]+>)\s+(?:\?\w+|<[^>]+>|"[^"]*")\s*\.')

def read_archive():
    req=urllib.request.Request(SRC,headers={"User-Agent":"ScaleRAG-2026-RDF-microshard/1.0"})
    with urllib.request.urlopen(req,timeout=90) as src:raw=src.read(16*1024*1024+1)
    if len(raw)>16*1024*1024:raise AssertionError("download cap")
    assert hashlib.sha256(raw).hexdigest()==EXPECTED_SHA
    return zipfile.ZipFile(io.BytesIO(raw))

def disk_layout(items):
    pred=defaultdict(list);siz=Counter()
    for ln in items:
        parts=ln.strip().split(None,2)
        if len(parts)<3:continue
        p=parts[1].decode()
        pred[p].append(ln);siz[p]+=len(ln)
    total=sum(siz.values());mean=total/4;cap=1.1*mean
    biggest=max(siz,key=siz.get)
    # If kept indivisible, impossible to balance when this is > cap.
    impossible=siz[biggest]>cap
    heavy=[bytearray() for _ in range(4)]
    for ln in pred[biggest]:
        idx=min(range(4),key=lambda i:len(heavy[i]))
        heavy[idx].extend(ln)
    balances=[len(h) for h in heavy]
    placement={}
    for p,n in sorted(siz.items(),key=lambda pair:(-pair[1],pair[0])):
        if p==biggest:continue
        j=min(range(4),key=lambda i:(balances[i],i))
        placement[p]=j;balances[j]+=n
    return pred,siz,biggest,heavy,placement,balances,cap,impossible

def spans(query,part,heavy):
    destinations=set()
    for p in query:
        if p==heavy:
            destinations.update(range(4))
        else:
            destinations.add(part[p])
    return len(destinations)

def gate(queries,part,heavy):
    n=len(queries)
    if not n:return {"n":0}
    z=[spans(q,part,heavy) for q in queries]
    return {"n":n,"local_pct":round(100*sum(s==1 for s in z)/n,4),
            "extra_shard_touches":sum(s-1 for s in z),
            "mean_shards":round(sum(z)/n,4)}

def optimize(train,part,siz,heavy,balances,cap,criterion):
    start=gate(train,part,heavy)["extra_shard_touches"]
    best_rank=None;best_pair=None;best_info=None
    valid=0
    for p,q in itertools.combinations(sorted(part),2):
        a,b=part[p],part[q]
        if a==b:continue
        newa=balances[a]-siz[p]+siz[q]
        newb=balances[b]-siz[q]+siz[p]
        if newa>cap or newb>cap:continue
        cand=part.copy();cand[p],cand[q]=b,a
        gain=start-gate(train,cand,heavy)["extra_shard_touches"]
        cost=siz[p]+siz[q]
        valid+=1
        if criterion=="maximize_observed":
            rank=(gain,-cost,-len(p+q))
        elif criterion=="gain_per_byte":
            rank=(gain/max(cost,1),gain,-cost)
        else:raise ValueError(criterion)
        if gain>0 and (best_rank is None or rank>best_rank):
            best_rank=rank;best_pair=(p,q);best_info={"gain_train":gain,"moved_raw_bytes":cost}
    return best_pair,best_info,valid

def migrate_payload(pair,pred):
    if not pair:return {"migrated":False,"moved_raw_bytes":0}
    payload=b"".join(pred[pair[0]])+b"".join(pred[pair[1]])
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            data=b""
            while len(data)<8:data+=self.request.recv(8-len(data))
            need=struct.unpack("!Q",data)[0];received=hashlib.sha256()
            while need:
                chunk=self.request.recv(min(65536,need))
                if not chunk:raise OSError("incomplete")
                received.update(chunk);need-=len(chunk)
            self.request.sendall(received.digest())
    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address=True;daemon_threads=True
    with Server(("127.0.0.1",0),Handler) as srv:
        t=threading.Thread(target=srv.serve_forever,daemon=True);t.start()
        repeats=[]
        for _ in range(7):
            tic=time.perf_counter_ns()
            with socket.create_connection(srv.server_address,timeout=10) as sock:
                sock.settimeout(10)
                sock.sendall(struct.pack("!Q",len(payload)))
                sock.sendall(payload)
                digest=b""
                while len(digest)<32:
                    more=sock.recv(32-len(digest))
                    if not more:raise IOError("missing")
                    digest+=more
            assert digest==hashlib.sha256(payload).digest()
            repeats.append((time.perf_counter_ns()-tic)/1e6)
        srv.shutdown()
    repeats.sort()
    return {"migrated":True,"moved_raw_bytes":len(payload),
            "local_loopback_median_ms":round(statistics.median(repeats),4),
            "local_loopback_p95_nearest_ms":round(repeats[-1],4),
            "verified_content_sha256":hashlib.sha256(payload).hexdigest()}

def main():
    with read_archive() as z:
        lines=z.read("static.nt").splitlines(keepends=True)
        raw=z.read("queries.sparql").decode("utf8")
    pred,siz,heavy,chunks,part,balances,cap,impossible=disk_layout(lines)
    query_lines=[x.strip() for x in raw.splitlines() if x.strip().startswith("SELECT")]
    queries=[tuple(sorted(set(TRIP.findall(q)))) for q in query_lines]
    unknown=Counter(p for q in queries for p in q if p not in siz)
    known=[q for q in queries if q and all(p in siz for p in q)]
    midpoint=max(1,len(known)//2)
    train,test=known[:midpoint],known[midpoint:]
    assert len(known)>=10 and len(test)>0
    baseline=gate(test,part,heavy)
    res={}
    for crit in ("maximize_observed","gain_per_byte"):
        pair,info,nvalid=optimize(train,part,siz,heavy,balances,cap,crit)
        modified=part.copy()
        if pair:
            a,b=part[pair[0]],part[pair[1]]
            modified[pair[0]],modified[pair[1]]=b,a
        after=gate(test,modified,heavy)
        res[crit]={"pair":pair,"selection_info":info,"byte_feasible_swap_count":nvalid,
            "heldout_test":after,
            "saved_extra_shard_touches_heldout":baseline["extra_shard_touches"]-after["extra_shard_touches"],
            "transfer":migrate_payload(pair,pred)}
    report={"schema":"candidate3-independent-physical-microshard-v1",
        "archive_sha256":EXPECTED_SHA,"static_rdf_ntriples":len(lines),
        "static_rdf_bytes":sum(siz.values()),
        "predicates":len(siz),"heavy_predicate":heavy,"heavy_predicate_bytes":siz[heavy],
        "indivisible_byte_balancing_impossible":impossible,
        "hard_shard_byte_cap":cap,"fragmented_shard_bytes":balances,
        "fragmentation_feasible":max(balances)<=cap,
        "heavy_chunks_bytes":[len(x) for x in chunks],
        "SPARQL_templates_found":len(query_lines),
        "usable_query_patterns":len(known),
        "unmatched_predicates":dict(unknown),
        "split":{"train_templates":len(train),"heldout_templates":len(test)},
        "heldout_baseline":baseline,"options":res,
        "limitations":["Only synthetic Stream WatDiv query templates (not organic logged frequencies)",
          "Train/test halves of a tiny template sample: NOT an independent large-scale confirmation",
          "Unbound heavy predicate routed conservatively to all 4 shards",
          "RDF physical transfer measured as verified TCP loopback payload only",
          "No SPARQL join execution, real server routing, queuing, capacity provision, CPU accounting",
          "Rebalancing heavy fragments and index rebuilding not included in migration cost",
          "No evidence of algorithmic novelty, production net savings or GraphRAG quality"] }
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("MICROSHARD_GATE_START");print(json.dumps(report,indent=2));print("MICROSHARD_GATE_END")
if __name__=="__main__":main()
