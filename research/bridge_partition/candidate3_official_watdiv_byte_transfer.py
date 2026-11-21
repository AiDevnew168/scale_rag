#!/usr/bin/env python3
"""Locked *new* original WatDiv 10M physical-byte stress-workload transfer test.

Independent synthetic benchmark family vs 2018 Wikidata and StreamWatDiv small.
Full official 10M N-Triples graph: exact per-predicate raw byte weights from
streaming 1.54GB N-Triples (never load graph in memory). Official stress-100:
warmup selects observed-only moves, five independently named test workloads
score only. All duplicate EXACT queries between warmup and test are excluded
in separate disjoint evaluations. Data is NOT an organic timestamped query log.
No actual cross-server SPARQL joins or physical migration performed here.
"""
import hashlib, io, json, math, re, tarfile, urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from statistics import mean
ROOT="https://dsg.uwaterloo.ca/watdiv/"
DATA="watdiv.10M.tar.bz2"
QUERIES="stress-workloads.tar.gz"
HASH_GRAPH="1d0a8a4725c98974eb7347ce3e6d9cab44f9f40389589809674254151b745af6"
HASH_QUERY="98796d4c8db67a1f68b3d1958d8f1334d5d38fe6da1c5e8eae72a8823ac7eed5"
PRED=re.compile(r'(?:\?\w+|<[^>]+>)\s+(<[^>]+>)\s+(?:\?\w+|<[^>]+>|"[^"]*")\s*\.')
OUT=Path("results_candidate3_official_watdiv");OUT.mkdir(exist_ok=True)

def grab(path,cap,digest):
    req=urllib.request.Request(ROOT+path,headers={"User-Agent":"Candidate3-third-family-locked-WatDiv-eval/1.0"})
    data=bytearray();h=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=120) as r:
        while True:
            b=r.read(1024*1024)
            if not b:break
            if len(data)+len(b)>cap:raise RuntimeError("official archive cap exceeded")
            data.extend(b);h.update(b)
    assert h.hexdigest()==digest,(path,h.hexdigest())
    return bytes(data)

def physical_size_table(archive):
    b=Counter();lines=0;total=0;max_line=0
    # Streaming tar reader; decompresses official full 10M NTriples exactly once.
    with tarfile.open(fileobj=io.BytesIO(archive),mode="r|bz2") as tar:
        first=next(x for x in tar if x.isfile())
        assert first.name=="watdiv.10M.nt"
        with tar.extractfile(first) as src:
            for line in src:
                if not line.strip():continue
                parts=line.split(None,2)
                if len(parts)<3:raise ValueError(f"Invalid NTriple line {lines}")
                p=parts[1].decode()
                b[p]+=len(line)
                total+=len(line);lines+=1
                max_line=max(max_line,len(line))
    assert len(b)>=20 and lines>1000000 and total>100000000
    return b,{"source_NTriples":first.name,
       "triples_parsed":lines,"raw_total_bytes":total,
       "max_single_triple_line_bytes":max_line,
       "predicate_count":len(b),"top_predicates_bytes":b.most_common(15)}

def parse_workloads(archive):
    groups={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode="r:gz") as t:
        names=["watdiv-stress-100/warmup.sparql"]+[
            f"watdiv-stress-100/test.{i}.sparql" for i in range(1,6)]
        for name in names:
            member=t.getmember(name)
            data=t.extractfile(member).read()
            lines=[line.strip() for line in data.decode("utf8").splitlines() if line.strip()]
            assert len(lines)>1000 and all(line.startswith("SELECT") for line in lines)
            seen=set();records=[]
            for q in lines:
                props=tuple(sorted(set(PRED.findall(q))))
                seen.add(hashlib.sha256(q.encode()).hexdigest())
                records.append({"pattern":props,"text_hash":hashlib.sha256(q.encode()).hexdigest()})
            groups[name]={"records":records,"n_unique_texts":len(seen),
                          "raw_file_sha256":hashlib.sha256(data).hexdigest()}
    return groups

