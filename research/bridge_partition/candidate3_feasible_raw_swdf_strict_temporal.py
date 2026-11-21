#!/usr/bin/env python3
"""PRECOMMITTED original FEASIBLE SWDF dated log strict SPARQL eligibility.

Does NOT execute or optimize any query, even when future query is selected.
Only emits SHA256 and aggregated role counts. Original query text and IP
addresses are never placed in reports, logs or GitHub commits.

Source SHA is immutably pinned from preceding source-only verification run
44906760524; exact day split fixed by PRECOMMIT b70f5a...
"""
import collections,datetime,gzip,hashlib,json,re,urllib.parse,zipfile
from pathlib import Path
import gdown
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.term import URIRef
import candidate3_feasible_raw_swdf_dated_source as raw
import candidate3_swdf_locked_audit as graphlib

OUT=Path("results_candidate3_raw_swdf_strict_temporal")
OUT.mkdir(exist_ok=True)
SOURCE_SHA="2c0f80343a6aba3de2796899a141b2f02049f29bd0d45c3883e826aca00993df"
SOURCE_ID=raw.SOURCE_ID
GRAPH_SHA="65a622f1f1510271ee3a5762756a93cd9f13f2ecbddbb85fe74c2b110a90d6fb"
ALLOW={"SelectQuery","Project","BGP","Slice","Distinct","Reduced","OrderBy","OrderCondition"}

def select_predicates(query):
    try:
        parsed=prepareQuery(query)
        nodes=[];triples=[]
        def walk(x):
            if isinstance(x,CompValue):
                nodes.append(x.name)
                if x.name=="BGP":triples.extend(x["triples"])
                for k,v in x.items():
                    if k not in ("triples","_vars"):walk(v)
            elif isinstance(x,(tuple,list,set)):
                for v in x:walk(v)
        walk(parsed.algebra)
        if not nodes or not set(nodes).issubset(ALLOW):
            return None,"unsupported_algebra"
        if parsed.algebra.get("datasetClause"):
            return None,"named_graph_not_eligible"
        if not 2<=len(triples)<=6:
            return None,"not_2_to_6_patterns"
        if not all(isinstance(p,URIRef) for _,p,_ in triples):
            return None,"dynamic_or_path_predicate"
        predicates=tuple(sorted({str(p) for _,p,_ in triples}))
        if len(predicates)<2:
            return None,"less_than_2_distinct_predicates"
        return predicates,None
    except Exception as e:
        return None,"SPARQL_parse_"+type(e).__name__

def read_graph_predicate_ids():
    z=graphlib.downloaded()
    assert hashlib.sha256(z.read_bytes()).hexdigest()==GRAPH_SHA
    with zipfile.ZipFile(z) as ar:
        assert ar.namelist()==["swdf.nt"]
        lines=ar.read("swdf.nt").splitlines()
    result=set()
    for line in lines:
        if not line.strip():continue
        pieces=line.split(None,2)
        if len(pieces)<3 or not pieces[1].startswith(b"<") or not pieces[1].endswith(b">"):
            raise RuntimeError("Invalid full source RDF triple structure")
        result.add(pieces[1][1:-1].decode("utf-8"))
    return result,len(lines)

