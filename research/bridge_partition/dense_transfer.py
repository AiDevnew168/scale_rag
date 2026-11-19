#!/usr/bin/env python3
"""Document-held-out dense semantic COACCESS feasibility, not RAG retrieval.

Trains a page-pair coaccess model from real source-document supports in TRAIN
documents only. A frozen pretrained text encoder uses no test gold. Gold test
supports evaluate placement of original page nodes, NEVER build partitions.
Diagnostic methods are established baselines, not new algorithms.
"""
import sys, json, math, random, hashlib, itertools
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pilot
import document_transfer as dt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"topo_fea"))
import audit

SEED=271119
OUT=Path("results_dense_transfer");OUT.mkdir(exist_ok=True)
MODEL="sentence-transformers/all-MiniLM-L6-v2"
REVISION="c9745ed1d9f207416be6d2e6f8de32d1f16199b1" # verify actual resolver, fail if unavailable

def all_page_vectors(text_by_doc,doc_order):
    model=SentenceTransformer(MODEL,device="cpu",revision=REVISION)
    encoded={}
    for doc in doc_order:
        samples=[t[:1800] if t.strip() else " " for t in text_by_doc[doc]]
        emb=model.encode(samples,batch_size=64,convert_to_numpy=True,
                         normalize_embeddings=True,show_progress_bar=False)
        encoded[doc]=np.asarray(emb,dtype=np.float32)
        if len(encoded)%30==0:print("EMBED_DOCS",len(encoded),flush=True)
    return encoded

def feature(a,b,n,S,D,L):
    lex=dt.feat(a,b,n,S,L)
    dense=float(np.dot(D[a],D[b]))
    return lex+[dense,abs(dense),dense*lex[2],dense*lex[0]]

def pairwise_edges(n,S,D,L,scorer_sparse,scorer_dense,top=4):
    candidate=[(i,j) for i in range(n) for j in range(i+2,n)]
    if not candidate:return {m:set() for m in ("sparse","dense","dense_learned","dense_direct","late_fusion")}
    sparse=np.asarray([dt.feat(a,b,n,S,L) for a,b in candidate])
    extended=np.asarray([feature(a,b,n,S,D,L) for a,b in candidate])
    old=scorer_sparse.predict_proba(sparse)[:,1]
    new=scorer_dense.predict_proba(extended)[:,1]
    dense=np.asarray([D[a]@D[b] for a,b in candidate])
    # Fixed 50:50 probability fusion of models, not a calibrated reranker.
    scores={"sparse":old,"dense_learned":new,"dense_direct":dense,
            "late_fusion":.5*(old+new)}
    scores["dense"]=.5*(new+np.clip((dense+1)/2,0,1))
    edges={}
    for name,sc in scores.items():
        ranks=defaultdict(list)
        for idx,(a,b) in enumerate(candidate):
            ranks[a].append((float(sc[idx]),b))
            ranks[b].append((float(sc[idx]),a))
        chosen=set()
        for node in range(n):
            for value,v in sorted(ranks[node],key=lambda x:(-x[0],x[1]))[:top]:
                chosen.add(tuple(sorted((node,v))))
        edges[name]=chosen
    return edges

