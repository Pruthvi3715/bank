import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_backend_root = Path(__file__).resolve().parents[1]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.pipeline.orchestrator import DetectionOrchestrator
from app.models.schemas import TransactionBase
from app.simulation.generator import generate_scenario


def main() -> int:
    """
    Deterministically generate a demo scenario and write a full cached
    pipeline response to backend/demo_cache/<name>.json.
    """
    name = os.getenv("DEMO_CACHE_NAME", "demo_track_a")
    seed = int(os.getenv("DEMO_SEED", "1337"))
    noise_txns = int(os.getenv("DEMO_NOISE_TXNS", "475"))
    base_time = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc) - timedelta(hours=24)

    raw_txns = generate_scenario(
        seed=seed,
        base_time=base_time,
        num_accounts=int(os.getenv("DEMO_NUM_ACCOUNTS", "200")),
        noise_txns=noise_txns,
    )
    txns = [TransactionBase(**t) for t in raw_txns]

    orchestrator = DetectionOrchestrator()
    results = orchestrator.run_detection_pipeline(transactions=txns)

    cache_dir = Path(__file__).resolve().parents[1] / "demo_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_path = cache_dir / f"{name}.json"
    out_path.write_text(json.dumps(results, default=str, indent=2), encoding="utf-8")

    print(f"Wrote demo cache: {out_path}")
    print(f"Alerts: {len(results.get('alerts', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

