# GraphSentinel Backend

AI-Powered Fund Flow Fraud Detection System API

## Quick Start

### Local Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run with demo mode (pre-cached responses)
DEMO_MODE=1 uvicorn app.main:app --reload

# Run live detection (generates fresh graph)
DEMO_MODE=0 uvicorn app.main:app --reload
```

### Docker

```bash
# Build and run
docker build -t graphsentinel ./backend
docker run -p 8000:8000 graphsentinel

# Or use docker-compose
docker-compose up --build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Basic health check |
| `/api/health/ready` | GET | Readiness probe |
| `/api/demo-track-a` | GET | Pre-cached demo response |
| `/api/run-pipeline` | POST | Run detection (demo or live) |
| `/api/run-pipeline-csv` | POST | Run detection on CSV upload |
| `/api/feedback` | POST | Submit investigator feedback |
| `/api/feedback/config` | GET | Get scorer configuration |
| `/api/feedback/decisions` | GET | List feedback decisions |
| `/api/adversarial-test` | GET | Run adversarial fraud tests |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `1` | Use pre-cached demo responses |
| `DEMO_CACHE_NAME` | `demo_track_a` | Demo cache file name |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PREFILTER_MIN_AMOUNT` | `500` | Minimum transaction amount |

## Demo Mode

When `DEMO_MODE=1`:
- Returns pre-cached fraud detection results
- No LLM API calls needed
- Reliable for presentations

When `DEMO_MODE=0`:
- Generates fresh synthetic transactions
- Runs live graph algorithms
- Includes LLM explanations (if configured)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_pipeline.py::test_cycle_and_smurfing_detection -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app & endpoints
│   ├── adversarial.py       # Adversarial test scenarios
│   ├── feedback_store.py    # Investigator feedback loop
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── pipeline/
│   │   ├── orchestrator.py  # Detection pipeline
│   │   ├── graph_agent.py   # Graph construction
│   │   ├── pathfinder_agent.py  # Pattern detection
│   │   ├── context_agent.py # Context analysis
│   │   ├── scorer_agent.py  # Risk scoring
│   │   └── report_agent.py  # SAR generation
│   └── simulation/
│       └── generator.py     # Synthetic data generation
├── config/
│   └── settings.py          # Configuration
├── data/                    # Data files
├── demo_cache/             # Pre-cached demo responses
├── tests/                  # Test suite
├── Dockerfile              # Container definition
└── requirements.txt         # Python dependencies
```

## Fraud Patterns Detected

1. **Round-Tripping (Cycle)** - Circular fund flows
2. **Smurfing** - Multiple sub-threshold transactions to single target
3. **Hub-and-Spoke** - Central node routing funds
4. **Pass-Through** - Near-zero balance relay accounts
5. **Dormant Activation** - Long-dormant accounts suddenly active
6. **Temporal Layering** - Long-duration transaction chains

## License

MIT - For hackathon demonstration purposes