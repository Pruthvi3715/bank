"""
GraphSentinel Configuration — All thresholds and weights in one place.

This file centralises every tunable parameter so operators can adjust
detection behaviour without redeploying code.

Environment variables take precedence:
    GS_CYCLE_MAX_HOPS          → CYCLE_MAX_HOPS
    GS_MISMATCH_THRESHOLD       → MISMATCH_RATIO_THRESHOLD
    etc.

Load via:
    import sys; sys.path.insert(0, 'backend')
    from config import settings
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_float(key: str, default: float) -> float:
    val = os.getenv(key)
    return float(val) if val else default


def _env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    return int(val) if val else default


# ── Detection Thresholds ──────────────────────────────────────────────────────
CYCLE_MAX_HOPS: int = _env_int("GS_CYCLE_MAX_HOPS", 8)
CYCLE_MAX_COUNT: int = _env_int("GS_CYCLE_MAX_COUNT", 50)
FAN_IN_MIN_SOURCES: int = _env_int("GS_FAN_IN_MIN", 5)
HUB_MIN_IN_DEGREE: int = _env_int("GS_HUB_MIN_IN", 3)
HUB_MIN_OUT_DEGREE: int = _env_int("GS_HUB_MIN_OUT", 3)
PASSTHROUGH_RATIO_THRESHOLD: float = _env_float("GS_PASSTHROUGH_RATIO", 0.85)
DORMANT_MIN_INACTIVE_MONTHS: int = _env_int("GS_DORMANT_MONTHS", 6)
TEMPORAL_MIN_GAP_DAYS: int = _env_int("GS_TEMPORAL_GAP_DAYS", 90)
TEMPORAL_MIN_HOPS: int = _env_int("GS_TEMPORAL_MIN_HOPS", 3)
TEMPORAL_MAX_HOPS: int = _env_int("GS_TEMPORAL_MAX_HOPS", 6)

# ── Profile Mismatch (PS3 Requirement) ───────────────────────────────────────
MISMATCH_RATIO_THRESHOLD: float = _env_float("GS_MISMATCH_THRESHOLD", 3.0)
MISMATCH_RISK_BONUS: float = _env_float("GS_MISMATCH_BONUS", 25.0)

# ── ML Thresholds ─────────────────────────────────────────────────────────────
ANOMALY_CONTAMINATION: float = _env_float("GS_CONTAMINATION", 0.05)
ML_SCORE_THRESHOLD: float = _env_float("GS_ML_THRESHOLD", 0.5)


# ── Risk Scoring Weights ────────────────────────────────────────────────────────
@dataclass
class ScoringConfig:
    CYCLE_BASE: float = 40.0
    SMURFING_BASE: float = 25.0
    HUB_SPOKE_BASE: float = 30.0
    PASSTHROUGH_BASE: float = 15.0
    DORMANT_BASE: float = 20.0
    TEMPORAL_BASE: float = 20.0

    TEMPORAL_VELOCITY_BONUS: float = 20.0
    CROSS_CHANNEL_BONUS: float = 10.0
    NEAR_THRESHOLD_BONUS: float = 15.0
    PASS_THROUGH_BONUS: float = 15.0
    DORMANT_BONUS: float = 20.0
    MISMATCH_BONUS: float = MISMATCH_RISK_BONUS

    MAX_SCORE: float = 100.0
    MAX_INNOCENCE_DISCOUNT: float = 30.0


SCORING = ScoringConfig()

# ── SAR Chatbot ────────────────────────────────────────────────────────────────
LLM_MODEL: str = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")
LLM_MAX_TOKENS: int = _env_int("GS_LLM_MAX_TOKENS", 800)
LLM_TEMPERATURE: float = _env_float("GS_LLM_TEMPERATURE", 0.3)

# ── Privacy / TokenVault ──────────────────────────────────────────────────────
TOKENVAULT_SALT_BYTES: int = _env_int("GS_SALT_BYTES", 16)
TOKEN_ROLE_LABELS: dict = field(
    default_factory=lambda: {
        "hub": "HUB_NODE",
        "cycle_origin": "CYCLE_ORIGIN",
        "dormant": "DORMANT_ACCOUNT",
        "smurf_target": "SMURF_TARGET",
        "passthrough": "PASSTHROUGH_NODE",
        "layering": "LAYERING_NODE",
        "fan_in": "FANIN_ACCOUNT",
        "fan_out": "FANOUT_ACCOUNT",
    }
)

# ── Pipeline ──────────────────────────────────────────────────────────────────
DEMO_MODE: bool = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")
DEMO_CACHE_NAME: str = os.getenv("DEMO_CACHE_NAME", "demo_track_a")

# ── WebSocket ─────────────────────────────────────────────────────────────────
WS_PING_INTERVAL: int = _env_int("GS_WS_PING_INTERVAL", 30)
WS_PING_TIMEOUT: int = _env_int("GS_WS_PING_TIMEOUT", 10)

# ── Kafka / Redpanda ──────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("REDPANDA_BROKERS", "localhost:9092")
KAFKA_TRANSACTIONS_TOPIC: str = "transactions"
KAFKA_ALERTS_TOPIC: str = "alerts"
KAFKA_PIPELINE_EVENTS_TOPIC: str = "pipeline_events"

# ── ChromaDB ─────────────────────────────────────────────────────────────────
CHROMADB_URL: str = os.getenv("CHROMADB_URL", "http://localhost:8001")
CHROMADB_COLLECTION_ALERTS: str = "sar_alerts"
CHROMADB_COLLECTION_GUIDELINES: str = "regulatory_guidelines"
CHROMADB_COLLECTION_QA: str = "investigator_qa"
EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

# ── JWT ───────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "graphsentinel-dev-secret")
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = _env_int("GS_JWT_EXPIRE", 480)
