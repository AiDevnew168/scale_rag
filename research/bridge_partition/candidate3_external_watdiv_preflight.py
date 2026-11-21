#!/usr/bin/env python3
"""Fresh external WatDiv graph/workload eligibility gate (NO policy tuning).

Official paired source: archived WatDiv 10M triple graph, plus original stress
workload. This must NOT be interpreted as a real organic user log or a claim of
unseen historic Wikidata properties. 80MB compressed graph download cap;
downloaded source hash/contents preserved in report, NOT benchmark test queries.
"""
import bz2, gzip, hashlib, io, json, os, re, tarfile, urllib.request
from pathlib import Path
from collections import Counter
from itertools import islice
ROOT="https://dsg.uwaterloo.ca/watdiv/"
FILES={
 "graph":("watdiv.10M.tar.bz2",85*1024*1024),
 "queries":("stress-workloads.tar.gz",40*1024*1024)}
OUT=Path("results_candidate3_watdiv_external");OUT.mkdir(exist_ok=True)

def download(source,maxlen):
    url=ROOT+source
    req=urllib.request.Request(url,headers={"User-Agent":"ScaleRAG-Candidate3-external-independent-audit/1.0"})
    h=hashlib.sha256();data=bytearray();metadata={}
    with urllib.request.urlopen(req,timeout=80) as response:
        metadata={"http_status":response.status,
                  "content_length_header":response.headers.get("Content-Length"),
                  "content_type":response.headers.get("Content-Type")}
        while True:
            c=response.read(1024*1024)
            if not c:break
            if len(data)+len(c)>maxlen:raise ValueError(f"Download of {source} exceeds {maxlen} bytes cap")
            data.extend(c);h.update(c)
    return bytes(data),{"source":url,"downloaded_bytes":len(data),"sha256":h.hexdigest(),**metadata}

def catalogue(archive,type_name):
    files=[];sample={}
    mode="r:bz2" if type_name=="graph" else "r:gz"
    with tarfile.open(fileobj=io.BytesIO(archive),mode=mode) as tar:
        members=[m for m in tar.getmembers() if m.isfile()]
        for m in members:
            item={"name":m.name,"uncompressed_bytes":m.size}
            files.append(item)
            if type_name=="queries":
                if m.size>2*1024*1024:continue
                data=tar.extractfile(m).read()
                text=data.decode("utf8",errors="replace")
                if any(w in text for w in ("SELECT","PREFIX","WHERE")):
                    sample[m.name]={"sha256":hashlib.sha256(data).hexdigest(),
                        "select_occurrences":len(re.findall(r"\\bSELECT\\b",text,re.I)),
                        "preview_first_1000_chars":text[:1000]}
            else:
                if len(sample)>=3:continue
                with tar.extractfile(m) as f:
                    first=list(islice(f,3))
                sample[m.name]={"head_first_three_lines":[x.decode("utf8",errors="replace")[:700] for x in first]}
    return {"member_count":len(files),"largest_member_bytes":max((x["uncompressed_bytes"] for x in files),default=0),
            "first_30_members":files[:30],"total_uncompressed_bytes":sum(x["uncompressed_bytes"] for x in files),
            "query_file_count_with_select":len(sample) if type_name=="queries" else None,
            "sample_or_query_metadata":dict(list(sample.items())[:20])}

def main():
    result={"schema":"candidate3-external-watdiv-reproducible-preflight-v1",
     "official_source":ROOT,
     "dataset_family":"WatDiv independent RDF dataset with benchmark queries, NOT organic time-stamped query logs",
     "precommit_decision":{
       "holdout_unit":"exact text hash and normalized query-pattern family",
       "n_train":"half distinct query template identities",
       "n_test":"other half; must be exactly disjoint before policy selection",
       "query_parsing":"SPARQL parser or explicit predicate variable handling, NOT regex-only full SPARQL semantics",
       "physical_byte_cap":"<= 110 percent of mean serialized triples per shard with four shards",
       "no_positive_claim_if_no_nonempty_answers_or_no_query_diversity":True},
     "files":{},
     "limitations":[
       "Preflight only. No adaptation, execution speed, query accuracy or net economics measured.",
       "Source is synthetic WatDiv stress testing, not a second organic real-user query dataset.",
       "External archive may be unavailable; no substitute will be silently treated as matching."]}
    for name,(path,cap) in FILES.items():
        try:
            b,meta=download(path,cap)
            meta["archive_contents"]=catalogue(b,name)
            result["files"][name]=meta
        except Exception as exc:
            result["files"][name]={"status":"UNAVAILABLE",
              "error":type(exc).__name__+": "+str(exc)[:450]}
    ok=all("archive_contents" in x for x in result["files"].values())
    result["status"]="both_archives_verified" if ok else "blocked_external_source"
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    print("EXTERNAL_WATDIV_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("EXTERNAL_WATDIV_END",flush=True)
if __name__=="__main__":main()
