import os
import pytest
import pytest_asyncio

# Force SQLite for testing — must be set BEFORE importing feedback_store
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_feedback.db"

from app.feedback_store import (
    init_db,
    close_db,
    add_decision,
    get_scorer_config,
    get_decisions,
    InvestigatorDecision,
    ScorerConfig,
    async_session_factory,
    engine,
    Base,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create fresh tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_add_decision_returns_record():
    """add_decision returns a dict with ok=True and model_version."""
    result = await add_decision(
        "alert-001", "confirmed_fraud", 5, "Cycle", "Clear cycle"
    )
    assert result["ok"] is True
    assert result["model_version"] >= 1


@pytest.mark.asyncio
async def test_add_false_positive_updates_scorer_config():
    """false_positive with confidence>=4 should create/update ScorerConfig."""
    await add_decision("alert-002", "false_positive", 5, "Smurfing", "Legit payroll")
    config = await get_scorer_config()
    assert "Smurfing" in config
    assert config["Smurfing"]["gst_discount_pct"] >= 28.0


@pytest.mark.asyncio
async def test_add_false_positive_low_confidence_no_discount():
    """false_positive with confidence<4 should NOT update scorer config."""
    await add_decision("alert-003", "false_positive", 2, "HubAndSpoke", "")
    config = await get_scorer_config()
    assert "HubAndSpoke" not in config


@pytest.mark.asyncio
async def test_get_decisions_returns_all():
    """get_decisions() returns all decisions."""
    await add_decision("alert-004", "confirmed_fraud", 4, "Cycle", "")
    await add_decision("alert-005", "unclear", 3, "Smurfing", "Need more info")
    decisions = await get_decisions()
    assert len(decisions) == 2


@pytest.mark.asyncio
async def test_get_decisions_filter_by_alert():
    """get_decisions(alert_id) filters correctly."""
    await add_decision("alert-006", "confirmed_fraud", 5, "Cycle", "")
    await add_decision("alert-007", "false_positive", 4, "Cycle", "")
    decisions = await get_decisions(alert_id="alert-006")
    assert len(decisions) == 1
    assert decisions[0]["alert_id"] == "alert-006"


@pytest.mark.asyncio
async def test_scorer_config_discount_capped_at_30():
    """Multiple false_positives should cap gst_discount_pct at 30."""
    for i in range(5):
        await add_decision(f"alert-cap-{i}", "false_positive", 5, "Dormant", "")
    config = await get_scorer_config()
    assert config["Dormant"]["gst_discount_pct"] <= 30.0


@pytest.mark.asyncio
async def test_decision_fields_persisted():
    """All fields are correctly stored and retrieved."""
    await add_decision(
        "alert-008", "confirmed_fraud", 4, "PassThrough", "Suspicious routing"
    )
    decisions = await get_decisions(alert_id="alert-008")
    d = decisions[0]
    assert d["decision"] == "confirmed_fraud"
    assert d["confidence"] == 4
    assert d["pattern_type"] == "PassThrough"
    assert d["notes"] == "Suspicious routing"
    assert "timestamp" in d
