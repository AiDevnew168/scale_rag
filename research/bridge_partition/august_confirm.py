#!/usr/bin/env python3
"""Pre-specified Aug-Sep 2017 *independent-interval* holdout for bounded migration.

Algorithms and hard 10%-node migration budget frozen in source before reading
the independent 2017-08-07..2017-09-03 organic SPARQL workload. Node IDs
are top 120 predicates from 2017-06-12..25, selected from TRAIN ONLY.
Observed adaptation traffic: 2017-06-26..2017-07-02. No remaining future
traffic supplies labels to partitioners or selects the fixed baselines.

This is a physical-placement proxy for KG SPARQL patterns, NOT RAG QA.
"""
import csv,gzip,hashlib,io,itertools,json,math
from collections import Counter
from datetime import datetime
from pathlib import Path
import urllib.request
import mtkahypar
import temporal_wikidata as a
import temporal_hypergraph as h
import temporal_refresh as r

K=4;N=120;SEED=261119
OUT=Path("results_wikidata_aug_confirm");OUT.mkdir(exist_ok=True)
TEST_URL=("https://analytics.wikimedia.org/datasets/one-off/wikidata/"
          "sparql_query_logs/2017-08-07_2017-09-03/"
          "2017-08-07_2017-09-03_organic.tsv.gz")
START=datetime(2017,8,7)

def august_queries():
    req=urllib.request.Request(TEST_URL,headers={"User-Agent":"AcademicWorkloadAudit/1.0"})
    raw=urllib.request.urlopen(req,timeout=120).read()
    result=[]
    from urllib.parse import unquote_plus
    for x in csv.DictReader(io.StringIO(gzip.decompress(raw).decode("utf8",errors="replace")),delimiter="\t"):
        try:
            stamp=datetime.strptime(x["timestamp"][:19],"%Y-%m-%d %H:%M:%S")
            day=(stamp-START).days
        except(ValueError,KeyError):continue
        if not 0<=day<28:continue
        props=tuple(sorted(set(a.PATT.findall(unquote_plus(x["anonymizedQuery"])))))
        result.append((day,props))
    return result,hashlib.sha256(raw).hexdigest()

def old_metis(train,selected):
    co=Counter()
    for _,pp in train:co.update(itertools.combinations(pp,2))
    return a.balanced_metis(selected,co)

