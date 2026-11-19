#!/usr/bin/env python3
"""Preflight diagnostic: evaluate gold set feasibility without exposing it to retrieval."""
import hashlib, json, random, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
BASE="https://huggingface.co/datasets/diandianone123/topographrag-bench/resolve/main/"
SEED=261119
def gold(q):
    if q["question_type"]=="synthesis":
        facts=q.get("answer",{}).get("evidence_points",[]) or []
        required=set((q.get("evidence_validation") or {}).get("required") or [])
        if required: facts=[p for p in facts if p.get("fact_id") in required]
        return {(int(x["source_page"]),int(x["source_layout"])) for x in facts if x.get("source_page") is not None and x.get("source_layout") is not None}
    return {(int(x["page_id"]),int(x["layout_id"])) for x in q.get("evidence_sources",[]) if x.get("page_id") is not None and x.get("layout_id") is not None}
def choose(questions):
    rng=random.Random(SEED);output=[]
    for kind,target in [("bridge_chain",180),("synthesis",120)]:
        groups=defaultdict(list)
        for q in questions:
            if q["question_type"]==kind and len(gold(q))>1:groups[q["doc_id"]].append(q)
        docs=sorted(groups);rng.shuffle(docs)
        for group in groups.values():rng.shuffle(group)
        picked=[]
        while len(picked)<target and any(groups.values()):
            for doc in docs:
                if groups[doc] and len(picked)<target:picked.append(groups[doc].pop())
        output+=picked
    rng.shuffle(output)
    return output
qs=json.load(urllib.request.urlopen(BASE+"annotations/benchmark.json"))
assert len(qs)==2024
s=choose(qs)
samples={q.get("mh_id") or q.get("sq_id") for q in s}
print("SOURCE_QUESTION_COUNT",len(qs),"SELECTED",len(s),"DOCS",len({q["doc_id"] for q in s}))
print("SAMPLE_KEY_DUPLICATES",len(s)-len(samples))
for typ in ["bridge_chain","synthesis"]:
    a=[q for q in s if q["question_type"]==typ]
    cnt=Counter(map(lambda q:len(gold(q)),a))
    print("GOLD_SET_DISTRIBUTION",typ,sorted(cnt.items()),"n_le_2",sum(len(gold(q))<=2 for q in a),"n_le_6",sum(len(gold(q))<=6 for q in a),"n_gt6",sum(len(gold(q))>6 for q in a))
    print("EVIDENCE_SOURCE_SHAPES",typ,"sample gold", sorted(gold(a[0]))[:3] if a else None)
print("GOLD_ANNOTATIONS_ONLY_USED_IN_METRICS", True)
