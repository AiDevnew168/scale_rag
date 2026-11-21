#!/usr/bin/env python3
"""Controlled HTTP-less TCP routing-only replay against independent RDF template queries.

IMPORTANT: This is NOT SPARQL execution; endpoint only acknowledges a shard touch.
Compare serial and parallel routing; migration uses measured RDF payload transfer.
Claim economic break-even ONLY for this local component, not a distributed KG.
"""
import concurrent.futures, json, random, socket, socketserver, statistics, struct, threading, time
from collections import Counter
from pathlib import Path
import candidate3_streamwatdiv_microshard as core

OUT=Path("results_candidate3_tcp_router");OUT.mkdir(exist_ok=True)
class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        fd=self.request
        fd.settimeout(3)
        received=b""
        while len(received)<4:
            packet=fd.recv(4-len(received))
            if not packet:raise IOError("header lost")
            received+=packet
        n=struct.unpack("!I",received)[0]
        if n>65536:raise ValueError("overlarge")
        while n:
            packet=fd.recv(n)
            if not packet:raise IOError("payload lost")
            n-=len(packet)
        if self.server.delay_ms>0:time.sleep(self.server.delay_ms/1000)
        fd.sendall(b"OK")
class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True;daemon_threads=True
def contact(addr,qid):
    request=str(qid).encode()
    with socket.create_connection(addr,timeout=3) as sock:
        sock.settimeout(3)
        sock.sendall(struct.pack("!I",len(request))+request)
        received=b""
        while len(received)<2:
            b=sock.recv(2-len(received))
            if not b:raise IOError("bad response")
            received+=b
        assert received==b"OK"

def route(q,placement,split):
    r=set()
    for p in q:
        if p in split:r.update(int(j) for j in split[p])
        else:r.add(placement[p])
    return sorted(r)

def run_one(q,placement,split,servers,parallel,pool):
    destinations=route(q,placement,split)
    tic=time.perf_counter_ns()
    if parallel:
        jobs=[pool.submit(contact,servers[i].server_address,p) for p,i in enumerate(destinations)]
        for x in jobs:x.result()
    else:
        for i in destinations:contact(servers[i].server_address,i)
    return (time.perf_counter_ns()-tic)/1e6

def measure(test,before,after,split,servers,parallel,reps=5):
    old=[];new=[]
    by_template={i:[] for i in range(len(test))}
    rng=random.Random(20261121)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for q in test:
            run_one(q,before,split,servers,parallel,pool)
            run_one(q,after,split,servers,parallel,pool)
        pairs=[]
        for iteration in range(reps):
            order=list(range(len(test)));rng.shuffle(order)
            for j in order:
                q=test[j]
                if (iteration+j)%2:
                    vals=(run_one(q,before,split,servers,parallel,pool),
                          run_one(q,after,split,servers,parallel,pool))
                else:
                    right=run_one(q,after,split,servers,parallel,pool)
                    left=run_one(q,before,split,servers,parallel,pool)
                    vals=(left,right)
                old.append(vals[0]);new.append(vals[1]);pairs.append(vals[0]-vals[1]);by_template[j].append(vals[0]-vals[1])
    grouped=[statistics.mean(by_template[i]) for i in range(len(test))]
    boot_rng=random.Random(20261121)
    bootstrap=sorted(sum(grouped[boot_rng.randrange(len(grouped))] for _ in grouped) for _ in range(4000))
    return {"n_templates":len(grouped),"template_bootstrap_ci95_saved_ms_one_batch":[round(bootstrap[99],4),round(bootstrap[3899],4)],
        "per_template_mean_saved_ms":[round(v,4) for v in grouped],
        "n_pairs":len(pairs),"median_baseline_ms":round(statistics.median(old),4),
        "median_swap_ms":round(statistics.median(new),4),
        "mean_baseline_ms":round(statistics.mean(old),4),
        "mean_swap_ms":round(statistics.mean(new),4),
        "sum_saved_ms_over_all_measured_pairs":round(sum(pairs),4),
        "saved_ms_normalized_to_one_20_query_batch":round(sum(pairs)/reps,4),
        "paired_deltas_positive":sum(x>0 for x in pairs),
        "p95_baseline_ms":round(sorted(old)[int(.95*len(old))-1],4),
        "p95_swap_ms":round(sorted(new)[int(.95*len(new))-1],4)}

