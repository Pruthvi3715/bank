"""GraphSentinel configuration."""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLES_DIR = DATA_DIR / "samples"

# Detection thresholds (Pathfinder)
CYCLE_MAX_HOPS = 8
CYCLE_MAX_COUNT = 50
FAN_IN_MIN_SOURCES = 5
HUB_MIN_IN_DEGREE = 3
HUB_MIN_OUT_DEGREE = 3
PASSTHROUGH_RATIO_THRESHOLD = 0.85
DORMANT_MIN_INACTIVE_MONTHS = 6
TEMPORAL_MIN_GAP_DAYS = 90
TEMPORAL_MIN_HOPS = 3
TEMPORAL_MAX_HOPS = 6

# Pre-filter
PREFILTER_MIN_AMOUNT = 500

# Risk score bands
RISK_BANDS = {
    "critical": (90, 100),
    "high": (70, 89),
    "elevated": (40, 69),
    "monitor": (0, 39),
}
