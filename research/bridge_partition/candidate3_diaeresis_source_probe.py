#!/usr/bin/env python3
"""Original author DIAERESIS SWDF source ZIP probe; no answer inspection."""
import hashlib,json,urllib.request,zipfile,io
from pathlib import Path
SRC="https://users.ics.forth.gr/~kondylak/SWJ/swdf.zip"
OUT=Path("results_candidate3_diaeresis_original_source")
OUT.mkdir(exist_ok=True)
def main():
    d={"schema":"candidate3-original-DIAERESIS-SWDF-source-preflight-v1",
      "upstream_commit":"22dfe190078973f644f5d6279181e54ec116f6e3",
      "author_source":SRC,"benchmark_source":"https://github.com/isl/DIAERESIS",
      "state":"BLOCKED","not_full_algorithm_run":True}
    try:
        req=urllib.request.Request(SRC,headers={"User-Agent":"ScaleRAG-DIAERESIS-reproduction/1.0"})
        with urllib.request.urlopen(req,timeout=55) as resp:
            body=resp.read(90_000_001)
        assert len(body)<=90_000_000
        d["download_bytes"]=len(body)
        d["source_zip_sha256"]=hashlib.sha256(body).hexdigest()
        with zipfile.ZipFile(io.BytesIO(body)) as zipf:
            d["members"]=[{"filename":m.filename,"compressed":m.compress_size,
              "uncompressed":m.file_size} for m in zipf.infolist()]
        d["state"]="AUTHOR_SOURCE_ARCHIVE_AVAILABLE"
    except Exception as exc:
        d["failure"]=type(exc).__name__+": "+str(exc)[:350]
    (OUT/"report.json").write_text(json.dumps(d,indent=2))
    print("DIAERESIS_SOURCE_PREFLIGHT_START");print(json.dumps(d,indent=2))
    print("DIAERESIS_SOURCE_PREFLIGHT_END")
if __name__=="__main__":main()