def byte_layout(weights):
    total=sum(weights.values());cap=math.ceil(1.1*total/4)
    loads=[0,0,0,0];route={};single={}
    for p,w in sorted(weights.items(),key=lambda x:(-x[1],x[0])):
        target=min(range(4),key=lambda j:(loads[j],j))
        if loads[target]+w<=cap:
            single[p]=target;route[p]={target};loads[target]+=w
            continue
        remaining=w;places=set()
        for j in sorted(range(4),key=lambda j:(loads[j],j)):
            avail=cap-loads[j]
            take=min(remaining,avail)
            if take:
                places.add(j);loads[j]+=take;remaining-=take
            if remaining==0:break
        assert remaining==0,(p,w,loads,cap)
        route[p]=places
    assert sum(loads)==total and max(loads)<=cap
    return single,route,loads,cap

def span(route,q):
    return len(set().union(*(route[p] for p in q)))

def metric(recs,route):
    spans=[span(route,r["pattern"]) for r in recs]
    return {"n":len(spans),
      "extra_shard_touches":sum(x-1 for x in spans),
      "local_pct":round(100*sum(x==1 for x in spans)/len(spans),4) if spans else None,
      "mean_shards":round(sum(spans)/len(spans),5) if spans else None}

def candidate(original,weights,loads,cap,observed):
    pats=Counter(r["pattern"] for r in observed)
    distinct=list(pats)
    counts=list(pats.values())
    old=[span(original,p) for p in distinct]
    linked=defaultdict(set)
    for i,p in enumerate(distinct):
        for x in p:linked[x].add(i)
    available=sorted(p for p in weights if len(original[p])==1)
    methods={"head_local":{"score":(0,0),"pair":None,"observed_gain":0,"move_bytes":0},
             "all_touches":{"score":(0,0),"pair":None,"observed_gain":0,"move_bytes":0},
             "gain_per_byte":{"score":(0,0),"pair":None,"observed_gain":0,"move_bytes":0}}
    examined=0;feasible=0;possible=[]
    for i,p in enumerate(available):
        for q in available[i+1:]:
            a=next(iter(original[p]));b=next(iter(original[q]))
            if a==b:continue
            examined+=1
            size_p,size_q=weights[p],weights[q]
            if loads[a]-size_p+size_q>cap or loads[b]-size_q+size_p>cap:continue
            feasible+=1
            new=original.copy()
            new[p]={b};new[q]={a}
            local=touch=0
            for idx in linked[p]|linked[q]:
                now=span(new,distinct[idx])
                touch+=(old[idx]-now)*counts[idx]
                local+=(int(now==1)-int(old[idx]==1))*counts[idx]
            migrated=size_p+size_q
            possible.append((p,q,local,touch,migrated))
            ranking={"head_local":(local,touch),
                     "all_touches":(touch,local),
                     "gain_per_byte":(touch/max(1,migrated),touch)}
            for name,score in ranking.items():
                if score>methods[name]["score"] and score[0]>0:
                    methods[name]={"score":score,"pair":[p,q],
                      "observed_local_gain":local,"observed_touches_saved":touch,
                      "move_bytes":migrated}
    assert examined>500,(examined,feasible)
    decisions={}
    for name,m in methods.items():
        q=m["pair"];new=original.copy()
        if q:
            a=next(iter(original[q[0]]));b=next(iter(original[q[1]]))
            new[q[0]]={b};new[q[1]]={a}
        decisions[name]={"placement":new,"decision":m}
    return decisions,{"swaps_considered":examined,"byte_capacity_feasible_swaps":feasible,
                      "nontrivial_alternatives_count":len(possible)}

