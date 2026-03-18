import io
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import BaseModel
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import TransactionBase
from app.pipeline.orchestrator import DetectionOrchestrator
from app import adversarial
from app.feedback_store import add_decision, get_decisions, get_scorer_config

app = FastAPI(
    title="GraphSentinel API", description="AI-Powered Fund Flow Fraud Detection API"
)

allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = DetectionOrchestrator()


def _is_demo_mode() -> bool:
    return str(os.getenv("DEMO_MODE", "")).strip().lower() in {"1", "true", "yes", "on"}


def _load_demo_cache(name: str = "demo_track_a") -> dict:
    """
    Load a full cached pipeline response for demo reliability.

    Cache location: backend/demo_cache/<name>.json
    """
    cache_dir = Path(__file__).resolve().parents[2] / "demo_cache"
    path = cache_dir / f"{name}.json"
    if not path.exists():
        return {
            "alerts": [],
            "graph": {"nodes": [], "links": []},
            "stats": {"total_txns": 0, "total_nodes": 0, "total_edges": 0, "alerts_generated": 0, "pattern_counts": {}},
            "agent_activity": [{"agent": "Demo", "message": f"DEMO_MODE enabled but cache file not found: {path}"}],
        }
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _parse_datetime(value) -> datetime:
    try:
        return pd.to_datetime(value, utc=False).to_pydatetime()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp value: {value}") from exc


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
        amount = row.get("amount")
        try:
            amount = float(amount)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid amount value: {amount}") from exc

        txn = TransactionBase(
            txn_id=str(row.get("txn_id") or uuid.uuid4()),
            sender_id=str(row["sender_id"]).strip(),
            receiver_id=str(row["receiver_id"]).strip(),
            amount=amount,
            timestamp=_parse_datetime(row["timestamp"]),
            channel=str(row.get("channel") or "UPI").strip().upper(),
            account_type=str(row.get("account_type") or "Savings").strip(),
            device_id=(str(row["device_id"]).strip() if row.get("device_id") else None),
            ip_address=(str(row["ip_address"]).strip() if row.get("ip_address") else None),
        )
        transactions.append(txn)

    if not transactions:
        raise HTTPException(status_code=400, detail="CSV did not contain any transactions")

    return transactions


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


def _load_demo_track_a() -> dict:
    """Load pre-cached Track A response (guaranteed path, no live LLM)."""
    data_dir = Path(__file__).resolve().parent / "data"
    path = data_dir / "demo_track_a.json"
    if not path.exists():
        return {
            "alerts": [],
            "graph": {"nodes": [], "links": []},
            "stats": {"total_txns": 0, "total_nodes": 0, "total_edges": 0, "alerts_generated": 0, "pattern_counts": {}},
            "agent_activity": [{"agent": "Data", "message": "Track A fixture file not found. Run pipeline once to generate."}],
        }
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/demo-track-a")
def demo_track_a():
    """Track A: Guaranteed demo path. Returns pre-cached result (~25s equivalent, no live LLM)."""
    return _load_demo_track_a()


@app.get("/api/adversarial-test")
def adversarial_test(test: Optional[str] = None):
    """
    Adversarial Test Mode: cycle+1 hop, split hub, time-distributed smurfing.
    ?test=cycle_plus_hop|split_hub|time_distributed_smurfing for one test, or omit for all.
    """
    if test == "cycle_plus_hop":
        return adversarial.run_cycle_plus_hop_test()
    if test == "split_hub":
        return adversarial.run_split_hub_test()
    if test == "time_distributed_smurfing":
        return adversarial.run_time_distributed_smurfing_test()
    if test is None or test == "all":
        return adversarial.run_all_adversarial_tests()
    raise HTTPException(status_code=400, detail="Unknown test. Use cycle_plus_hop, split_hub, time_distributed_smurfing, or all.")


class FeedbackBody(BaseModel):
    alert_id: str
    decision: str  # confirmed_fraud | false_positive | unclear
    confidence: int  # 1-5
    pattern_type: str = ""
    notes: str = ""


@app.post("/api/feedback")
def submit_feedback(body: FeedbackBody):
    """
    Investigator feedback: mark alert as confirmed_fraud, false_positive, or unclear.
    When false_positive with confidence >= 4, GST innocence discount for that pattern type is increased.
    """
    if body.decision not in ("confirmed_fraud", "false_positive", "unclear"):
        raise HTTPException(status_code=400, detail="decision must be confirmed_fraud, false_positive, or unclear")
    if not 1 <= body.confidence <= 5:
        raise HTTPException(status_code=400, detail="confidence must be 1-5")
    return add_decision(
        alert_id=body.alert_id,
        decision=body.decision,
        confidence=body.confidence,
        pattern_type=body.pattern_type or "",
        notes=body.notes or "",
    )


@app.get("/api/feedback/config")
def get_feedback_config():
    """Return current scorer_config (per-pattern weight overrides from investigator feedback)."""
    return get_scorer_config()


@app.get("/api/feedback/decisions")
def list_feedback_decisions(alert_id: Optional[str] = None):
    """List investigator decisions, optionally filtered by alert_id."""
    return get_decisions(alert_id=alert_id)


@app.post("/api/run-pipeline")
def run_pipeline():
    if _is_demo_mode():
        return _load_demo_cache(os.getenv("DEMO_CACHE_NAME", "demo_track_a"))
    return orchestrator.run_detection_pipeline()


@app.post("/api/run-pipeline-csv")
async def run_pipeline_csv(file: UploadFile = File(...)):
    if _is_demo_mode():
        return _load_demo_cache(os.getenv("DEMO_CACHE_NAME", "demo_track_a"))
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
    return orchestrator.run_detection_pipeline(transactions=transactions)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
