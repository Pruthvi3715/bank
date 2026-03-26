import asyncio
import uuid
from datetime import datetime
from queue import Queue
from threading import Thread
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
from app.pipeline.advanced_detector import AdvancedDetector
from app.ml.anomaly_detector import AnomalyDetector


# Minimum risk score to generate an alert (PRD: "elevated" band starts at 40)
_ALERT_THRESHOLD = 40.0

# Thread-safe queue for streaming agent activity to WebSocket clients
_activity_queue: Queue = Queue()


def emit_activity(agent: str, message: str) -> None:
    """Emit an agent activity step to the WebSocket broadcast queue."""
    _activity_queue.put({"agent": agent, "message": message})


def get_pending_activities() -> List[Dict[str, str]]:
    """Drain all pending activity events from the queue. Call from async context."""
    events = []
    while not _activity_queue.empty():
        try:
            events.append(_activity_queue.get_nowait())
        except Exception:
            break
    return events


def _get_edges_for_pair(graph: nx.MultiDiGraph, u: str, v: str) -> List[Dict[str, Any]]:
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
        self._last_graph: Optional[nx.MultiDiGraph] = None

    # ------------------------------------------------------------------
    # Main pipeline entry points
    # ------------------------------------------------------------------
    def run_detection_pipeline(
        self,
        transactions: Optional[List[TransactionBase]] = None,
        scorer_config: Optional[Dict[str, Any]] = None,
        sync_neo4j: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the full detection pipeline.

        If transactions is None a fresh synthetic scenario is generated.
        Pass a list of TransactionBase objects to use uploaded CSV data.
        scorer_config: pre-fetched scorer config dict. If None, fetched synchronously.
        sync_neo4j: if True, attempt to sync the graph to Neo4j after the pipeline
                    completes (best-effort; failures are logged, not raised).
        """
        activity: List[Dict[str, str]] = []

        if transactions is None:
            raw_txns = generate_scenario()
            transactions = [TransactionBase(**t) for t in raw_txns]
            activity.append(
                {
                    "agent": "Data",
                    "message": f"Generated synthetic scenario: {len(transactions)} transactions",
                }
            )
            emit_activity(
                "Data",
                f"Generated synthetic scenario: {len(transactions)} transactions",
            )
        else:
            activity.append(
                {
                    "agent": "Data",
                    "message": f"Loaded {len(transactions)} transactions from CSV",
                }
            )
            emit_activity("Data", f"Loaded {len(transactions)} transactions from CSV")

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
        activity.append(
            {
                "agent": "PreFilter",
                "message": f"After pre-filter (amount >= {min_amount}): {len(transactions)} transactions",
            }
        )
        emit_activity(
            "PreFilter",
            f"After pre-filter (amount >= {min_amount}): {len(transactions)} transactions",
        )

        # Build graph
        graph_agent = GraphAgent()
        graph = graph_agent.process_transactions(transactions)
        activity.append(
            {
                "agent": "Graph Agent",
                "message": f"Ingesting batch: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges",
            }
        )
        emit_activity(
            "Graph Agent",
            f"Ingesting batch: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges",
        )

        # Detect patterns
        pathfinder = PathfinderAgent(graph)
        detections = pathfinder.run_all_detections()

        # Log pathfinder findings
        for cycle in detections.get("cycles", [])[:5]:
            cycle_str = " → ".join(cycle) + f" → {cycle[0]}"
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"Cycle detected — nodes {cycle_str}",
                }
            )
            emit_activity("Pathfinder Agent", f"Cycle detected — nodes {cycle_str}")
        if detections.get("cycles") and len(detections["cycles"]) > 5:
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"... and {len(detections['cycles']) - 5} more cycles",
                }
            )
        for target in detections.get("smurfing_targets", [])[:3]:
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"Smurfing (fan-in) target: {target}",
                }
            )
            emit_activity("Pathfinder Agent", f"Smurfing (fan-in) target: {target}")
        if (
            detections.get("smurfing_targets")
            and len(detections["smurfing_targets"]) > 3
        ):
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"... and {len(detections['smurfing_targets']) - 3} more smurfing targets",
                }
            )
        for hub in detections.get("hubs", [])[:3]:
            activity.append(
                {"agent": "Pathfinder Agent", "message": f"Hub-and-spoke hub: {hub}"}
            )
            emit_activity("Pathfinder Agent", f"Hub-and-spoke hub: {hub}")
        for node in detections.get("pass_through", [])[:3]:
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"Pass-through node: {node}",
                }
            )
            emit_activity("Pathfinder Agent", f"Pass-through node: {node}")
        for node in detections.get("dormant", [])[:3]:
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"Dormant activation: {node}",
                }
            )
            emit_activity("Pathfinder Agent", f"Dormant activation: {node}")
        for path in detections.get("temporal_layering", [])[:2]:
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"Temporal layering path ({len(path)} hops): {' → '.join(path[:5])}{'...' if len(path) > 5 else ''}",
                }
            )
            emit_activity(
                "Pathfinder Agent",
                f"Temporal layering path ({len(path)} hops): {' → '.join(path[:5])}{'...' if len(path) > 5 else ''}",
            )
        if detections.get("cycles") and len(detections["cycles"]) > 5:
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"... and {len(detections['cycles']) - 5} more cycles",
                }
            )
        for target in detections.get("smurfing_targets", [])[:3]:
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"Smurfing (fan-in) target: {target}",
                }
            )
        if (
            detections.get("smurfing_targets")
            and len(detections["smurfing_targets"]) > 3
        ):
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"... and {len(detections['smurfing_targets']) - 3} more smurfing targets",
                }
            )
        for hub in detections.get("hubs", [])[:3]:
            activity.append(
                {"agent": "Pathfinder Agent", "message": f"Hub-and-spoke hub: {hub}"}
            )
        for node in detections.get("pass_through", [])[:3]:
            activity.append(
                {"agent": "Pathfinder Agent", "message": f"Pass-through node: {node}"}
            )
        for node in detections.get("dormant", [])[:3]:
            activity.append(
                {"agent": "Pathfinder Agent", "message": f"Dormant activation: {node}"}
            )
        for path in detections.get("temporal_layering", [])[:2]:
            activity.append(
                {
                    "agent": "Pathfinder Agent",
                    "message": f"Temporal layering path ({len(path)} hops): {' → '.join(path[:5])}{'...' if len(path) > 5 else ''}",
                }
            )

        # Advanced detection algorithms (Tarjan, Louvain, PageRank, etc.)
        advanced = AdvancedDetector(graph)
        advanced_results = advanced.run_all_advanced(kyc_db=self.mock_kyc_db)

        tarjan_sccs = advanced_results.get("tarjan_sccs", [])
        if tarjan_sccs:
            activity.append(
                {
                    "agent": "Advanced Detector",
                    "message": f"Tarjan SCC: {len(tarjan_sccs)} strongly-connected components",
                }
            )
            emit_activity(
                "Advanced Detector",
                f"Tarjan SCC: {len(tarjan_sccs)} strongly-connected components",
            )
        fraud_rings = advanced_results.get("fraud_rings", [])
        if fraud_rings:
            activity.append(
                {
                    "agent": "Advanced Detector",
                    "message": f"Louvain: {len(fraud_rings)} dense fraud ring communities",
                }
            )
            emit_activity(
                "Advanced Detector",
                f"Louvain: {len(fraud_rings)} dense fraud ring communities",
            )
        centrality = advanced_results.get("centrality", {})
        top_pr = centrality.get("top_pagerank", [])[:3]
        if top_pr:
            activity.append(
                {
                    "agent": "Advanced Detector",
                    "message": f"PageRank top nodes: {', '.join(n[0] for n in top_pr)}",
                }
            )
            emit_activity(
                "Advanced Detector",
                f"PageRank top nodes: {', '.join(n[0] for n in top_pr)}",
            )
        top_bw = centrality.get("top_betweenness", [])[:3]
        if top_bw:
            activity.append(
                {
                    "agent": "Advanced Detector",
                    "message": f"Betweenness bridges: {', '.join(n[0] for n in top_bw)}",
                }
            )
            emit_activity(
                "Advanced Detector",
                f"Betweenness bridges: {', '.join(n[0] for n in top_bw)}",
            )
        dormant_motifs = advanced_results.get("dormant_motifs", [])
        if dormant_motifs:
            activity.append(
                {
                    "agent": "Advanced Detector",
                    "message": f"Dormant motifs: {len(dormant_motifs)} early-warning activations",
                }
            )
            emit_activity(
                "Advanced Detector",
                f"Dormant motifs: {len(dormant_motifs)} early-warning activations",
            )
        mismatches = advanced_results.get("profile_mismatches", [])
        if mismatches:
            activity.append(
                {
                    "agent": "Advanced Detector",
                    "message": f"Profile mismatches: {len(mismatches)} accounts exceed 3x income",
                }
            )
            emit_activity(
                "Advanced Detector",
                f"Profile mismatches: {len(mismatches)} accounts exceed 3x income",
            )

        # ML scoring (Isolation Forest + Gradient Boosting)
        ml_detector = AnomalyDetector()
        ml_scores = ml_detector.score_all_nodes(graph, kyc_db=self.mock_kyc_db)
        feature_importance = ml_detector.get_feature_importance()
        activity.append(
            {
                "agent": "ML Detector",
                "message": f"IF + GB scored {len(ml_scores)} nodes",
            }
        )
        emit_activity("ML Detector", f"IF + GB scored {len(ml_scores)} nodes")
        context_agent = ContextAgent(self.mock_kyc_db)
        if scorer_config is None:
            try:
                scorer_config = asyncio.get_event_loop().run_until_complete(
                    get_scorer_config()
                )
            except RuntimeError:
                scorer_config = {}
        scorer_agent = ScorerAgent(
            context_agent, graph=graph, scorer_config=scorer_config
        )
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
                alerts.append(
                    self._make_alert(
                        score_data, cycle, edges, report_agent, ml_scores=ml_scores
                    )
                )

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
                    self._make_alert(
                        score_data,
                        nodes,
                        edges,
                        report_agent,
                        edge_labels,
                        ml_scores=ml_scores,
                    )
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
                edge_labels = [f"{s}->{hub}" for s in spokes_in] + [
                    f"{hub}->{t}" for t in spokes_out
                ]
                alerts.append(
                    self._make_alert(
                        score_data,
                        nodes,
                        edges,
                        report_agent,
                        edge_labels,
                        ml_scores=ml_scores,
                    )
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
                edge_labels = [f"{p}->{node}" for p in preds] + [
                    f"{node}->{s}" for s in succs
                ]
                alerts.append(
                    self._make_alert(
                        score_data,
                        nodes,
                        edges,
                        report_agent,
                        edge_labels,
                        ml_scores=ml_scores,
                    )
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
                edge_labels = [f"{p}->{node}" for p in preds] + [
                    f"{node}->{s}" for s in succs
                ]
                alerts.append(
                    self._make_alert(
                        score_data,
                        nodes,
                        edges,
                        report_agent,
                        edge_labels,
                        ml_scores=ml_scores,
                    )
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
            score_data = scorer_agent.score_pattern(
                "TemporalLayering", path, edges=edges
            )
            if score_data["final_score"] >= _ALERT_THRESHOLD:
                alerts.append(
                    self._make_alert(
                        score_data,
                        path,
                        edges,
                        report_agent,
                        edge_labels,
                        ml_scores=ml_scores,
                    )
                )

        # Deduplicate alerts with identical node sets
        alerts = self._deduplicate_alerts(alerts)
        alerts = self._deduplicate_overlapping_alerts(alerts, min_overlap=0.5)

        # Sort by risk score desc
        alerts.sort(key=lambda a: a.risk_score, reverse=True)

        activity.append(
            {
                "agent": "Scorer Agent",
                "message": f"Risk Score computed for {len(alerts)} flagged subgraphs",
            }
        )
        emit_activity(
            "Scorer Agent", f"Risk Score computed for {len(alerts)} flagged subgraphs"
        )
        for a in alerts[:5]:
            activity.append(
                {
                    "agent": "Report Agent",
                    "message": f"Alert {a.pattern_type}: Score {a.risk_score:.0f}/100 — {a.disposition}",
                }
            )
            emit_activity(
                "Report Agent",
                f"Alert {a.pattern_type}: Score {a.risk_score:.0f}/100 — {a.disposition}",
            )
        if len(alerts) > 5:
            activity.append(
                {
                    "agent": "Report Agent",
                    "message": f"... and {len(alerts) - 5} more alerts",
                }
            )

        # Build visualization payload (with centrality + ML data)
        CHANNEL_COLORS = {
            "UPI": "#378ADD",
            "NEFT": "#EF9F27",
            "RTGS": "#1D9E75",
            "IMPS": "#7F77DD",
            "SWIFT": "#D85A30",
            "ATM": "#888780",
        }
        pagerank_data = centrality.get("pagerank", {})
        betweenness_data = centrality.get("betweenness", {})
        nodes_viz = []
        for n in graph.nodes():
            attrs = graph.nodes[n]
            nd = {
                "id": n,
                "pagerank": round(pagerank_data.get(n, 0), 6),
                "betweenness": round(betweenness_data.get(n, 0), 6),
                "total_sent": attrs.get("total_sent", 0),
                "total_received": attrs.get("total_received", 0),
                "channels": list(attrs.get("channels", set())),
            }
            if n in ml_scores:
                nd["if_score"] = ml_scores[n]["if_score"]
                nd["xgb_score"] = ml_scores[n]["xgb_score"]
            nodes_viz.append(nd)

        edges_viz = []
        for u, v, d in graph.edges(data=True):
            channel = d.get("channel", "")
            edges_viz.append(
                {
                    "source": u,
                    "target": v,
                    "amount": d.get("amount", 0),
                    "channel": channel,
                    "color": CHANNEL_COLORS.get(channel, "#888780"),
                    "timestamp": str(d.get("timestamp", ""))
                    if d.get("timestamp")
                    else None,
                }
            )

        # Store graph reference for later Neo4j sync
        self._last_graph = graph

        # Best-effort Neo4j sync (non-blocking for the pipeline)
        if sync_neo4j:
            try:
                from app.graph_store.neo4j_store import sync_graph_to_neo4j

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule as background task — don't block the pipeline
                    asyncio.ensure_future(sync_graph_to_neo4j(graph))
                else:
                    loop.run_until_complete(sync_graph_to_neo4j(graph))
            except Exception as exc:
                import logging

                logging.getLogger(__name__).warning("Neo4j sync skipped: %s", exc)

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
            "advanced_detection": {
                "tarjan_sccs": len(tarjan_sccs),
                "fraud_rings": len(fraud_rings),
                "centrality_top": {
                    "pagerank": top_pr[:5] if top_pr else [],
                    "betweenness": top_bw[:5] if top_bw else [],
                },
                "dormant_motifs": len(dormant_motifs),
                "profile_mismatches": len(mismatches),
            },
            "ml_info": {
                "feature_importance": feature_importance,
                "model_status": {
                    "isolation_forest": "trained",
                    "xgboost": "trained" if ml_detector.xgb_model else "heuristic",
                },
            },
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
        ml_scores: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> AlertBase:
        if edge_labels is None:
            edge_labels = [
                f"{e.get('sender_id', '?')}->{e.get('receiver_id', '?')}" for e in edges
            ]
        explanation = report_agent.generate_sar_draft(score_data, edges)

        # Compute average ML scores across alert nodes
        avg_if = 0.0
        avg_xgb = 0.0
        if ml_scores:
            if_vals = [ml_scores.get(n, {}).get("if_score", 0) for n in nodes]
            xgb_vals = [ml_scores.get(n, {}).get("xgb_score", 0) for n in nodes]
            avg_if = sum(if_vals) / len(if_vals) if if_vals else 0
            avg_xgb = sum(xgb_vals) / len(xgb_vals) if xgb_vals else 0

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
            if_score=round(avg_if, 4),
            xgb_score=round(avg_xgb, 4),
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