def main():
    graph=grab(DATA,85*1024*1024,HASH_GRAPH)
    weights,physical=physical_size_table(graph)
    del graph
    corpora=parse_workloads(grab(QUERIES,40*1024*1024,HASH_QUERY))
    for group in corpora.values():
        bad=[r for r in group["records"] if len(r["pattern"])<2 or any(p not in weights for p in r["pattern"])]
        group["unparsable_or_unmatched_queries"]=len(bad)
        group["eligible_records"]=[r for r in group["records"] if len(r["pattern"])>=2
                                  and all(p in weights for p in r["pattern"])]
    train=corpora["watdiv-stress-100/warmup.sparql"]["eligible_records"]
    seen_patterns={r["pattern"] for r in train}
    train_hashes={r["text_hash"] for r in train}
    static,layout,loads,cap=byte_layout(weights)
    decisions,diag=candidate(layout,weights,loads,cap,train)
    all_groups={}
    for k in range(1,6):
        name=f"watdiv-stress-100/test.{k}.sparql"
        raw=corpora[name]["eligible_records"]
        overlap=sum(r["text_hash"] in train_hashes for r in raw)
        distinct=[r for r in raw if r["text_hash"] not in train_hashes]
        novel=[r for r in distinct if r["pattern"] not in seen_patterns]
        base=metric(distinct,layout)
        comparators={}
        for label,m in decisions.items():
            placement=m["placement"];result=metric(distinct,placement)
            new_metric=metric(novel,placement)
            base_novel=metric(novel,layout)
            comparators[label]={
              "test":result,
              "saved_touches_vs_static":base["extra_shard_touches"]-result["extra_shard_touches"],
              "novel_query_metrics":new_metric,
              "novel_touches_saved":base_novel["extra_shard_touches"]-new_metric["extra_shard_touches"]}
        all_groups[str(k)]={"source":name,"total_raw_queries":len(raw),
          "exact_text_overlap_with_training":overlap,
          "n_distinct_holdout_after_train_hash_exclusion":len(distinct),
          "n_novel_predicate_combinations":len(novel),
          "static":base,
          "comparators":comparators}
    full={"schema":"candidate3-locked-official-WatDiv10M-byte-weighted-one-swap-transfer-v1",
      "source":{"original_graph_url":ROOT+DATA,"graph_sha256":HASH_GRAPH,
                "query_archive_url":ROOT+QUERIES,"query_archive_sha256":HASH_QUERY},
      "physical":physical,
      "byte_layout":{"per_shard_bytes":loads,"upper_cap_bytes":cap,
                     "fragmented_predicates":sum(len(v)>1 for v in layout.values()),
                     "single_shard_predicates":len(static),
                     "analytical_not_materialized_fragments":True},
      "training":{"raw_queries":len(train),
                  "unique_text_hashes":len(train_hashes),
                  "distinct_predicate_combinations":len(seen_patterns)},
      "candidate_search":diag,
      "training_only_decisions":{k:v["decision"] for k,v in decisions.items()},
      "test_workloads":all_groups,
      "limitations":[
        "WatDiv synthetic stress queries: five generated test workloads, NOT chronological user query logs",
        "All test queries excluded from decision; exact training text duplicates excluded from test scoring",
        "An analytical byte allocation by predicate size with fragmented predicates, not actual relocated N-Triples",
        "Predicate-set shard span proxy only; does NOT execute SPARQL joins, check answer equivalence or latency",
        "No actual migration/index byte overhead; move_bytes include serialized N-Triples only, not replicated index",
        "The five workloads may share query templates, hence are NOT five independent scientific replications",
        "No executable WISE/WASP baseline or equal-byte replica/cache competitor in this gate",
        "Novel means predicate combination unseen in warmup, not statistically independent new-domain pattern"] }
    OUT.joinpath("report.json").write_text(json.dumps(full,indent=2))
    print("WATDIV_BYTE_TRANSFER_START",flush=True)
    print(json.dumps(full,indent=2),flush=True)
    print("WATDIV_BYTE_TRANSFER_END",flush=True)
if __name__=="__main__":main()
