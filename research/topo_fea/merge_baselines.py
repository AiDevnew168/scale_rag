#!/usr/bin/env python3
"""Cross-run paired ranking comparisons; 300 exact question IDs verified."""
import csv,json,random
from pathlib import Path
from collections import defaultdict
import numpy as np

def load(path):
    with Path(path).open(newline="",encoding="utf8") as f:
        return {r["qid"]:r for r in csv.DictReader(f)}
def bootstrap(rows, new, old, seed=261119):
    groups=defaultdict(list)
    for r in rows:groups[int(r["doc_id"])].append(r)
    docs=sorted(groups)
    wins=sum(int(r[new])>int(r[old]) for r in rows)
    losses=sum(int(r[new])<int(r[old]) for r in rows)
    rng=random.Random(seed); dist=[]
    for _ in range(2000):
        picks=[rng.choice(docs) for _ in docs]
        rs=[r for d in picks for r in groups[d]]
        dist.append(100*sum(int(r[new])-int(r[old]) for r in rs)/len(rs))
    lo,hi=np.percentile(dist,[2.5,97.5])
    return dict(wins=wins,losses=losses,ties=len(rows)-wins-losses,
                delta_pp=round(100*(wins-losses)/len(rows),3),
                ci95_pp=[round(float(lo),3),round(float(hi),3)])
def main():
    bm=load("artifacts_bm25/per_question_bm25.csv")
    ce=load("artifacts_ce/per_question_ce.csv")
    sr=load("artifacts_structural/per_question_structural.csv")
    assert len(bm)==len(ce)==len(sr)==300
    assert set(bm)==set(ce)==set(sr)
    rows=[]
    for qid in sorted(bm):
        b,c,s=bm[qid],ce[qid],sr[qid]
        assert int(b["doc_id"])==int(c["doc_id"])==int(s["doc_id"])
        assert b["kind"]==c["kind"]==s["kind"]
        assert int(b["tfidf_full_6"])==int(c["tfidf_full_6"])
        assert int(s["ce_full_6"])==int(c["cross_encoder_full_6"])
        rows.append(dict(qid=qid,doc_id=b["doc_id"],kind=b["kind"],
                         tfidf_full6=b["tfidf_full_6"],bm25_full6=b["bm25_full_6"],
                         ce_full6=c["cross_encoder_full_6"],ce_mmr_full6=s["ce_mmr_full_6"],
                         role_greedy_full6=s["role_greedy_full_6"],
                         role_exact_full6=s["role_exact_full_6"],
                         tfidf_recall6=b["tfidf_recall_6"],bm25_recall6=b["bm25_recall_6"],
                         ce_recall6=c["cross_encoder_recall_6"]))
    methods=["tfidf","bm25","ce","ce_mmr","role_greedy","role_exact"]
    def pct(part,key):return round(100*sum(float(r[key]) for r in part)/len(part),3)
    result={"schema":"topo-300-frozen-ce-bm25-matched-compare-v1","n":len(rows),
       "documents":len({x["doc_id"] for x in rows}),
       "methods_full6_pct":{name:pct(rows,f"{name}_full6") for name in methods},
       "recall6_pct":{name:pct(rows,f"{name}_recall6") for name in ("tfidf","bm25","ce")},
       "paired_against_bm25":{name:bootstrap(rows,f"{name}_full6","bm25_full6") for name in methods if name!="bm25"},
       "by_kind":{kind:{"n":len([x for x in rows if x["kind"]==kind]),
             "full6_pct":{name:pct([x for x in rows if x["kind"]==kind],f"{name}_full6") for name in methods},
             "role_greedy_vs_bm25":bootstrap([x for x in rows if x["kind"]==kind],"role_greedy_full6","bm25_full6")}
                 for kind in ("bridge_chain","synthesis")},
       "limits":["Exploratory, same original 300-question sample from 191 documents",
          "All methods use real layout text/OCR/VLM descriptions only, not direct image pixels",
          "CE-family shares TF-IDF Top-50; BM25 initial pool differs, but same source document",
          "No real scientific relation constraints were annotated/solved",
          "No VLM answer accuracy; this is exact evidence-set retrieval at k=6"]}
    Path("crossrun_report.json").write_text(json.dumps(result,indent=2))
    print("CROSSRUN_REPORT_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("CROSSRUN_REPORT_END",flush=True)
if __name__=="__main__":main()
