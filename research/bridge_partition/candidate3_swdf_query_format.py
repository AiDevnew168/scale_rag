#!/usr/bin/env python3
"""First 4 KiB ONLY of external SWDF real-log format for parser construction.

Does not expose or evaluate full future workload.
"""
import hashlib,json,urllib.request
from pathlib import Path
OUT=Path("results_candidate3_SWDF_query_format");OUT.mkdir(exist_ok=True)
SOURCE="https://raw.githubusercontent.com/dice-group/feasible/master/SWDF-CleanQueries.txt"
req=urllib.request.Request(SOURCE,headers={"Range":"bytes=0-4095","User-Agent":"Candidate3-SPARQL-source-format-only/1.0"})
with urllib.request.urlopen(req,timeout=45) as response:
    raw=response.read(4097)
    status=response.status
    cr=response.headers.get("Content-Range")
assert status==206 and len(raw)==4096,("Reject unbounded response",status,cr,len(raw))
sample=raw.decode("utf8",errors="replace")
lines=sample.splitlines()
result={"schema":"candidate3-SWDF-unopened-query-prefix-format-v1",
    "source":SOURCE,"prefix_source_4096_sha256":hashlib.sha256(raw).hexdigest(),
    "http_status":status,"content_range":cr,
    "n_whole_lines_in_first4kb":max(len(lines)-1,0),
    "line_preview_first_500":lines[0][:500] if lines else "",
    "line_2_preview_first_500":lines[1][:500] if len(lines)>1 else "",
    "do_not_use_first_lines_as_independent_holdout":True,
    "rest_of_query_file_unread":True}
OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
print("SWDF_QUERY_FORMAT_START");print(json.dumps(result,indent=2));print("SWDF_QUERY_FORMAT_END")
