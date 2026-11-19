#!/usr/bin/env python3
"""Query-text-only online shift, no future gold and no observed gold for deployable method.

Uses original TopoGraphRAG page layout text and new incoming query strings.
A query is converted to pseudo support pages via lexical query-page TF-IDF;
best ONE cross-shard swap picked using ONLY observed query text. All future
evidence support labels are evaluation-only. Compare against frozen and
observed-gold feedback upper-control, plus fully retrospective future oracle.
Exploratory: real pages, no pixel VLM, no distributed latency, page weights 1.
"""
import json, math, random, os, sys, urllib.request, hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pilot
import one_swap_oracle as g
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"topo_fea"))
import audit
SEED=310119
MODE=os.environ.get("ONLINE_SOURCE","bridge_chain")
assert MODE in ("bridge_chain","synthesis")
TARGET="synthesis" if MODE=="bridge_chain" else "bridge_chain"
OUT=Path("results_text_signal_"+MODE);OUT.mkdir(exist_ok=True)

def top_pages_for_queries(contents, queries, top_n):
    v=TfidfVectorizer(stop_words="english",ngram_range=(1,2),
                      sublinear_tf=True,max_features=30000)
    try:
        M=v.fit_transform(contents)
        scores=(v.transform([q["question"] for q in queries])@M.T).toarray()
    except ValueError:
        return [tuple(range(min(top_n,len(contents)))) for _ in queries]
    pp=[]
    for row in scores:
        # Filter nothing by gold, only lexical rank on original page text.
        idx=np.argsort(-row,kind="stable")[:top_n]
        pp.append(tuple(sorted(map(int,idx))))
    return pp

def best_feedback_swap(part, predicted):
    # Shared candidate set with observed-gold comparator.
    pp=[set(p) for p in predicted]
    def cost(p):
        return sum(len({p[x] for x in need})==1 for need in pp)
    labels=list(part);best=(cost(labels),None)
    for i in range(len(labels)):
        for j in range(i+1,len(labels)):
            if labels[i]==labels[j]:continue
            labels[i],labels[j]=labels[j],labels[i]
            gain=cost(labels)
            labels[i],labels[j]=labels[j],labels[i]
            if gain>best[0]:best=(gain,(i,j))
    if best[1]:
        i,j=best[1];labels[i],labels[j]=labels[j],labels[i]
    return labels

def contents_by_page(entries,n):
    texts=[""]*n
    for e in entries:
        p=e["page"]
        if 0<=p<n:texts[p]+=" "+e["text"][:1000]
    return [s[:16000] or "empty page" for s in texts]

def main():
    questions=pilot.download("annotations/benchmark.json")
    man=pilot.download("manifest.json")
    sizes={int(d["doc_id"]):len(d["files"]["page_images"]) for d in man["documents"]}
    archive=Path("layouts.tar.zst")
    if not archive.exists():
        urllib.request.urlretrieve(
          "https://huggingface.co/datasets/diandianone123/topographrag-bench/resolve/main/archives/layout_content.tar.zst",archive)
    print("LAYOUT_HASH",hashlib.sha256(archive.read_bytes()).hexdigest(),flush=True)
    doclayouts, stats=audit.text_layouts(archive,man)
    by=defaultdict(list)
    for q in questions:
        pp=pilot.pages(q);d=int(q["doc_id"])
        if len(pp)>=2 and 0<=min(pp) and max(pp)<sizes[d]:
            by[d].append(q)
    rows=[];docinfo=[];diagn=Counter()
    for d in sorted(by):
        n=sizes[d]
        if not 20<=n<=39:continue
        old=[q for q in by[d] if q["question_type"]==MODE]
        new=[q for q in by[d] if q["question_type"]==TARGET]
        if len(old)<2 or len(new)<4:continue
        rng=random.Random(SEED+d);rng.shuffle(new)
        cut=max(2,len(new)//2)
        seen,future=new[:cut],new[cut:]
        if len(future)<2:continue
        base=pilot.metis_pages(n,4,old,400)
        content=contents_by_page(doclayouts[d],n)
        topn=2 if MODE=="synthesis" else 3
        pseudo=top_pages_for_queries(content,seen,topn)
        query_model=best_feedback_swap(base,pseudo)
        observed_gold,gold_gain=g.oracle_one_swap(base,seen)
        future_gold,future_gain=g.oracle_one_swap(base,future)
        # Compare demand estimation directly, but ONLY metric after predictions.
        gold_seen=[set(pilot.pages(q)) for q in seen]
        lexical_recalls=[len(set(a)&b)/len(b) for a,b in zip(pseudo,gold_seen)]
        diagn["observed_support_recall_sum"]+=sum(lexical_recalls)
        diagn["observed_support_recall_n"]+=len(lexical_recalls)
        for name,p in {"query_text":query_model,"gold_feedback":observed_gold,
                       "future_oracle":future_gold}.items():
            assert max(Counter(p).values())<=math.ceil(n/4)
            assert sum(a!=b for a,b in zip(p,base))<=2
        docinfo.append({"doc_id":d,"n_pages":n,"old_count":len(old),
                 "observed_count":len(seen),"future_count":len(future),
                 "feedback_oracle_local_gain":gold_gain,
                 "future_oracle_local_gain":future_gain})
        for q in future:
            pp=pilot.pages(q)
            row={"doc_id":d,"qid":q.get("mh_id") or q.get("sq_id")}
            for name,p in (("frozen",base),("query_text",query_model),
                           ("gold_feedback",observed_gold),("future_oracle",future_gold)):
                row[name]=len({p[t] for t in pp})
            rows.append(row)
    assert len(rows)>=50 and len(docinfo)>=15,(len(rows),len(docinfo))
    methods=("frozen","query_text","gold_feedback","future_oracle")
    report={"schema":"online-semantic-observed-query-placement-v1",
      "mode":MODE+"_to_"+TARGET,"n_docs":len(docinfo),"n_future_queries":len(rows),
      "observed_lexical_support_recall":round(diagn["observed_support_recall_sum"]/diagn["observed_support_recall_n"],4),
      "methods":{m:g.test_stats(rows,m) for m in methods},
      "paired":{f"{m}_vs_frozen":g.bootstrap(rows,m,"frozen") for m in methods[1:]},
      "caveats":["Future supports used in scorer only, except fully labeled retrospective oracle",
                 "Gold-feedback selector is an idealized observed-support control, not deployed method",
                 "Query-text selector sees only observed incoming question text plus source page descriptions",
                 "Gold historical support pages still used for base partition (oracle historic log)",
                 "No measured latency or full multimodal RAG; page count proxy only",
                 "Same benchmark and document-shared train/test, exploratory not confirmatory"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
    OUT.joinpath("by_doc.json").write_text(json.dumps(docinfo,indent=2))
    print("TEXT_SIGNAL_RESULT_START")
    print(json.dumps(report,indent=2))
    print("TEXT_SIGNAL_RESULT_END")
if __name__=="__main__":main()
