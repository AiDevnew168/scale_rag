#!/usr/bin/env python3
"""Independent query-cluster and timing risk check on completed TRAIN-only replay.

Input: frozen 24 ORIGINAL training query texts with exactly 2 repetitions.
No original query text, no customer metadata; never silently exclude failures.
This is conditional descriptive sensitivity, NOT a formal confidence bound
under natural temporal drift or evidence of production economic profit.
"""
import argparse
import collections
import json
import math
import random
import statistics
from pathlib import Path
import candidate3_trainonly_selective_fetch_verdict as basic

N_BOOTSTRAP=5000
SEED=20261121

def quantile(values, p):
    a=sorted(values)
    if not a:
        raise ValueError("no values")
    return a[max(0,min(len(a)-1,math.floor(p*(len(a)-1))))]

def assess(report):
    initial=basic.interpret(report)
    guarded={
        "schema":"candidate3-train-only-cluster-latency-sensitivity-v1",
        "primary_24x2_verdict":initial,
        "research_inference":"EXPLORATORY_NO_PRODUCTION_OR_JOURNAL_PROOF",
        "n_bootstrap":N_BOOTSTRAP,
        "cluster_unit":"original_exact_query_text_NOT_timing_repetition",
        "no_independence_or_temporal_mixing_assumption_certified":True,
        "journals_SOTA_GO":False,
    }
    if initial.get("status")!="EXPLORATORY_TRAIN_ONLY_MEASURED":
        return guarded|{"status":"BLOCKED_INVALID_FROZEN_PAIRS"}
    rows=report["deidentified_original_training_paired_rows"]
    by_hash=collections.defaultdict(list)
    for row in rows:
        by_hash[row["text_sha256"]].append(row)
    hashes=sorted(by_hash)
    if len(hashes)!=24 or any(len(by_hash[h])!=2 for h in hashes):
        return guarded|{"status":"INVALID_QUERY_CLUSTERS"}
    delta_by_hash={
        h:statistics.mean(r["saved_ms"] for r in by_hash[h]) for h in hashes
    }
    frac_by_hash={
        h:statistics.mean(1-r["pushdown_rdf_bytes"]/r["full_rdf_bytes"]
                         for r in by_hash[h]) for h in hashes
    }
    gain=[delta_by_hash[h] for h in hashes]
    gain_mean=statistics.mean(gain)
    n_negative=sum(x<0 for x in gain)
    rng=random.Random(SEED)
    resampled_gain=[]
    resampled_bytes=[]
    randomization_null=[]
    for _ in range(N_BOOTSTRAP):
        sampled=[hashes[rng.randrange(len(hashes))] for _ in hashes]
        resampled_gain.append(statistics.mean(delta_by_hash[h] for h in sampled))
        resampled_bytes.append(statistics.median(frac_by_hash[h] for h in sampled))
        randomization_null.append(
            sum((1 if rng.randrange(2) else -1)*delta_by_hash[h] for h in hashes)/len(hashes))
    gain_q=[quantile(resampled_gain,0.025),quantile(resampled_gain,0.975)]
    bytes_q=[quantile(resampled_bytes,0.025),quantile(resampled_bytes,0.975)]
    empirical_signflip_p=(1+sum(abs(x)>=abs(gain_mean) for x in randomization_null))/(N_BOOTSTRAP+1)
    return guarded|{
        "status":"VALID_CONDITIONAL_QUERY_CLUSTER_SENSITIVITY",
        "n_query_clusters":len(hashes),
        "observed_mean_query_saved_ms":round(gain_mean,5),
        "query_cluster_bootstrap95_latency_ms_DESCRIPTIVE":
            [round(x,5) for x in gain_q],
        "query_cluster_bootstrap95_median_fraction_rdf_bytes_saved_DESCRIPTIVE":
            [round(x,6) for x in bytes_q],
        "n_query_clusters_with_negative_mean_latency":n_negative,
        "random_signflip_exploratory_two_sided_p":round(empirical_signflip_p,5),
        "signflip_exchangeability_under_null_unverified":True,
        "baseline_query_order_cache_and_container_cohosting_may_bias_timing":True,
        "positive_lower_gain_under_cluster_sensitivity":gain_q[0]>0,
        "research_development_gate_not_publication":
            bool(initial.get("engineering_followup_if_both") and gain_q[0]>0),
        "note":"A sign-flip null is not justified without sign symmetry; do not label this p-value confirmatory."
    }

def main():
    a=argparse.ArgumentParser()
    a.add_argument("report",type=Path)
    args=a.parse_args()
    output=assess(json.loads(args.report.read_text(encoding="utf8")))
    print(json.dumps(output,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
