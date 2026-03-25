"""
Graph feature extraction for ML models.
Extracts 10 numerical features per account node.
Used by both Isolation Forest and Gradient Boosting.
"""

import numpy as np
import networkx as nx
from typing import Optional, Tuple, List


FEATURE_NAMES = [
    "in_degree",
    "out_degree",
    "in_out_ratio",
    "total_in",
    "total_out",
    "channel_mix",
    "off_hours_ratio",
    "dormancy_days",
    "txn_count",
    "amount_variance",
]


def extract_node_features(
    graph: nx.MultiDiGraph,
    node: str,
    account_data: Optional[dict] = None,
) -> np.ndarray:
    """Extract 10 numerical features for a single account node."""
    if node not in graph:
        return np.zeros(10)

    in_deg = graph.in_degree(node)
    out_deg = graph.out_degree(node)

    in_amounts = [d.get("amount", 0) for _, _, d in graph.in_edges(node, data=True)]
    out_amounts = [d.get("amount", 0) for _, _, d in graph.out_edges(node, data=True)]

    total_in = sum(in_amounts)
    total_out = sum(out_amounts)
    in_out_ratio = total_in / (total_out + 1e-6)

    attrs = graph.nodes.get(node, {})
    channels = attrs.get("channels", set())
    channel_mix = len(channels) if isinstance(channels, (set, list)) else 0

    timestamps = []
    for _, _, d in graph.out_edges(node, data=True):
        ts = d.get("timestamp")
        if ts and hasattr(ts, "hour"):
            timestamps.append(ts)
    for _, _, d in graph.in_edges(node, data=True):
        ts = d.get("timestamp")
        if ts and hasattr(ts, "hour"):
            timestamps.append(ts)

    off_hours = sum(1 for t in timestamps if t.hour < 6 or t.hour >= 22)
    off_hours_ratio = off_hours / (len(timestamps) + 1e-6)

    first_seen = attrs.get("first_seen")
    last_seen = attrs.get("last_seen")
    dormancy_days = (last_seen - first_seen).days if first_seen and last_seen else 0

    txn_count = len(in_amounts) + len(out_amounts)
    all_amounts = in_amounts + out_amounts
    amount_variance = float(np.std(all_amounts)) if all_amounts else 0.0

    return np.array(
        [
            in_deg,
            out_deg,
            in_out_ratio,
            total_in,
            total_out,
            channel_mix,
            off_hours_ratio,
            dormancy_days,
            txn_count,
            amount_variance,
        ]
    )


def extract_all_features(
    graph: nx.MultiDiGraph, kyc_db: Optional[dict] = None
) -> Tuple[np.ndarray, List[str]]:
    """Extract features for all nodes. Returns (feature_matrix, node_ids)."""
    nodes = list(graph.nodes())
    if not nodes:
        return np.zeros((0, 10)), []

    features = []
    for node in nodes:
        account_data = (kyc_db or {}).get(node, {})
        features.append(extract_node_features(graph, node, account_data))

    return np.vstack(features), nodes
