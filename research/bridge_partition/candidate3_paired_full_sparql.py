#!/usr/bin/env python3
"""Paired cluster-bootstrap A/B for full SPARQL with genuine shard processes.

Both alternatives use four independent Oxigraph-backed workers with identical
raw RDF-byte capacities and identical SELECT queries. The swapped alternative
is physically migrated during a query barrier, fixed stays static.
Ten exact-hash-disjoint test query templates; five randomized interleaved paired
repetitions per mode; bootstrap *query templates*, never repeat samples as
independent. Negative findings are allowed and must be reported.
"""
import hashlib, json, multiprocessing as mp, random, statistics
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_real_sparql_shards as engine
import candidate3_streamwatdiv_microshard as core

OUT=Path("results_candidate3_paired_sparql");OUT.mkdir(exist_ok=True)
SEED=20261121
REPS=5
BOOT=4000

def start_group(payloads):
    ready=mp.Queue();workers=[]
    for i,data in enumerate(payloads):
        proc=mp.Process(target=engine.serve,args=(i,data,ready),daemon=True)
        proc.start();workers.append(proc)
    metadata=[ready.get(timeout=120) for _ in range(4)]
    assert len({r["worker"] for r in metadata})==4
    return {r["worker"]:r["port"] for r in metadata},workers

def shutdown(group):
    for p in group:
        if p.is_alive():p.terminate()
        p.join(timeout=3)

def stat(values):
    return {"mean":round(statistics.mean(values),4),
            "p50":round(statistics.median(values),4),
            "p95_nearest":engine.percentile(values,.95)}

def repeat(test,truth,route_a,route_b,ports_a,ports_b,parallel):
    randomize=random.Random(SEED+(8 if parallel else 2))
    # Interleaved, randomized A/B order with identical per-query workload.
    diffs={i:[] for i in range(len(test))}
    tm_a={i:[] for i in range(len(test))}
    tm_b={i:[] for i in range(len(test))}
    bytes_a=bytes_b=touch_a=touch_b=0
    for q in test:  # symmetric warm-up before the timed window
        engine.fetch_query(q,route_a,ports_a,parallel)
        engine.fetch_query(q,route_b,ports_b,parallel)
    for rep in range(REPS):
        ix=list(range(len(test)));randomize.shuffle(ix)
        for i in ix:
            q=test[i];h=hashlib.sha256(q.encode()).hexdigest()
            if randomize.randrange(2):
                a=engine.fetch_query(q,route_a,ports_a,parallel)
                b=engine.fetch_query(q,route_b,ports_b,parallel)
            else:
                b=engine.fetch_query(q,route_b,ports_b,parallel)
                a=engine.fetch_query(q,route_a,ports_a,parallel)
            assert a["correctness"]==truth[h] and b["correctness"]==truth[h], "ANSWER MISMATCH"
            tm_a[i].append(a["total_query_ms"]);tm_b[i].append(b["total_query_ms"])
            diffs[i].append(a["total_query_ms"]-b["total_query_ms"])
            bytes_a+=a["network_bytes"];bytes_b+=b["network_bytes"]
            touch_a+=a["shards"];touch_b+=b["shards"]
    template_means=[statistics.mean(diffs[i]) for i in sorted(diffs)]
    bootstrap_rng=random.Random(SEED+(18 if parallel else 3))
    sims=sorted(sum(template_means[bootstrap_rng.randrange(len(template_means))]
        for _ in template_means) for __ in range(BOOT))
    flat_a=sum((tm_a[i] for i in sorted(tm_a)),[])
    flat_b=sum((tm_b[i] for i in sorted(tm_b)),[])
    return {"mode":"parallel" if parallel else "serial",
      "n_unique_test_templates":len(test),"repetitions_per_template":REPS,
      "n_full_answer_pairs":len(flat_a),
      "all_full_answers_match_central_store":True,
      "fixed":stat(flat_a),"swapped":stat(flat_b),
      "network_bytes_fixed":bytes_a,"network_bytes_swapped":bytes_b,
      "shard_contacts_fixed":touch_a,"shard_contacts_swapped":touch_b,
      "mean_saved_ms_per_one_10_query_batch":round(sum(template_means),4),
      "CI95_query_cluster_bootstrap_saved_ms_per_10query_batch":[round(sims[99],4),round(sims[3899],4)],
      "per_template_mean_saved_ms":[round(x,4) for x in template_means],
      "positive_paired_measurements":sum(v>0 for row in diffs.values() for v in row)}

