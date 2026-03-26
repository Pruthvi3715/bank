import asyncio
import io
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    Response,
    WebSocket,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.schemas import TransactionBase
from app.pipeline.orchestrator import DetectionOrchestrator, get_pending_activities
from app import adversarial
from app.feedback_store import (
    add_decision,
    get_decisions,
    get_scorer_config,
    init_db,
    close_db,
)
from app.sar_chatbot import (
    cache_pipeline_result,
    generate_chat_response,
    get_alert_by_id,
    get_cached_result,
    QUICK_QUESTIONS,
)
from app.cache.redis_cache import init_redis, close_redis, cache_set, cache_get
from app.export.pdf_export import generate_alert_pdf
from app.export.summary_pdf import generate_project_summary_pdf
from app.events.consumer import (
    start_streaming,
    stop_streaming,
    _BOOTSTRAP_SERVERS,
    _BATCH_SIZE,
    _BATCH_TIMEOUT_SEC,
    _running,
    _txn_buffer,
    _ENABLE_STREAMING,
)
from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    oauth2_scheme,
    require_role,
    Token,
    User,
)
from app.graph_store.neo4j_store import (
    init_neo4j,
    close_neo4j,
    sync_graph_to_neo4j,
    run_cypher,
    get_node_neighbors,
    get_graph_stats,
)

app = FastAPI(
    title="GraphSentinel API",
    description="AI-Powered Fund Flow Fraud Detection API",
    version="1.0.0",
)


_activity_poll_task: Optional[asyncio.Task] = None


async def _poll_activity_queue() -> None:
    """Poll the orchestrator activity queue and broadcast each event to all WS clients."""
    while True:
        await asyncio.sleep(0.3)
        try:
            events = get_pending_activities()
            for evt in events:
                await broadcast_agent_event(
                    agent=evt["agent"],
                    status="active",
                    message=evt["message"],
                )
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    await init_neo4j()
    streaming_task = await start_streaming()
    global _activity_poll_task
    _activity_poll_task = asyncio.create_task(_poll_activity_queue())
    yield
    if _activity_poll_task:
        _activity_poll_task.cancel()
        try:
            await _activity_poll_task
        except Exception:
            pass
    await stop_streaming()
    await close_neo4j()
    await close_db()
    await close_redis()
    if streaming_task:
        try:
            streaming_task.cancel()
        except Exception:
            pass


app.router.lifespan_context = lifespan


# ── WebSocket for Live Agent Activity ────────────────────────────────────────
_active_ws_clients: set = set()


@app.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    await websocket.accept()
    _active_ws_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "flush":
                events = get_pending_activities()
                for evt in events:
                    payload = json.dumps(
                        {"agent": evt["agent"], "message": evt["message"]}
                    )
                    await websocket.send_text(payload)
    except Exception:
        pass
    finally:
        _active_ws_clients.discard(websocket)


async def broadcast_agent_event(agent: str, status: str, message: str, **extra):
    payload = json.dumps(
        {"agent": agent, "status": status, "message": message, **extra}
    )
    dead = set()
    for ws in list(_active_ws_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _active_ws_clients.discard(ws)


# ── CORS ───────────────────────────────────────────────────────────────────────
allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,"
    "http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002,"
    "http://192.168.1.102:3000,http://0.0.0.0:3000",
)
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Orchestrator ────────────────────────────────────────────────────────
orchestrator = DetectionOrchestrator()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _is_demo_mode() -> bool:
    return str(os.getenv("DEMO_MODE", "")).strip().lower() in {"1", "true", "yes", "on"}


def _load_demo_cache(name: str = "demo_track_a") -> dict:
    cache_dir = Path(__file__).resolve().parents[1] / "demo_cache"
    path = cache_dir / f"{name}.json"
    if not path.exists():
        return {
            "alerts": [],
            "graph": {"nodes": [], "links": []},
            "stats": {
                "total_txns": 0,
                "total_nodes": 0,
                "total_edges": 0,
                "alerts_generated": 0,
                "pattern_counts": {},
            },
            "agent_activity": [
                {"agent": "Demo", "message": f"DEMO_MODE but cache not found: {path}"}
            ],
        }
    with open(path, encoding="utf-8") as f:
        return json.load(f)


