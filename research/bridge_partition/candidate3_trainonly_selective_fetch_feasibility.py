#!/usr/bin/env python3
"""Strictly TRAIN-only original SWDF query-structure gate for selective RDF fetch.

No test/calibration query content, answers, query latency or source IP is opened.
This is a source-algebra feasibility probe, NOT an algorithm or timing result.
All source archives immutable SHA-checked. Output aggregate counters only.
"""
import collections
import datetime
import gzip
import hashlib
import json
import re
from pathlib import Path

from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.term import URIRef, Literal, Variable

import candidate3_feasible_raw_swdf_dated_source as raw
import candidate3_feasible_raw_swdf_strict_temporal as strict

OUT=Path("results_candidate3_swdf_trainonly_selective_fetch_feasibility")
OUT.mkdir(exist_ok=True)
SOURCE_SHA="2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df"
TRAIN_DAYS=88


def describe_eligible_query(query):
    """Only counts fixed terms, join shared variables and candidate local pruning."""
    algebra=prepareQuery(query).algebra
    triples=[]
    def walk(node):
        if isinstance(node,CompValue):
            if node.name=="BGP":
                triples.extend(node["triples"])
            for k,v in node.items():
                if k not in ("triples","_vars"):
                    walk(v)
        elif isinstance(node,(list,tuple,set)):
            for v in node:walk(v)
    walk(algebra)
    if not triples:
        raise ValueError("empty algebra triples")
    usage=collections.Counter(t for triple in triples for t in triple
                              if isinstance(t,Variable))
    predicate_labels={str(p) for s,p,o in triples}
    if len(predicate_labels)<2:
        raise ValueError("not multi-predicate")
    fixed_patterns=[(s,p,o) for s,p,o in triples if
                    isinstance(s,(URIRef,Literal)) or
                    isinstance(o,(URIRef,Literal))]
    join_vars={v for v,n in usage.items() if n>=2}
    fixed_join_anchor=sum(any(isinstance(t,Variable) and t in join_vars
                         for t in (s,o)) for s,p,o in fixed_patterns)
    # Conservative potential: any constant triple can be reduced locally;
    # a shared variable on that anchored triple also enables semijoin.
    return {
        "patterns":len(triples),
        "unique_predicates":len(predicate_labels),
        "has_subject_or_object_constant":bool(fixed_patterns),
        "has_constant_object":any(isinstance(o,(URIRef,Literal))
                                  for s,p,o in triples),
        "has_shared_variable":bool(join_vars),
        "has_fixed_pattern_with_shared_variable":fixed_join_anchor>0,
        "has_only_predicate_constants":not fixed_patterns,
    }


def utc_day(m):
    try:
        d=datetime.datetime.strptime(m.group(1),"%d/%b/%Y:%H:%M:%S %z")
        return d.astimezone(datetime.timezone.utc).date().isoformat()
    except ValueError:
        return None


def analyze(sourcepath,allowed_predicates):
    days=set()
    with gzip.open(sourcepath,"rb") as reader:
        for line in reader:
            m=raw.APACHE.search(line.decode("utf8",errors="replace"))
            if m:
                day=utc_day(m)
                if day:days.add(day)
    days=sorted(days)
    if len(days)!=176:
        raise RuntimeError("Expected pinned 176 day inventory")
    train=set(days[:TRAIN_DAYS])
    counts=collections.Counter()
    unique={}
    with gzip.open(sourcepath,"rb") as reader:
        for line in reader:
            m=raw.APACHE.search(line.decode("utf8",errors="replace"))
            if not m or m.group(2).upper()!="GET":
                continue
            if utc_day(m) not in train:
                continue  # Do not parse later query text for feasibility.
            query=raw.parse_query(m.group(3))
            if query is None or not re.search(r"\bSELECT\b",query,re.I):
                continue
            h=hashlib.sha256(query.encode()).hexdigest()
            if h not in unique:
                if len(query)>16000:
                    unique[h]=None
                else:
                    preds,err=strict.select_predicates(query)
                    if err is not None or not set(preds).issubset(allowed_predicates):
                        unique[h]=None
                    else:
                        unique[h]=describe_eligible_query(query)
            features=unique[h]
            if features is not None:
                counts["eligible_original_training_occurrences"]+=1
                for k,value in features.items():
                    if k.startswith("has_") and value:
                        counts["occ_"+k]+=1
    positives=[v for v in unique.values() if v is not None]
    if counts["eligible_original_training_occurrences"] != 4707:
        raise RuntimeError("Frozen source train-eligible count drift; no diagnosis")
    result={
       "schema":"candidate3-trainonly-original-SWDF-selective-fetch-structural-feasibility-v1",
       "original_access_log_SHA256":SOURCE_SHA,
       "calendar_split":"first_88_days_training_only",
       "future_calibration_or_test_query_text_examined":False,
       "future_answer_latency_or_rdf_snapshots_examined":False,
       "eligible_original_training_occurrences":4707,
       "eligible_unique_training_texts":len(positives),
       "train_occurrence_features":dict(counts),
       "train_unique_text_features":{
           k:sum(bool(f[k]) for f in positives)
           for k in ("has_subject_or_object_constant","has_constant_object",
                     "has_shared_variable","has_fixed_pattern_with_shared_variable",
                     "has_only_predicate_constants")},
       "potential_join_pruning_not_proof_real_bytes_or_latency":True,
       "semijoin_pushdown_known_prior_art_not_novel":True,
       "next_generation_requires_an_independent_new_dataset":True,
       "user_private_query_text_or_IP_exported":False,
    }
    return result


def main():
    target=OUT/"SWDF.log.gz"
    result_path=strict.OUT/"SWDF.log.gz"
    import gdown
    import candidate3_swdf_locked_audit as graph
    got=gdown.download(id=raw.SOURCE_ID,output=str(target),quiet=True,fuzzy=True)
    if not got or not target.is_file() or raw.sha_file(target)!=SOURCE_SHA:
        raise RuntimeError("Immutable 2014 raw log missing or SHA mismatch")
    graph_ids,_=strict.read_graph_predicate_ids()
    report=analyze(target,graph_ids)
    (OUT/"report.json").write_text(json.dumps(report,indent=2))
    print("TRAIN_ONLY_SOURCE_SELECTIVE_FETCH_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("TRAIN_ONLY_SOURCE_SELECTIVE_FETCH_END",flush=True)


if __name__=="__main__":
    main()
