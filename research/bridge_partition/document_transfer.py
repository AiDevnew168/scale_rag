#!/usr/bin/env python3
"""Document-disjoint prediction of cross-page co-access for graph placement.

All gold test supports are scorer-only. Input page contents/positions are visible.
Real TopoGraphRAG layouts, not pixel image, entity KG or actual routing latency.
"""
import hashlib,itertools,json,math,random,sys
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import pymetis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0,str(Path(__file__).resolve().parent))
import pilot
SEED=271119;OUT=Path("results_doc_heldout");OUT.mkdir(exist_ok=True)
RNG=random.Random(SEED)
K=4

def pages_by_doc(layouts,n):
    contents=[""]*n
    for x in layouts:
        p=x["page"]
        if 0<=p<n:contents[p]+=" "+x["text"][:600]
    return [s[:14000] for s in contents]

def feat(i,j,n,S,content_lengths):
    a=min(i,j);b=max(i,j)
    d=b-a
    return [float(S[a,b]),d/n,1/(1+d),int(d<=2),int(d<=5),
            (a/n),(b/n), math.log1p(content_lengths[a]),
            math.log1p(content_lengths[b]),
            abs(math.log1p(content_lengths[a])-math.log1p(content_lengths[b]))]

def pairs_from_query(qs):
    positive=set()
    for q in qs:
        pp=pilot.pages(q)
        positive.update(itertools.combinations(pp,2))
    return positive

def build_training_pairs(docids,workloads,contents,npages,vectorizer):
    X=[];y=[];rng=random.Random(SEED)
    for doc in docids:
        n=npages[doc];q=workloads[doc];gold=pairs_from_query(q)
        M=vectorizer.transform(contents[doc])
        S=(M@M.T).toarray()
        L=[len(x) for x in contents[doc]]
        positives=sorted((i,j) for i,j in gold if i<n and j<n)
        # Unobserved pairs are only weak negatives: other valid future
        # co-access might exist but be absent from a finite query log.
        negatives=[(i,j) for i in range(n) for j in range(i+1,n)
                   if (i,j) not in gold]
        rng.shuffle(negatives)
        negatives=negatives[:min(len(negatives),max(30,5*len(positives)))]
        for pair,label in [(p,1) for p in positives]+[(p,0) for p in negatives]:
            X.append(feat(*pair,n,S,L));y.append(label)
    return np.asarray(X,dtype=float),np.asarray(y,dtype=int)

def choose_graph(n, S, L, scorer):
    # Every method receives exactly the same page positions and
    # page-text similarity. Only the pair ranking changes.
    methods=("semantic","trained","nearby")
    ranks={mode:defaultdict(list) for mode in methods}
    pairs=[(i,j) for i in range(n) for j in range(i+1,n) if j-i>1]
    if not pairs:return {m:set() for m in methods}
    X=np.asarray([feat(i,j,n,S,L) for i,j in pairs],dtype=float)
    probability=scorer.predict_proba(X)[:,1]
    for z,(i,j) in enumerate(pairs):
        scores={"semantic":float(S[i,j]),"trained":float(probability[z]),
                "nearby":-float(j-i)}
        for mode,score in scores.items():
            ranks[mode][i].append((score,j))
            ranks[mode][j].append((score,i))
    out={}
    for mode in methods:
        chosen=set()
        for node in range(n):
            rank=sorted(ranks[mode][node],key=lambda x:(-x[0],x[1]))
            for score,other in rank[:min(4,len(rank))]:
                chosen.add(tuple(sorted((node,other))))
        out[mode]=chosen
    return out

def partition(n,extra,k=4):
    edges=defaultdict(int)
    for i in range(n-1):edges[(i,i+1)]+=100
    for i,j in extra:edges[(i,j)]+=200
    nbr=defaultdict(list)
    for (i,j),w in sorted(edges.items()):
        nbr[i].append((j,w));nbr[j].append((i,w))
    xadj=[0];adjncy=[];weights=[];adj=[[] for _ in range(n)]
    for i in range(n):
        adj[i]=sorted(nbr[i])
        for j,w in adj[i]:adjncy.append(j);weights.append(w)
        xadj.append(len(adjncy))
    _,membership=pymetis.part_graph(k,xadj=xadj,adjncy=adjncy,
                                  eweights=weights,vweights=[1]*n,
                                  options=pymetis.Options(seed=pilot.SEED))
    membership=list(membership)
    cap=math.ceil(n/k);count=Counter(membership)
    moves=0
    while max(count.values())>cap:
        cand=[]
        for u,old in enumerate(membership):
            if count[old]<=cap:continue
            for t in range(k):
                if t==old or count[t]>=cap:continue
                delta=sum(w*(int(t!=membership[v])-int(old!=membership[v]))
                          for v,w in adj[u])
                cand.append((delta,u,t,old))
        if not cand:raise AssertionError("capacity repair infeasible")
        delta,u,t,old=min(cand)
        membership[u]=t;count[old]-=1;count[t]+=1
        moves+=1
        if moves>n*k:raise AssertionError("nonconvergent capacity repair")
    assert max(count.values())<=cap
    return membership

def eval_metrics(rows,m):
    spans=[x[m] for x in rows]
    return {"n":len(spans),
            "local_pct":round(100*sum(x==1 for x in spans)/len(spans),3),
            "mean_shards":round(float(np.mean(spans)),4)}
