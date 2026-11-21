#!/usr/bin/env python3
"""Source-only authentic historical SWDF HTTP access-log eligibility audit.

This is the independent raw-log *access and timestamps* phase. No algorithm
selection, no RDF answer execution, no per-query text/user IP serialization.
RDF/SPARQL algebra eligibility is a separate preregistered follow-up phase.
"""
import collections,datetime,gzip,hashlib,json,re,urllib.parse
from pathlib import Path
import gdown

ROOT=Path("results_candidate3_raw_swdf_provenance")
ROOT.mkdir(exist_ok=True)
SOURCE_ID="0B1tUDhWNTjO-T3BweE9YeE1rUGM"
URL="https://drive.google.com/file/d/"+SOURCE_ID+"/view"
MAX_ZIP=160_000_000
MAX_RAW=800_000_000
MAX_LINES=6_000_000
APACHE=re.compile(r'\[([^]]+)\]\s+"(GET|POST)\s+(.+?)\s+HTTP/[0-9.]+',re.I)
DTS=("%d/%b/%Y:%H:%M:%S %z","%d/%b/%Y:%H:%M:%S")
def sha_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(1024*1024),b""):h.update(buf)
    return h.hexdigest()
def parse_query(request_url):
    u=urllib.parse.urlsplit(request_url)
    if "sparql" not in u.path.lower():return None
    fields=urllib.parse.parse_qs(u.query,keep_blank_values=True)
    queries=fields.get("query",[])
    if len(queries)!=1:return None
    return queries[0]
def audit(path):
    by_day=collections.Counter();candidate_by_day=collections.Counter()
    date_errors=collections.Counter();query_tags=collections.Counter()
    unique_sha=set();total=0;parsed_time=0;candidate=0;strict_signal=0;rawbytes=0
    earliest=None;latest=None;unparsed_examples=collections.Counter()
    with gzip.open(path,"rb") as reader:
        for raw in reader:
            total+=1;rawbytes+=len(raw)
            if total>MAX_LINES or rawbytes>MAX_RAW:
                raise RuntimeError("SOURCE_LIMIT_REACHED: stop source audit, no partial success")
            line=raw.decode("utf-8",errors="replace")
            m=APACHE.search(line)
            if not m:
                date_errors["unrecognized_request_line"]+=1
                continue
            try:
                dt=None
                for fmt in DTS:
                    try:dt=datetime.datetime.strptime(m.group(1),fmt);break
                    except ValueError:pass
                if dt is None:raise ValueError("unknown Apache date")
                day=(dt.astimezone(datetime.timezone.utc) if dt.tzinfo else dt).date().isoformat()
            except (ValueError,TypeError):
                date_errors["time_unparseable"]+=1;continue
            parsed_time+=1;by_day[day]+=1
            tm=dt.isoformat()
            if earliest is None or tm<earliest:earliest=tm
            if latest is None or tm>latest:latest=tm
            if m.group(2).upper()!="GET":
                query_tags["non_GET"]+=1;continue
            q=parse_query(m.group(3))
            if q is None:
                query_tags["no_exactly_one_query_parameter"]+=1
                continue
            candidate+=1;candidate_by_day[day]+=1
            digest=hashlib.sha256(q.encode("utf8")).digest()
            unique_sha.add(digest)
            text=q.upper()
            if re.search(r"\bSELECT\b",text):
                query_tags["SELECT_lexical_signal"]+=1
                if re.search(r"\bWHERE\b",text):
                    strict_signal+=1
            elif re.search(r"\bASK\b",text):query_tags["ASK_lexical_signal"]+=1
            elif re.search(r"\bCONSTRUCT\b",text):query_tags["CONSTRUCT_lexical_signal"]+=1
            elif re.search(r"\bDESCRIBE\b",text):query_tags["DESCRIBE_lexical_signal"]+=1
            else:query_tags["query_type_not_classified"]+=1
    return {"decompressed_bytes":rawbytes,
      "n_http_log_lines":total,"n_http_requests_with_real_parseable_timestamps":parsed_time,
      "n_full_calendar_UTC_days":len(by_day),
      "earliest_datetime_lexical":earliest,"latest_datetime_lexical":latest,
      "observed_HTTP_request_counts_per_UTC_day":dict(sorted(by_day.items())),
      "observed_query_request_counts_per_UTC_day":dict(sorted(candidate_by_day.items())),
      "n_original_query_requests_with_timestamp":candidate,
      "n_exact_SHA256_unique_original_query_texts":len(unique_sha),
      "n_select_and_where_lexical_signals_not_SPARQL_parsed":strict_signal,
      "query_type_signals_not_SPARQL_parsed":dict(query_tags),
      "excluded_log_lines":dict(date_errors),
      "exact_semantic_SPARQL_eligibility":"PENDING_FIXED_ALGEBRA_PARSER_NEXT_STAGE",
      "text_or_IP_exfiltrated_to_artifact":False}
def main():
    target=ROOT/"SWDF.log.gz"
    report={"schema":"candidate3-raw-FEASIBLE-SWDF-dated-log-source-eligibility-v1",
        "frozen_protocol_commit":"b70f5a1da34f263e7a31dbbff9923aa0d684cd47",
        "author_source_original":URL,
        "source_id":SOURCE_ID,"status":"BLOCKED",
        "known_limitations":[
          "Source from original FEASIBLE project overlaps source domain of previously opened cleaned queries: NOT a fully independent corpus.",
          "Only format and UTC day counts checked here; no full SPARQL algebra or RDF snapshot alignment examined.",
          "Do not claim timestamped study until >=14 true UTC days and valid original SELECT structural gates pass.",
          "No query contents, client IP addresses, or complete raw log placed in reports or stdout.",
          "No workload decision, net economic measurement, or future query outcomes used in source probe."]}
    try:
        output=gdown.download(id=SOURCE_ID,output=str(target),quiet=True,fuzzy=True)
        if not output or not target.is_file():
            raise RuntimeError("Original Google Drive gzip unavailable")
        size=target.stat().st_size
        if size>MAX_ZIP:raise RuntimeError("Original compressed source too large for bounded runner")
        with target.open("rb") as f:
            assert f.read(2)==b"\x1f\x8b","Original artifact not gzip"
        report.update({"source_zip_sha256":sha_file(target),
          "source_compressed_bytes":size,
          "eligibility":audit(target)})
        e=report["eligibility"]
        if e["n_full_calendar_UTC_days"]<14:
            report["status"]="BLOCKED_INSUFFICIENT_TRUE_CALENDAR_DAYS"
        elif e["n_original_query_requests_with_timestamp"]<200:
            report["status"]="BLOCKED_INSUFFICIENT_TIMESTAMPED_QUERIES"
        else:
            report["status"]="DATE_AND_RAW_QUERY_SOURCE_ELIGIBLE_NEEDS_ALGEBRA_AND_GRAPH_AUDIT"
    except Exception as exc:
        report["status"]="BLOCKED_SOURCE_FAILURE"
        report["failure"]=type(exc).__name__+": "+str(exc)[:500]
    (ROOT/"report.json").write_text(json.dumps(report,indent=2))
    print("ORIGINAL_RAW_SWDF_DATED_SOURCE_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("ORIGINAL_RAW_SWDF_DATED_SOURCE_END",flush=True)
if __name__=="__main__":main()
