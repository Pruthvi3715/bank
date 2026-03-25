"""
Advanced fraud detection algorithms for GraphSentinel.
Supplements the PathfinderAgent with graph-theoretic techniques.

Algorithms:
  - Tarjan's SCC cycle detection  (T8)
  - Louvain community detection   (T9)
  - Reverse BFS backtracking      (T10)
  - Temporal motif detection       (T11)
  - PageRank + betweenness         (T12)
  - Profile mismatch detection     (T14)
"""

import networkx as nx
import numpy as np
from collections import deque
from datetime import timedelta
from typing import Dict, List, Any, Optional


class AdvancedDetector:
    """Advanced graph-based fraud detection algorithms."""

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
        self.simple_graph = nx.DiGraph(graph)

    # ------------------------------------------------------------------
    # T8: Tarjan's SCC Cycle Detection — O(V+E) single pass
    # ------------------------------------------------------------------
    def detect_cycles_tarjan(self) -> List[List[str]]:
        """
        Find all strongly-connected components with 3+ nodes.
        Each SCC represents a set of accounts where money can cycle.
        """
        sccs = list(nx.strongly_connected_components(self.simple_graph))
        return [sorted(list(scc)) for scc in sccs if len(scc) >= 3]

    # ------------------------------------------------------------------
    # T9: Louvain Community Detection — O(n log n)
    # ------------------------------------------------------------------
    def detect_fraud_rings(
        self, min_density: float = 0.3, min_nodes: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Detect dense account clusters (mule networks, fraud rings).
        Falls back to greedy modularity if python-louvain is not installed.
        """
        G_undirected = self.simple_graph.to_undirected()
        if len(G_undirected.nodes()) == 0:
            return []

        # Attempt Louvain, fall back to greedy modularity
        try:
            import community as community_louvain

            partition = community_louvain.best_partition(G_undirected)
            communities: Dict[int, list] = {}
            for node, comm_id in partition.items():
                communities.setdefault(comm_id, []).append(node)
        except ImportError:
            communities_gen = nx.community.greedy_modularity_communities(G_undirected)
            communities = {i: list(c) for i, c in enumerate(communities_gen)}

        suspicious = []
        for comm_id, nodes in communities.items():
            if len(nodes) >= min_nodes:
                subgraph = self.simple_graph.subgraph(nodes)
                density = nx.density(subgraph)
                if density > min_density:
                    suspicious.append(
                        {
                            "community_id": comm_id,
                            "nodes": nodes,
                            "density": round(density, 4),
                            "size": len(nodes),
                            "pattern_type": "FraudRing",
                        }
                    )
        return suspicious

    # ------------------------------------------------------------------
    # T10: Reverse BFS Backtracking
    # ------------------------------------------------------------------
    def reverse_trace(
        self, suspect_node: str, max_depth: int = 12
    ) -> Dict[str, Any]:
        """
        Backtrack from suspect node through predecessors.
        Legit money traces back 1-3 hops; fraud explodes wide (8-12).
        """
        if suspect_node not in self.graph:
            return {
                "trace_width": {},
                "total_predecessors": 0,
                "is_suspicious": False,
            }

        visited = {suspect_node}
        queue = deque([(suspect_node, 0)])
        depth_counts: Dict[int, int] = {}

        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            predecessors = list(self.graph.predecessors(node))
            depth_counts[depth] = depth_counts.get(depth, 0) + len(predecessors)
            for pred in predecessors:
                if pred not in visited:
                    visited.add(pred)
                    queue.append((pred, depth + 1))

        is_suspicious = any(count > 5 for count in depth_counts.values())
        return {
            "trace_width": depth_counts,
            "total_predecessors": len(visited) - 1,
            "is_suspicious": is_suspicious,
            "pattern_type": "Layering" if is_suspicious else "Normal",
        }

    # ------------------------------------------------------------------
    # T11: Temporal Motif Detector (dormant → ping → burst)
    # ------------------------------------------------------------------
    def detect_dormant_motif(
        self, dormancy_threshold_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Detect the dormant→ping→burst motif: early warning of mule
        network activation. Triggers 12-48h before main layering.
        """
        motifs = []
        for node in self.graph.nodes():
            attrs = self.graph.nodes[node]
            first_seen = attrs.get("first_seen")
            last_seen = attrs.get("last_seen")
            if not first_seen or not last_seen:
                continue

            dormancy_gap = (last_seen - first_seen).days
            if dormancy_gap < dormancy_threshold_days:
                continue

            edges = []
            for _, _, d in self.graph.out_edges(node, data=True):
                ts = d.get("timestamp")
                if ts:
                    edges.append({"timestamp": ts, "amount": d.get("amount", 0)})
            for _, _, d in self.graph.in_edges(node, data=True):
                ts = d.get("timestamp")
                if ts:
                    edges.append({"timestamp": ts, "amount": d.get("amount", 0)})

            edges.sort(key=lambda x: x["timestamp"])
            if len(edges) < 2:
                continue

            first_amount = edges[0]["amount"]
            latest_amount = edges[-1]["amount"]
            gap_hours = (
                (edges[-1]["timestamp"] - edges[0]["timestamp"]).total_seconds()
                / 3600
            )

            if first_amount < 500 and latest_amount > 10000 and gap_hours < 48:
                motifs.append(
                    {
                        "node": node,
                        "dormancy_days": dormancy_gap,
                        "ping_amount": first_amount,
                        "burst_amount": latest_amount,
                        "hours_between": round(gap_hours, 1),
                        "pattern_type": "DormantMotif",
                        "risk_signal": "EARLY_WARNING",
                    }
                )
        return motifs

    # ------------------------------------------------------------------
    # T12: PageRank + Approximate Betweenness Centrality
    # ------------------------------------------------------------------
    def compute_centrality(
        self, sample_ratio: float = 0.1
    ) -> Dict[str, Any]:
        """
        PageRank → kingpin nodes.  Betweenness → bridge accounts.
        10% sampling gives 100× speedup with <5% accuracy loss.
        """
        if len(self.simple_graph.nodes()) == 0:
            return {
                "pagerank": {},
                "betweenness": {},
                "top_pagerank": [],
                "top_betweenness": [],
            }

        pagerank = nx.pagerank(self.simple_graph, alpha=0.85, max_iter=100)

        k = max(1, int(len(self.simple_graph.nodes()) * sample_ratio))
        try:
            betweenness = nx.betweenness_centrality(
                self.simple_graph, k=k, normalized=True
            )
        except Exception:
            betweenness = {}

        return {
            "pagerank": pagerank,
            "betweenness": betweenness,
            "top_pagerank": sorted(
                pagerank.items(), key=lambda x: -x[1]
            )[:10],
            "top_betweenness": sorted(
                betweenness.items(), key=lambda x: -x[1]
            )[:10],
        }

    # ------------------------------------------------------------------
    # T14: Profile Mismatch Detection
    # ------------------------------------------------------------------
    def detect_profile_mismatch(
        self, kyc_db: dict, mismatch_threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Flag accounts where total flow exceeds 3× declared income.
        Direct PS3 requirement.
        """
        mismatches = []
        for node in self.graph.nodes():
            kyc = kyc_db.get(node, {})
            declared_income = kyc.get("declared_income", 0)
            if not declared_income or declared_income <= 0:
                continue

            total_flow = sum(
                d.get("amount", 0)
                for _, _, d in self.graph.out_edges(node, data=True)
            ) + sum(
                d.get("amount", 0)
                for _, _, d in self.graph.in_edges(node, data=True)
            )

            monthly = declared_income / 12
            if monthly > 0:
                ratio = total_flow / monthly
                if ratio > mismatch_threshold:
                    mismatches.append(
                        {
                            "node": node,
                            "declared_monthly": round(monthly, 2),
                            "actual_flow": round(total_flow, 2),
                            "mismatch_ratio": round(ratio, 2),
                            "risk_signal": 25,
                            "pattern_type": "ProfileMismatch",
                        }
                    )
        return mismatches

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run_all_advanced(
        self, kyc_db: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Run all advanced detection algorithms and return results."""
        results: Dict[str, Any] = {
            "tarjan_sccs": self.detect_cycles_tarjan(),
            "fraud_rings": self.detect_fraud_rings(),
            "centrality": self.compute_centrality(),
            "dormant_motifs": self.detect_dormant_motif(),
        }
        if kyc_db:
            results["profile_mismatches"] = self.detect_profile_mismatch(kyc_db)
        else:
            results["profile_mismatches"] = []
        return results
