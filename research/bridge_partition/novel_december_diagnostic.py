#!/usr/bin/env python3
"""Audit shift/concentration and unique-pattern view on unseen December WDQS.
Only a descriptive distribution diagnostic; no model selection.
"""
import json,datetime,itertools,hashlib
from collections import Counter
from pathlib import Path
import temporal_wikidata as base
import hyperedge_generalization as hg
OUT=Path("results_december_diagnostic");OUT.mkdir(exist_ok=True)
URL="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/2017-12-03_2017-12-30/2017-12-03_2017-12-30_organic.tsv.gz"
def main():
    june,_=base.load()
    hist=[q for q in june if q[0]<14]
    freq=Counter()
    for day,props in hist:freq.update(props)
    selected=[p for p,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:120]]
    train,_=base.prop_stats(hist,selected)
    seen={q for _,q in train}
    raw,sha=hg.period(URL,datetime.datetime(2017,12,3))
    test,_=base.prop_stats(raw,selected)
    novel=[q for _,q in test if q not in seen]
    counts=Counter(novel)
    print("DEC_NOVEL_FREQ_TOP",counts.most_common(10),flush=True)
    preds={b:hg.hybrid(train,120,b)[0] for b in (0,0.25,1)}
    def span(q,p):return len(set(p[i] for i in q))
    total=len(novel)
    def metrics(qs,p):
        return {"local":round(100*sum(span(q,p)==1 for q in qs)/len(qs),3),
                "n":len(qs),"mean_activated":round(sum(span(q,p) for q in qs)/len(qs),4)}
    samples=list(counts)
    result={"schema":"wikidata-december-concentration-v1",
      "source_sha256":sha,"n_requests":len(test),"n_novel_requests":total,
      "n_unique_novel_patterns":len(counts),
      "top1_share_pct":round(100*counts.most_common(1)[0][1]/total,3),
      "top10_share_pct":round(100*sum(v for _,v in counts.most_common(10))/total,3),
      "top10":[{"pattern":[selected[i] for i in q],"count":count,
                "by_beta":{str(b):span(q,preds[b]) for b in preds}}
               for q,count in counts.most_common(10)],
      "request_weighted":{str(b):metrics(novel,preds[b]) for b in preds},
      "unique_pattern_weighted":{str(b):metrics(samples,preds[b]) for b in preds},
      "size_distribution_request":dict(Counter(str(len(q)) for q in novel)),
      "size_distribution_unique":dict(Counter(str(len(q)) for q in samples)),
      "limitations":["Descriptive post-hoc diagnosis, December labels already inspected",
        "Training only June properties, no current 2026 Wikidata change accounted",
        "SPARQL parser extracts wdt: property IRIs; no physical graph distribution or wall-clock runtime"]}
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("DEC_DIAGNOSTIC_START");print(json.dumps(result,indent=2));print("DEC_DIAGNOSTIC_END")
if __name__=="__main__":main()
