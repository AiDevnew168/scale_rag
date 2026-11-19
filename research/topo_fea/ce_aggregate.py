#!/usr/bin/env python3
"""Aggregate 5 real CE shards only if exact sample and SHA fingerprints match."""
import csv,json,random,os
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
import audit

ROOT=Path("results_ce_shards")
OUT=Path("results_ce")
OUT.mkdir(exist_ok=True)

def pct(rows,key):
    return round(100*sum(r[key] for r in rows)/len(rows),3)
def bootstrap(rows,a,b):
    bydoc=defaultdict(list)
    for r in rows:bydoc[r["doc_id"]].append(r)
    docs=sorted(bydoc);rng=random.Random(audit.SEED)
    boots=[]
    for _ in range(2000):
        sampled=[rng.choice(docs) for _ in docs]
        allrows=[x for d in sampled for x in bydoc[d]]
        boots.append(100*sum(x[a]-x[b] for x in allrows)/len(allrows))
    ci=np.percentile(boots,[2.5,97.5])
    return dict(wins=sum(x[a]>x[b] for x in rows),
                losses=sum(x[a]<x[b] for x in rows),
                delta_pp=round(100*sum(x[a]-x[b] for x in rows)/len(rows),3),
                cluster_bootstrap_ci95_pp=[round(float(ci[0]),3),round(float(ci[1]),3)])
def main():
    manifests=[json.loads((ROOT/f"manifest_shard_{i}.json").read_text()) for i in range(5)]
    assert [x["shard"] for x in manifests]==list(range(5))
    assert {x["model_sha"] for x in manifests}.__len__()==1
    assert {x["source_sha256"] for x in manifests}.__len__()==1
    assert {x["layout_sha256"] for x in manifests}.__len__()==1
    rows=[];rankings=[]
    for shard in range(5):
        rows+=json.loads((ROOT/f"rows_shard_{shard}.json").read_text())
        rankings += [json.loads(line) for line in (ROOT/f"rankings_shard_{shard}.jsonl").read_text().splitlines() if line]
    assert len(rows)==len(rankings)==300
    assert len(set(x["qid"] for x in rows))==len(rows)
    assert set(x["qid"] for x in rows)==set(x["qid"] for x in rankings)
    assert len({x["doc_id"] for x in rows})==191
    assert round(pct(rows,"tfidf_full_6"),2)==33.0
    assert abs(pct(rows,"tfidf_full_50")-80.667)<.01
    with (OUT/"per_question_ce.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (OUT/"ce_rankings.jsonl").open("w") as f:
        for x in rankings:f.write(json.dumps(x)+"\n")
    keys=[f"{model}_{metric}_{k}" for model in ("tfidf","ce") for metric in ("full","recall") for k in (2,6,12,50)]
    by_kind={}
    for kind in ("bridge_chain","synthesis"):
        sub=[r for r in rows if r["kind"]==kind]
        by_kind[kind]={"n":len(sub),"pct":{key:pct(sub,key) for key in keys},
                       "paired6":bootstrap(sub,"ce_full_6","tfidf_full_6")}
    counts=dict(gold_in_pool=sum(x["pool_full"] for x in rows),
                top6_tfidf_success=sum(x["tfidf_full_6"] for x in rows),
                top6_ce_success=sum(x["ce_full_6"] for x in rows),
                remaining_pool_headroom_after_ce=sum(x["pool_full"] and not x["ce_full_6"] for x in rows))
    result={"schema":"topo-cross-encoder-sharded-v1","run_type":"5 shards x 60 real questions, pooled post-hoc",
      "n":len(rows),"docs":len({x["doc_id"] for x in rows}),
      "model":manifests[0]["model_id"],"model_revision":manifests[0]["model_sha"],
      "max_length":384,"seed":audit.SEED,
      "source_sha256":manifests[0]["source_sha256"],
      "layout_sha256":manifests[0]["layout_sha256"],
      "overall_pct":{key:pct(rows,key) for key in keys},
      "by_topology":by_kind,"paired_at2":bootstrap(rows,"ce_full_2","tfidf_full_2"),
      "paired_at6":bootstrap(rows,"ce_full_6","tfidf_full_6"),
      "paired_at12":bootstrap(rows,"ce_full_12","tfidf_full_12"),
      "counts":counts,
      "limits":["A true pretrained CrossEncoder, not a multimodal model or a 2026 SOTA reranker",
                "All model inputs use real layout text/OCR/VLM descriptions and user question; no direct image pixels",
                "Same per-document lexical Top-50 candidate pool, all gold fields excluded during scoring",
                "Same exploratory sample as prior experiments; not independently held out",
                "No semantic edge-compatibility gold or VLM answer generation"]}
    (OUT/"report_ce.json").write_text(json.dumps(result,indent=2))
    print("CE_AGGREGATE_REPORT_BEGIN");print(json.dumps(result,indent=2));print("CE_AGGREGATE_REPORT_END")
if __name__=="__main__":main()
