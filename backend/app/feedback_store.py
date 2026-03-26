"""
Investigator feedback loop (PRD Section 12.2).

Persistent PostgreSQL store for investigator_decisions and scorer_config.
When investigator marks false_positive with high confidence, we adjust
innocence discount for that pattern type (e.g. GST discount -20% -> -28%).
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    # Fallback: local SQLite for dev without Docker
    _db_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "feedback.db"
    )
    os.makedirs(os.path.dirname(_db_path), exist_ok=True)
    DATABASE_URL = f"sqlite+aiosqlite:///{_db_path}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


# ---------------------------------------------------------------------------
# ORM base & models
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class InvestigatorDecision(Base):
    __tablename__ = "investigator_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(128), nullable=False, index=True)
    decision = Column(String(32), nullable=False)
    confidence = Column(Integer, nullable=False)
    pattern_type = Column(String(64), nullable=False, default="")
    notes = Column(Text, nullable=False, default="")
    model_version = Column(Integer, nullable=False, default=1)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ScorerConfig(Base):
    __tablename__ = "scorer_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_type = Column(String(64), nullable=False, unique=True)
    gst_discount_pct = Column(Float, nullable=False, default=20.0)
    model_version = Column(Integer, nullable=False, default=1)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------
async def init_db() -> None:
    """Create tables if they don't exist. Call once during app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose engine. Call during app shutdown."""
    await engine.dispose()


# ---------------------------------------------------------------------------
# Core API (async)
# ---------------------------------------------------------------------------
async def add_decision(
    alert_id: str,
    decision: str,
    confidence: int,
    pattern_type: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Record investigator decision. decision: confirmed_fraud | false_positive | unclear.
    confidence: 1-5. When false_positive and confidence >= 4, increase GST discount
    for this pattern type so similar alerts get a stronger innocence discount.
    """
    async with async_session_factory() as session:
        async with session.begin():
            # Fetch current model_version from any existing scorer config row
            result = await session.execute(
                select(ScorerConfig.model_version).order_by(
                    ScorerConfig.model_version.desc()
                )
            )
            row = result.first()
            model_version = (row[0] + 1) if row else 1

            decision_row = InvestigatorDecision(
                alert_id=alert_id,
                decision=decision,
                confidence=confidence,
                pattern_type=pattern_type,
                notes=notes,
                model_version=model_version,
            )
            session.add(decision_row)

            if decision == "false_positive" and confidence >= 4 and pattern_type:
                # Strengthen innocence discount for this pattern type
                result = await session.execute(
                    select(ScorerConfig).where(
                        ScorerConfig.pattern_type == pattern_type
                    )
                )
                cfg_row = result.scalar_one_or_none()

                if cfg_row is None:
                    cfg_row = ScorerConfig(
                        pattern_type=pattern_type,
                        gst_discount_pct=28.0,
                        model_version=model_version,
                    )
                    session.add(cfg_row)
                else:
                    current = cfg_row.gst_discount_pct
                    new_val = min(30.0, current + 8.0)
                    cfg_row.gst_discount_pct = new_val
                    cfg_row.model_version = model_version
                    cfg_row.updated_at = datetime.now(timezone.utc)

        return {"ok": True, "model_version": model_version}


async def get_scorer_config() -> Dict[str, Any]:
    async with async_session_factory() as session:
        result = await session.execute(select(ScorerConfig))
        rows = result.scalars().all()
        return {
            row.pattern_type: {
                "gst_discount_pct": row.gst_discount_pct,
                "model_version": row.model_version,
            }
            for row in rows
        }


async def get_decisions(alert_id: Optional[str] = None) -> List[Dict[str, Any]]:
    async with async_session_factory() as session:
        stmt = select(InvestigatorDecision)
        if alert_id is not None:
            stmt = stmt.where(InvestigatorDecision.alert_id == alert_id)
        stmt = stmt.order_by(InvestigatorDecision.created_at.desc())
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "alert_id": r.alert_id,
                "decision": r.decision,
                "confidence": r.confidence,
                "pattern_type": r.pattern_type,
                "notes": r.notes,
                "model_version": r.model_version,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
