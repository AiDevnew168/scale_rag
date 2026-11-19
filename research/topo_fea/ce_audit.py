#!/usr/bin/env python3
"""Frozen-pool reranking by an actual pretrained CrossEncoder; gold kept in scorer."""
import csv, hashlib, json, os, random, time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import CrossEncoder
import audit

MODEL_ID=os.environ.get("CE_MODEL","cross-encoder/ms-marco-MiniLM-L6-v2")
MODEL_REV=os.environ.get("CE_REVISION") or None
OUT=Path("results_ce");OUT.mkdir(exist_ok=True)
SEED=audit.SEED
torch.manual_seed(SEED)
np.random.seed(SEED)
torch.set_num_threads(max(1,min(4,os.cpu_count() or 2)))

def meanpct(rows,key):
    return round(100*sum(x[key] for x in rows)/len(rows),3) if rows else None

def paired_bootstrap(rows, a, b, trials=2000):
    bydoc=defaultdict(list)
    for row in rows:bydoc[row["doc_id"]].append(row)
    docs=sorted(bydoc)
    wins=sum(x[a]>x[b] for x in rows)
    losses=sum(x[a]<x[b] for x in rows)
    rng=random.Random(SEED)
    dist=[]
    for _ in range(trials):
        samples=[rng.choice(docs) for _ in docs]
        vals=[rr for d in samples for rr in bydoc[d]]
        dist.append(100*sum(x[a]-x[b] for x in vals)/len(vals))
    lo,hi=np.percentile(dist,[2.5,97.5])
    return {"wins":wins,"losses":losses,"ties":len(rows)-wins-losses,
            "delta_pp":round(100*sum(x[a]-x[b] for x in rows)/len(rows),3),
            "cluster_bootstrap_ci95_pp":[round(float(lo),3),round(float(hi),3)]}

