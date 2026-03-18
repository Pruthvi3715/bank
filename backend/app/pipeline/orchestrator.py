import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

import networkx as nx
import pandas as pd

from app.models.schemas import TransactionBase, AlertBase
from app.simulation.generator import generate_scenario, build_mock_kyc
from app.feedback_store import get_scorer_config
from app.pipeline.graph_agent import GraphAgent
from app.pipeline.pathfinder_agent import PathfinderAgent
from app.pipeline.context_agent import ContextAgent
from app.pipeline.scorer_agent import ScorerAgent
from app.pipeline.report_agent import ReportAgent


# Minimum risk score to generate an alert (PRD: "elevated" band starts at 40)
_ALERT_THRESHOLD = 40.0


def _get_edges_for_pair(
    graph: nx.MultiDiGraph, u: str, v: str
) -> List[Dict[str, Any]]:
    """Return all edge attribute dicts between u and v in the MultiDiGraph."""
    data = graph.get_edge_data(u, v)
    if data is None:
        return [{"sender_id": u, "receiver_id": v}]
    # MultiDiGraph returns {0: {...}, 1: {...}, ...}
    result = []
    for edge_attrs in data.values():
        result.append({"sender_id": u, "receiver_id": v, **edge_attrs})
    return result or [{"sender_id": u, "receiver_id": v}]


