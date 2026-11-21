#!/usr/bin/env python3
"""Cost-envelope admission on LOCKED original WatDiv10M 5-fold output.

Consumes exact immutable upstream Github Actions run 44869561656 artifact;
does NOT re-access or train on test features. Admission selects no move, max
observed touch gain, or gain/byte using ONLY observed training touch gains,
fixed target horizon H=2400 query arrivals, and externally supplied per-touch
critical-path milliseconds / ideal network bandwidth.
All post-hoc scenario profiles are explicitly exploratory, NOT measured
production latency, not preregistration before seeing the original fold data.
"""
import json, random
from pathlib import Path
ROOT=Path("bundle")
OUT=Path("results_candidate3_byte_economics_envelope")
OUT.mkdir(exist_ok=True)
SOURCE_RUN=44869561656
SOURCE_ARTIFACT_ID=14693710835
EXPECTED_GRAPH="1d0a8a4725c98974eb7347ce3e6d9cab44f9f40389589809674254151b745af6"
HORIZON=2400
PROFILES=[(ms,mbps) for ms in (0,0.1,0.5,1,5,20) for mbps in (100,1000)]
METHODS=("head_local","gain_per_byte")

def transfer_ms(b,mbps):
    return b*8/(mbps*1000)

def main():
    files=list(ROOT.rglob("report.json"))
    assert len(files)==1,files
    data=json.loads(files[0].read_text())
    assert data["schema"]=="candidate3-original-WatDiv10M-fivefold-exact-pattern-disjoint-v1"
    assert data["source"]["graph_sha256"]==EXPECTED_GRAPH
    assert len(data["folds"])==5 and data["n_pattern_families"]==121
    assert all(f["overlap_exact_query_text_hash"]==0 and f["overlap_pattern_family"]==0 for f in data["folds"])
    result={"schema":"candidate3-WatDiv10M-observed-only-economic-admission-envelope-v1",
      "source_evidence":{"github_actions_run":SOURCE_RUN,
           "artifact_id":SOURCE_ARTIFACT_ID,"graph_sha":EXPECTED_GRAPH},
      "predeclared_fixed_target_horizon_queries":HORIZON,
      "profiles":{},
      "method":"Training-only normalized touch-gain * fixed request horizon * assumed per-touch critical path minus raw NTriples transfer time; choose max predicted net positive, else no migration.",
      "baseline":"no migration (zero net) and two equal byte-feasible candidate swaps",
      "interpretation":"IDEALIZED conditional scenarios, NOT measured distributed costs, not a new algorithm",
      "limitations":[
        "Profiles constructed after prior fivefold results were observed; exploratory economic sensitivity, not independent confirmation.",
        "No complete SPARQL runtime here; per-touch cost parameter is an ASSUMPTION, not measured serial or parallel critical path.",
        "Raw NTriples byte transfers only; excludes source+dest index changes, durable writes, caches, failure recovery, routing barrier, and storage operations.",
        "Five hypothetical separate training/test folds incur FIVE independent migration costs; not a single chronological service trajectory.",
        "Original 121 pattern families are synthetic, not independent real-user shifts; bootstrap conditional on this one corpus.",
        "Forecast horizon 2400 fixed ex ante in code; no test labels enter policy; train fold volumes only.",
        "No prior-art WISE/WASP/equal-memory replication controller is implemented; cost admission rule is standard not novel."]}
    for touch_ms,bandwidth_mbps in PROFILES:
        key=f"serial_saved_ms_per_touch_{touch_ms:g}__bandwidth_{bandwidth_mbps}Mbps"
        rows=[];per_family={}
        comparisons={"head_local":0.0,"gain_per_byte":0.0,"no_move":0.0}
        selected_migration=0
        selected_gains=0
        for fold in data["folds"]:
            rankings=[(0.0,"no_move")]
            for method in METHODS:
                item=fold["results"][method]
                predicted_saved=HORIZON*(item["observed_train_touches_saved"]/fold["n_train"])
                predicted_gain=touch_ms*predicted_saved-transfer_ms(
                    item["physical_predicate_payload_move_bytes"],bandwidth_mbps)
                rankings.append((predicted_gain,method))
                comparisons[method]+=touch_ms*item["heldout_extra_shard_touches_saved"]-transfer_ms(
                    item["physical_predicate_payload_move_bytes"],bandwidth_mbps)
            estimate,chosen=max(rankings,key=lambda x:(x[0],x[1]=="no_move"))
            assert estimate>=0
            if chosen=="no_move":
                moved_bytes=0;saved=0;raw_by_family={}
            else:
                item=fold["results"][chosen]
                moved_bytes=item["physical_predicate_payload_move_bytes"]
                saved=item["heldout_extra_shard_touches_saved"]
                raw_by_family=item["pattern_cluster_saved_touches"]
            for family in fold["results"]["head_local"]["pattern_cluster_saved_touches"]:
                assert family not in per_family, "All distinct families must be tested once"
                per_family[family]=raw_by_family.get(family,0)
            selected_migration+=moved_bytes;selected_gains+=saved
            rows.append({"fold":fold["fold"],"choice":chosen,
                "forecast_predicted_net_ms":round(estimate,4),
                "actual_heldout_extra_touches_saved":saved,
                "moved_serialized_bytes":moved_bytes,
                "ideal_net_ms_in_fold":round(touch_ms*saved-transfer_ms(moved_bytes,bandwidth_mbps),4)})
        assert len(per_family)==121
        total_net=touch_ms*selected_gains-transfer_ms(selected_migration,bandwidth_mbps)
        r=random.Random(20261121)
        vals=list(per_family.values())
        simulated=sorted(touch_ms*sum(vals[r.randrange(len(vals))] for __ in vals)
              -transfer_ms(selected_migration,bandwidth_mbps) for _ in range(4000))
        winner={"choices":rows,
            "moved_bytes_five_hypothetical_folds":selected_migration,
            "saved_extra_touches_five_hypothetical_folds":selected_gains,
            "net_ms_under_profile":round(total_net,4),
            "pattern_cluster_bootstrap_CI95_net_ms":[round(simulated[99],4),round(simulated[3899],4)]}
        out={"scenario_parameters":{"assumed_saved_critical_path_ms_per_extra_touch":touch_ms,
                    "assumed_transport_mbps":bandwidth_mbps,
                    "network_rtt_and_index_costs":"not included"},
              "observed_only_admission":winner,
              "always_migrate_controls_net_ms":{m:round(v,4) for m,v in comparisons.items()}}
        result["profiles"][key]=out
    OUT.joinpath("report.json").write_text(json.dumps(result,indent=2))
    compact={"schema":result["schema"],"source_evidence":result["source_evidence"],
      "assumptions":result["method"],
      "profiles":{k:{"selected":v["observed_only_admission"],
                "always_migrate_controls_net_ms":v["always_migrate_controls_net_ms"]}
                for k,v in result["profiles"].items() if
                   "per_touch_1__" in k or "per_touch_5__" in k or "per_touch_20__" in k}}
    print("ECONOMIC_ENVELOPE_START",flush=True)
    print(json.dumps(compact,indent=2),flush=True)
    print("ECONOMIC_ENVELOPE_END",flush=True)
if __name__=="__main__":main()