def main():
    q=pilot.download("annotations/benchmark.json")
    manifest=pilot.download("manifest.json")
    n_pages={int(d["doc_id"]):len(d["files"]["page_images"]) for d in manifest["documents"]}
    grouped=defaultdict(list)
    for row in q:
        pp=pilot.pages(row)
        doc=int(row["doc_id"])
        if len(pp)>1 and min(pp)>=0 and max(pp)<n_pages[doc]:
            grouped[doc].append(row)
    docs=sorted(doc for doc,queries in grouped.items()
                if len(queries)>=4 and n_pages[doc]>=8)
    assert len(docs)>=130
    rng=random.Random(SEED);rng.shuffle(docs)
    ntrain=round(.7*len(docs))
    train=sorted(docs[:ntrain]);test=sorted(docs[ntrain:])
    assert not set(train).intersection(test)
    archive=Path("layouts.tar.zst")
    if not archive.exists():
        import urllib.request
        urllib.request.urlretrieve(
            "https://huggingface.co/datasets/diandianone123/topographrag-bench/resolve/main/archives/layout_content.tar.zst",archive)
    print("LAYOUT_SHA",hashlib.sha256(archive.read_bytes()).hexdigest(),flush=True)
    layouts,_=audit.text_layouts(archive,manifest)
    content={doc:dt.pages_by_doc(layouts[doc],n_pages[doc]) for doc in docs}
    vectorizer=TfidfVectorizer(stop_words="english",min_df=2,max_features=20000,sublinear_tf=True)
    vectorizer.fit([p for doc in train for p in content[doc]])
    # Pretrained dense encoder is frozen: no gold supervision or tuning.
    D=all_page_vectors(content,docs)
    Xold=[];Xnew=[];yy=[]
    rng=random.Random(SEED)
    for doc in train:
        n=n_pages[doc]
        mat=vectorizer.transform(content[doc])
        S=(mat@mat.T).toarray()
        L=[len(x) for x in content[doc]]
        gold=dt.pairs_from_query(grouped[doc])
        positive=sorted((a,b) for a,b in gold if a<n and b<n)
        negative=[(a,b) for a in range(n) for b in range(a+1,n) if (a,b) not in gold]
        rng.shuffle(negative)
        negative=negative[:min(len(negative),max(30,5*len(positive)))]
        for (a,b),label in [(p,1) for p in positive]+[(p,0) for p in negative]:
            Xold.append(dt.feat(a,b,n,S,L))
            Xnew.append(feature(a,b,n,S,D[doc],L))
            yy.append(label)
    old_model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=300,random_state=SEED,class_weight="balanced"))
    new_model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=300,random_state=SEED,class_weight="balanced"))
    old_model.fit(Xold,yy);new_model.fit(Xnew,yy)
    print("TRAIN_DOCS",len(train),"TEST_DOCS",len(test),"TRAIN_PAIRS",len(yy),"POSITIVES",sum(yy),flush=True)
    rows=[];graph_stats=Counter()
    for doc in test:
        n=n_pages[doc]
        mat=vectorizer.transform(content[doc]);S=(mat@mat.T).toarray()
        L=[len(x) for x in content[doc]]
        edges=pairwise_edges(n,S,D[doc],L,old_model,new_model)
        graph_stats.update({x:len(e) for x,e in edges.items()})
        partitions={"contiguous":pilot.part_contig(n,4),
                    "structure":dt.partition(n,set())}
        for m,e in edges.items():partitions[m]=dt.partition(n,e)
        for method,part in partitions.items():
            assert max(Counter(part).values())<=math.ceil(n/4)
        for qu in grouped[doc]:
            pp=pilot.pages(qu)
            row={"doc_id":doc,"qid":qu.get("mh_id") or qu.get("sq_id"),"kind":qu["question_type"]}
            for method,part in partitions.items():row[method]=len({part[p] for p in pp})
            rows.append(row)
        if len(rows)%150<10:print("SCORED",len(rows),flush=True)
    methods=("contiguous","structure","sparse","dense_direct","dense","dense_learned","late_fusion")
    report={"schema":"dense-cross-doc-coaccess-prediction-v1",
        "seed":SEED,"encoder":MODEL,"encoder_revision":REVISION,
        "n_train_docs":len(train),"n_test_docs":len(test),
        "train_pairs":len(yy),"train_positive":sum(yy),
        "n_test_queries":len(rows),
        "metrics":{m:dt.eval_metrics(rows,m) for m in methods},
        "paired":{k:dt.bootstrap(rows,*v) for k,v in {
          "dense_learned_vs_sparse":("dense_learned","sparse"),
          "late_fusion_vs_sparse":("late_fusion","sparse"),
          "dense_direct_vs_structure":("dense_direct","structure"),
          "dense_learned_vs_structure":("dense_learned","structure"),
          "sparse_vs_structure":("sparse","structure")}.items()},
        "test_query_types":dict(Counter(r["kind"] for r in rows)),
        "graph_edge_counts":dict(graph_stats),
        "caveats":["Data are original 201 source-document layout texts, no raw pixels",
          "Dense encoder pretrained, frozen, no test gold as model or partition input",
          "Gold source pages of test queries used ONLY to score shard co-location",
          "Test documents disjoint from training documents; same benchmark inspected previously, exploratory comparison",
          "Unobserved coaccess pairs are weak negatives; edge budget approximated via four candidates per node",
          "Equal page-count capacity not measured byte memory, query routing or wall-clock latency",
          "All graph classifiers are baseline diagnostics, not novelty claims"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_query.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
    OUT.joinpath("split.json").write_text(json.dumps({"train":train,"test":test},indent=2))
    print("DENSE_TRANSFER_START");print(json.dumps(report,indent=2));print("DENSE_TRANSFER_END")
    assert len(test)==43 and len(rows)>400
if __name__=="__main__":main()
