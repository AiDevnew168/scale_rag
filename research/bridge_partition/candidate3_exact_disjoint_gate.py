#!/usr/bin/env python3
"""Exact-query disjoint heldout rerun for previously reused Stream WatDiv templates.

This is a methodological correction, not a new independent benchmark.
Prior 'first20 train/last20 test' split may leak identical query templates.
The real byte-balanced graph remains identical. Query sets are SHA-pinned and
disjoint before candidate selection; final heldout never enters decisions.
"""
import hashlib,json,random
from collections import Counter
from pathlib import Path
import candidate3_streamwatdiv_microshard as core

OUT=Path("results_candidate3_exact_disjoint")
OUT.mkdir(exist_ok=True)
SEED=20261121

def main():
    with core.read_archive() as zipfile:
        lines=zipfile.read("static.nt").splitlines(keepends=True)
        for l in zipfile.read("stream-events.jsonl").splitlines():
            e=json.loads(l)
            for t in e.get("triples",[]):lines.append(t.encode()+b"\n")
        querystrings=[q.strip() for q in zipfile.read("queries.sparql").decode("utf8").splitlines()
            if q.strip().startswith("SELECT")]
    assert len(querystrings)==40
    digests=[hashlib.sha256(q.encode()).hexdigest() for q in querystrings]
    unique={}
    for i,(q,h) in enumerate(zip(querystrings,digests)):
        unique.setdefault(h,(i,q))
    assert len(unique)>=12
    r=random.Random(SEED)
    shuffled=sorted(unique)
    r.shuffle(shuffled)
    cut=len(shuffled)//2
    train_hashes=set(shuffled[:cut])
    test_hashes=set(shuffled[cut:])
    assert not(train_hashes & test_hashes)
    train_qs=[unique[h][1] for h in shuffled[:cut]]
    test_qs=[unique[h][1] for h in shuffled[cut:]]
    train=[tuple(sorted(set(core.TRIP.findall(q)))) for q in train_qs]
    test=[tuple(sorted(set(core.TRIP.findall(q)))) for q in test_qs]
    pred,siz,heavy,split,part,balances,cap,impossible=core.disk_layout(lines)
    assert all(p in siz for q in train+test for p in q)
    assert max(balances)<=cap
    baseline=core.gate(test,part,split)
    methods={}
    for criterion in ("maximize_observed","gain_per_byte"):
        pair,meta,num=core.optimize(train,part,siz,split,balances,cap,criterion)
        moved=part.copy()
        if pair:
            moved[pair[0]],moved[pair[1]]=moved[pair[1]],moved[pair[0]]
        test_scores=core.gate(test,moved,split)
        methods[criterion]={"swap":pair,"training":meta,"n_feasible_choices":num,
          "heldout":test_scores,
          "heldout_saved_extra_shard_touches":
             baseline["extra_shard_touches"]-test_scores["extra_shard_touches"],
          "physical_migration_bytes":sum(siz[p] for p in pair) if pair else 0,
          "post_swap_byte_capacity_feasible": max(
            [balances[k]+sum(siz[p] for p in pair if part[p]!=k and moved[p]==k)
                 -sum(siz[p] for p in pair if part[p]==k and moved[p]!=k)
             for k in range(4)])<=cap if pair else True}
    report={"schema":"candidate3-exact-template-disjoint-correction-v1",
      "source_archive_sha256":core.EXPECTED_SHA,
      "original_40_query_count":len(querystrings),
      "unique_exact_query_texts":len(unique),
      "first20_vs_last20_overlapping_exact_query_hashes":len(set(digests[:20])&set(digests[20:])),
      "exact_query_duplicate_groups":[[i for i,h in enumerate(digests) if h==digest]
                  for digest in sorted(unique) if digests.count(digest)>1],
      "new_seed":SEED,"n_train_unique_templates":len(train_hashes),
      "n_test_unique_templates":len(test_hashes),
      "hash_overlap_new_split":len(train_hashes&test_hashes),
      "byte_capacity_limit":cap,"shard_bytes":balances,
      "test_baseline":baseline,"comparison":methods,
      "limitations":[
        "Previously inspected synthetic source: corrected split is exploratory, NOT independent preregistration",
        "Only 20 unique template questions; cannot support large-scale novelty claims",
        "Full RDF all events accumulated in a single static union, NOT temporal correctness",
        "Heldout shard activations are structural proxy, not real SPARQL execution times",
        "Matched-capacity replication and WISE/WASP not implemented here"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("DISJOINT_GATE_START");print(json.dumps(report,indent=2));print("DISJOINT_GATE_END")
if __name__=="__main__":main()
