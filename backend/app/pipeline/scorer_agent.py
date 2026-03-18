import os
import sys
from typing import Any, Dict, List, Optional
import networkx as nx

_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
if _config_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_config_path))

try:
    import settings as cfg
except ImportError:
    class cfg:  # type: ignore
        PASSTHROUGH_RATIO_THRESHOLD = 0.85
        DORMANT_MIN_INACTIVE_MONTHS = 6


# PRD-defined scoring weights (Section 4.3)
_BASE_SCORES: Dict[str, float] = {
    "Cycle": 40.0,
    "Smurfing": 25.0,
    "HubAndSpoke": 30.0,
    "PassThrough": 15.0,
    "DormantActivation": 20.0,
    "TemporalLayering": 20.0,
}

_TEMPORAL_VELOCITY_BONUS = 20.0   # rapid multi-hop <24 hrs
_CROSS_CHANNEL_BONUS = 10.0        # funds switch channel mid-hop
_NEAR_THRESHOLD_BONUS = 15.0       # structuring near ₹50 000 CTR limit
_PASS_THROUGH_BONUS = 15.0         # zero-retention forwarding
_DORMANT_BONUS = 20.0              # dormant re-activation


class ScorerAgent:
    """
    Aggregates Pathfinder structural signals + Context innocence signals
    into a single Risk Score (0–100) per flagged subgraph.

    All six PRD signals are implemented:
      1. Structural pattern base score
      2. Temporal velocity (<24 hr multi-hop)
      3. Cross-channel switching
      4. Near-threshold structuring (₹45 K–₹49.9 K)
      5. Pass-through node ratio
      6. Dormant account activation
    """

    def __init__(
        self,
        context_agent,
        graph: nx.MultiDiGraph = None,
        scorer_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.context_agent = context_agent
        self.graph = graph  # optional; enables signal analysis on edges
        self.scorer_config = scorer_config or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def score_pattern(
        self,
        pattern_type: str,
        nodes: List[str],
        edges: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Returns a scoring dict with full signal breakdown.
        """
        if edges is None:
            edges = []

        # --- Signal 1: structural base score ---
        base = _BASE_SCORES.get(pattern_type, 20.0)

        # --- Signal 2: temporal velocity ---
        vel_bonus = self._temporal_velocity_bonus(edges)

        # --- Signal 3: cross-channel switching ---
        cc_bonus = self._cross_channel_bonus(edges)

        # --- Signal 4: near-threshold structuring ---
        nt_bonus = self._near_threshold_bonus(edges)

        # --- Signal 5: pass-through ---
        pt_bonus = self._pass_through_bonus(nodes)

        # --- Signal 6: dormant activation ---
        da_bonus = self._dormant_activation_bonus(nodes)

        raw_score = base + vel_bonus + cc_bonus + nt_bonus + pt_bonus + da_bonus
        raw_score = min(raw_score, 100.0)

        # --- Innocence discount (average across involved nodes, capped 30%) ---
        discounts = [
            self.context_agent.evaluate_node(
                n, pattern_type=pattern_type, scorer_config=self.scorer_config
            )
            for n in nodes
        ]
        avg_discount = sum(discounts) / len(discounts) if discounts else 0.0
        avg_discount = min(avg_discount, 30.0)

        final_score = raw_score * (1.0 - avg_discount / 100.0)
        final_score = max(0.0, min(100.0, final_score))

        disposition = self._disposition(final_score, avg_discount)

        return {
            "pattern_type": pattern_type,
            "structural_score": base,
            "innocence_discount": round(avg_discount, 2),
            "final_score": round(final_score, 2),
            "disposition": disposition,
            "scoring_signals": {
                "structural_base": base,
                "temporal_velocity": vel_bonus,
                "cross_channel": cc_bonus,
                "near_threshold_structuring": nt_bonus,
                "pass_through": pt_bonus,
                "dormant_activation": da_bonus,
            },
        }

    # ------------------------------------------------------------------
    # Signal helpers
    # ------------------------------------------------------------------
    def _temporal_velocity_bonus(self, edges: List[Dict[str, Any]]) -> float:
        """Bonus if all hops occur within a 24-hour window."""
        if len(edges) < 2:
            return 0.0
        try:
            timestamps = [e["timestamp"] for e in edges if e.get("timestamp")]
            if not timestamps:
                return 0.0
            span = max(timestamps) - min(timestamps)
            from datetime import timedelta
            if span < timedelta(hours=24):
                return _TEMPORAL_VELOCITY_BONUS
        except Exception:
            pass
        return 0.0

    def _cross_channel_bonus(self, edges: List[Dict[str, Any]]) -> float:
        """Bonus if multiple payment channels are used across the subgraph."""
        channels = {e.get("channel") for e in edges if e.get("channel")}
        return _CROSS_CHANNEL_BONUS if len(channels) > 1 else 0.0

    def _near_threshold_bonus(self, edges: List[Dict[str, Any]]) -> float:
        """Bonus if amounts cluster just below the ₹50 000 CTR reporting limit."""
        flagged = sum(
            1 for e in edges if 45000 <= e.get("amount", 0) < 50000
        )
        return _NEAR_THRESHOLD_BONUS if flagged > 0 else 0.0

    def _pass_through_bonus(self, nodes: List[str]) -> float:
        """Bonus if any node in the subgraph is a pass-through mule."""
        if self.graph is None:
            return 0.0
        for node in nodes:
            attrs = self.graph.nodes.get(node, {})
            recv = attrs.get("total_received", 0.0)
            sent = attrs.get("total_sent", 0.0)
            if recv > 0 and sent / recv >= cfg.PASSTHROUGH_RATIO_THRESHOLD:
                return _PASS_THROUGH_BONUS
        return 0.0

    def _dormant_activation_bonus(self, nodes: List[str]) -> float:
        """Bonus if any node in the subgraph was dormant before recent activity."""
        if self.graph is None:
            return 0.0
        from datetime import timedelta
        threshold = timedelta(days=cfg.DORMANT_MIN_INACTIVE_MONTHS * 30)
        for node in nodes:
            attrs = self.graph.nodes.get(node, {})
            first = attrs.get("first_seen")
            last = attrs.get("last_seen")
            if first and last and (last - first) >= threshold:
                return _DORMANT_BONUS
        return 0.0

    # ------------------------------------------------------------------
    # Disposition
    # ------------------------------------------------------------------
    @staticmethod
    def _disposition(score: float, discount: float) -> str:
        if score >= 70:
            return "Immediate Review"
        if score >= 40:
            return "Deferred Review" if discount > 0 else "Immediate Review"
        return "Auto-clear" if discount > 0 else "Monitor"
