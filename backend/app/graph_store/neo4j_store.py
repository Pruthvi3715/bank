import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

import networkx as nx
from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)

_driver: Optional[AsyncDriver] = None


async def init_neo4j() -> None:
    """Create the Neo4j async driver and verify connectivity."""
    global _driver
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "graphsentinel123")
    try:
        _driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        await _driver.verify_connectivity()
        logger.info("Neo4j connected: %s", uri)
    except Exception as exc:
        logger.warning("Neo4j unavailable (%s) — graph store disabled", exc)
        _driver = None


async def close_neo4j() -> None:
    """Close the Neo4j driver."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


def _ensure_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised — call init_neo4j() first")
    return _driver


# ---------------------------------------------------------------------------
# Graph sync
# ---------------------------------------------------------------------------


def _serialize_node_attrs(attrs: dict) -> dict:
    """Prepare node attributes for Neo4j storage."""
    channels = attrs.get("channels", set())
    if isinstance(channels, set):
        channels = sorted(channels)

    first_seen = attrs.get("first_seen")
    last_seen = attrs.get("last_seen")

    return {
        "type": attrs.get("type", "Account"),
        "is_suspect": bool(attrs.get("is_suspect", False)),
        "total_sent": float(attrs.get("total_sent", 0.0)),
        "total_received": float(attrs.get("total_received", 0.0)),
        "channels": list(channels) if channels else [],
        "first_seen": first_seen.isoformat()
        if hasattr(first_seen, "isoformat")
        else str(first_seen)
        if first_seen
        else None,
        "last_seen": last_seen.isoformat()
        if hasattr(last_seen, "isoformat")
        else str(last_seen)
        if last_seen
        else None,
    }


async def sync_graph_to_neo4j(graph: nx.MultiDiGraph) -> dict:
    """
    Persist a NetworkX MultiDiGraph into Neo4j.

    - Wipes existing data
    - Creates uniqueness constraint on Account.node_id
    - Batch-creates nodes via UNWIND
    - Batch-creates edges via UNWIND

    Returns sync stats.
    """
    driver = _ensure_driver()
    t0 = time.time()

    async with driver.session() as session:
        # Clear existing data
        await session.run("MATCH (n) DETACH DELETE n")

        # Create constraint (idempotent)
        try:
            await session.run(
                "CREATE CONSTRAINT account_node_id IF NOT EXISTS "
                "FOR (a:Account) REQUIRE a.node_id IS UNIQUE"
            )
        except Exception:
            # Older Neo4j may not support IF NOT EXISTS
            try:
                await session.run(
                    "CREATE CONSTRAINT account_node_id "
                    "FOR (a:Account) REQUIRE a.node_id IS UNIQUE"
                )
            except Exception:
                pass

        # Batch-create nodes
        node_list = []
        for node_id in graph.nodes():
            attrs = graph.nodes[node_id]
            entry = {"node_id": str(node_id)}
            entry.update(_serialize_node_attrs(attrs))
            node_list.append(entry)

        nodes_created = 0
        if node_list:
            result = await session.run(
                "UNWIND $nodes AS n "
                "CREATE (a:Account {node_id: n.node_id}) "
                "SET a.type = n.type, "
                "    a.is_suspect = n.is_suspect, "
                "    a.total_sent = n.total_sent, "
                "    a.total_received = n.total_received, "
                "    a.channels = n.channels, "
                "    a.first_seen = n.first_seen, "
                "    a.last_seen = n.last_seen",
                nodes=node_list,
            )
            summary = await result.consume()
            nodes_created = summary.counters.nodes_created

        # Batch-create edges
        edge_list = []
        for u, v, data in graph.edges(data=True):
            timestamp = data.get("timestamp")
            edge_list.append(
                {
                    "sender_id": str(u),
                    "receiver_id": str(v),
                    "txn_id": str(data.get("txn_id", "")),
                    "amount": float(data.get("amount", 0)),
                    "timestamp": timestamp.isoformat()
                    if hasattr(timestamp, "isoformat")
                    else str(timestamp)
                    if timestamp
                    else None,
                    "channel": str(data.get("channel", "")),
                }
            )

        edges_created = 0
        if edge_list:
            result = await session.run(
                "UNWIND $edges AS e "
                "MATCH (s:Account {node_id: e.sender_id}) "
                "MATCH (r:Account {node_id: e.receiver_id}) "
                "CREATE (s)-[t:TRANSFER {txn_id: e.txn_id}]->(r) "
                "SET t.amount = e.amount, "
                "    t.timestamp = e.timestamp, "
                "    t.channel = e.channel",
                edges=edge_list,
            )
            summary = await result.consume()
            edges_created = summary.counters.relationships_created

    sync_time_ms = round((time.time() - t0) * 1000)
    stats = {
        "nodes_created": nodes_created,
        "edges_created": edges_created,
        "sync_time_ms": sync_time_ms,
    }
    logger.info("Neo4j sync complete: %s", stats)
    return stats


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


async def run_cypher(query: str, params: Optional[dict] = None) -> List[dict]:
    """Execute an arbitrary Cypher query and return rows as dicts."""
    driver = _ensure_driver()
    async with driver.session() as session:
        result = await session.run(query, params or {})
        records = [dict(r) async for r in result]
        return records


async def get_node_neighbors(node_id: str, depth: int = 1) -> dict:
    """Return a node and its neighbours up to *depth* hops."""
    driver = _ensure_driver()
    depth = max(1, min(depth, 5))
    query = (
        "MATCH path = (a:Account {node_id: $node_id})-[*1..{depth}]-(b:Account) "
        "RETURN DISTINCT a AS center, "
        "       [n IN nodes(path) | properties(n)] AS neighbors, "
        "       [r IN relationships(path) | properties(r)] AS relationships"
    ).format(depth=depth)
    async with driver.session() as session:
        result = await session.run(query, {"node_id": node_id})
        rows = [dict(r) async for r in result]
        if not rows:
            # Check if node exists at all
            check = await session.run(
                "MATCH (a:Account {node_id: $node_id}) RETURN a",
                {"node_id": node_id},
            )
            rec = [dict(r) async for r in check]
            if not rec:
                return {"found": False, "node_id": node_id}
            return {
                "found": True,
                "node_id": node_id,
                "neighbors": [],
                "relationships": [],
            }
        return {"found": True, "node_id": node_id, "results": rows}


async def get_graph_stats() -> dict:
    """Return node/edge counts and top-10 nodes by degree."""
    driver = _ensure_driver()
    async with driver.session() as session:
        counts = await session.run(
            "MATCH (n) "
            "WITH count(n) AS node_count "
            "OPTIONAL MATCH ()-[r]->() "
            "RETURN node_count, count(r) AS edge_count"
        )
        row = [dict(r) async for r in counts]
        node_count = row[0]["node_count"] if row else 0
        edge_count = row[0]["edge_count"] if row else 0

        top = await session.run(
            "MATCH (a:Account) "
            "WITH a, size((a)--()) AS degree "
            "RETURN a.node_id AS node_id, degree "
            "ORDER BY degree DESC LIMIT 10"
        )
        top_nodes = [dict(r) async for r in top]

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "top_nodes_by_degree": top_nodes,
    }


async def clear_graph() -> dict:
    """Wipe all graph data from Neo4j."""
    driver = _ensure_driver()
    async with driver.session() as session:
        result = await session.run("MATCH (n) DETACH DELETE n")
        summary = await result.consume()
    return {
        "nodes_deleted": summary.counters.nodes_deleted,
        "relationships_deleted": summary.counters.relationships_deleted,
    }
