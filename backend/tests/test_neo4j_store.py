import os
import pytest
import pytest_asyncio
import networkx as nx

# Point to unreachable Neo4j
os.environ["NEO4J_URI"] = "bolt://localhost:19999"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "wrong"

from app.graph_store.neo4j_store import (
    init_neo4j,
    close_neo4j,
    _driver,
    _ensure_driver,
    _serialize_node_attrs,
    sync_graph_to_neo4j,
    run_cypher,
    get_node_neighbors,
    get_graph_stats,
    clear_graph,
)


@pytest_asyncio.fixture(autouse=True)
async def setup():
    """Reset driver state before each test."""
    import app.graph_store.neo4j_store as ns

    ns._driver = None
    yield
    ns._driver = None


@pytest.mark.asyncio
async def test_init_neo4j_unavailable():
    """init_neo4j with unreachable server should set _driver to None."""
    await init_neo4j()
    import app.graph_store.neo4j_store as ns

    assert ns._driver is None


@pytest.mark.asyncio
async def test_ensure_driver_raises_when_none():
    """_ensure_driver raises RuntimeError when driver is None."""
    with pytest.raises(RuntimeError, match="not initialised"):
        _ensure_driver()


@pytest.mark.asyncio
async def test_close_neo4j_when_none():
    """close_neo4j when driver is None should not raise."""
    await close_neo4j()


@pytest.mark.asyncio
async def test_serialize_node_attrs():
    """_serialize_node_attrs correctly serializes node attributes."""
    from datetime import datetime

    attrs = {
        "type": "Account",
        "is_suspect": True,
        "total_sent": 50000.0,
        "total_received": 30000.0,
        "channels": {"UPI", "NEFT"},
        "first_seen": datetime(2026, 1, 15, 10, 30, 0),
        "last_seen": datetime(2026, 3, 20, 14, 0, 0),
    }
    result = _serialize_node_attrs(attrs)
    assert result["type"] == "Account"
    assert result["is_suspect"] is True
    assert result["total_sent"] == 50000.0
    assert result["total_received"] == 30000.0
    assert set(result["channels"]) == {"UPI", "NEFT"}
    assert result["first_seen"] == "2026-01-15T10:30:00"
    assert result["last_seen"] == "2026-03-20T14:00:00"


@pytest.mark.asyncio
async def test_serialize_node_attrs_defaults():
    """_serialize_node_attrs handles missing attributes gracefully."""
    result = _serialize_node_attrs({})
    assert result["type"] == "Account"
    assert result["is_suspect"] is False
    assert result["total_sent"] == 0.0
    assert result["total_received"] == 0.0
    assert result["channels"] == []
    assert result["first_seen"] is None
    assert result["last_seen"] is None


@pytest.mark.asyncio
async def test_serialize_node_attrs_string_timestamps():
    """_serialize_node_attrs handles string timestamps."""
    result = _serialize_node_attrs(
        {
            "first_seen": "2026-01-01T00:00:00",
            "last_seen": "2026-12-31T23:59:59",
        }
    )
    assert result["first_seen"] == "2026-01-01T00:00:00"
    assert result["last_seen"] == "2026-12-31T23:59:59"


@pytest.mark.asyncio
async def test_sync_graph_raises_when_no_driver():
    """sync_graph_to_neo4j raises RuntimeError when driver is None."""
    graph = nx.MultiDiGraph()
    graph.add_node("A", type="Account")
    with pytest.raises(RuntimeError):
        await sync_graph_to_neo4j(graph)


@pytest.mark.asyncio
async def test_run_cypher_raises_when_no_driver():
    """run_cypher raises RuntimeError when driver is None."""
    with pytest.raises(RuntimeError):
        await run_cypher("MATCH (n) RETURN n")


@pytest.mark.asyncio
async def test_get_node_neighbors_raises_when_no_driver():
    """get_node_neighbors raises RuntimeError when driver is None."""
    with pytest.raises(RuntimeError):
        await get_node_neighbors("A")


@pytest.mark.asyncio
async def test_get_graph_stats_raises_when_no_driver():
    """get_graph_stats raises RuntimeError when driver is None."""
    with pytest.raises(RuntimeError):
        await get_graph_stats()


@pytest.mark.asyncio
async def test_clear_graph_raises_when_no_driver():
    """clear_graph raises RuntimeError when driver is None."""
    with pytest.raises(RuntimeError):
        await clear_graph()