async def _load_demo_cache_async(name: str = "demo_track_a") -> dict:
    """Load demo cache, checking Redis first before falling back to file."""
    redis_key = f"demo:{name}"
    cached = await cache_get(redis_key)
    if cached is not None:
        return cached
    result = _load_demo_cache(name)
    await cache_set(redis_key, result, ttl=86400)
    return result


def _parse_datetime(value) -> datetime:
    try:
        return pd.to_datetime(value, utc=False).to_pydatetime()
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid timestamp: {value}"
        ) from exc


def _rows_to_transactions(df: pd.DataFrame) -> list[TransactionBase]:
    required = {"sender_id", "receiver_id", "amount", "timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(sorted(missing))}",
        )
    transactions: list[TransactionBase] = []
    for row in df.to_dict(orient="records"):
        amount = float(row["amount"])
        txn = TransactionBase(
            txn_id=str(row.get("txn_id") or uuid.uuid4()),
            sender_id=str(row["sender_id"]).strip(),
            receiver_id=str(row["receiver_id"]).strip(),
            amount=amount,
            timestamp=_parse_datetime(row["timestamp"]),
            channel=str(row.get("channel") or "UPI").strip().upper(),
            account_type=str(row.get("account_type") or "Savings").strip(),
            device_id=str(row["device_id"]).strip() if row.get("device_id") else None,
            ip_address=str(row["ip_address"]).strip()
            if row.get("ip_address")
            else None,
        )
        transactions.append(txn)
    if not transactions:
        raise HTTPException(
            status_code=400, detail="CSV did not contain any transactions"
        )
    return transactions


# ── Auth Endpoints ─────────────────────────────────────────────────────────────
class LoginForm(BaseModel):
    username: str
    password: str


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: LoginForm):
    """
    OAuth2-compatible token endpoint.
    Returns a JWT Bearer token for authenticated requests.
    Demo credentials:
      - investigator / investigate123  (role: investigator)
      - senior_analyst / analyst456    (role: senior_analyst)
      - readonly / readonly789         (role: readonly)
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user["user_id"], "role": user["role"]},
        expires_delta=timedelta(minutes=480),
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/auth/me", response_model=User)
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """Return the current authenticated user's profile."""
    return current_user


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# ── Demo Endpoints ────────────────────────────────────────────────────────────
@app.get("/api/demo-track-a")
async def demo_track_a():
    """Track A: Guaranteed demo path. Returns pre-cached result (no live LLM)."""
    cache_name = os.getenv("DEMO_CACHE_NAME", "demo_track_a")
    result = await _load_demo_cache_async(cache_name)
    cache_pipeline_result(result)
    return result


@app.get("/api/adversarial-test")
def adversarial_test(test: Optional[str] = None):
    """
    Adversarial Test Mode. Use ?test=<name> for single test.
    Options: cycle_plus_hop | split_hub | time_distributed_smurfing | all
    """
    if test == "cycle_plus_hop":
        return adversarial.run_cycle_plus_hop_test()
    if test == "split_hub":
        return adversarial.run_split_hub_test()
    if test == "time_distributed_smurfing":
        return adversarial.run_time_distributed_smurfing_test()
    if test is None or test == "all":
        return adversarial.run_all_adversarial_tests()
    raise HTTPException(
        status_code=400,
        detail="Use ?test=cycle_plus_hop|split_hub|time_distributed_smurfing|all",
    )


# ── Pipeline ──────────────────────────────────────────────────────────────────
@app.post("/api/run-pipeline")
async def run_pipeline(
    current_user: User = Depends(require_role(["investigator", "senior_analyst"])),
):
    """Run the fraud detection pipeline. Requires investigator or senior_analyst role."""
    scorer_config = await get_scorer_config()
    if _is_demo_mode():
        result = await _load_demo_cache_async(
            os.getenv("DEMO_CACHE_NAME", "demo_track_a")
        )
    else:
        import asyncio

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: orchestrator.run_detection_pipeline(scorer_config=scorer_config),
        )
    cache_pipeline_result(result)
    await cache_set("pipeline:latest", result, ttl=7200)
    return result


