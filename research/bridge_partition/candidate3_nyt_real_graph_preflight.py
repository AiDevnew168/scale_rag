#!/usr/bin/env python3
"""Complete independent NYT linked RDF source and predeclared query-family probe.

Real graph, synthetic BGP queries derived from source schema. Does NOT run a
single SPARQL query or optimize any policy. Exactly archives every triple.
"""
import collections,hashlib,itertools,json
from pathlib import Path
from remotezip import RemoteZip

ZIP_URL="https://zenodo.org/api/records/22140177/files/rdf_datasets.zip/content"
EXPECTED_ZIP_MEMBER_BYTES=51_498_878
SEED=20261121
OUT=Path("results_candidate3_NYT_real_graph_source")
OUT.mkdir(exist_ok=True)

def get_full_raw():
    with RemoteZip(ZIP_URL,timeout=100) as z:
        info=z.getinfo("NYT.nt")
        assert info.file_size==EXPECTED_ZIP_MEMBER_BYTES
        raw=z.read("NYT.nt")
    assert len(raw)==EXPECTED_ZIP_MEMBER_BYTES
    return raw

def families(raw):
    by_subject=collections.defaultdict(set)
    frequencies=collections.Counter()
    bad=0;n=0
    for line in raw.splitlines():
        if not line.strip():continue
        parts=line.split(None,2)
        if len(parts)!=3 or not parts[1].startswith(b"<") or not parts[1].endswith(b">"):
            bad+=1;continue
        s,p=parts[0].decode("utf8"),parts[1].decode("utf8")
        by_subject[s].add(p);frequencies[p]+=1;n+=1
    assert bad==0,(bad,n)
    support=collections.Counter()
    for predicates in by_subject.values():
        arranged=sorted(predicates)[:20]
        for size in (2,3):
            support.update(itertools.combinations(arranged,size))
    groups=sorted(((p,count) for p,count in support.items() if count>=1),
          key=lambda v:(-v[1],v[0]))
    return by_subject,frequencies,groups,n

def main():
    raw=get_full_raw()
    subs,fr,group,n=families(raw)
    sha=hashlib.sha256(raw).hexdigest()
    report={"schema":"candidate3-NYT-new-complete-real-RDF-source-query-family-preflight-v1",
      "source_original_zip_url":ZIP_URL,"full_member":"NYT.nt",
      "source_complete_original_NTriples_sha256":sha,
      "source_bytes":len(raw),
      "triples_parsed_all":n,"distinct_subjects":len(subs),
      "distinct_predicates":len(fr),
      "distinct_pair_or_triple_predicate_families":len(group),
      "top_125_support_counts":[s for _,s in group[:125]],
      "full_query_family_available":len(group)>=100,
      "query_selection_locked_top125_min100":True,
      "test_query_results_unopened":True,
      "origin_of_new_query_workload":"SYNTHETIC_FROM_REAL_GRAPH_NOT_REAL_USER_LOG",
      "source_gate":"ELIGIBLE_FOR_ENGINEERING_CORRECTNESS" if len(group)>=100 else
                     "BLOCKED_NOT_ENOUGH_DISTINCT_FAMILIES",
      "not_a_paper_real_log_economic_proof":True}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    print("NYT_REAL_SOURCE_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("NYT_REAL_SOURCE_END",flush=True)
if __name__=="__main__":main()