def main():
    with core.read_archive() as z:
        lines=z.read("static.nt").splitlines(keepends=True)
        for raw in z.read("stream-events.jsonl").splitlines():
            e=json.loads(raw)
            lines.extend(t.encode()+b"\n" for t in e["triples"])
        querystrings=[q.strip() for q in z.read("queries.sparql").decode().splitlines()
                    if q.strip().startswith("SELECT")]
    uniques={hashlib.sha256(q.encode()).hexdigest():q for q in querystrings}
    assert len(querystrings)==40 and len(uniques)==20
    rng=random.Random(SEED);order=sorted(uniques);rng.shuffle(order)
    train=[uniques[h] for h in order[:10]]
    test=[uniques[h] for h in order[10:]]
    pred,siz,heavy,split,part,balances,cap,_=core.disk_layout(lines)
    packs,actual,route=engine.payloads_by_shard(pred,siz,cap)
    assert actual==balances
    pair,meta,_=core.optimize(
        [tuple(sorted(set(core.TRIP.findall(q)))) for q in train],
        part,siz,split,balances,cap,"maximize_observed")
    assert pair
    central=Store()
    central.bulk_load(input=b"".join(lines),format=RdfFormat.N_TRIPLES)
    truth={hashlib.sha256(q.encode()).hexdigest():engine.evaluate(central,q) for q in test}
    assert sum(x["count"]>0 for x in truth.values())>=1
    ports_a,workers_a=start_group(packs)
    ports_b,workers_b=start_group(packs)
    try:
        route_b,migration=engine.transfer_pair(pair,pred,route,ports_b)
        results={}
        for parallel in (False,True):
            key="parallel" if parallel else "serial"
            results[key]=repeat(test,truth,route,route_b,ports_a,ports_b,parallel)
            lo,hi=results[key]["CI95_query_cluster_bootstrap_saved_ms_per_10query_batch"]
            cost=migration["coordinator_barrier_ms"]
            results[key]["net_mean_ms_per_batch_after_migration"]=round(
                results[key]["mean_saved_ms_per_one_10_query_batch"]-cost,4)
            results[key]["CI95_net_ms_after_one_barrier_migration"]=[round(lo-cost,4),round(hi-cost,4)]
        report={"schema":"candidate3-full-sparql-paired-four-shard-a-b-v1",
          "archive_sha256":core.EXPECTED_SHA,
          "physical_bytes_each_shard":balances,
          "byte_cap":cap,
          "unique_train":len(train),"unique_test":len(test),
          "exact_text_hash_overlap":0,
          "complete_nonempty_test_queries":sum(x["count"]>0 for x in truth.values()),
          "selected_swap_train_only":pair,"training_gain":meta,
          "measured_barrier_migration":migration,
          "paired_results":results,
          "limitations":[
            "Both configurations each use 4 localhost TCP Oxigraph workers (8 processes simultaneously for fair paired A/B)",
            "Coordinator eagerly fetches predicate fragments and executes actual original SELECT; no native distributed join planning",
            "Stream triples accumulated, not a time-evolving RDF database",
            "Correctness signatures are full answer multiset count + cryptographic hash",
            "Experiment uses 10 unique query templates; 5 repeated measurements do NOT increase independent query count",
            "Network localhost, not independent physical servers",
            "Migration one-time with queries stopped, not a multi-host atomic live transaction",
            "Measured cost omits cache invalidation, index durability/recovery, power and enterprise provisioning",
            "WISE/WASP and memory-matched replication absent; novelty and net production cost unproven"] }
        OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
        print("PAIRED_SPARQL_START",flush=True)
        print(json.dumps(report,indent=2),flush=True)
        print("PAIRED_SPARQL_END",flush=True)
    finally:
        shutdown(workers_a);shutdown(workers_b)
if __name__=="__main__":main()