def main():
    r.quick_test_swap_delta()
    raw,train_sha=a.load()
    historic=[x for x in raw if x[0]<14]
    feedback=[x for x in raw if 14<=x[0]<21]
    freq=Counter()
    for _,pp in historic:freq.update(set(pp))
    selected=tuple(x for x,v in sorted(freq.items(),
                                    key=lambda p:(-p[1],p[0]))[:N])
    assert len(selected)==N
    train,excluded_train=a.prop_stats(historic,selected)
    observed,excluded_feedback=a.prop_stats(feedback,selected)
    future_raw,test_sha=august_queries()
    test,excluded_test=a.prop_stats(future_raw,selected)
    print("AUGUST_INDEPENDENT_TEST_SHA256",test_sha,"TOTAL",len(future_raw),
          "ELIGIBLE",len(test),flush=True)
    assert len(test)>30000 and len(train)>40000 and len(observed)>18000
    frozen_metis=old_metis(train,selected)
    observed_metis=old_metis(observed,selected)
    frozen_hyper=h.partition_direct(train,N,mtkahypar.Objective.KM1)
    observed_hyper=h.partition_direct(train+observed,N,mtkahypar.Objective.KM1)
    wtrain=r.to_weight_matrix(train,N)
    wobs=r.to_weight_matrix(observed,N)
    wblend=wtrain/max(1,len(train))+wobs/max(1,len(observed))
    budget=12
    metis_bounded,mmoved=r.refine_swaps(frozen_metis,wobs,budget)
    hyper_bounded,hmoved=r.refine_swaps(frozen_hyper,wobs,budget)
    hyper_blended,hbmoved=r.refine_swaps(frozen_hyper,wblend,budget)
    methods={
      "popularity_by_historical_frequency":[i*K//N for i in range(N)],
      "metis_frozen14":frozen_metis,
      "metis_observed7_full":observed_metis,
      "metis_bounded10pct":metis_bounded,
      "hyper_frozen14":frozen_hyper,
      "hyper_observed21_full":observed_hyper,
      "hyper_bounded10pct":hyper_bounded,
      "hyper_blended10pct":hyper_blended}
    assert max(Counter(metis_bounded).values())==N/K
    assert max(Counter(hyper_bounded).values())==N/K
    for key,part in methods.items():
        assert len(part)==N and max(Counter(part).values())==N/K,(key,Counter(part))
        if "bounded" in key:
            assert r.optimal_label_moves(frozen_metis if key.startswith("metis") else frozen_hyper,part)<=budget
    metrics={key:r.eval_subset(test,part) for key,part in methods.items()}
    pairs=[
      ("hyper_frozen14","metis_frozen14"),
      ("hyper_bounded10pct","hyper_frozen14"),
      ("hyper_blended10pct","hyper_frozen14"),
      ("hyper_observed21_full","hyper_frozen14"),
      ("hyper_bounded10pct","metis_frozen14"),
      ("metis_bounded10pct","metis_frozen14"),
      ("metis_observed7_full","metis_frozen14"),
      ("hyper_bounded10pct","metis_bounded10pct")]
    paired={x+"_vs_"+y:r.day_bootstrap(test,methods[x],methods[y]) for x,y in pairs}
    # A crucial no-frequency-inflation control: evaluate each query
    # property-set at most once, plus entirely new property-set combinations.
    # Novelty is among the SAME 120 train-selected predicates.
    def distinct(rows):
        seen=set();result=[]
        for day,pp in rows:
            if pp in seen:continue
            seen.add(pp);result.append((day,pp))
        return result
    seen_previously={pp for _,pp in train+observed}
    fresh=[(day,pp) for day,pp in test if pp not in seen_previously]
    subgroups={"unique_future_patterns":distinct(test),
       "future_patterns_unseen_in_train_and_feedback":fresh,
       "unique_truly_new_future_patterns":distinct(fresh)}
    subgroup_metrics={
       group:{"n":len(data),
          "methods":{name:r.eval_subset(data,part)
              for name,part in methods.items() if name in (
                "metis_frozen14","metis_bounded10pct","hyper_frozen14",
                "hyper_bounded10pct","hyper_blended10pct")},
          "paired_hyper_frozen_vs_metis_frozen":r.day_bootstrap(
              data,methods["hyper_frozen14"],methods["metis_frozen14"]),
          "paired_hyper_bounded_vs_hyper_frozen":r.day_bootstrap(
              data,methods["hyper_bounded10pct"],methods["hyper_frozen14"]),
          "paired_hyper_bounded_vs_metis_bounded":r.day_bootstrap(
              data,methods["hyper_bounded10pct"],methods["metis_bounded10pct"])}
       for group,data in subgroups.items() if len(data)>100}
    migration={key:{"vs_metis_frozen14":r.optimal_label_moves(frozen_metis,part),
                    "vs_hyper_frozen14":r.optimal_label_moves(frozen_hyper,part)}
               for key,part in methods.items()}
    report={"schema":"august-independent-temporal-migration-confirm-v1",
      "seed":SEED,"original_train_sha256":train_sha,
      "untouched_future_url":TEST_URL,"future_sha256":test_sha,
      "periods":{"training_first14":"2017-06-12..2017-06-25",
                 "observed_feedback7":"2017-06-26..2017-07-02",
                 "test_independent_august28":"2017-08-07..2017-09-03"},
      "n_raw_future_requests":len(future_raw),
      "n_eligible_test_requests":len(test),
      "n_training_requests":len(train),
      "n_observed_update_requests":len(observed),
      "n_predicates":N,"n_shards":K,"hard_max_nodes_per_shard":N//K,
      "hard_migration_budget":budget,"actual_local_swap_moves":{
         "metis_bounded10pct":mmoved,"hyper_bounded10pct":hmoved,
         "hyper_blended10pct":hbmoved},
      "metrics":metrics,"paired":paired,"subgroup_generalization":subgroup_metrics,
      "minimum_label_aligned_moved_nodes":migration,
      "excluded_future_queries":excluded_test,
      "limitations":["Prospective independent later log file, but model family selection previously explored on older Wikidata periods",
         "Organic SPARQL predicate co-occurrence not natural-language GraphRAG question-answer quality",
         "120 predicates with equal node weights; not real KG triples, actual memory bytes or network latency",
         "Only questions mentioning 2-12 of selected historic predicates evaluated",
         "Unique pattern subgroup is a set-of-predicates deduplication, not full SPARQL query identity",
         "One fixed 10pct migration budget; no full SWORD/WISE/WASP or more sophisticated dynamic baseline",
         "No future test query/answer information enters methods; tests only score predefined variants",
         "Bootstrap resamples 28 day-blocks and reflects only within-period temporal variability"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    OUT.joinpath("placements.json").write_text(json.dumps(methods,indent=2))
    print("AUGUST_CONFIRM_REPORT_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("AUGUST_CONFIRM_REPORT_END",flush=True)
if __name__=="__main__":main()
