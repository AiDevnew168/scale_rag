#!/usr/bin/env python3
"""Post-hoc structural controls on *frozen* CrossEncoder scores: no new model calls.

Exploratory only: two roles are parsed heuristically from question (no gold);
the exact solver is a TWO-ROLE matching control, NOT general constrained RAG.
"""
import csv,json,random,re
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import audit

OUT=Path("results_ce_post")
OUT.mkdir(exist_ok=True)
def split_roles(q):
    m=re.match(r"(?is)^(?:for|among|in|of)\b(.{12,350}?),\s*(.+)$",q)
    if m: return m.group(1),m.group(2)
    p=re.search(r",\s*(?:what|which|how|where|who|why)\b",q,re.I)
    if p:return q[:p.start()],q[p.start()+1:]
    words=q.split();cut=max(1,len(words)//2)
    return " ".join(words[:cut])," ".join(words[cut:])
def ranks(scores):
    arr=np.asarray(scores)
    n=len(arr)
    ids=np.argsort(-arr,kind="stable")
    percentile=np.zeros(n)
    if n==1:return np.ones(n)
    for r,i in enumerate(ids):percentile[i]=1.0-r/(n-1)
    return percentile
def exact_pair(values1,values2,n):
    best=(-1e30,0,1)
    for i in range(n):
        for j in range(n):
            if j==i:continue
            z=float(values1[i]+values2[j])
            if z>best[0]:best=(z,i,j)
    return [best[1],best[2]]
def greedy_pair(a,b,n):
    i=max(range(n),key=lambda x:a[x])
    j=max((x for x in range(n) if x!=i),key=lambda x:b[x])
    return [i,j]
def evaluate(rows,a,b):
    bydoc=defaultdict(list)
    for x in rows:bydoc[x["doc_id"]].append(x)
    docs=sorted(bydoc); rng=random.Random(audit.SEED)
    boot=[]
    for _ in range(2000):
        picked=[rng.choice(docs) for _ in docs]
        observed=[x for d in picked for x in bydoc[d]]
        boot.append(100*sum(x[a]-x[b] for x in observed)/len(observed))
    low,high=np.percentile(boot,[2.5,97.5])
    return dict(wins=sum(x[a]>x[b] for x in rows),losses=sum(x[a]<x[b] for x in rows),
                delta_pp=round(100*sum(x[a]-x[b] for x in rows)/len(rows),3),
                ci95_pp=[round(float(low),3),round(float(high),3)])
def main():
    p=audit.download("annotations/benchmark.json","benchmark.json")
    m=audit.download("manifest.json","manifest.json")
    a=audit.download("archives/layout_content.tar.zst","layouts.tar.zst")
    allqs=audit.sample(json.loads(p.read_text()))
    qmap={q.get("mh_id") or q.get("sq_id"):q for q in allqs}
    docs,st=audit.text_layouts(a,json.loads(m.read_text()))
    corpus={}
    tfidf={}
    for d in {q["doc_id"] for q in allqs}:
        items=docs[d]
        corpus[d]={(x["page"],x["layout"]):x["text"] for x in items}
        v=TfidfVectorizer(stop_words="english",max_features=45000,ngram_range=(1,2),sublinear_tf=True)
        M=v.fit_transform([x["text"] for x in items])
        tfidf[d]=(v,items,M,{(x["page"],x["layout"]):i for i,x in enumerate(items)})
    raw=[json.loads(line) for line in Path("results_ce/ce_rankings.jsonl").read_text().splitlines() if line.strip()]
    assert len(raw)==300,len(raw)
    result=[];disagree=Counter()
    for rr in raw:
        q=qmap[rr["qid"]];doc=rr["doc_id"];src=rr["pool"]
        n=len(src);assert n>=2
        scores=np.array([x["ce_score"] for x in src])
        ce_order=list(np.argsort(-scores,kind="stable"))
        ce_pct=ranks(scores)
        v,items,M,idmap=tfidf[doc]
        inds=[idmap[(x["page"],x["layout"])] for x in src]
        r1,r2=split_roles(q["question"])
        A=np.asarray((M[inds]@v.transform([r1]).T).toarray()).ravel()
        B=np.asarray((M[inds]@v.transform([r2]).T).toarray()).ravel()
        w=.60
        u1=(1-w)*ce_pct+w*ranks(A)
        u2=(1-w)*ce_pct+w*ranks(B)
        lim=min(40,n)
        exact=exact_pair(u1,u2,lim)
        greedy=greedy_pair(u1,u2,lim)
        def finish(pair):
            return pair+[i for i in ce_order if i not in pair]
        # Maximal Marginal Relevance over normalized CE scores.
        mmr=[]
        while len(mmr)<min(6,n):
            def val(i):
                sim=max((float(M[inds[i]].multiply(M[inds[j]]).sum()) for j in mmr),default=0.)
                return ce_pct[i]-.3*sim
            mmr.append(max((i for i in range(n) if i not in mmr),key=val))
        orders={"ce":ce_order,"ce_mmr":mmr,"role_greedy":finish(greedy),"role_exact":finish(exact)}
        gold=audit.gold(q)
        x={"qid":rr["qid"],"doc_id":doc,"kind":q["question_type"],"n_gold":len(gold)}
        for name,order in orders.items():
            for k in (2,6):
                picked={(src[i]["page"],src[i]["layout"]) for i in order[:k]}
                x[f"{name}_full_{k}"]=int(gold<=picked)
                x[f"{name}_recall_{k}"]=len(gold&picked)/len(gold)
        result.append(x)
        if exact!=greedy:disagree["pair_order_diff"]+=1
        if set(exact)!=set(greedy):disagree["pair_membership_diff"]+=1
    with (OUT/"per_question_structural.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    methods=("ce","ce_mmr","role_greedy","role_exact")
    keys=[f"{method}_full_{k}" for method in methods for k in (2,6)]
    def dist(rows):
        return {k:round(100*sum(x[k] for x in rows)/len(rows),3) for k in keys}
    report={"schema":"topo-ce-posthoc-role-matching-v1","n":len(result),
      "seed":audit.SEED,"method":"no additional CE calls, frozen scores from run 44501115217",
      "aggregate_pct":dist(result),
      "by_kind":{typ:{"n":len([x for x in result if x["kind"]==typ]),
                          "pct":dist([x for x in result if x["kind"]==typ])}
                 for typ in ("bridge_chain","synthesis")},
      "paired":{f"{method}_versus_ce_at{k}":evaluate(result,f"{method}_full_{k}",f"ce_full_{k}")
                for method in methods[1:] for k in (2,6)},
      "pair_disagreement":dict(disagree),
      "limitations":["Post-hoc exploratory role heuristics on previously explored 300 questions",
         "Only two lexical query roles, not verified semantics nor real graph edge labels",
         "This exact role assignment is elementary bipartite matching; no NP-hard constrained flow tested",
         "Potential model truncation and no direct image pixels",
         "Not evidence of correctness for semantic compatibility constraints"]}
    (OUT/"report_structural.json").write_text(json.dumps(report,indent=2))
    print("STRUCTURAL_REPORT_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("STRUCTURAL_REPORT_END",flush=True)
    assert len(result)==300
if __name__=="__main__":main()