class DetectionOrchestrator:
    def __init__(self):
        self.mock_kyc_db = build_mock_kyc()

    # ------------------------------------------------------------------
    # Main pipeline entry points
    # ------------------------------------------------------------------
    def run_detection_pipeline(
        self, transactions: Optional[List[TransactionBase]] = None
    ) -> Dict[str, Any]:
        """
        Run the full detection pipeline.

        If transactions is None a fresh synthetic scenario is generated.
        Pass a list of TransactionBase objects to use uploaded CSV data.
        """
        activity: List[Dict[str, str]] = []

        if transactions is None:
            raw_txns = generate_scenario()
            transactions = [TransactionBase(**t) for t in raw_txns]
            activity.append({"agent": "Data", "message": f"Generated synthetic scenario: {len(transactions)} transactions"})
        else:
            activity.append({"agent": "Data", "message": f"Loaded {len(transactions)} transactions from CSV"})

        # Pre-filter: ignore micro-transactions (configurable via settings)
        try:
            import sys, os
            _cfg = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
            if _cfg not in sys.path:
                sys.path.insert(0, os.path.abspath(_cfg))
            import settings as cfg
            min_amount = cfg.PREFILTER_MIN_AMOUNT
        except Exception:
            min_amount = 500
        transactions = [t for t in transactions if t.amount >= min_amount]
        activity.append({"agent": "PreFilter", "message": f"After pre-filter (amount >= {min_amount}): {len(transactions)} transactions"})

        # Build graph
        graph_agent = GraphAgent()
        graph = graph_agent.process_transactions(transactions)
        activity.append({"agent": "Graph Agent", "message": f"Ingesting batch: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges"})

        # Detect patterns
        pathfinder = PathfinderAgent(graph)
        detections = pathfinder.run_all_detections()

        # Log pathfinder findings
        for cycle in detections.get("cycles", [])[:5]:
            cycle_str = " → ".join(cycle) + f" → {cycle[0]}"
            activity.append({"agent": "Pathfinder Agent", "message": f"Cycle detected — nodes {cycle_str}"})
        if detections.get("cycles") and len(detections["cycles"]) > 5:
            activity.append({"agent": "Pathfinder Agent", "message": f"... and {len(detections['cycles']) - 5} more cycles"})
        for target in detections.get("smurfing_targets", [])[:3]:
            activity.append({"agent": "Pathfinder Agent", "message": f"Smurfing (fan-in) target: {target}"})
        if detections.get("smurfing_targets") and len(detections["smurfing_targets"]) > 3:
            activity.append({"agent": "Pathfinder Agent", "message": f"... and {len(detections['smurfing_targets']) - 3} more smurfing targets"})
        for hub in detections.get("hubs", [])[:3]:
            activity.append({"agent": "Pathfinder Agent", "message": f"Hub-and-spoke hub: {hub}"})
        for node in detections.get("pass_through", [])[:3]:
            activity.append({"agent": "Pathfinder Agent", "message": f"Pass-through node: {node}"})
        for node in detections.get("dormant", [])[:3]:
            activity.append({"agent": "Pathfinder Agent", "message": f"Dormant activation: {node}"})
        for path in detections.get("temporal_layering", [])[:2]:
            activity.append({"agent": "Pathfinder Agent", "message": f"Temporal layering path ({len(path)} hops): {' → '.join(path[:5])}{'...' if len(path) > 5 else ''}"})

        # Scoring & SAR (scorer_config from investigator feedback loop)
        context_agent = ContextAgent(self.mock_kyc_db)
        scorer_config = get_scorer_config()
        scorer_agent = ScorerAgent(context_agent, graph=graph, scorer_config=scorer_config)
        report_agent = ReportAgent()

        alerts: List[AlertBase] = []

        # ---- Pattern 1: Cycles ----
        for cycle in detections.get("cycles", []):
            edges = []
            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i + 1) % len(cycle)]
                edges.extend(_get_edges_for_pair(graph, u, v))
            score_data = scorer_agent.score_pattern("Cycle", cycle, edges=edges)
            if score_data["final_score"] >= _ALERT_THRESHOLD:
                alerts.append(self._make_alert(score_data, cycle, edges, report_agent))

        # ---- Pattern 2: Smurfing ----
        seen_smurfing: set = set()
        for target in detections.get("smurfing_targets", []):
            if target in seen_smurfing:
                continue
            seen_smurfing.add(target)
            senders = list(set(graph.predecessors(target)))
            nodes = senders + [target]
            edges = []
            for s in senders:
                edges.extend(_get_edges_for_pair(graph, s, target))
            score_data = scorer_agent.score_pattern("Smurfing", nodes, edges=edges)
            if score_data["final_score"] >= _ALERT_THRESHOLD:
                edge_labels = [f"{s}->{target}" for s in senders]
                alerts.append(
                    self._make_alert(score_data, nodes, edges, report_agent, edge_labels)
                )

        # ---- Pattern 3: Hub-and-Spoke ----
        seen_hubs: set = set()
        for hub in detections.get("hubs", []):
            if hub in seen_hubs:
                continue
            seen_hubs.add(hub)
            spokes_in = list(set(graph.predecessors(hub)))
            spokes_out = list(set(graph.successors(hub)))
            nodes = list({hub} | set(spokes_in) | set(spokes_out))
            edges = []
            for s in spokes_in:
                edges.extend(_get_edges_for_pair(graph, s, hub))
            for t in spokes_out:
                edges.extend(_get_edges_for_pair(graph, hub, t))
            score_data = scorer_agent.score_pattern("HubAndSpoke", nodes, edges=edges)
            if score_data["final_score"] >= _ALERT_THRESHOLD:
                edge_labels = (
                    [f"{s}->{hub}" for s in spokes_in]
                    + [f"{hub}->{t}" for t in spokes_out]
                )
                alerts.append(
                    self._make_alert(score_data, nodes, edges, report_agent, edge_labels)
                )

        # ---- Pattern 4: Pass-Through ----
        seen_pt: set = set()
        for node in detections.get("pass_through", []):
            if node in seen_pt:
                continue
            seen_pt.add(node)
            preds = list(set(graph.predecessors(node)))
            succs = list(set(graph.successors(node)))
            nodes = list({node} | set(preds) | set(succs))
            edges = []
            for p in preds:
                edges.extend(_get_edges_for_pair(graph, p, node))
            for s in succs:
                edges.extend(_get_edges_for_pair(graph, node, s))
            score_data = scorer_agent.score_pattern("PassThrough", nodes, edges=edges)
            if score_data["final_score"] >= _ALERT_THRESHOLD:
                edge_labels = (
                    [f"{p}->{node}" for p in preds]
                    + [f"{node}->{s}" for s in succs]
                )
                alerts.append(
                    self._make_alert(score_data, nodes, edges, report_agent, edge_labels)
                )

        # ---- Pattern 5: Dormant Activation ----
        seen_dormant: set = set()
        for node in detections.get("dormant", []):
            if node in seen_dormant:
                continue
            seen_dormant.add(node)
            preds = list(set(graph.predecessors(node)))
            succs = list(set(graph.successors(node)))
            nodes = list({node} | set(preds) | set(succs))
            edges = []
            for p in preds:
                edges.extend(_get_edges_for_pair(graph, p, node))
            for s in succs:
                edges.extend(_get_edges_for_pair(graph, node, s))
            score_data = scorer_agent.score_pattern(
                "DormantActivation", nodes, edges=edges
            )
            if score_data["final_score"] >= _ALERT_THRESHOLD:
                edge_labels = (
                    [f"{p}->{node}" for p in preds]
                    + [f"{node}->{s}" for s in succs]
                )
                alerts.append(
                    self._make_alert(score_data, nodes, edges, report_agent, edge_labels)
                )

        # ---- Pattern 6: Temporal Layering ----
        for path in detections.get("temporal_layering", []):
            if len(path) < 4:
                continue
            edges = []
            edge_labels: List[str] = []
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edges.extend(_get_edges_for_pair(graph, u, v))
                edge_labels.append(f"{u}->{v}")
            score_data = scorer_agent.score_pattern("TemporalLayering", path, edges=edges)
            if score_data["final_score"] >= _ALERT_THRESHOLD:
                alerts.append(
                    self._make_alert(score_data, path, edges, report_agent, edge_labels)
                )

        # Deduplicate alerts with identical node sets
        alerts = self._deduplicate_alerts(alerts)
        alerts = self._deduplicate_overlapping_alerts(alerts, min_overlap=0.5)

        # Sort by risk score desc
        alerts.sort(key=lambda a: a.risk_score, reverse=True)

        activity.append({"agent": "Scorer Agent", "message": f"Risk Score computed for {len(alerts)} flagged subgraphs"})
        for a in alerts[:5]:
            activity.append({"agent": "Report Agent", "message": f"Alert {a.pattern_type}: Score {a.risk_score:.0f}/100 — {a.disposition}"})
        if len(alerts) > 5:
            activity.append({"agent": "Report Agent", "message": f"... and {len(alerts) - 5} more alerts"})

        # Build visualization payload
        nodes_viz = [{"id": n} for n in graph.nodes()]
        edges_viz = []
        for u, v, d in graph.edges(data=True):
            edges_viz.append(
                {
                    "source": u,
                    "target": v,
                    "amount": d.get("amount", 0),
                    "channel": d.get("channel", ""),
                }
            )

        # Pattern summary
        pattern_counts: Dict[str, int] = {}
        for a in alerts:
            pattern_counts[a.pattern_type] = pattern_counts.get(a.pattern_type, 0) + 1

        return {
            "alerts": [a.model_dump() for a in alerts],
            "graph": {"nodes": nodes_viz, "links": edges_viz},
            "stats": {
                "total_txns": len(transactions),
                "total_nodes": graph.number_of_nodes(),
                "total_edges": graph.number_of_edges(),
                "alerts_generated": len(alerts),
                "pattern_counts": pattern_counts,
            },
            "agent_activity": activity,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_alert(
        self,
        score_data: Dict[str, Any],
        nodes: List[str],
        edges: List[Dict[str, Any]],
        report_agent: ReportAgent,
        edge_labels: Optional[List[str]] = None,
    ) -> AlertBase:
        if edge_labels is None:
            edge_labels = [
                f"{e.get('sender_id', '?')}->{e.get('receiver_id', '?')}"
                for e in edges
            ]
        explanation = report_agent.generate_sar_draft(score_data, edges)
        return AlertBase(
            alert_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            subgraph_nodes=nodes,
            subgraph_edges=edge_labels,
            risk_score=score_data["final_score"],
            pattern_type=score_data["pattern_type"],
            structural_score=score_data["structural_score"],
            innocence_discount=score_data["innocence_discount"],
            disposition=score_data["disposition"],
            channels=sorted(
                list(
                    {
                        e.get("channel")
                        for e in edges
                        if e.get("channel") is not None and e.get("channel") != ""
                    }
                )
            ),
            scoring_signals=score_data.get("scoring_signals", {}),
            llm_explanation=explanation,
        )

    @staticmethod
    def _deduplicate_alerts(alerts: List[AlertBase]) -> List[AlertBase]:
        """Remove alerts that cover the exact same set of nodes."""
        seen: set = set()
        unique = []
        for a in alerts:
            key = (a.pattern_type, frozenset(a.subgraph_nodes))
            if key not in seen:
                seen.add(key)
                unique.append(a)
        return unique

    @staticmethod
    def _deduplicate_overlapping_alerts(
        alerts: List[AlertBase], *, min_overlap: float = 0.5
    ) -> List[AlertBase]:
        """
        If two alerts overlap on >min_overlap of the smaller node set,
        keep only the higher-risk alert.

        This intentionally deduplicates across pattern types for demo clarity.
        """
        if not alerts:
            return alerts

        candidates = sorted(alerts, key=lambda a: a.risk_score, reverse=True)
        kept: List[AlertBase] = []
        kept_nodes: List[set] = []

        def overlap_ratio(a_set: set, b_set: set) -> float:
            if not a_set or not b_set:
                return 0.0
            inter = len(a_set & b_set)
            denom = min(len(a_set), len(b_set))
            return inter / denom if denom else 0.0

        for a in candidates:
            a_set = set(a.subgraph_nodes or [])
            dup = False
            for b_set in kept_nodes:
                if overlap_ratio(a_set, b_set) > min_overlap:
                    dup = True
                    break
            if not dup:
                kept.append(a)
                kept_nodes.append(a_set)
        return kept