def bootstrap(rows,a,b):
    docs=defaultdict(list)
    for row in rows:docs[row["doc_id"]].append(row)
    ids=sorted(docs);rng=random.Random(SEED)
    vals=[]
    for _ in range(2000):
        selected=[rng.choice(ids) for _ in ids]
        xx=[r for d in selected for r in docs[d]]
        vals.append(100*sum((r[a]==1)-(r[b]==1) for r in xx)/len(xx))
    lo,hi=np.percentile(vals,[2.5,97.5])
    return {"delta_pp":round(100*sum((r[a]==1)-(r[b]==1) for r in rows)/len(rows),3),
      "ci95_pp":[round(float(lo),3),round(float(hi),3)],
      "wins":sum(r[a]==1 and r[b]!=1 for r in rows),
      "losses":sum(r[b]==1 and r[a]!=1 for r in rows)}
def main():
    q=pilot.download("annotations/benchmark.json")
    m=pilot.download("manifest.json")
    n_pages={d["doc_id"]:len(d["files"]["page_images"]) for d in m["documents"]}
    work=defaultdict(list)
    for row in q:
        pp=pilot.pages(row);doc=row["doc_id"]
        if len(pp)<2 or not pp or min(pp)<0 or max(pp)>=n_pages[doc]:continue
        work[doc].append(row)
    docs=sorted(doc for doc,v in work.items() if len(v)>=4 and n_pages[doc]>=8)
    assert len(docs)>=130
    rng=random.Random(SEED);rng.shuffle(docs)
    ntr=round(.7*len(docs))
    train_docs=sorted(docs[:ntr]);test_docs=sorted(docs[ntr:])
    assert not set(train_docs)&set(test_docs)
    layouts,stats=pilot.text_layouts(pilot.download(
        "manifest.json") if False else __import__("audit").download(
            "archives/layout_content.tar.zst","layouts.tar.zst"),m)
    contents={doc:pages_by_doc(layouts[doc],n_pages[doc]) for doc in docs}
    vectorizer=TfidfVectorizer(stop_words="english",min_df=2,
            max_features=20000,sublinear_tf=True)
    vectorizer.fit([p for doc in train_docs for p in contents[doc]])
    X,y=build_training_pairs(train_docs,work,contents,n_pages,vectorizer)
    print("TRAIN_PAIRS",len(y),"POS",int(y.sum()),"DOCS",len(train_docs),
          "TEST_DOCS",len(test_docs),flush=True)
    assert len(y)>200 and y.sum()>100
    scorer=make_pipeline(StandardScaler(),LogisticRegression(
        max_iter=300,random_state=SEED,class_weight="balanced"))
    scorer.fit(X,y)
    rows=[];labels=[];size=Counter()
    for doc in test_docs:
        n=n_pages[doc]
        M=vectorizer.transform(contents[doc])
        S=(M@M.T).toarray();L=[len(t) for t in contents[doc]]
        chosen=choose_graph(n,S,L,scorer)
        variants={
            "contiguous":pilot.part_contig(n,K),
            "structure":partition(n,set()),
            "nearby":partition(n,chosen["nearby"]),
            "semantic":partition(n,chosen["semantic"]),
            "learned":partition(n,chosen["trained"])}
        for name,p in variants.items():assert max(Counter(p).values())<=math.ceil(n/K)
        labels.append({"doc_id":doc,"n_pages":n,
            "train_doc":False,"n_queries":len(work[doc]),
            "edge_counts":{k:len(v) for k,v in chosen.items()}})
        for query in work[doc]:
            needed=pilot.pages(query)
            rr={"doc_id":doc,"qid":query.get("mh_id") or query.get("sq_id"),
                "kind":query["question_type"]}
            for key,part in variants.items():rr[key]=len({part[p] for p in needed})
            rows.append(rr)
    methods=("contiguous","structure","nearby","semantic","learned")
    assert len(rows)>100
    report={"schema":"document-disjoint-forecast-placement-v1",
      "source_dataset":"diandianone123/topographrag-bench",
      "seed":SEED,"n_training_docs":len(train_docs),"n_test_docs":len(test_docs),
      "n_train_pair_examples":len(y),"n_train_observed_coaccess_pairs":int(y.sum()),
      "n_test_queries":len(rows),
      "test_metrics":{k:eval_metrics(rows,k) for k in methods},
      "paired":{name:bootstrap(rows,*vals) for name,vals in {
         "learned_vs_structure":("learned","structure"),
         "learned_vs_semantic":("learned","semantic"),
         "learned_vs_nearby":("learned","nearby"),
         "semantic_vs_structure":("semantic","structure")}.items()},
      "test_query_types":dict(Counter(r["kind"] for r in rows)),
      "cautions":["Entire TEST documents held out from supervised coaccess training",
        "No test gold evidence used to construct partition or select graph edges",
        "TF-IDF vocabulary fit ONLY on train-document page texts",
        "Gold train support coaccess is proxy for past logs; unlabeled pairs are not necessarily true negatives",
        "Entity type and original page content from benchmark layout descriptions, not raw image pixels",
        "Equal page weight, NOT measured memory/bytes; no real router, LLM or latency",
        "This is an exploratory diagnostic after prior experiments on the same overall benchmark"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_query.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
    OUT.joinpath("split_docs.json").write_text(json.dumps(
        {"training":train_docs,"testing":test_docs,"test_metadata":labels},indent=2))
    print("DOC_HELDOUT_REPORT_START")
    print(json.dumps(report,indent=2))
    print("DOC_HELDOUT_REPORT_END")
if __name__=="__main__":main()
