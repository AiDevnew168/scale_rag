#!/usr/bin/env python3
"""Fast no-test-label-disclosure correctness smoke on SWDF calibration only."""
import json, hashlib
from pathlib import Path
from pyoxigraph import Store,RdfFormat
import candidate3_swdf_real_full_sparql_economics as main
import candidate3_paired_full_sparql as paired
import candidate3_real_sparql_shards as engine
OUT=Path("results_candidate3_SWDF_calibration_smoke");OUT.mkdir(exist_ok=True)
def run():
    graph,by_pred,size,roles,packs,loads,route,cap=main.prepare_source()
    calibration=roles["calibration"][:8]
    central=Store()
    central.bulk_load(input=graph,format=RdfFormat.N_TRIPLES)
    ports,workers=paired.start_group(packs)
    frag={p for p in route if len(route[p])>1}
    entries=[]
    try:
        for r in calibration:
            row={"query_hash":r["text_hash"],"pattern":r["pattern"]}
            try:
                expected=engine.evaluate(central,r["query"])
                actual=main.query_four_workers(r["query"],r["pattern"],route,ports,frag)
                row.update({"central":expected,"distributed":actual["answer"],
                  "match":expected==actual["answer"],
                  "network_bytes":actual["network_bytes"],
                  "shard_contacts":actual["shard_contacts"]})
            except Exception as e:
                row["error"]=type(e).__name__+": "+str(e)[:350]
            entries.append(row)
    finally:paired.shutdown(workers)
    r={"schema":"candidate3-calibration-only-4-live-SWDF-shard-SPARQL-smoke-v1",
      "n_calibration":len(entries),
      "n_correct":sum(x.get("match",False) for x in entries),
      "n_error":sum("error" in x for x in entries),
      "heldout_query_texts_evaluated":0,
      "source_utf8_normalization":json.loads((main.OUT/"source_utf8_transcode_audit.json").read_text()),
      "entries":entries}
    OUT.joinpath("report.json").write_text(json.dumps(r,indent=2))
    print("SWDF_CALIB_SMOKE_START",flush=True);print(json.dumps(r,indent=2),flush=True)
    print("SWDF_CALIB_SMOKE_END",flush=True)
if __name__=="__main__":run()
