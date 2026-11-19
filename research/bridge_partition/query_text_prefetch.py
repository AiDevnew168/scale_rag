#!/usr/bin/env python3
"""Blind query-text prefetch placement: compare one-swap feedback and future text.

A *batch-of-queries-known* scenario, NOT forecasting unknown questions.
Future question WORDING is used in prospective prefetch planner; future GOLD
support IDs are never passed into planning. Evaluate on actual gold supports.
"""
import json, os, random, math
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import pilot
import one_swap_oracle as previous
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"topo_fea"))
import audit
MODE=os.environ.get("ONLINE_SOURCE","bridge_chain")
TARGET="synthesis" if MODE=="bridge_chain" else "bridge_chain"
OUT=Path("results_text_prefetch_"+MODE);OUT.mkdir(exist_ok=True)
SEED=310119

def best_one_swap(part,page_sets):
    """Optimize predicted query page sets, never any target gold annotations."""
    n=len(part)
    def hits(a):
        return sum(len({a[x] for x in q})==1 for q in page_sets if q)
    best=hits(part);move=None
    for i in range(n):
        for j in range(i+1,n):
            if part[i]==part[j]:continue
            part[i],part[j]=part[j],part[i]
            x=hits(part)
            part[i],part[j]=part[j],part[i]
            if x>best:
                best=x;move=(i,j)
    out=list(part)
    if move:
        i,j=move;out[i],out[j]=out[j],out[i]
    return out

def page_contents(layouts,n):
    result=[""]*n
    for x in layouts:
        p=x["page"]
        if 0<=p<n:result[p]+=" "+x["text"][:550]
    return [t[:14000] for t in result]

def predict_page_sets(questions,contents,n_top):
    vec=TfidfVectorizer(stop_words="english",max_features=30000,
                         ngram_range=(1,2),sublinear_tf=True)
    try:M=vec.fit_transform(contents)
    except ValueError:return [tuple() for _ in questions]
    Q=vec.transform([q["question"] for q in questions])
    sims=(Q@M.T).toarray()
    result=[]
    for q,score in zip(questions,sims):
        indices=list(np.argsort(-score,kind="stable")[:n_top])
        result.append(tuple(indices))
    return result

