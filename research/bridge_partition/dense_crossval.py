#!/usr/bin/env python3
"""Threefold document-disjoint CV for dense vs sparse pairwise coaccess.

Each source doc is test exactly once. Frozen pretrained MiniLM is external;
fold-specific TF-IDF and pairwise link classifiers fit only training documents.
Gold test query supports score localization ONLY, never enter fold training.
This remains exploratory, not an untouched benchmark or a new algorithm.
"""
import json,math,random,hashlib,urllib.request
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from huggingface_hub import model_info
import dense_transfer as d
import document_transfer as dt
import pilot
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"topo_fea"))
import audit

SEED=271120
OUT=Path("results_dense_cv");OUT.mkdir(exist_ok=True)

def make_scorer():
    return make_pipeline(StandardScaler(),
        LogisticRegression(max_iter=300,random_state=SEED,class_weight="balanced"))

def main():
    questions=pilot.download("annotations/benchmark.json")
    manifest=pilot.download("manifest.json")
    n_pages={int(x["doc_id"]):len(x["files"]["page_images"]) for x in manifest["documents"]}
    work=defaultdict(list)
    for q in questions:
        pp=pilot.pages(q);doc=int(q["doc_id"])
        if len(pp)>1 and min(pp)>=0 and max(pp)<n_pages[doc]:work[doc].append(q)
    docs=sorted(z for z in work if len(work[z])>=4 and n_pages[z]>=8)
    assert len(docs)>=130
    archive=Path("layouts.tar.zst")
    if not archive.exists():
        urllib.request.urlretrieve(
            "https://huggingface.co/datasets/diandianone123/topographrag-bench/resolve/main/archives/layout_content.tar.zst",archive)
    print("LAYOUT_SHA256",hashlib.sha256(archive.read_bytes()).hexdigest(),flush=True)
    layout,_=audit.text_layouts(archive,manifest)
    content={doc:dt.pages_by_doc(layout[doc],n_pages[doc]) for doc in docs}
    d.REVISION=model_info(d.MODEL).sha
    assert len(d.REVISION)==40
    print("FROZEN_ENCODER_COMMIT",d.REVISION,flush=True)
    D=d.all_page_vectors(content,docs)
    shuffled=docs[:];rng=random.Random(SEED);rng.shuffle(shuffled)
    folds=[sorted(shuffled[i::3]) for i in range(3)]
    assert len(set(x for group in folds for x in group))==len(docs)
    rows=[];metadata=[]
    for fold,test in enumerate(folds):
        train=sorted(set(docs)-set(test))
        assert not set(test)&set(train)
        vec=TfidfVectorizer(stop_words="english",min_df=2,
             max_features=20000,sublinear_tf=True)
        vec.fit([p for doc in train for p in content[doc]])
        X0=[];X1=[];y=[]
        rng2=random.Random(SEED+fold)
        for doc in train:
            n=n_pages[doc]
            m=vec.transform(content[doc]);S=(m@m.T).toarray()
            L=list(map(len,content[doc]))
            gold=dt.pairs_from_query(work[doc])
            positive=sorted((a,b) for a,b in gold if a<n and b<n)
            negative=[(a,b) for a in range(n) for b in range(a+1,n)
                      if (a,b) not in gold]
            rng2.shuffle(negative)
            negative=negative[:min(len(negative),max(30,5*len(positive)))]
            for (a,b),label in [(pair,1) for pair in positive]+[(pair,0) for pair in negative]:
                X0.append(dt.feat(a,b,n,S,L))
                X1.append(d.feature(a,b,n,S,D[doc],L))
                y.append(label)
        sm=make_scorer();dm=make_scorer()
        sm.fit(X0,y);dm.fit(X1,y)
        metadata.append({"fold":fold,"train_doc_ids":train,"test_doc_ids":test,
              "train_pairs":len(y),"positive_train_pairs":sum(y)})
        for doc in test:
            n=n_pages[doc]
            m=vec.transform(content[doc]);S=(m@m.T).toarray()
            L=list(map(len,content[doc]))
            edges=d.pairwise_edges(n,S,D[doc],L,sm,dm)
            parts={"structural":dt.partition(n,set()),
                  "sparse":dt.partition(n,edges["sparse"]),
                  "dense_learned":dt.partition(n,edges["dense_learned"]),
                  "dense_direct":dt.partition(n,edges["dense_direct"]),
                  "late_fusion":dt.partition(n,edges["late_fusion"])}
            assert all(max(Counter(p).values())<=math.ceil(n/4) for p in parts.values())
            for q in work[doc]:
                needed=pilot.pages(q)
                row={"doc_id":doc,"fold":fold,
                     "qid":q.get("mh_id") or q.get("sq_id"),
                     "kind":q["question_type"]}
                for method,p in parts.items():
                    row[method]=len({p[t] for t in needed})
                rows.append(row)
        print("FOLD_DONE",fold,"TEST_DOCS",len(test),"TOTAL_QUERIES",len(rows),flush=True)
    methods=("structural","sparse","dense_learned","dense_direct","late_fusion")
    metrics={m:dt.eval_metrics(rows,m) for m in methods}
    pairs={name:dt.bootstrap(rows,*pair) for name,pair in {
        "dense_learned_vs_sparse":("dense_learned","sparse"),
        "dense_learned_vs_structural":("dense_learned","structural"),
        "dense_direct_vs_structural":("dense_direct","structural"),
        "late_fusion_vs_sparse":("late_fusion","sparse")}.items()}
    by_fold={}
    for fold in range(3):
        subset=[x for x in rows if x["fold"]==fold]
        by_fold[str(fold)]={"n_docs":len(folds[fold]),"n_queries":len(subset),
            "metrics":{m:dt.eval_metrics(subset,m) for m in methods},
            "paired":dt.bootstrap(subset,"dense_learned","sparse")}
    by_kind={}
    for kind in ("bridge_chain","synthesis"):
        subset=[x for x in rows if x["kind"]==kind]
        by_kind[kind]={"n":len(subset),"metrics":{m:dt.eval_metrics(subset,m) for m in methods},
            "paired":dt.bootstrap(subset,"dense_learned","sparse")}
    result={"schema":"dense-threefold-document-disjoint-coaccess-v1",
      "seed":SEED,"folds":3,"n_source_docs":len(docs),"n_questions":len(rows),
      "model":d.MODEL,"model_commit":d.REVISION,
      "metrics":metrics,"paired":pairs,"by_fold":by_fold,"by_kind":by_kind,
      "limitations":["Each document test exactly once but all folds draw from the same repeatedly studied benchmark",
        "Not a prospective untouched benchmark and no end-to-end RAG answer accuracy",
        "Pretrained text embedding (no image pixels) plus conventional logistic pair classifier",
        "Test gold coaccess pages ONLY used by scoring, never for partition decisions",
        "Four equal page-count shards per doc; physical byte and routing latency unmeasured",
        "Unobserved pairs may be positives under a future query: training negative label noise",
        "Cross-validated improvement should not be mistaken for a new graph algorithm"]}
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
    OUT.joinpath("fold_manifest.json").write_text(json.dumps(metadata,indent=2))
    print("DENSE_CV_START");print(json.dumps(result,indent=2));print("DENSE_CV_END")
    assert len(rows)>1200
if __name__=="__main__":main()