def main():
    with core.read_archive() as z:
        lines=z.read("static.nt").splitlines(keepends=True)
        for line in z.read("stream-events.jsonl").splitlines():
            event=json.loads(line)
            for triple in event.get("triples",[]):
                lines.append(triple.encode("utf8")+b"\n")
        querytext=z.read("queries.sparql").decode()
    pred,sizes,big,split,part,balances,cap,_=core.disk_layout(lines)
    assert max(balances)<=cap
    queries=[tuple(sorted(set(core.TRIP.findall(x)))) for x in querytext.splitlines() if x.strip().startswith("SELECT")]
    queries=[q for q in queries if q and all(p in sizes for p in q)]
    assert len(queries)==40
    train,test=queries[:20],queries[20:]
    pair,selection,_=core.optimize(train,part,sizes,split,balances,cap,"maximize_observed")
    assert pair
    new=part.copy();new[pair[0]],new[pair[1]]=part[pair[1]],part[pair[0]]
    assert core.gate(test,part,split)["extra_shard_touches"]==48
    assert core.gate(test,new,split)["extra_shard_touches"]==43
    physical=core.migrate_payload(pair,pred)
    servers=[Server(("127.0.0.1",0),Handler) for _ in range(4)]
    threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in servers]
    for t in threads:t.start()
    records={}
    try:
        for delay in (0,1,5):
            for s in servers:s.delay_ms=delay
            for mode in (False,True):
                label=("parallel" if mode else "serial")+f"_{delay}ms_injected_server_delay"
                values=measure(test,part,new,split,servers,mode)
                values["hypothetical_net_ms_one_batch_minus_median_migration"]=round(
                    values["saved_ms_normalized_to_one_20_query_batch"]-
                    physical["local_loopback_median_ms"],4)
                values["conservative_ci95_net_after_p95_migration_ms"]=[round(x-physical["local_loopback_p95_nearest_ms"],4) for x in values["template_bootstrap_ci95_saved_ms_one_batch"]]
                records[label]=values
    finally:
        for s in servers:s.shutdown();s.server_close()
    report={"schema":"candidate3-real-predicate-data-tcp-router-ack-microbenchmark-v1",
        "source_sha":core.EXPECTED_SHA,
        "kind":"TINY LOCAL TCP ACK-ONLY ROUTING OVERHEAD, NOT QUERY EXECUTION",
        "n_query_patterns_train":len(train),"n_query_patterns_test":len(test),
        "physical_bytes_by_shard":balances,"physical_capacity_upper_bound":cap,
        "physical_fragment_predicates":len(split),
        "one_swap_pair":pair,"migration":physical,
        "heldout_locality_baseline":core.gate(test,part,split),
        "heldout_locality_one_swap":core.gate(test,new,split),
        "route_overhead":records,
        "critical_limitations":[
           "Measured query endpoint acknowledges a TCP shard touch without performing any SPARQL join or index lookup",
           "Both strategies share same localhost servers; only activation count differs, not data or cached IO",
           "Migration separately measured to verified TCP sink, NOT applied atomically to those running servers",
           "Injected 1/5ms delay is a controlled sensitivity profile, not observed network RTT",
           "Small 20-query template holdout from synthetic RDF workload, not organic user log replay",
           "Results cannot prove production p95 latency, throughput, economic savings or new algorithm",
           "No extra-storage replication/caching matched-byte baseline"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("ROUTING_MICROBENCH_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("ROUTING_MICROBENCH_END",flush=True)
if __name__=="__main__":main()
