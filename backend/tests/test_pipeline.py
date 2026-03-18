from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import TransactionBase
from app.pipeline.context_agent import ContextAgent
from app.pipeline.graph_agent import GraphAgent
from app.pipeline.pathfinder_agent import PathfinderAgent
from app.pipeline.scorer_agent import ScorerAgent


def _txn(
    txn_id: str,
    sender: str,
    receiver: str,
    amount: float,
    ts: datetime,
    channel: str = "NEFT",
) -> TransactionBase:
    return TransactionBase(
        txn_id=txn_id,
        sender_id=sender,
        receiver_id=receiver,
        amount=amount,
        timestamp=ts,
        channel=channel,
        account_type="Savings",
    )


def test_cycle_and_smurfing_detection():
    now = datetime.now()
    txns = [
        _txn("1", "A", "B", 1000, now),
        _txn("2", "B", "C", 1100, now + timedelta(minutes=5)),
        _txn("3", "C", "A", 1200, now + timedelta(minutes=10)),
    ]
    for i in range(7):
        txns.append(_txn(f"s{i}", f"S{i}", "Z", 49000, now + timedelta(minutes=20 + i), "IMPS"))

    graph = GraphAgent().process_transactions(txns)
    pathfinder = PathfinderAgent(graph)

    cycles = pathfinder.detect_cycles()
    smurfs = pathfinder.detect_smurfing(fan_in_threshold=5)

    cycle_nodes = set().union(*[set(c) for c in cycles]) if cycles else set()
    assert {"A", "B", "C"}.issubset(cycle_nodes)
    assert "Z" in smurfs


def test_hub_pass_through_and_dormant_detection():
    start = datetime.now() - timedelta(days=365)
    recent = datetime.now()
    txns = [
        _txn("a1", "I1", "HUB", 60000, recent),
        _txn("a2", "I2", "HUB", 61000, recent + timedelta(minutes=2)),
        _txn("a3", "I3", "HUB", 62000, recent + timedelta(minutes=4)),
        _txn("a4", "HUB", "O1", 50000, recent + timedelta(minutes=6)),
        _txn("a5", "HUB", "O2", 51000, recent + timedelta(minutes=8)),
        _txn("a6", "HUB", "O3", 52000, recent + timedelta(minutes=10)),
        _txn("b1", "SRC", "MULE", 100000, recent + timedelta(minutes=12)),
        _txn("b2", "MULE", "DST", 99000, recent + timedelta(minutes=14), "IMPS"),
        _txn("c1", "X", "DORM", 1000, start, "UPI"),
        _txn("c2", "DORM", "Y", 45000, recent, "RTGS"),
        _txn("c3", "DORM", "Y2", 46000, recent + timedelta(minutes=4), "NEFT"),
        _txn("c4", "DORM", "Y3", 47000, recent + timedelta(minutes=8), "IMPS"),
    ]

    graph = GraphAgent().process_transactions(txns)
    pathfinder = PathfinderAgent(graph)
    detections = pathfinder.run_all_detections()

    assert "HUB" in detections["hubs"]
    assert "MULE" in detections["pass_through"]
    assert "DORM" in detections["dormant"]


def test_temporal_layering_detection():
    now = datetime.now()
    txns = [
        _txn("t1", "L1", "L2", 10000, now - timedelta(days=200), "NEFT"),
        _txn("t2", "L2", "L3", 9800, now - timedelta(days=120), "RTGS"),
        _txn("t3", "L3", "L4", 9600, now - timedelta(days=20), "IMPS"),
    ]
    graph = GraphAgent().process_transactions(txns)
    pathfinder = PathfinderAgent(graph)
    paths = pathfinder.detect_temporal_layering(min_gap_days=90, min_hops=3, max_hops=5)
    assert any(path == ["L1", "L2", "L3", "L4"] for path in paths)


def test_scorer_applies_temporal_and_cross_channel_bonuses():
    now = datetime.now()
    txns = [
        _txn("1", "A", "B", 49000, now, "NEFT"),
        _txn("2", "B", "C", 48000, now + timedelta(minutes=20), "RTGS"),
        _txn("3", "C", "D", 47000, now + timedelta(minutes=40), "IMPS"),
    ]
    graph = GraphAgent().process_transactions(txns)
    edges = []
    for u, v, d in graph.edges(data=True):
        edges.append({"sender_id": u, "receiver_id": v, **d})

    scorer = ScorerAgent(ContextAgent({}), graph=graph)
    score = scorer.score_pattern("TemporalLayering", ["A", "B", "C", "D"], edges=edges)

    assert score["scoring_signals"]["temporal_velocity"] == 20.0
    assert score["scoring_signals"]["cross_channel"] == 10.0
    assert score["scoring_signals"]["near_threshold_structuring"] == 15.0


def test_csv_ingestion_endpoint():
    client = TestClient(app)
    csv_content = (
        "txn_id,sender_id,receiver_id,amount,timestamp,channel,account_type\n"
        "x1,A,B,49000,2026-03-01T10:00:00,NEFT,Savings\n"
        "x2,B,C,48000,2026-03-01T11:00:00,RTGS,Savings\n"
        "x3,C,A,47000,2026-03-01T12:00:00,IMPS,Savings\n"
    )
    response = client.post(
        "/api/run-pipeline-csv",
        files={"file": ("sample.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert "alerts" in body
    assert "graph" in body
    assert "stats" in body
