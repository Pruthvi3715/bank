import os
import pytest
import pytest_asyncio

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_api.db"
os.environ["REDIS_URL"] = "redis://localhost:19999"
os.environ["NEO4J_URI"] = "bolt://localhost:19999"
os.environ["DEMO_MODE"] = "false"
os.environ["KAFKA_ENABLE_STREAMING"] = "false"
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

from httpx import AsyncClient, ASGITransport
from app.main import app, lifespan


@pytest_asyncio.fixture
async def client():
    """Create an async test client with manually managed lifespan."""
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest_asyncio.fixture
async def auth_token(client):
    """Get a JWT token for authenticated requests."""
    resp = await client.post(
        "/token",
        json={
            "username": "investigator",
            "password": "investigate123",
        },
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """Return Authorization headers dict."""
    return {"Authorization": f"Bearer {auth_token}"}


# ── Health ──
@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


# ── Feedback Endpoints ──
@pytest.mark.asyncio
async def test_feedback_submit(client, auth_headers):
    resp = await client.post(
        "/api/feedback",
        json={
            "alert_id": "test-alert-001",
            "decision": "confirmed_fraud",
            "confidence": 5,
            "pattern_type": "Cycle",
            "notes": "Clear round-tripping",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


@pytest.mark.asyncio
async def test_feedback_false_positive_updates_config(client, auth_headers):
    resp = await client.post(
        "/api/feedback",
        json={
            "alert_id": "test-alert-002",
            "decision": "false_positive",
            "confidence": 5,
            "pattern_type": "Smurfing",
            "notes": "Legit payroll",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    config_resp = await client.get("/api/feedback/config")
    assert config_resp.status_code == 200
    config = config_resp.json()
    assert "Smurfing" in config
    assert config["Smurfing"]["gst_discount_pct"] >= 28.0


@pytest.mark.asyncio
async def test_feedback_decisions_list(client, auth_headers):
    # Submit a decision first
    await client.post(
        "/api/feedback",
        json={
            "alert_id": "test-alert-003",
            "decision": "unclear",
            "confidence": 2,
            "pattern_type": "HubAndSpoke",
            "notes": "",
        },
        headers=auth_headers,
    )

    resp = await client.get("/api/feedback/decisions")
    assert resp.status_code == 200
    decisions = resp.json()
    assert isinstance(decisions, list)
    assert len(decisions) >= 1


@pytest.mark.asyncio
async def test_feedback_decisions_filter(client, auth_headers):
    await client.post(
        "/api/feedback",
        json={
            "alert_id": "filter-test-001",
            "decision": "confirmed_fraud",
            "confidence": 4,
            "pattern_type": "Cycle",
            "notes": "",
        },
        headers=auth_headers,
    )

    resp = await client.get("/api/feedback/decisions?alert_id=filter-test-001")
    assert resp.status_code == 200
    decisions = resp.json()
    assert all(d["alert_id"] == "filter-test-001" for d in decisions)


@pytest.mark.asyncio
async def test_feedback_invalid_decision(client, auth_headers):
    resp = await client.post(
        "/api/feedback",
        json={
            "alert_id": "test-invalid",
            "decision": "bad_value",
            "confidence": 3,
            "pattern_type": "Cycle",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_feedback_invalid_confidence(client, auth_headers):
    resp = await client.post(
        "/api/feedback",
        json={
            "alert_id": "test-invalid-conf",
            "decision": "confirmed_fraud",
            "confidence": 10,
            "pattern_type": "Cycle",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_feedback_unauthorized(client):
    """Feedback without auth token should return 401."""
    resp = await client.post(
        "/api/feedback",
        json={
            "alert_id": "test-noauth",
            "decision": "confirmed_fraud",
            "confidence": 3,
            "pattern_type": "Cycle",
        },
    )
    assert resp.status_code in (401, 403)


# ── Graph Endpoints ──
@pytest.mark.asyncio
async def test_graph_sync_no_pipeline(client, auth_headers):
    """Graph sync without running pipeline should return 404."""
    import app.main as m

    old_graph = m.orchestrator._last_graph
    m.orchestrator._last_graph = None

    resp = await client.post("/api/graph/sync", headers=auth_headers)
    assert resp.status_code == 404

    m.orchestrator._last_graph = old_graph


@pytest.mark.asyncio
async def test_graph_query_blocks_destructive(client, auth_headers):
    """Destructive Cypher queries should be blocked."""
    resp = await client.post(
        "/api/graph/query",
        json={
            "query": "MATCH (n) DETACH DELETE n",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Destructive" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_graph_query_blocks_drop(client, auth_headers):
    resp = await client.post(
        "/api/graph/query",
        json={
            "query": "DROP CONSTRAINT foo",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_graph_stats_no_neo4j(client, auth_headers):
    """Graph stats should return 503 when Neo4j is unavailable."""
    resp = await client.get("/api/graph/stats", headers=auth_headers)
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_graph_node_neighbors_no_neo4j(client, auth_headers):
    """Node neighbors should return 503 when Neo4j is unavailable."""
    resp = await client.get("/api/graph/node/A123/neighbors", headers=auth_headers)
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_graph_endpoints_unauthorized(client):
    """Graph endpoints without auth should return 401/403."""
    resp = await client.post("/api/graph/sync")
    assert resp.status_code in (401, 403)

    resp = await client.post("/api/graph/query", json={"query": "MATCH (n) RETURN n"})
    assert resp.status_code in (401, 403)


# ── Pipeline Endpoints ──
@pytest.mark.asyncio
async def test_run_pipeline(client, auth_headers):
    """Run the pipeline and verify it returns expected structure."""
    resp = await client.post("/api/run-pipeline", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert "graph" in data
    assert "stats" in data
    assert "agent_activity" in data
    assert "nodes" in data["graph"]
    assert "links" in data["graph"]


@pytest.mark.asyncio
async def test_pipeline_caches_to_redis(client, auth_headers):
    """After pipeline runs, pipeline:latest should be in cache."""
    await client.post("/api/run-pipeline", headers=auth_headers)
    from app.cache.redis_cache import cache_get

    cached = await cache_get("pipeline:latest")
    assert cached is not None
    assert "alerts" in cached


# ── Demo Endpoints ──
@pytest.mark.asyncio
async def test_demo_track_a(client):
    """Demo endpoint should return cached result."""
    resp = await client.get("/api/demo-track-a")
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert "graph" in data


# ── Auth Endpoints ──
@pytest.mark.asyncio
async def test_login_valid(client):
    resp = await client.post(
        "/token",
        json={
            "username": "investigator",
            "password": "investigate123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid(client):
    resp = await client.post(
        "/token",
        json={
            "username": "wrong",
            "password": "wrong",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_me(client, auth_headers):
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "investigator"
    assert data["role"] == "investigator"
