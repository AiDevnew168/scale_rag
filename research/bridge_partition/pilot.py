#!/usr/bin/env python3
"""Held-out query-span diagnostic on real TopoGraphRAG page workloads.

NOT a new RAG retrieval model, not a distributed latency benchmark.
Train gold supports are a proxy for historic successful query traces;
test gold supports are ONLY used for evaluation.
"""
import hashlib, itertools, json, math, os, random, statistics, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import pymetis

SEED = 261119
ROOT = "https://huggingface.co/datasets/diandianone123/topographrag-bench/resolve/main/"
SCENARIO=os.environ.get("BRIDGE_SCENARIO","random")
assert SCENARIO in ("random","bridge_to_synthesis","synthesis_to_bridge")
OUT = Path("results_bridge_"+SCENARIO); OUT.mkdir(exist_ok=True)

def download(name):
    target = Path(name.rsplit("/", 1)[-1])
    if not target.exists():
        urllib.request.urlretrieve(ROOT + name, target)
    raw = target.read_bytes()
    print("SOURCE", name, len(raw), hashlib.sha256(raw).hexdigest(), flush=True)
    return json.loads(raw)

def pages(q):
    if q["question_type"] == "bridge_chain":
        return tuple(sorted({int(e["page_id"]) for e in q["evidence_sources"]}))
    if q["question_type"] == "synthesis":
        need = set((q.get("evidence_validation") or {}).get("required", []))
        pts = (q.get("answer") or {}).get("evidence_points", [])
        return tuple(sorted({int(e["source_page"]) for e in pts
                             if not need or e.get("fact_id") in need}))
    return ()