def main():
    p=audit.download("annotations/benchmark.json","benchmark.json")
    manifest_path=audit.download("manifest.json","manifest.json")
    archive=audit.download("archives/layout_content.tar.zst","layouts.tar.zst")
    questions=json.loads(p.read_text())
    selected=audit.sample(questions)
    assert len(selected)==300
    ids=[q.get("mh_id") or q.get("sq_id") for q in selected]
    (OUT/"sample_ids.json").write_text(json.dumps(ids,indent=2))
    docs,stats=audit.text_layouts(archive,json.loads(manifest_path.read_text()))
    docs_selected=defaultdict(list)
    for q in selected:docs_selected[q["doc_id"]].append(q)
    print("PREPARED_QUESTIONS",len(selected),"DOCS",len(docs_selected),flush=True)
    print("LOADING_CROSS_ENCODER",MODEL_ID,"REV",MODEL_REV,flush=True)
    start=time.monotonic()
    ce=CrossEncoder(MODEL_ID,device="cpu",max_length=384,**({"revision":MODEL_REV} if MODEL_REV else {}))
    print("MODEL_READY_SEC",round(time.monotonic()-start,2),flush=True)
    try:
        from huggingface_hub import HfApi
        model_sha=HfApi().model_info(MODEL_ID).sha
    except Exception as ex:
        model_sha="unavailable:"+type(ex).__name__
    print("MODEL_SHA",model_sha,flush=True)
    results=[];rankings=[]; missing=Counter();done=0
    for doc,qs in docs_selected.items():
        items=docs.get(doc,[])
        if len(items)<2:
            missing["doc_missing"]+=len(qs)
            continue
        try:
            vec=TfidfVectorizer(stop_words="english",ngram_range=(1,2),sublinear_tf=True,max_features=45000)
            M=vec.fit_transform([x["text"] for x in items])
        except ValueError:
            missing["vocab_missing"]+=len(qs)
            continue
        for q in qs:
            words=q["question"]
            lex=np.asarray((M@vec.transform([words]).T).toarray()).reshape(-1)
            pool=audit.choose_pool(lex,50)
            # Gold evidence IDs are NEVER read in ranker inputs.
            pairs=[(words,items[i]["text"]) for i in pool]
            ce_scores=np.asarray(ce.predict(pairs,batch_size=16,show_progress_bar=False,convert_to_numpy=True)).reshape(-1)
            ce_order=np.argsort(-ce_scores,kind="stable")
            ce_candidates=[pool[int(k)] for k in ce_order]
            gold=audit.gold(q) # ONLY in evaluation
            pool_keys={(items[i]["page"],items[i]["layout"]) for i in pool}
            x={"qid":q.get("mh_id") or q.get("sq_id"),"doc_id":doc,
               "kind":q["question_type"],"n_gold":len(gold),
               "gold_in_pool":int(gold<=pool_keys)}
            for method,order in [("tfidf",pool),("cross_encoder",ce_candidates)]:
                for k in (2,6,12,50):
                    chosen={(items[i]["page"],items[i]["layout"]) for i in order[:k]}
                    x[f"{method}_full_{k}"]=int(gold<=chosen)
                    x[f"{method}_recall_{k}"]=len(gold&chosen)/len(gold)
            results.append(x)
            rankings.append({"qid":x["qid"],"doc_id":doc,
                             "pool":[{"page":items[i]["page"],"layout":items[i]["layout"],
                                       "type":items[i]["type"],
                                       "tfidf_score":round(float(lex[i]),7),
                                       "ce_score":round(float(ce_scores[j]),7)}
                                     for j,i in enumerate(pool)]})
            done+=1
            if done%20==0:
                print("RERANK_PROGRESS",done,"/300","elapsed_s",round(time.monotonic()-start,1),flush=True)
    if results:
        with (OUT/"per_question_ce.csv").open("w",newline="",encoding="utf8") as f:
            w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    with (OUT/"ce_rankings.jsonl").open("w",encoding="utf8") as f:
        for row in rankings:f.write(json.dumps(row)+"\n")
    keys=[f"{method}_{what}_{budget}" for method in ("tfidf","cross_encoder")
          for what in ("full","recall") for budget in (2,6,12,50)]
    split={}
    for kind in ("bridge_chain","synthesis"):
        sub=[q for q in results if q["kind"]==kind]
        split[kind]={"n":len(sub),"mean_pct":{key:meanpct(sub,key) for key in keys},
                     "paired_at6":paired_bootstrap(sub,"cross_encoder_full_6","tfidf_full_6")}
    cases={"gold_in_pool":sum(x["gold_in_pool"] for x in results),
           "tfidf_success6":sum(x["tfidf_full_6"] for x in results),
           "ce_success6":sum(x["cross_encoder_full_6"] for x in results),
           "tfidf_success_given_pool":sum(x["gold_in_pool"]*x["tfidf_full_6"] for x in results),
           "ce_success_given_pool":sum(x["gold_in_pool"]*x["cross_encoder_full_6"] for x in results),
           "remaining_ce_headroom":sum(x["gold_in_pool"] and not x["cross_encoder_full_6"] for x in results)}
    report={"schema":"topo-cross-encoder-v1","seed":SEED,
            "source_annotation_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
            "source_layout_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
            "model":MODEL_ID,"model_revision":model_sha,"max_length_tokens":384,
            "candidate_pool":"TF-IDF Top-50 within source document",
            "questions_scored":len(results),"n_documents":len({q["doc_id"] for q in results}),
            "missing":dict(missing),"overall_pct":{k:meanpct(results,k) for k in keys},
            "by_topology":split,"counts":cases,
            "paired_at2":paired_bootstrap(results,"cross_encoder_full_2","tfidf_full_2"),
            "paired_at6":paired_bootstrap(results,"cross_encoder_full_6","tfidf_full_6"),
            "paired_at12":paired_bootstrap(results,"cross_encoder_full_12","tfidf_full_12"),
            "elapsed_seconds":round(time.monotonic()-start,1),
            "limitations":["This is layout text/OCR/VLM text, NOT a direct visual RAG benchmark",
                "MiniLM-L6 reranker is a pretrained semantic baseline, not the strongest multimodal reranker",
                "Single global query-document CE score is not joint evidence assembly",
                "Reference gold available only in scorer and not supplied as model input",
                "No end-to-end VLM answer test",
                "300 original queries were explored previously; comparisons are diagnostic, not independent confirmation"]}
    (OUT/"report_ce.json").write_text(json.dumps(report,indent=2))
    print("CE_REPORT_BEGIN",flush=True);print(json.dumps(report,indent=2),flush=True);print("CE_REPORT_END",flush=True)
    assert len(results)==300,("Incomplete sample",len(results),dict(missing))
    assert abs(meanpct(results,"tfidf_full_6")-33.0)<0.01,"TF-IDF baseline drift"
    assert abs(meanpct(results,"tfidf_full_50")-80.667)<0.01,"Pool drift"
if __name__=="__main__":main()
