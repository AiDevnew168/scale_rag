#!/usr/bin/env python3
"""Conditional transport-bytes invariance for the existing raw-predicate-fetch coordinator.

This is a transparent accounting invariant, not a new distributed query algorithm.
For each predicate, source raw fragments partition the original records; swap
only relocates them; replication duplicates an entire source partition. Routing
must retrieve every original partition once, never two copies of the same
partition. Under those assumptions the total *RDF response body* bytes cannot
depend on placement (but TCP connection overhead and latency can).
"""
from collections import Counter


def verify_one_query(pattern, route, fragment_data, original_parts, groups):
    """Use groups from the real shard router, not a synthetic ranking proxy.

    fragment_data: predicate -> shard -> immutable raw source bytes.
    original_parts: predicate -> tuple of immutable disjoint source fragments.
    Return body bytes and shard contacts, or fail if source coverage differs.
    """
    if not pattern or len(pattern) != len(set(pattern)):
        raise ValueError("Require nonempty unique predicate witness")
    delivered = {p: [] for p in pattern}
    for shard, predicates in groups.items():
        for p in predicates:
            if p not in delivered or p not in fragment_data or shard not in fragment_data[p]:
                raise ValueError("Router requested nonexistent/irrelevant fragment")
            delivered[p].append(fragment_data[p][shard])
    total = 0
    for p in pattern:
        source = Counter(original_parts[p])
        served = Counter(delivered[p])
        if source != served:
            raise ValueError("Predicate source coverage not exact (missing or duplicate replica)")
        total += sum(len(part) for part in delivered[p])
    return {"rdf_response_bytes": total, "contacted_shards": len(groups)}


def compare(pattern, before_route, after_route,
            before_fragments, after_fragments, source_parts,
            actual_router, fragmented):
    """Prove actual router sends exact source partitions in both policies."""
    before = actual_router(pattern, before_route, fragmented)
    after = actual_router(pattern, after_route, fragmented)
    orig = verify_one_query(pattern, before_route, before_fragments, source_parts, before)
    alt = verify_one_query(pattern, after_route, after_fragments, source_parts, after)
    if orig["rdf_response_bytes"] != alt["rdf_response_bytes"]:
        raise AssertionError("Transport invariant violated despite exact fragment coverage")
    return {"before": orig, "after": alt, "rdf_bytes_saved": 0,
            "shard_contacts_saved": orig["contacted_shards"]-alt["contacted_shards"]}


def classify_physical_report(data):
    """Reject false economic success even when a workflow run itself succeeds."""
    if data.get("schema") != "candidate3-original-authentic-176day-four-process-semantic-economic-v1":
        return {"status": "UNKNOWN_REPORT_SCHEMA", "claim_positive_net": False}
    methods = data.get("methods", {})
    statuses = {}
    for name in ("no_move", "one_swap", "two_swap_greedy", "replica_only", "swap_replica"):
        row = methods.get(name, {})
        test = row.get("original_temporal_test", {})
        correct = test.get("n_semantically_correct_paired")
        requested = test.get("n_requested")
        economic = row.get("economic", {})
        if (correct is None or requested is None or correct != requested
                or not row.get("full_query_correctness_gate", False)
                or not economic.get("valid", False)):
            statuses[name] = {"economics": "INVALID",
                              "paired_pass": correct, "requested": requested,
                              "reported_rdf_bytes_saved":
                                  test.get("observed_RDF_payload_bytes_saved_correct_queries"),
                              "reported_contacts_saved":
                                  test.get("observed_contacts_saved_correct_queries")}
        else:
            statuses[name] = {"economics": "EXPLORATORY_ONLY",
                              "paired_pass": correct, "requested": requested,
                              "reported_rdf_bytes_saved":
                                  test.get("observed_RDF_payload_bytes_saved_correct_queries"),
                              "reported_contacts_saved":
                                  test.get("observed_contacts_saved_correct_queries")}
    return {"status": ("INVALID_FOR_ECONOMIC_INFERENCE" if any(
                       r["economics"] == "INVALID" for r in statuses.values())
                       else "EXPLORATORY_NOT_A_DEPLOYED_TRIAL"),
            "methods": statuses, "actual_selected_action": data.get("selected_real_policy"),
            "actual_incremental_gain_vs_static_ms": (0.0 if
                    data.get("selected_real_policy") == "no_move" else None),
            "claim_positive_net": False, "journal_GO": False}