def part_contig(n, k):
    return [min(k-1, (i*k)//n) for i in range(n)]

def part_random(n, k, seed):
    rng = random.Random(seed)
    idx = list(range(n)); rng.shuffle(idx)
    labels = part_contig(n, k)
    part = [0]*n
    for i, node in enumerate(idx):part[node] = labels[i]
    return part

def metis_pages(n, k, training, weight):
    # First-order, query-blind document page graph.
    edges = defaultdict(int)
    for a in range(n-1):
        edges[(a,a+1)] += 100
    if weight:
        # Preserve all TRAIN query co-occurrences as a clique surrogate
        # (this is known workload-aware partitioning, not novelty).
        for q in training:
            pp = pages(q)
            m = len(pp)
            if m < 2:continue
            inc = max(1, int(round(weight * 2 / (m*(m-1)))))
            for a,b in itertools.combinations(pp,2):
                edges[(a,b)] += inc
    adj = [[] for _ in range(n)]
    for (u,v),w in sorted(edges.items()):
        if u == v:continue
        adj[u].append((v,w));adj[v].append((u,w))
    xadj=[0]; adjncy=[]; eweights=[]
    for neigh in adj:
        for v,w in sorted(neigh):
            adjncy.append(v);eweights.append(w)
        xadj.append(len(adjncy))
    _, membership = pymetis.part_graph(
        k, xadj=xadj, adjncy=adjncy, eweights=eweights,
        vweights=[1]*n, options=pymetis.Options(seed=SEED))
    # Enforce *identical hard per-shard maximum* to avoid buying lower span
    # through a larger shard. This is a standard local cut-gain repair, not novelty.
    membership=list(membership)
    cap=math.ceil(n/k)
    counts=Counter(membership)
    rounds=0
    while max(counts.values())>cap:
        moves=[]
        for u,old in enumerate(membership):
            if counts[old]<=cap:continue
            for target in range(k):
                if target==old or counts[target]>=cap:continue
                change=0
                for v,w in adj[u]:
                    change+=w*(int(target!=membership[v])-int(old!=membership[v]))
                moves.append((change,u,target,old))
        if not moves:raise AssertionError("No feasible balance repair move")
        change,u,target,old=min(moves)
        membership[u]=target
        counts[old]-=1
        counts[target]+=1
        rounds+=1
        if rounds>n*k:raise AssertionError("Balance repair did not terminate")
    assert max(counts.values())<=cap
    return membership

def min_active(pages_needed, primary, copies):
    pp=set(pages_needed)
    if not pp:return 0
    shards = {}
    for p in pp:
        shards[p] = {primary[p]} | {shard for node,shard in copies if node==p}
    k=max(primary)+1
    for s in range(1,k+1):
        for combo in itertools.combinations(range(k),s):
            used=set(combo)
            if all(shards[p] & used for p in pp):
                return s
    raise AssertionError("unreachable")

def replicate_greedy(primary, training, limit):
    """Historic-query-only greedy page replication, max 1 copy per source node."""
    if limit <= 0:return set()
    k=max(primary)+1
    occupied=set(); copies=set()
    candidates={(p,s) for q in training for p in pages(q)
                for s in range(k) if s != primary[p]}
    # The simple objective evaluates complete query localizability (1 shard).
    for _ in range(limit):
        scores=[]
        for pair in sorted(candidates):
            if pair[0] in occupied:continue
            gain=sum(min_active(pages(q), primary, copies) -
                     min_active(pages(q), primary, copies | {pair})
                     for q in training)
            if gain>0:scores.append((gain,pair))
        if not scores:break
        _,pair=max(scores,key=lambda x:(x[0],-x[1][0],-x[1][1]))
        copies.add(pair);occupied.add(pair[0])
    return copies

def replicate_frequency(primary, training, limit):
    """Equal-copy-count train-only popularity/neighbor-shard baseline."""
    if limit <= 0:return set()
    k=max(primary)+1
    freq=Counter(p for q in training for p in pages(q))
    candidates=[]
    for p,count in freq.items():
        for shard in range(k):
            if shard==primary[p]:continue
            neighbors=sum(1 for q in training if p in pages(q) and
                          any(primary[v]==shard for v in pages(q) if v!=p))
            candidates.append((neighbors,count,-p,-shard,(p,shard)))
    candidates.sort(reverse=True)
    selected=set();seen=set()
    for *_,pair in candidates:
        if pair[0] in seen:continue
        selected.add(pair);seen.add(pair[0])
        if len(selected)>=limit:break
    return selected

def metric(rows,mode):
    spans=[x[mode] for x in rows]
    return {"n":len(spans),
        "local_pct":round(100*sum(s==1 for s in spans)/len(spans),3),
        "mean_activated_shards":round(float(np.mean(spans)),4),
        "mean_extra_shards":round(float(np.mean(spans))-1,4),
        "p90_activated_shards":float(np.percentile(spans,90)),
        "spans":dict(Counter(map(str,spans)))}

def clustered_difference(rows, a, b, seed=SEED):
    docs=defaultdict(list)
    for r in rows:docs[r["doc_id"]].append(r)
    ids=sorted(docs)
    observed=100*np.mean([int(x[a]==1)-int(x[b]==1) for x in rows])
    rng=random.Random(seed)
    samples=[]
    for _ in range(2000):
        picked=[rng.choice(ids) for _ in ids]
        data=[r for d in picked for r in docs[d]]
        samples.append(100*np.mean([int(x[a]==1)-int(x[b]==1) for x in data]))
    return {"delta_local_pp":round(float(observed),3),
       "document_cluster_bootstrap_ci95_pp":list(map(lambda x:round(float(x),3),
                                                      np.percentile(samples,[2.5,97.5]))),
       "wins":sum(x[a]==1 and x[b]>1 for x in rows),
       "losses":sum(x[b]==1 and x[a]>1 for x in rows)}

def main():
    qs=download("annotations/benchmark.json")
    manifest=download("manifest.json")
    assert len(qs)==2024 and len(manifest["documents"])==201
    # Original PDF page image paths are metadata, not support labels.
    npages={int(d["doc_id"]):len(d["files"]["page_images"])
            for d in manifest["documents"]}
    grouped=defaultdict(list)
    skipped=Counter()
    for q in qs:
        pp=pages(q)
        if len(pp)<2:
            skipped["one_evidence_page"]+=1;continue
        d=int(q["doc_id"])
        if min(pp)<0 or max(pp)>=npages[d]:
            skipped["gold_page_out_of_pdf_range"]+=1;continue
        grouped[d].append(q)
    rng=random.Random(SEED)
    records=[]; split_manifest=[]; imbalance=defaultdict(list)
    for doc in sorted(grouped):
        n=npages[doc];allq=sorted(grouped[doc],
                 key=lambda q:q.get("mh_id") or q.get("sq_id") or "")
        if n<8 or len(allq)<4:
            skipped["small_doc_or_workload"]+=len(allq);continue
        rng.shuffle(allq)
        if SCENARIO=="random":
            ntrain=max(2,min(len(allq)-2,int(round(.6*len(allq)))))
            train,test=allq[:ntrain],allq[ntrain:]
        else:
            source,target=(("bridge_chain","synthesis") if SCENARIO=="bridge_to_synthesis"
                           else ("synthesis","bridge_chain"))
            train=[q for q in allq if q["question_type"]==source]
            test=[q for q in allq if q["question_type"]==target]
            if len(train)<2 or len(test)<1:
                skipped["missing_cross_type_workload"]+=len(allq);continue
        k=4
        labels={
            "contiguous":part_contig(n,k),
            "random":part_random(n,k,SEED+doc),
            "metis_structure":metis_pages(n,k,train,0),
            "metis_workload":metis_pages(n,k,train,400)
        }
        for name,lab in labels.items():
            counts=Counter(lab)
            assert set(counts)==set(range(k)),(doc,name,counts)
            imbalance[name].append(max(counts.values())/(n/k))
        # A separate operational strategy replicates a few source pages using
        # *only prior training-query traces*; no test annotations are consulted.
        # Hard cap: 5% extra copies of the original PDF page count, min 1.
        replication_limit=max(1,int(.05*n))
        replica=replicate_greedy(labels["metis_structure"],train,replication_limit)
        frequency_replica=replicate_frequency(labels["metis_structure"],train,len(replica))
        assert len(frequency_replica)==len(replica)
        split_manifest.append({"doc_id":doc,"pages":n,
          "train_ids":[q.get("mh_id") or q.get("sq_id") for q in train],
          "test_ids":[q.get("mh_id") or q.get("sq_id") for q in test],
          "replicas":len(replica),"replica_budget":replication_limit,
          "metis_structure_max_part_pages":max(Counter(labels["metis_structure"]).values()),
          "metis_workload_max_part_pages":max(Counter(labels["metis_workload"]).values())})
        for q in test:
            needed=pages(q)
            row={"doc_id":doc,"qid":q.get("mh_id") or q.get("sq_id"),
                 "type":q["question_type"],"n_evidence_pages":len(needed),
                 "n_document_pages":n}
            for name,lab in labels.items():
                row[name]=min_active(needed,lab,set())
            row["metis_structure_replicated"]=min_active(
                needed,labels["metis_structure"],replica)
            row["metis_structure_frequency_replicated"]=min_active(
                needed,labels["metis_structure"],frequency_replica)
            records.append(row)
    assert records and len({x["doc_id"] for x in records})>=20
    modes=("contiguous","random","metis_structure","metis_workload",
           "metis_structure_replicated","metis_structure_frequency_replicated")
    report={"schema":"bridge-partition-2026-feasibility-v1",
       "source_dataset":"diandianone123/topographrag-bench",
       "seed":SEED,"scenario":SCENARIO,"n_queries":len(records),"n_documents":len(split_manifest),
       "n_train_queries":sum(len(s["train_ids"]) for s in split_manifest),
       "skipped":dict(skipped),
       "methods":{mode:metric(records,mode) for mode in modes},
       "imbalance_max_over_ideal":{x:round(max(a),3) for x,a in imbalance.items()},
       "replica_copies_total":sum(s["replicas"] for s in split_manifest),
       "original_pages_total":sum(s["pages"] for s in split_manifest),
       "realized_copy_ratio_pct":round(100*sum(s["replicas"] for s in split_manifest)/sum(s["pages"] for s in split_manifest),3),
       "max_part_pages_exceed_ceil":{key:sum(d[key+"_max_part_pages"]>math.ceil(d["pages"]/4) for d in split_manifest)
         for key in ("metis_structure","metis_workload")},
       "by_query_kind":{kind:{method:metric([x for x in records if x["type"]==kind],method)
              for method in modes}
              for kind in ("bridge_chain","synthesis") if any(x["type"]==kind for x in records)},
       "replica_budget_total":sum(s["replica_budget"] for s in split_manifest),
       "paired":{
         "metis_workload_vs_metis_structure":clustered_difference(
             records,"metis_workload","metis_structure"),
         "metis_workload_vs_contiguous":clustered_difference(
             records,"metis_workload","contiguous"),
         "metis_structure_replicated_vs_metis_structure":clustered_difference(
             records,"metis_structure_replicated","metis_structure"),
         "replication_greedy_vs_frequency_at_equal_copies":clustered_difference(
             records,"metis_structure_replicated","metis_structure_frequency_replicated")},
       "cautions":["This is a page-shard placement diagnostic, NOT measured GraphRAG accuracy or latency",
         "Workload METIS and train-only replication are known algorithmic baselines, NOT novel algorithms",
         "Training uses gold support pages as a proxy for historic successful queries; deployment traces may be noisy",
         "All test queries unseen at layout construction, but share source documents with training workload",
         "Cross-type scenario tests transfer from one topology family to the other, not new document generalization",
         "No query-time retrieval, cross-encoder, graph extraction, remote networking, or LLM call",
         "Node weights are equal pages, not actual memory bytes; shards are balanced by page count",
         "Per-document replica allowance has minimum one copy, so 5 percent is not a hard global realized budget",
         "Numbers describe oracle evidence span, not whether a real router finds those partitions"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(x)+"\n" for x in records))
    OUT.joinpath("splits.json").write_text(json.dumps(split_manifest,indent=2))
    print("BRIDGE_PILOT_RESULT_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("BRIDGE_PILOT_RESULT_END",flush=True)
if __name__=="__main__":main()
