#!/usr/bin/env python3
"""Novel-combination-targeted hyperedge regularization: independent December holdout.

Train 2017 June12-25, dev July10-Aug06 unseen June predicate combinations,
TEST December03-Dec30 organic query log, never touched by tuning or training.
Partition units are the same 120 June popular property IDs. Diagnostic, not QA.
"""
import datetime,hashlib,itertools,json,math,random
from collections import Counter
from pathlib import Path
import temporal_wikidata as base
import hyperedge_generalization as hg
OUT=Path("results_novel_december");OUT.mkdir(exist_ok=True)
DEC_URL="https://analytics.wikimedia.org/datasets/one-off/wikidata/sparql_query_logs/2017-12-03_2017-12-30/2017-12-03_2017-12-30_organic.tsv.gz"
BETAS=hg.BETAS
def main():
    june,sha1=base.load()
    train_raw=[r for r in june if r[0]<14]
    freq=Counter()
    for _,q in train_raw:freq.update(q)
    selected=[p for p,_ in sorted(freq.items(),key=lambda x:(-x[1],x[0]))[:120]]
    train,_=base.prop_stats(train_raw,selected)
    seen=set(q for _,q in train)
    july,sha2=hg.period(hg.jm.URL,hg.jm.START)
    dev,_=base.prop_stats(july,selected)
    dev_novel=[q for q in dev if q[1] not in seen]
    assert len(dev_novel)>300
    p={str(beta):hg.hybrid(train,120,beta)[0] for beta in BETAS}
    devscores={str(beta):hg.score(dev_novel,p[str(beta)]) for beta in BETAS}
    chosen=min(BETAS,key=lambda b:(devscores[str(b)]["mean_shards"],
                                -devscores[str(b)]["local_pct"],b))
    print("FROZEN_FROM_NOVEL_DEV",chosen,"DEV_COUNTS",len(dev_novel),flush=True)
    december,sha3=hg.period(DEC_URL,datetime.datetime(2017,12,3))
    test,exclusions=base.prop_stats(december,selected)
    assert len(test)>50000
    novel=[q for q in test if q[1] not in seen]
    familiar=[q for q in test if q[1] in seen]
    assert len(novel)>1000
    scores={str(beta):hg.score(test,p[str(beta)]) for beta in BETAS}
    scores_novel={str(beta):hg.score(novel,p[str(beta)]) for beta in BETAS}
    baseline=p["0"]
    co=Counter()
    for _,q in train:co.update(itertools.combinations(q,2))
    metis=base.balanced_metis(selected,co)
    report={"schema":"novel-hyperedge-december-independent-v1",
       "train_period":"2017 June12-25","dev_period":"2017 July10-Aug06",
       "test_period":"2017 December03-Dec30",
       "source_sha256":{"train":sha1,"dev":sha2,"test":sha3},
       "n_queries":{"train":len(train),"novel_dev":len(dev_novel),"december_total":len(test),
                    "december_novel":len(novel),"december_familiar":len(familiar)},
       "selected_beta_by_novel_dev":chosen,
       "dev_novel_scores":devscores,
       "december_total_scores":scores,
       "december_novel_scores":scores_novel,
       "december_familiar_scores":{str(b):hg.score(familiar,p[str(b)]) for b in BETAS},
       "benchmark":{"baseline_direct_KM1":hg.score(test,baseline),
         "METIS_clique":hg.score(test,metis),
         "METIS_novel":hg.score(novel,metis)},
       "paired_december":{"chosen_vs_direct_total":hg.ci_days(test,p[str(chosen)],baseline),
          "chosen_vs_direct_novel":hg.ci_days(novel,p[str(chosen)],baseline),
          "chosen_vs_metis_novel":hg.ci_days(novel,p[str(chosen)],metis)},
       "cautions":["December source is a different heldout 28-day logfile, query gold used only for final scoring",
         "Novel means unseen COMBINATION of June-selected property IDs, not novel property names",
         "This is a fixed 120-property simulated partition; no RDF triple byte weights or RAG latency",
         "Weights selected by July dev unseen-pattern score, which has been partially studied previously",
         "Only four existing regularization candidates, not an original new algorithm",
         "Repeated uses of June training data; independent December holdout does not establish 2026 deployment validity"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("DECEMBER_NOVEL_START");print(json.dumps(report,indent=2));print("DECEMBER_NOVEL_END")
if __name__=="__main__":main()
