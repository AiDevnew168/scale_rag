#!/usr/bin/env python3
"""Real BM25 independent-pool and fusion ceiling; annotations used only to score."""
import json,re,random,csv
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
import audit

OUT=Path("results_bm25");OUT.mkdir(exist_ok=True)
def tok(s):
    return re.findall(r"(?u)\b\w\w+\b",s.casefold())
def ave(rs,k):
    return round(100*sum(x[k] for x in rs)/len(rs),3) if rs else None
def paired(rows,a,b):
    docrows=defaultdict(list)
    for x in rows:docrows[x["doc_id"]].append(x)
    docs=sorted(docrows)
    rng=random.Random(audit.SEED)
    deltas=[]
    for _ in range(2000):
        selected=[rng.choice(docs) for _ in docs]
        drawn=[x for d in selected for x in docrows[d]]
        deltas.append(100*sum(x[a]-x[b] for x in drawn)/len(drawn))
    ci=np.percentile(deltas,[2.5,97.5])
    return dict(wins=sum(x[a]>x[b] for x in rows),losses=sum(x[a]<x[b] for x in rows),
                delta_pp=round(100*sum(x[a]-x[b] for x in rows)/len(rows),3),
                ci95_pp=[round(float(ci[0]),3),round(float(ci[1]),3)])
def main():
    p=audit.download("annotations/benchmark.json","benchmark.json")
    m=audit.download("manifest.json","manifest.json")
    a=audit.download("archives/layout_content.tar.zst","layouts.tar.zst")
    qs=audit.sample(json.loads(p.read_text()))
    docs,st=audit.text_layouts(a,json.loads(m.read_text()))
    selected=defaultdict(list)
    for q in qs:selected[q["doc_id"]].append(q)
    rows=[];by_top=defaultdict(list)
    for doc,queries in selected.items():
        items=docs[doc]
        toks=[tok(x["text"]) or ["empty"] for x in items]
        bm=BM25Okapi(toks)
        vec=TfidfVectorizer(stop_words="english",ngram_range=(1,2),sublinear_tf=True,max_features=45000)
        matrix=vec.fit_transform([x["text"] for x in items])
        for q in queries:
            query=q["question"]
            bm_scores=bm.get_scores(tok(query))
            tfidf_scores=np.asarray((matrix@vec.transform([query]).T).toarray()).ravel()
            t=audit.choose_pool(tfidf_scores,50)
            b=audit.choose_pool(bm_scores,50)
            fused=list(dict.fromkeys(t[:25]+b[:25]))
            fused.extend(i for i in t+b if i not in fused and len(fused)<50)
            fused=fused[:50]
            gold=audit.gold(q)
            r={"qid":q.get("mh_id") or q.get("sq_id"),"doc_id":doc,"kind":q["question_type"],"gold_n":len(gold)}
            for name,idx in [("tfidf",t),("bm25",b),("union",fused)]:
                for k in (2,6,12,50):
                    selected_keys={(items[i]["page"],items[i]["layout"]) for i in idx[:k]}
                    r[f"{name}_full_{k}"]=int(gold<=selected_keys)
                    r[f"{name}_recall_{k}"]=round(len(gold&selected_keys)/len(gold),6)
            rows.append(r);by_top[q["question_type"]].append(r)
    with (OUT/"per_question_bm25.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    keys=[f"{method}_full_{k}" for method in ("tfidf","bm25","union") for k in (2,6,12,50)]
    result={"schema":"topo-bm25-pool-check-v1","n":len(rows),"seed":audit.SEED,
      "all_percent":{k:ave(rows,k) for k in keys},
      "by_topology":{typ:{"n":len(rr),"percent":{k:ave(rr,k) for k in keys}} for typ,rr in by_top.items()},
      "paired_bm25_vs_tfidf6":paired(rows,"bm25_full_6","tfidf_full_6"),
      "paired_bm25_vs_tfidf50":paired(rows,"bm25_full_50","tfidf_full_50"),
      "paired_union_vs_tfidf50":paired(rows,"union_full_50","tfidf_full_50"),
      "limitations":["Only lexical text/OCR/VLM description representations","Union pool may differ from fixed original candidate pool","Gold only used in evaluation, never for fusion"]}
    (OUT/"report_bm25.json").write_text(json.dumps(result,indent=2))
    print("BM25_RESULT_START");print(json.dumps(result,indent=2));print("BM25_RESULT_END")
    assert len(rows)==300
    assert abs(ave(rows,"tfidf_full_6")-33.0)<0.01
    assert abs(ave(rows,"tfidf_full_50")-80.667)<0.01
if __name__=="__main__":main()
