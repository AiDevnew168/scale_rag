#!/usr/bin/env python3
"""Get bytes of provider's original SWDF dump, or mark unavailable.

No query log contents are fetched. Maximum 200MiB. No false source success
when a Google Drive HTML error/login page is returned. SHA256 and archive
format listing audited. File remains job-scoped and only JSON metadata uploaded.
"""
import hashlib,json,os,tarfile,zipfile,gzip,io
from pathlib import Path
import gdown
ID="0B1tUDhWNTjO-cjBqUG1BZF9RTnM"
OUT=Path("results_candidate3_SWDF_original_dump");OUT.mkdir(exist_ok=True)
LIMIT=200*1024*1024
def main():
    path=OUT/"source.bin"
    r={"schema":"candidate3-original-FEASIBLE-SWDF-graph-byte-access-v1",
       "source_url":"https://drive.google.com/file/d/"+ID+"/view",
       "source_type":"Original DICE FEASIBLE SWDF RDF dump, version must still be checked",
       "query_workload_unopened":True}
    try:
        returned=gdown.download(id=ID,output=str(path),quiet=True,fuzzy=True)
        if returned is None or not path.exists():raise RuntimeError("Google Drive source inaccessible")
        length=path.stat().st_size
        if length>LIMIT:raise RuntimeError("Source exceeds 200MiB safety cap")
        b=path.read_bytes()
        if b.lstrip()[:40].lower().startswith((b"<html",b"<!doctype",b"<head")):
            raise RuntimeError("Google Drive returned an HTML page, not RDF bytes")
        r["download"]={"size_bytes":length,"sha256":hashlib.sha256(b).hexdigest(),
            "first16_bytes_hex":b[:16].hex()}
        if zipfile.is_zipfile(io.BytesIO(b)):
            with zipfile.ZipFile(io.BytesIO(b)) as z:
                members=[{"name":i.filename,"uncompressed_bytes":i.file_size,
                          "compressed_bytes":i.compress_size} for i in z.infolist()]
                r["archive"]={"kind":"zip","members":members[:40]}
        elif tarfile.is_tarfile(path):
            with tarfile.open(path) as z:
                r["archive"]={"kind":"tar","members":[{"name":x.name,"size":x.size} for x in z.getmembers()[:40]]}
        elif b[:2]==b"\x1f\x8b":
            with gzip.open(path,"rb") as f:head=f.read(500)
            r["archive"]={"kind":"gzip","decompressed_first200":head[:200].decode(errors="replace")}
        else:
            r["archive"]={"kind":"raw","first300":b[:300].decode(errors="replace")}
        r["status"]="source_bytes_acquired_graph_alignment_unverified"
    except Exception as e:
        r["status"]="blocked";r["error"]=type(e).__name__+": "+str(e)[:500]
    finally:
        if path.exists():path.unlink()
    (OUT/"report.json").write_text(json.dumps(r,indent=2))
    print("ORIGINAL_SWDF_GRAPH_START");print(json.dumps(r,indent=2));print("ORIGINAL_SWDF_GRAPH_END")
if __name__=="__main__":main()