@app.post("/api/run-pipeline-csv")
async def run_pipeline_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["investigator", "senior_analyst"])),
):
    """Upload a CSV file and run the pipeline on it. Requires investigator or senior_analyst role."""
    if _is_demo_mode():
        result = _load_demo_cache(os.getenv("DEMO_CACHE_NAME", "demo_track_a"))
        cache_pipeline_result(result)
        return result
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty")
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to parse CSV file") from exc
    transactions = _rows_to_transactions(df)
    scorer_config = await get_scorer_config()
    result = orchestrator.run_detection_pipeline(
        transactions=transactions, scorer_config=scorer_config
    )
    cache_pipeline_result(result)
    await cache_set("pipeline:latest", result, ttl=7200)
    return result


@app.post("/api/run-pipeline-csv/stream")
async def stream_csv_to_kafka(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["investigator", "senior_analyst"])),
):
    """
    Upload a CSV and stream each row as a Kafka event to graphsentinel.transactions.raw.
    The Kafka consumer will batch and run detection automatically.
    Returns the number of transactions streamed.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty")

    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to parse CSV file") from exc

    try:
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(
            bootstrap_servers=_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        await producer.start()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Kafka/Redpanda not available. Set KAFKA_ENABLE_STREAMING=true and ensure REDPANDA_BROKERS is configured.",
        )

    transactions = _rows_to_transactions(df)
    sent = 0
    try:
        for txn in transactions:
            await producer.send(
                "graphsentinel.transactions.raw",
                value=txn.model_dump(mode="json"),
            )
            sent += 1
    finally:
        await producer.stop()

    return {
        "status": "streamed",
        "count": sent,
        "topic": "graphsentinel.transactions.raw",
        "note": "Kafka consumer will batch and run detection automatically",
    }


@app.get("/api/streaming/status")
def get_streaming_status(
    current_user: User = Depends(
        require_role(["investigator", "senior_analyst", "readonly"])
    ),
):
    """Check if Kafka streaming consumer is active and configured."""
    return {
        "streaming_enabled": _ENABLE_STREAMING,
        "consumer_active": _running,
        "buffer_size": len(_txn_buffer),
        "batch_size": _BATCH_SIZE,
        "batch_timeout_sec": _BATCH_TIMEOUT_SEC,
    }


# ── Feedback ──────────────────────────────────────────────────────────────────
class FeedbackBody(BaseModel):
    alert_id: str
    decision: str
    confidence: int
    pattern_type: str = ""
    notes: str = ""


@app.post("/api/feedback")
async def submit_feedback(
    body: FeedbackBody,
    current_user: User = Depends(require_role(["investigator", "senior_analyst"])),
):
    """
    Submit investigator feedback for an alert.
    Requires investigator or senior_analyst role.
    """
    if body.decision not in ("confirmed_fraud", "false_positive", "unclear"):
        raise HTTPException(
            status_code=400,
            detail="decision must be confirmed_fraud | false_positive | unclear",
        )
    if not 1 <= body.confidence <= 5:
        raise HTTPException(status_code=400, detail="confidence must be 1-5")
    return await add_decision(
        alert_id=body.alert_id,
        decision=body.decision,
        confidence=body.confidence,
        pattern_type=body.pattern_type or "",
        notes=body.notes or "",
    )


@app.get("/api/feedback/config")
async def get_feedback_config():
    return await get_scorer_config()


@app.get("/api/feedback/decisions")
async def list_feedback_decisions(alert_id: Optional[str] = None):
    return await get_decisions(alert_id=alert_id)


# ── SAR Chatbot ────────────────────────────────────────────────────────────────
class SARChatRequest(BaseModel):
    alert_id: str
    message: str
    history: list = []


@app.post("/api/sar-chat")
def sar_chat(
    body: SARChatRequest,
    current_user: User = Depends(get_current_active_user),
):
    """SAR Chatbot: Conversational investigation. Available to all authenticated users."""
    response = generate_chat_response(
        alert_id=body.alert_id,
        message=body.message,
        history=body.history,
    )
    return {"response": response, "alert_id": body.alert_id}


@app.get("/api/sar-chat/quick-questions")
def get_quick_questions():
    return {"questions": QUICK_QUESTIONS}


@app.get("/api/sar/{alert_id}/pdf")
def export_alert_pdf(
    alert_id: str,
    current_user: User = Depends(require_role(["investigator", "senior_analyst"])),
):
    """Generate a FIU-IND formatted PDF SAR report. Requires investigator or senior_analyst role."""
    alert = get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    try:
        pdf_bytes = generate_alert_pdf(alert)
        filename = (
            f"GraphSentinel_SAR_{alert_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")


@app.get("/api/project-summary.pdf")
def download_project_summary(
    current_user: User = Depends(
        require_role(["investigator", "senior_analyst", "readonly"])
    ),
):
    """Download one-page project summary PDF for hackathon submission."""
    try:
        pdf_bytes = generate_project_summary_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="GraphSentinel_Project_Summary.pdf"'
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")


# ── Node & Graph ───────────────────────────────────────────────────────────────
@app.get("/api/node/{node_id}")
def get_node_detail(node_id: str):
    cached = get_cached_result()
    if not cached:
        raise HTTPException(status_code=404, detail="Run the pipeline first")
    nodes = cached.get("graph", {}).get("nodes", [])
    node_info = next((n for n in nodes if n.get("id") == node_id), None)
    if not node_info:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    involved_alerts = [
        {
            "alert_id": a["alert_id"],
            "pattern_type": a["pattern_type"],
            "risk_score": a["risk_score"],
            "disposition": a["disposition"],
        }
        for a in cached.get("alerts", [])
        if node_id in a.get("subgraph_nodes", [])
    ]
    edges = cached.get("graph", {}).get("links", [])
    connected = [
        e for e in edges if e.get("source") == node_id or e.get("target") == node_id
    ]
    return {
        **node_info,
        "involved_alerts": involved_alerts,
        "connected_edges": connected[:20],
        "connection_count": len(connected),
    }


@app.get("/api/ml-info")
def get_ml_info():
    cached = get_cached_result() or {}
    ml_info = cached.get("ml_info", {})
    if not ml_info:
        ml_info = {
            "feature_importance": {
                "in_degree": 0.08,
                "out_degree": 0.09,
                "in_out_ratio": 0.15,
                "total_in": 0.12,
                "total_out": 0.11,
                "channel_mix": 0.10,
                "off_hours_ratio": 0.13,
                "dormancy_days": 0.07,
                "txn_count": 0.06,
                "amount_variance": 0.09,
            },
            "model_status": {
                "isolation_forest": "pending",
                "xgboost": "pending",
            },
        }
    return ml_info


# ── Neo4j Graph Endpoints ──────────────────────────────────────────────────────
@app.post("/api/graph/sync")
async def graph_sync(
    current_user: User = Depends(require_role(["investigator", "senior_analyst"])),
):
    """Sync the latest pipeline graph to Neo4j. Requires investigator or senior_analyst role."""
    graph = orchestrator._last_graph
    if graph is None:
        raise HTTPException(
            status_code=404,
            detail="No pipeline graph available. Run the pipeline first.",
        )
    try:
        stats = await sync_graph_to_neo4j(graph)
        return {"status": "synced", **stats}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j sync failed: {exc}")


class CypherQuery(BaseModel):
    query: str
    params: Optional[dict] = None


@app.post("/api/graph/query")
async def graph_query(
    body: CypherQuery,
    current_user: User = Depends(require_role(["investigator", "senior_analyst"])),
):
    """Run an arbitrary Cypher query against the Neo4j graph store. Requires investigator or senior_analyst role."""
    # Block destructive queries from the exploration endpoint
    lowered = body.query.strip().lower()
    if any(
        kw in lowered
        for kw in ("detach delete", "drop ", "create constraint", "create index")
    ):
        raise HTTPException(
            status_code=400,
            detail="Destructive queries are not allowed via this endpoint.",
        )
    try:
        results = await run_cypher(body.query, body.params)
        return {"results": results, "count": len(results)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Cypher query failed: {exc}")


@app.get("/api/graph/node/{node_id}/neighbors")
async def graph_node_neighbors(
    node_id: str,
    depth: int = 1,
    current_user: User = Depends(
        require_role(["investigator", "senior_analyst", "readonly"])
    ),
):
    """Get a node's neighbours from Neo4j up to *depth* hops (max 5)."""
    depth = max(1, min(depth, 5))
    try:
        data = await get_node_neighbors(node_id, depth)
        return data
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j query failed: {exc}")


@app.get("/api/graph/stats")
async def graph_stats_endpoint(
    current_user: User = Depends(
        require_role(["investigator", "senior_analyst", "readonly"])
    ),
):
    """Return Neo4j graph statistics (node/edge counts, top nodes by degree)."""
    try:
        stats = await get_graph_stats()
        return stats
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j query failed: {exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
