import sys
import os
from datetime import timedelta
from typing import List, Dict, Any

import networkx as nx

# Allow importing the top-level config package regardless of working directory
_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
if _config_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_config_path))

try:
    import settings as cfg
except ImportError:
    # Fallback defaults if config is unreachable
    class cfg:  # type: ignore
        CYCLE_MAX_HOPS = 8
        CYCLE_MAX_COUNT = 50
        FAN_IN_MIN_SOURCES = 5
        HUB_MIN_IN_DEGREE = 3
        HUB_MIN_OUT_DEGREE = 3
        PASSTHROUGH_RATIO_THRESHOLD = 0.85
        DORMANT_MIN_INACTIVE_MONTHS = 6
        TEMPORAL_MIN_GAP_DAYS = 90
        TEMPORAL_MIN_HOPS = 3
        TEMPORAL_MAX_HOPS = 6


class PathfinderAgent:
    """
    Runs topology algorithms to detect all five fraud patterns defined in the PRD.

    Patterns:
      1. Cycle          – directed round-trip (money laundering layering)
      2. Smurfing       – high fan-in structuring below CTR thresholds
      3. HubAndSpoke    – mule-network hub with high in- AND out-degree
      4. PassThrough    – nodes with near-zero retained balance (pass-through mules)
      5. DormantActivation – dormant accounts that suddenly activate with high volume
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    # ------------------------------------------------------------------
    # Pattern 1: Cycle (round-tripping)
    # ------------------------------------------------------------------
    def detect_cycles(
        self,
        max_length: int = cfg.CYCLE_MAX_HOPS,
        max_count: int = cfg.CYCLE_MAX_COUNT,
    ) -> List[List[str]]:
        """DFS cycle detection on the condensed (simple) digraph view."""
        # nx.simple_cycles works on any DiGraph / MultiDiGraph but is expensive on
        # large graphs – length_bound keeps it tractable.
        simple_view = nx.DiGraph(self.graph)  # collapse multi-edges for cycle search
        cycles: List[List[str]] = []
        try:
            for cycle in nx.simple_cycles(simple_view, length_bound=max_length):
                c = list(cycle)
                if len(c) > 2:
                    cycles.append(c)
                if len(cycles) >= max_count:
                    break
        except TypeError:
            # older networkx without length_bound
            for cycle in nx.simple_cycles(simple_view):
                c = list(cycle)
                if 2 < len(c) <= max_length:
                    cycles.append(c)
                if len(cycles) >= max_count:
                    break
        except Exception:
            pass
        return cycles

    # ------------------------------------------------------------------
    # Pattern 2: Smurfing / Structuring (high fan-in)
    # ------------------------------------------------------------------
    def detect_smurfing(
        self, fan_in_threshold: int = cfg.FAN_IN_MIN_SOURCES
    ) -> List[str]:
        """
        High fan-in: many distinct senders converging on one receiver.
        Uses the number of unique predecessors (not raw edge count) so that
        one sender making multiple transfers doesn't inflate the count.
        """
        targets = []
        for node in self.graph.nodes():
            unique_senders = len(set(self.graph.predecessors(node)))
            if unique_senders >= fan_in_threshold:
                targets.append(node)
        return targets

    # ------------------------------------------------------------------
    # Pattern 3: Hub-and-Spoke (mule network)
    # ------------------------------------------------------------------
    def detect_hub_and_spoke(
        self,
        in_degree_threshold: int = cfg.HUB_MIN_IN_DEGREE,
        out_degree_threshold: int = cfg.HUB_MIN_OUT_DEGREE,
    ) -> List[str]:
        """
        Hub node with high in-degree AND high out-degree — classic mule-network
        hub that aggregates from spokes and then fans out to layering accounts.
        Checks unique neighbour counts to avoid false positives from repeat txns.
        """
        hubs = []
        for node in self.graph.nodes():
            unique_in = len(set(self.graph.predecessors(node)))
            unique_out = len(set(self.graph.successors(node)))
            if unique_in >= in_degree_threshold and unique_out >= out_degree_threshold:
                hubs.append(node)
        return hubs

    # ------------------------------------------------------------------
    # Pattern 4: Pass-Through Nodes
    # ------------------------------------------------------------------
    def detect_pass_through(
        self, ratio_threshold: float = cfg.PASSTHROUGH_RATIO_THRESHOLD
    ) -> List[str]:
        """
        Pass-through mules: nodes where nearly all received funds are immediately
        forwarded.  Ratio = total_sent / total_received >= ratio_threshold and the
        node has both incoming and outgoing edges.
        """
        pass_through = []
        for node in self.graph.nodes():
            attrs = self.graph.nodes[node]
            received = attrs.get("total_received", 0.0)
            sent = attrs.get("total_sent", 0.0)
            if received > 0 and sent > 0:
                ratio = sent / received
                if (
                    ratio >= ratio_threshold
                    and self.graph.in_degree(node) > 0
                    and self.graph.out_degree(node) > 0
                ):
                    pass_through.append(node)
        return pass_through

    # ------------------------------------------------------------------
    # Pattern 5: Dormant Account Activation
    # ------------------------------------------------------------------
    def detect_dormant_activation(
        self,
        dormant_months: int = cfg.DORMANT_MIN_INACTIVE_MONTHS,
        min_txns_after: int = 3,
    ) -> List[str]:
        """
        Accounts that were inactive for >= dormant_months and then suddenly
        receive/send >= min_txns_after transactions within a short window.
        Uses first_seen / last_seen timestamps stored on nodes by GraphAgent.
        """
        dormant_nodes = []
        threshold_gap = timedelta(days=dormant_months * 30)
        for node in self.graph.nodes():
            attrs = self.graph.nodes[node]
            first_seen = attrs.get("first_seen")
            last_seen = attrs.get("last_seen")
            if first_seen is None or last_seen is None:
                continue
            # Proxy: if the spread of transactions for this node spans a large
            # gap (first vs last seen covers > dormant_months) AND there are
            # multiple edges, consider it a dormant activation candidate.
            if last_seen - first_seen >= threshold_gap:
                total_edges = self.graph.in_degree(node) + self.graph.out_degree(node)
                if total_edges >= min_txns_after:
                    dormant_nodes.append(node)
        return dormant_nodes

    # ------------------------------------------------------------------
    # Pattern 6: Temporal Layering (long-horizon)
    # ------------------------------------------------------------------
    def detect_temporal_layering(
        self,
        min_gap_days: int = cfg.TEMPORAL_MIN_GAP_DAYS,
        min_hops: int = cfg.TEMPORAL_MIN_HOPS,
        max_hops: int = cfg.TEMPORAL_MAX_HOPS,
    ) -> List[List[str]]:
        """
        Detect long-horizon multi-hop movement where funds progress through
        at least `min_hops` hops and the path spans >= min_gap_days.
        """
        results: List[List[str]] = []
        seen: set = set()
        min_gap = timedelta(days=min_gap_days)

        def _earliest_edge_after(u: str, v: str, after_ts):
            edge_map = self.graph.get_edge_data(u, v) or {}
            timestamps = []
            for attrs in edge_map.values():
                ts = attrs.get("timestamp")
                if ts is not None and (after_ts is None or ts > after_ts):
                    timestamps.append(ts)
            if not timestamps:
                return None
            return min(timestamps)

        def _dfs(path: List[str], last_ts):
            if len(path) > max_hops + 1:
                return

            if len(path) >= min_hops + 1:
                first_ts = _earliest_edge_after(path[0], path[1], None)
                if first_ts and last_ts and (last_ts - first_ts) >= min_gap:
                    key = tuple(path)
                    if key not in seen:
                        seen.add(key)
                        results.append(path.copy())

            current = path[-1]
            for nxt in self.graph.successors(current):
                if nxt in path:
                    continue
                edge_ts = _earliest_edge_after(current, nxt, last_ts)
                if edge_ts is None:
                    continue
                path.append(nxt)
                _dfs(path, edge_ts)
                path.pop()

        for node in self.graph.nodes():
            _dfs([node], None)
        return results

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run_all_detections(self) -> Dict[str, Any]:
        return {
            "cycles": self.detect_cycles(),
            "smurfing_targets": self.detect_smurfing(),
            "hubs": self.detect_hub_and_spoke(),
            "pass_through": self.detect_pass_through(),
            "dormant": self.detect_dormant_activation(),
            "temporal_layering": self.detect_temporal_layering(),
        }
