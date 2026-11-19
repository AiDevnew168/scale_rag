#!/usr/bin/env python3
"""A deterministic 1/5 shard of 300 original real-layout CE reranking pairs."""
import hashlib,json,os,sys,time,csv
from collections import defaultdict
from pathlib import Path
import numpy as np, torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import CrossEncoder
from huggingface_hub import HfApi
import audit

SHARD=int(os.environ.get("CE_SHARD","0"))
N=5
assert 0<=SHARD<N
MODEL="cross-encoder/ms-marco-MiniLM-L6-v2"
torch.manual_seed(audit.SEED)
np.random.seed(audit.SEED)
torch.set_num_threads(max(1,min(4,os.cpu_count() or 2)))
OUT=Path("results_ce_shard"); OUT.mkdir(exist_ok=True)
t0=time.monotonic()

def main():
    p=audit.download("annotations/benchmark.json","benchmark.json")
    m=audit.download("manifest.json","manifest.json")
    a=audit.download("archives/layout_content.tar.zst","layouts.tar.zst")
    questions=audit.sample(json.loads(p.read_text()))
    selected=questions[SHARD::N]
    assert len(questions)==300 and len(selected)==60
    qids=[q.get("mh_id") or q.get("sq_id") for q in selected]
    print("SHARD",SHARD,"N",len(selected),"DOCS",len({q["doc_id"] for q in selected}),flush=True)
    docs,source_stats=audit.text_layouts(a,json.loads(m.read_text()))
    model=CrossEncoder(MODEL,device="cpu",max_length=384)
    model_sha=HfApi().model_info(MODEL).sha
    print("MODEL",MODEL,"SHA",model_sha,"PREP_TIME",round(time.monotonic()-t0,1),flush=True)
    bydoc=defaultdict(list)
    for q in selected:bydoc[q["doc_id"]].append(q)
    rows=[];rankings=[]
    for doc,qs in bydoc.items():
        items=docs[doc]
        vec=TfidfVectorizer(stop_words="english",ngram_range=(1,2),sublinear_tf=True,max_features=45000)
        mat=vec.fit_transform([x["text"] for x in items])
        for q in qs:
            text=q["question"]
            scores=np.asarray((mat@vec.transform([text]).T).toarray()).reshape(-1)
            pool=audit.choose_pool(scores,50)
            pairs=[(text,items[i]["text"]) for i in pool]
            ce=np.asarray(model.predict(pairs,batch_size=16,show_progress_bar=False,convert_to_numpy=True)).reshape(-1)
            chosen_ce=[pool[i] for i in np.argsort(-ce,kind="stable")]
            # EVALUATION ONLY: all predictions are frozen before retrieving gold IDs.
            g=audit.gold(q)
            row={"qid":q.get("mh_id") or q.get("sq_id"),"doc_id":doc,
                 "kind":q["question_type"],"n_gold":len(g),
                 "pool_full":int(g<={(items[i]["page"],items[i]["layout"]) for i in pool})}
            for name,choice in [("tfidf",pool),("ce",chosen_ce)]:
                for k in (2,6,12,50):
                    view={(items[i]["page"],items[i]["layout"]) for i in choice[:k]}
                    row[f"{name}_full_{k}"]=int(g<=view)
                    row[f"{name}_recall_{k}"]=len(g&view)/len(g)
            rows.append(row)
            rankings.append({"qid":row["qid"],"doc_id":doc,
                             "pool":[{"page":items[i]["page"],"layout":items[i]["layout"],
                                       "type":items[i]["type"],
                                       "tfidf_score":round(float(scores[i]),7),
                                       "ce_score":round(float(ce[j]),7)}
                                     for j,i in enumerate(pool)]})
            if len(rows)%10==0:print("SHARD_PROGRESS",SHARD,len(rows),"/60","sec",round(time.monotonic()-t0,1),flush=True)
    with (OUT/f"rows_shard_{SHARD}.json").open("w") as f:
        json.dump(rows,f)
    with (OUT/f"rankings_shard_{SHARD}.jsonl").open("w") as f:
        for r in rankings:f.write(json.dumps(r)+"\n")
    manifest={"shard":SHARD,"n":len(rows),"model_id":MODEL,"model_sha":model_sha,
              "source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
              "layout_sha256":hashlib.sha256(a.read_bytes()).hexdigest(),
              "max_length":384,"seed":audit.SEED,"elapsed_seconds":round(time.monotonic()-t0,1)}
    (OUT/f"manifest_shard_{SHARD}.json").write_text(json.dumps(manifest,indent=2))
    print("SHARD_DONE",json.dumps(manifest),flush=True)
    assert len(rows)==60
if __name__=="__main__":main()