def main():
    target=OUT/"SWDF.log.gz"
    downloaded=gdown.download(id=SOURCE_ID,output=str(target),quiet=True,fuzzy=True)
    if not downloaded or not target.is_file():
        raise RuntimeError("Official original 2014 SWDF raw query log cannot be acquired")
    if raw.sha_file(target)!=SOURCE_SHA:
        raise RuntimeError("Original source immutable compressed SHA mismatch")
    graph_ids,graph_triples=read_graph_predicate_ids()
    # Pre-registered source days come from the full audited log; no split by
    # selected successful query results or query complexity.
    all_days=set()
    # First pass parses only timestamps to freeze genuine date boundaries.
    with gzip.open(target,"rb") as f:
        for line in f:
            m=raw.APACHE.search(line.decode("utf8",errors="replace"))
            if not m:continue
            try:
                date=datetime.datetime.strptime(m.group(1),"%d/%b/%Y:%H:%M:%S %z")
                all_days.add(date.astimezone(datetime.timezone.utc).date().isoformat())
            except ValueError:pass
    days=sorted(all_days)
    assert len(days)==176,("unexpected dataset chronology; refuse to reselect",len(days))
    cut1=len(days)*50//100;cut2=len(days)*70//100
    training=set(days[:cut1]);calibration=set(days[cut1:cut2]);holdout=set(days[cut2:])
    date_role={d:("training" if d in training else
          "calibration" if d in calibration else "holdout") for d in days}
    eligible=collections.Counter()
    eligible_days=collections.defaultdict(collections.Counter)
    texts=collections.defaultdict(set)
    families=collections.defaultdict(set)
    exclusions=collections.Counter()
    by_pred_family={}
    cache={}
    strict_unique=0
    line_total=0
    with gzip.open(target,"rb") as f:
        for line in f:
            line_total+=1
            m=raw.APACHE.search(line.decode("utf8",errors="replace"))
            if not m:continue
            try:
                date=datetime.datetime.strptime(m.group(1),"%d/%b/%Y:%H:%M:%S %z")
                day=date.astimezone(datetime.timezone.utc).date().isoformat()
            except ValueError:continue
            role=date_role[day]
            if m.group(2).upper()!="GET":continue
            query=raw.parse_query(m.group(3))
            if query is None:continue
            if not re.search(r"\bSELECT\b",query,re.I):
                exclusions["not_SELECT"]+=1;continue
            sha=hashlib.sha256(query.encode()).digest()
            if sha not in cache:
                if len(query)>16000:
                    cache[sha]=(None,"query_exceeds_16KB_parser_resource_cap")
                else:
                    predicate_names,err=select_predicates(query)
                    if err is None and not set(predicate_names).issubset(graph_ids):
                        predicate_names=None;err="predicate_not_in_original_full_RDF"
                    cache[sha]=(predicate_names,err)
                if cache[sha][1] is None:strict_unique+=1
            predicate_names,err=cache[sha]
            if err is not None:
                exclusions[err]+=1
                continue
            key=hashlib.sha256(json.dumps(predicate_names).encode()).hexdigest()
            eligible[role]+=1
            eligible_days[role][day]+=1
            texts[role].add(sha)
            families[role].add(key)
    past_h=texts["training"]|texts["calibration"]
    prior_families=families["training"]|families["calibration"]
    counts={
       "source_log_sha256":SOURCE_SHA,
       "source_graph_zip_sha256":GRAPH_SHA,
       "graph_full_original_triple_lines":graph_triples,
       "graph_distinct_predicate_types":len(graph_ids),
       "total_original_access_log_lines":line_total,
       "date_split_UTC":{"training_start":days[0],"training_end":days[cut1-1],
         "calibration_start":days[cut1],"calibration_end":days[cut2-1],
         "holdout_start":days[cut2],"holdout_end":days[-1],
         "days_by_role":{"training":cut1,"calibration":cut2-cut1,
                         "holdout":len(days)-cut2}},
       "original_STRICT_eligible_occurrences_by_role":dict(eligible),
       "strict_unique_parsed_SELECT_query_texts_overall":strict_unique,
       "strict_unique_texts_by_role":{role:len(texts[role]) for role in date_role.values()},
       "distinct_predicate_families_by_role":{role:len(families[role]) for role in set(date_role.values())},
       "heldout_new_exact_texts_vs_past":len(texts["holdout"]-past_h),
       "heldout_exact_text_overlap_vs_past":len(texts["holdout"]&past_h),
       "heldout_new_predicate_families_vs_past":len(families["holdout"]-prior_families),
       "heldout_overlap_predicate_families_vs_past":len(families["holdout"]&prior_families),
       "dates_with_strict_eligible_queries_by_role":{role:len(eligible_days[role])
            for role in set(date_role.values())},
       "strict_SPQL_parser_failures_across_occurrences":dict(exclusions)}
    condition=(len(days)>=14 and sum(eligible.values())>=200 and
               strict_unique>=30 and len(texts["holdout"])>=20 and
               len(families["holdout"])>=5)
    # Need separately demonstrated true 2014 snapshot to call the economic
    # gate confirmatory, not a post-2014 matched dump guessed from labels.
    report={"schema":"candidate3-original-FEASIBLE-2014-SWDF-algebra-eligibility-v1",
       "frozen_protocol_commit":"b70f5a1da34f263e7a31dbbff9923aa0d684cd47",
       "source_provenance_gate":"PASS_PINNED_FULL_ORIGINAL_LOG",
       "semantic_algebra_eligibility_gate":"PASS" if condition else "BLOCKED",
       "real_calendar_day_temporal_partition":"PASS",
       "snapshot_2014_event_time_RDF_graph_version_aligned":"NOT_VERIFIED",
       "original_query_full_answer_checks":"NOT_PERFORMED_IN_SOURCE_AUDIT",
       "train_or_calibration_has_seen_holdout_answers":False,
       "eligible_for_frozen_physical_exploratory_test":condition,
       "eligible_for_confirmatory_paper_profit_claim":False,
       "data":counts,
       "limitations":[
          "Original public SWDF 2014 log may overlap formerly used FEASIBLE cleaned queries; not fully unseen domain",
          "Original complete SWDF RDF graph has no independently verified as-of-2014 temporal snapshot identity",
          "Pretest stage reports aggregate FUTURE query counts and duplicate overlaps only; no future outcomes or SPARQL engine timings inspected",
          "Query text and client IPs are never logged or persisted in the published report",
          "Even if eligible for physical engineering, full semantic answer correctness and measured economic net remain separate mandatory gates"]}
    OUT.joinpath("report.json").write_text(json.dumps(report,indent=2))
    short={k:v for k,v in report.items() if k!="data"}
    short["data"]={k:v for k,v in counts.items()
        if k not in ("strict_SPQL_parser_failures_across_occurrences",)}
    short["top_algebra_exclusion_reasons"]=(collections.Counter(exclusions)).most_common(15)
    print("REAL_DATED_SWDF_ALGEBRA_GATE_START",flush=True)
    print(json.dumps(short,indent=2),flush=True)
    print("REAL_DATED_SWDF_ALGEBRA_GATE_END",flush=True)
if __name__=="__main__":main()
