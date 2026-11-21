#!/usr/bin/env python3
"""Fresh SWDF external REAL RDF graph + genuine LSQ query-log preflight.

This preflight runs AFTER the frozen preregistered source protocol commit
50c8582c... and must fail CLOSED for missing full graph. Does not run models.
"""
import hashlib,html,json,re,urllib.request,urllib.parse,urllib.error
from pathlib import Path
from collections import Counter
ROOT=Path("results_candidate3_fresh_swdf")
ROOT.mkdir(exist_ok=True)
LOG="https://raw.githubusercontent.com/AKSW/LSQ/develop/lsq-core/src/test/resources/logs/combined.swdf.log"
PAGES=[
 "https://hobbitdata.informatik.uni-leipzig.de/benchmarks-data/datasets-dumps/",
 "https://www.rdfhdt.org/datasets/",
 "https://raw.githubusercontent.com/dice-group/feasible/master/README.md",
]
AGENT={"User-Agent":"ScaleRAG-SWDF-frozen-independent-preflight/1.0","Accept":"*/*"}
def retrieve(url,max_bytes=5_000_000):
    req=urllib.request.Request(url,headers=AGENT)
    with urllib.request.urlopen(req,timeout=25) as res:
        typ=res.headers.get("Content-Type","")
        b=res.read(max_bytes+1)
        assert len(b)<=max_bytes,"file too large for preflight"
    return b,typ
def describe_lines(raw):
    txt=raw.decode("utf8",errors="replace")
    lines=[line for line in txt.splitlines() if line.strip()]
    tokens=Counter()
    for line in lines[:1000]:
        for word in ("SELECT","ASK","CONSTRUCT","PREFIX","timestamp","swdf","\t"):
            if word.lower() in line.lower():tokens[word]+=1
    return {"lines":len(lines),"first3_redacted_to_450":[x[:450] for x in lines[:3]],
      "sample_query_and_metadata_indicators":dict(tokens),"byte_sha256":hashlib.sha256(raw).hexdigest(),
      "length_bytes":len(raw)}
def main():
    result={"schema":"candidate3-frozen-external-swdf-source-preflight-v1",
      "frozen_protocol_commit":"50c8582c2ea7da54f32cc0f5ad2d0f954c3d178d",
      "log_source":{"url":LOG},"source_listings":[],
      "status":"BLOCKED_UNTIL_FULL_GRAPH_AND_QUERY_MATCH",
      "not_a_complete_distributed_benchmark":True}
    try:
        raw,typ=retrieve(LOG,2_000_000)
        result["log_source"].update(describe_lines(raw))
        result["log_source"]["content_type"]=typ
        (ROOT/"lsq_swdf_log.source").write_bytes(raw)
    except Exception as e:
        result["log_source"]["error"]=type(e).__name__+": "+str(e)[:400]
    for page in PAGES:
        item={"source":page}
        try:
            b,typ=retrieve(page,3_000_000)
            text=b.decode("utf8",errors="replace")
            item.update({"http_body_sha256":hashlib.sha256(b).hexdigest(),
                 "bytes":len(b),"content_type":typ})
            refs=re.findall(r"""(?:href|src)=["']([^"']+)""",text,re.I)
            matches=[urllib.parse.urljoin(page,html.unescape(v))
                       for v in refs if re.search(r"swdf|dog.?food|semantic.web|\.nt|\.hdt",v,re.I)]
            if "rdfhdt.org" in page:
                pos=text.lower().find("semantic web dog food")
                item["SWDF_HTML_CONTEXT"]=text[max(0,pos-500):pos+1100] if pos>=0 else None
            item["candidate_links"]=matches[:30]
        except Exception as e:
            item["error"]=type(e).__name__+": "+str(e)[:400]
        result["source_listings"].append(item)
    (ROOT/"report.json").write_text(json.dumps(result,indent=2))
    print("FRESH_SWDF_PREFLIGHT_START",flush=True)
    print(json.dumps(result,indent=2),flush=True)
    print("FRESH_SWDF_PREFLIGHT_END",flush=True)
if __name__=="__main__":main()