def main():
    allq=pilot.download("annotations/benchmark.json")
    man=pilot.download("manifest.json")
    n_pages={int(d["doc_id"]):len(d["files"]["page_images"]) for d in man["documents"]}
    group=defaultdict(list)
    for q in allq:
        pp=pilot.pages(q);d=int(q["doc_id"])
        if len(pp)>1 and min(pp)>=0 and max(pp)<n_pages[d]:group[d].append(q)
    # Fit a blind cross-document query-topology classifier (query TEXT ONLY)
    # on non-evaluation docs. Split by document before fitting vocabulary.
    eligible=set()
    for d in sorted(group):
        n=n_pages[d]
        if not 20<=n<=39:continue
        hist=[q for q in group[d] if q["question_type"]==MODE]
        target=[q for q in group[d] if q["question_type"]==TARGET]
        if len(hist)>=2 and len(target)>=4:eligible.add(d)
    train_questions=[q for q in allq if q.get("question_type") in ("bridge_chain","synthesis")
                     and int(q["doc_id"]) not in eligible]
    assert train_questions and set(q["doc_id"] for q in train_questions).isdisjoint(eligible)
    topology_vec=TfidfVectorizer(ngram_range=(1,2),stop_words="english",
                                max_features=20000,min_df=2)
    Xt=topology_vec.fit_transform([q["question"] for q in train_questions])
    topology_model=LogisticRegression(max_iter=500,class_weight="balanced",random_state=SEED)
    topology_model.fit(Xt,[int(q["question_type"]=="bridge_chain") for q in train_questions])
    archive=Path("layouts.tar.zst")
    if not archive.exists():
        import urllib.request
        urllib.request.urlretrieve(pilot.ROOT+"archives/layout_content.tar.zst",archive)
    source,stats=audit.text_layouts(archive,man)
    rows=[];included=[];warnings=Counter();topology_correct=Counter();movement=Counter();image_move_trace=[]
    for d in sorted(group):
        n=n_pages[d]
        if not 20<=n<=39:continue
        hist=[q for q in group[d] if q["question_type"]==MODE]
        target=[q for q in group[d] if q["question_type"]==TARGET]
        if len(hist)<2 or len(target)<4:continue
        rng=random.Random(SEED+d);rng.shuffle(target)
        cut=max(2,len(target)//2)
        seen,future=target[:cut],target[cut:]
        if len(future)<2:continue
        original=pilot.metis_pages(n,4,hist,400)
        text_pages=page_contents(source[d],n)
        try:
            predicted2=predict_page_sets(future,text_pages,2)
            predicted3=predict_page_sets(future,text_pages,3)
            observed=previous.oracle_one_swap(original,seen)[0]
            prefetch2=best_one_swap(original,predicted2)
            prefetch3=best_one_swap(original,predicted3)
            future_oracle=previous.oracle_one_swap(original,future)[0]
            # No gold future topology or support used. Classification uses
            # question wording only, with no labels from evaluation documents.
            predicted_bridge=topology_model.predict(
                topology_vec.transform([q["question"] for q in future]))
            predicted_rate=float(np.mean(predicted_bridge))
            do_prefetch=predicted_rate>=.5
            gated=prefetch3 if do_prefetch else original
            movement["gated_changed_docs"]+=int(gated!=original)
            movement["gated_page_moves"]+=sum(a!=b for a,b in zip(gated,original))
            movement["prefetch3_changed_docs"]+=int(prefetch3!=original)
            movement["prefetch3_page_moves"]+=sum(a!=b for a,b in zip(prefetch3,original))
            topology_correct["n_batches"]+=1
            topology_correct["n_correct_batches"]+=int(
                do_prefetch==(TARGET=="bridge_chain"))
            topology_correct["n_future_queries"]+=len(future)
            topology_correct["n_correct_future_questions"]+=int(
                do_prefetch==(TARGET=="bridge_chain"))*len(future)
        except Exception as e:
            warnings[type(e).__name__]+=1;continue
        included.append({"doc_id":d,"historical_q":len(hist),"feedback_q":len(seen),
           "future_q":len(future),"n_pages":n})
        move_indices=[p for p,(a,b) in enumerate(zip(original,gated)) if a!=b]
        if move_indices:
            # Official manifest page_images list is lexicographically sorted:
            # mapping by suffix preserves index=10 vs index=2.
            import re
            image_map={}
            for file_path in man["documents"][d]["files"]["page_images"]:
                matched=re.search(r"_(\d+)\.(?:jpg|jpeg|png)$",file_path,re.I)
                if matched:image_map[int(matched.group(1))]=file_path
            assert all(p in image_map for p in move_indices),(d,move_indices)
            benefits=[len({original[p] for p in pilot.pages(q)})-
                      len({gated[p] for p in pilot.pages(q)}) for q in future]
            image_move_trace.append({"doc_id":d,"n_pages":n,
                "incoming_questions":len(future),
                "page_indices":move_indices,
                "image_paths":[image_map[p] for p in move_indices],
                "saved_shard_activations":sum(benefits),
                "gains":sum(v>0 for v in benefits),"losses":sum(v<0 for v in benefits)})
        for q in future:
            needed=pilot.pages(q)
            row={"doc_id":d,"qid":q.get("mh_id") or q.get("sq_id")}
            for method,p in (("static",original),("observed_swap",observed),
                             ("prefetch2",prefetch2),("prefetch3",prefetch3),
                             ("topology_gated",gated),
                             ("future_oracle",future_oracle)):
                row[method]=len({p[x] for x in needed})
            rows.append(row)
    if len(included)<12 or len(rows)<40:raise RuntimeError(f"Not enough examples {len(included)} {len(rows)}")
    methods=("static","observed_swap","prefetch2","prefetch3","topology_gated","future_oracle")
    report={"schema":"prospective-question-text-prefetch-v1",
      "mode":MODE+"_to_"+TARGET,
      "n_docs":len(included),"n_queries":len(rows),
      "topology_prediction_counts":dict(topology_correct),
      "migration_diagnostics":dict(movement),
      "saved_shard_activations_gated_vs_static":sum(r["static"]-r["topology_gated"] for r in rows),
      "page_moves_per_saved_activation":round(movement["gated_page_moves"]/max(1,sum(r["static"]-r["topology_gated"] for r in rows)),3),
      "classifier_train_questions":len(train_questions),
      "classifier_train_documents":len(set(q["doc_id"] for q in train_questions)),
      "means":{m:previous.test_stats(rows,m) for m in methods},
      "paired":{
         "prefetch2_vs_static":previous.bootstrap(rows,"prefetch2","static"),
         "topology_gated_vs_static":previous.bootstrap(rows,"topology_gated","static"),
         "prefetch3_vs_static":previous.bootstrap(rows,"prefetch3","static"),
         "prefetch2_vs_observed":previous.bootstrap(rows,"prefetch2","observed_swap"),
         "oracle_vs_prefetch2":previous.bootstrap(rows,"future_oracle","prefetch2")},
      "warnings":dict(warnings),
      "cautions":[
        "Future QUESTION TEXT is known and used to plan before serving an incoming query batch: THIS IS NOT unknown-future forecasting",
        "Gated selection devised after reviewing previous per-type performance: exploratory, not independent confirmation",
        "Question topology classifier trained only on completely different documents and query text, not gold supports",
        "Future GOLD evidence pages never used in scoring or choosing prefetch swap; except separate explicitly labeled retrospective oracle",
        "One swap exchanges two equal-page-cost nodes, same migration budget across methods",
        "Full source page texts/visual descriptions, not image pixels; query text top-k lexical is an imperfect relevance proxy",
        "No measured service latency, actual retrieval, entity graph, byte weights or request-arrival delays",
        "Exploratory after previous experiments on same benchmark; CI not independent confirmatory"]
      }
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("per_question.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
    OUT.joinpath("document_ids.json").write_text(json.dumps(included,indent=2))
    OUT.joinpath("image_move_trace.json").write_text(json.dumps(image_move_trace,indent=2))
    print("PREFETCH_REPORT_START");print(json.dumps(report,indent=2));print("PREFETCH_REPORT_END")
if __name__=="__main__":main()
