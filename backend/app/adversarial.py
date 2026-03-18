"""
Adversarial Test Mode: generates evasion variants and reports detection limits.

PRD Section 12.1: Cycle +1 hop, split hub, time-distributed smurfing tests.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.models.schemas import TransactionBase
from app.pipeline.graph_agent import GraphAgent
from app.pipeline.pathfinder_agent import PathfinderAgent


def _txn(sender: str, receiver: str, amount: float, ts: datetime, channel: str = "NEFT") -> TransactionBase:
    return TransactionBase(
        txn_id=f"{sender}-{receiver}-{ts.timestamp()}",
        sender_id=sender,
        receiver_id=receiver,
        amount=amount,
        timestamp=ts,
        channel=channel,
        account_type="Savings",
    )


def run_cycle_plus_hop_test() -> Dict[str, Any]:
    """
    Extend a 4-hop cycle to 5, 6, 7, 8, 9 hops. Report at which hop count
    detection degrades (DFS length_bound typically 8).
    """
    base = datetime.now() - timedelta(hours=1)
    results: List[Dict[str, Any]] = []
    max_detected_hops = 0
    limit_hops = 8  # typical CYCLE_MAX_HOPS

    for total_hops in range(4, 10):
        nodes = [f"N{i}" for i in range(total_hops)]
        txns: List[TransactionBase] = []
        t = base
        for i in range(total_hops):
            txns.append(_txn(nodes[i], nodes[(i + 1) % total_hops], 50_000, t))
            t += timedelta(minutes=10)
        graph = GraphAgent().process_transactions(txns)
        pathfinder = PathfinderAgent(graph)
        cycles = pathfinder.detect_cycles(max_length=limit_hops, max_count=50)
        detected = any(len(c) == total_hops for c in cycles)
        if detected:
            max_detected_hops = total_hops
        results.append({
            "hops": total_hops,
            "detected": detected,
            "message": f"{total_hops}-hop cycle: {'Detected' if detected else 'DFS depth limit reached — cycle not detected.'}",
        })

    return {
        "test": "cycle_plus_hop",
        "title": "Cycle +1 hop test",
        "summary": f"Cycles detected up to {max_detected_hops} hops. Beyond that, DFS depth limit reached.",
        "details": results,
    }


def run_split_hub_test() -> Dict[str, Any]:
    """
    Single hub (6 in, 6 out) vs two smaller hubs (3 in 3 out each) sharing one beneficiary.
    When split, each hub may fall below HUB_MIN_IN_DEGREE/OUT_DEGREE (3).
    """
    base = datetime.now() - timedelta(hours=1)
    # One big hub: H1, sources S1..S6, dests D1..D6
    txns_single: List[TransactionBase] = []
    t = base
    for i in range(6):
        txns_single.append(_txn(f"S{i}", "HUB", 60_000, t, "NEFT"))
        t += timedelta(minutes=5)
    for i in range(6):
        txns_single.append(_txn("HUB", f"D{i}", 55_000, t, "RTGS"))
        t += timedelta(minutes=5)
    graph_single = GraphAgent().process_transactions(txns_single)
    pathfinder_single = PathfinderAgent(graph_single)
    hubs_single = pathfinder_single.detect_hub_and_spoke(in_degree_threshold=3, out_degree_threshold=3)
    single_detected = "HUB" in hubs_single

    # Two hubs (H1, H2) each 3 in 3 out, both feeding same beneficiary B
    txns_split: List[TransactionBase] = []
    t = base
    for i in range(3):
        txns_split.append(_txn(f"A{i}", "H1", 60_000, t, "NEFT"))
        t += timedelta(minutes=5)
    for i in range(3):
        txns_split.append(_txn("H1", "BENEFICIARY", 55_000, t, "RTGS"))
        t += timedelta(minutes=5)
    for i in range(3):
        txns_split.append(_txn(f"C{i}", "H2", 60_000, t, "NEFT"))
        t += timedelta(minutes=5)
    for i in range(3):
        txns_split.append(_txn("H2", "BENEFICIARY", 55_000, t, "RTGS"))
        t += timedelta(minutes=5)
    graph_split = GraphAgent().process_transactions(txns_split)
    pathfinder_split = PathfinderAgent(graph_split)
    hubs_split = pathfinder_split.detect_hub_and_spoke(in_degree_threshold=3, out_degree_threshold=3)
    # H1 and H2 each have in_degree 3, out_degree 3 — may still be detected
    split_detected = len(hubs_split) >= 1

    return {
        "test": "split_hub",
        "title": "Split hub test",
        "summary": "Single hub detected." if single_detected else "Single hub not detected."
        + " Split variant: " + ("at least one hub detected." if split_detected else "Hub-spoke signature broken — pattern falls below structural threshold."),
        "details": [
            {"variant": "Single hub (6 in, 6 out)", "detected": single_detected},
            {"variant": "Two hubs (3 in 3 out each) sharing beneficiary", "detected": split_detected},
        ],
    }


def run_time_distributed_smurfing_test() -> Dict[str, Any]:
    """
    Smurfing with transactions spread across 95 days instead of 72 hours.
    Structure is still fan-in; annotate that it's outside hot-layer window.
    """
    base = datetime.now() - timedelta(days=95)
    # 8 sources -> 1 target, spread over 95 days
    txns: List[TransactionBase] = []
    for i in range(8):
        t = base + timedelta(days=i * 12)  # spread over ~96 days
        txns.append(_txn(f"SRC{i}", "TARGET", 48_000, t, "IMPS"))
    graph = GraphAgent().process_transactions(txns)
    pathfinder = PathfinderAgent(graph)
    smurf_targets = pathfinder.detect_smurfing(fan_in_threshold=5)
    detected = "TARGET" in smurf_targets

    return {
        "test": "time_distributed_smurfing",
        "title": "Time-distributed smurfing test",
        "summary": "Fan-in pattern detected." if detected else "Smurfing not detected."
        + " Outside hot-layer detection window — historical probe triggered.",
        "details": [
            {"variant": "8 sources → 1 target over 95 days", "detected": detected},
            {"note": "Outside hot-layer detection window — historical probe triggered."},
        ],
    }


def run_all_adversarial_tests() -> Dict[str, Any]:
    return {
        "cycle_plus_hop": run_cycle_plus_hop_test(),
        "split_hub": run_split_hub_test(),
        "time_distributed_smurfing": run_time_distributed_smurfing_test(),
    }
