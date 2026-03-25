# GraphSentinel — Further Improvements Roadmap

## Overview

Based on analysis of the codebase (88% complete, 46/52 tasks), this document outlines all improvements organized by category and priority.

---

## 1. Immediate — Pre-Finale (Critical)

These should be done before the Grand Finale presentation.

| Priority | Improvement | Why It Matters |
|----------|-------------|----------------|
| CRITICAL | Create `.env.example` file | Judges can't run `docker-compose up` without knowing required env vars |
| CRITICAL | Fix stale Playwright tests | Tests reference old UI text; 6 tests may fail on fresh run |
| CRITICAL | Remove dead code in `scorer_agent.py` | Lines 207–216 have duplicate dormant bonus logic after a `return` statement |
| HIGH | Implement WebSocket (T37) | Live pipeline progress is a demo differentiator; currently fetch-only |
| HIGH | Create `run_demo_scenario.py` output verification | No validation that demo_cache produces expected results |
| HIGH | Update `GraphSentinel_PROGRESS.md` | Mark remaining tasks accurately; currently shows outdated status |

---

## 2. Architecture & Infrastructure

| Improvement | Current State | Proposed State | Effort |
|-------------|---------------|----------------|--------|
| **Neo4j full integration** | NetworkX in-memory only; Neo4j in docker-compose but unused | Replace NetworkX with Neo4j bolt driver for persistence, Cypher queries, visual browser | HIGH (2–3 days) |
| **Persistent database for feedback** | In-memory lists in `feedback_store.py` | PostgreSQL table for investigator decisions, scorer config, trusted accounts | MEDIUM (1 day) |
| **Redis caching layer** | File-based demo cache | Redis for SAR caching, session tokens, pipeline state | MEDIUM (1 day) |
| **Database migrations** | None | Alembic for PostgreSQL schema versioning | LOW (4 hours) |
| **Health check improvements** | Basic `/api/health` | Deep health checks for Neo4j, Redis, ChromaDB, Kafka connectivity | LOW (2 hours) |
| **Observability** | Basic logging | Structured logging (JSON), Prometheus metrics, distributed tracing (OpenTelemetry) | HIGH (2–3 days) |
| **Rate limiting** | None | API rate limiting per user/IP using Redis | LOW (4 hours) |
| **Connection pooling** | Default connections | SQLAlchemy async pools, Neo4j connection pool, Redis pool | MEDIUM (1 day) |

---

## 3. Detection & ML Improvements

| Improvement | Description | Impact |
|-------------|-------------|--------|
| **Graph Neural Networks (GNN)** | Replace rule-based detection with PyTorch Geometric GNNs (GraphSAGE, GAT) for learned fraud patterns | HIGH — catches novel patterns rules miss |
| **Real XGBoost training data** | Currently uses heuristic labels; train on IBM AMLSim ground truth with proper train/val/test split | HIGH — actual supervised learning |
| **Ensemble model stacking** | Combine Isolation Forest, XGBoost, and GNN predictions via meta-learner | MEDIUM — reduces individual model bias |
| **Anomaly explanation (SHAP)** | Add SHAP values to show which features drove each ML score | HIGH — regulatory explainability |
| **Temporal graph embeddings** | Use Node2Vec or DeepWalk for structural graph embeddings that capture neighborhood topology | MEDIUM — better feature representation |
| **Online learning** | Retrain models incrementally as investigator feedback accumulates | MEDIUM — model improves over time |
| **Threshold auto-tuning** | Use investigator feedback to auto-calibrate risk score thresholds per fraud type | MEDIUM — reduces false positives |
| **Cross-validation pipeline** | K-fold cross-validation with precision/recall/F1 reporting on held-out test set | LOW — validates model quality |
| **Feature store** | Centralized feature computation and versioning (Feast or custom) | LOW — reproducibility |

---

## 4. Privacy & Security

| Improvement | Current State | Proposed | Effort |
|-------------|---------------|----------|--------|
| **Login UI** | `auth.ts` exists but no login form | Add login page with JWT flow, role selection, session management | MEDIUM (1 day) |
| **RBAC enforcement** | 3 roles defined but not enforced on all endpoints | Middleware to enforce investigator/senior_analyst/readonly on every route | LOW (4 hours) |
| **Audit logging to DB** | Audit actions logged to stdout | Persistent audit_log table in PostgreSQL with queryable history | LOW (4 hours) |
| **Data encryption at rest** | Not implemented | Encrypt Neo4j data volumes, PostgreSQL TDE, encrypted demo_cache | HIGH (2 days) |
| **PII field-level encryption** | TokenVault covers graph IDs only | Encrypt customer names, PAN, Aadhaar in all storage layers | MEDIUM (1 day) |
| **Air-gapped LLM deployment** | Uses Claude API (internet) | Deploy Llama 3 or Mistral on bare-metal within bank perimeter | HIGH (3–5 days) |
| **Certificate pinning** | None | Pin API certificates for all external LLM calls | LOW (2 hours) |
| **Secrets management** | `.env` file | HashiCorp Vault or AWS Secrets Manager integration | MEDIUM (1 day) |
| **GDPR/DPDP compliance** | TokenVault only | Full data subject access requests, right to erasure, consent management | HIGH (1 week) |
| **Penetration testing** | None | OWASP Top 10 scan, API fuzzing, SQL injection testing | MEDIUM (2 days) |

---

## 5. Frontend & UX

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Multi-page routing** | Separate pages: `/alerts/[id]`, `/graph`, `/cases`, `/settings`, `/reports` | MEDIUM (1 day) |
| **Real-time WebSocket integration** | Live pipeline progress, live alert notifications, live graph updates | MEDIUM (1 day) |
| **Loading skeletons** | Replace spinner with skeleton placeholders for each panel | LOW (4 hours) |
| **Error boundaries** | React error boundaries with fallback UI for each major section | LOW (2 hours) |
| **Toast notifications** | Success/error feedback via snackbar for all API calls | LOW (3 hours) |
| **Keyboard shortcuts** | `G` for graph, `A` for alerts, `S` for SAR, `Ctrl+K` for search | LOW (4 hours) |
| **Advanced graph features** | Zoom-to-subgraph, path highlighting, node clustering, timeline slider | HIGH (2–3 days) |
| **Export capabilities** | CSV/JSON export for alerts, graph data, and filtered results | LOW (4 hours) |
| **Mobile responsive improvements** | Better tablet/phone layout for field investigators | MEDIUM (1 day) |
| **Accessibility audit** | WCAG 2.1 AA compliance, screen reader support, keyboard navigation | MEDIUM (1 day) |
| **Dark/light theme improvements** | Current theme system works; add high-contrast mode for visibility | LOW (2 hours) |
| **User preferences page** | Save filter defaults, notification preferences, display settings | LOW (4 hours) |

---

## 6. Data & Pipeline

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Real banking data adapters** | Connectors for core banking systems (Finacle, T24, Flexcube) | HIGH (1–2 weeks) |
| **Data quality validation** | Great Expectations or custom validators for incoming transaction data | MEDIUM (1 day) |
| **Schema evolution** | Avro/Protobuf schema registry for Kafka topics | MEDIUM (1 day) |
| **Backfill pipeline** | Historical data ingestion for warm/cold graph layers | HIGH (2–3 days) |
| **Data lineage tracking** | Track data transformations from raw → graph → alerts → SAR | MEDIUM (1 day) |
| **Synthetic data improvements** | More realistic fraud patterns: Hawala networks, trade-based laundering, cryptocurrency off-ramps | MEDIUM (1 day) |
| **Multi-bank data federation** | Encrypted, anonymized graph sharing between banks via FIU-IND | HIGH (1–2 weeks) |
| **Streaming windowing** | Tumbling/sliding windows for velocity analysis (1h, 24h, 7d aggregations) | MEDIUM (1 day) |

---

## 7. Testing & Quality

| Improvement | Current State | Proposed | Effort |
|-------------|---------------|----------|--------|
| **Unit test coverage** | 5 tests in `test_pipeline.py` | 80%+ coverage on all pipeline modules, ML models, scoring | HIGH (2–3 days) |
| **Integration tests** | Manual `test_api.py` smoke test | Automated API integration tests with fixtures | MEDIUM (1 day) |
| **Playwright test fixes** | Tests reference stale UI text | Update assertions to match current component labels | LOW (2 hours) |
| **Performance benchmarks** | None | Benchmark pipeline latency at 10K, 50K, 100K transactions | LOW (4 hours) |
| **Load testing** | None | Locust/k6 load tests targeting 1M transactions/day throughput | MEDIUM (1 day) |
| **Chaos engineering** | None | Kill Redis/Neo4j/Kafka mid-pipeline; verify graceful degradation | MEDIUM (1 day) |
| **Mutation testing** | None | mutmut to verify test suite quality | LOW (4 hours) |
| **CI/CD pipeline** | None | GitHub Actions: lint → test → build → deploy | MEDIUM (1 day) |
| **Contract testing** | None | Pact tests for backend-frontend API contracts | LOW (4 hours) |

---

## 8. Scalability & Performance

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Horizontal scaling** | Run multiple backend workers behind load balancer; Kafka consumer groups | MEDIUM (1 day) |
| **Graph partitioning** | Partition large graphs by bank branch or geographic region | HIGH (3 days) |
| **Query optimization** | Neo4j query profiling, index tuning, Cypher query caching | MEDIUM (1 day) |
| **Async processing** | Background task queue (Celery/RQ) for long-running ML inference | MEDIUM (1 day) |
| **CDN for frontend** | Cloudflare/AWS CloudFront for static assets | LOW (2 hours) |
| **Database read replicas** | Neo4j read replicas for investigation queries | HIGH (2 days) |
| **Caching strategy** | Multi-layer cache: Redis → local memory → disk; TTL policies per data type | MEDIUM (1 day) |

---

## 9. Regulatory & Compliance

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **FIU-IND API integration** | Direct SAR submission to FIU-IND portal (if API available) | HIGH (depends on FIU access) |
| **RBI Master Direction compliance** | Full KYC verification workflow, EDD triggers, CTR filing | HIGH (1–2 weeks) |
| **PMLA Section 12 compliance** | Mandatory investigator attestation before SAR filing; digital signatures | MEDIUM (1–2 days) |
| **DPDP Act data lifecycle** | Automated data retention enforcement, deletion schedules, consent tracking | HIGH (1 week) |
| **Basel III reporting** | Operational risk reporting templates, loss event tracking | MEDIUM (2–3 days) |
| **Audit trail immutability** | Write-once audit logs; tamper-evident storage (blockchain or hash chains) | MEDIUM (1 day) |

---

## 10. Developer Experience

| Improvement | Description | Effort |
|-------------|-------------|--------|
| **Comprehensive README** | Architecture diagrams, API docs, setup guide, contribution guidelines | LOW (4 hours) |
| **API documentation** | OpenAPI/Swagger auto-generated docs with examples | LOW (already has FastAPI auto-docs) |
| **Development environment** | Devcontainer setup for VS Code / GitHub Codespaces | LOW (4 hours) |
| **Code quality** | ruff formatter + mypy type checking + pre-commit hooks | LOW (2 hours) |
| **Architecture Decision Records** | ADRs documenting why each technology was chosen | LOW (2 hours) |
| **Onboarding guide** | Step-by-step guide for new developers to understand the codebase | LOW (4 hours) |

---

## Recommended Build Order (Post-Hackathon)

```
Week 1:  Fix critical gaps → .env.example, WebSocket, Neo4j integration, persistent DB
Week 2:  Security hardening → Login UI, RBAC enforcement, audit logging, secrets management
Week 3:  ML improvements → Real XGBoost training, SHAP explanations, GNN prototype
Week 4:  Testing → Unit tests, integration tests, performance benchmarks, CI/CD
Week 5:  Frontend polish → Multi-page routing, loading skeletons, error boundaries
Week 6:  Regulatory compliance → PMLA attestation, DPDP data lifecycle, audit immutability
Week 7:  Scalability → Horizontal scaling, graph partitioning, async processing
Week 8:  Production readiness → Load testing, chaos engineering, observability, deployment
```

---

## Priority Matrix

### Highest Impact / Lowest Effort (Quick Wins)
- Create `.env.example` file
- Fix stale Playwright tests
- Remove dead code in `scorer_agent.py`
- Loading skeletons
- Error boundaries
- Toast notifications
- Keyboard shortcuts
- Export capabilities (CSV/JSON)
- RBAC enforcement
- Audit logging to DB
- Certificate pinning

### Highest Impact / Highest Effort (Strategic Investments)
- Neo4j full integration
- Graph Neural Networks (GNN)
- Air-gapped LLM deployment
- Real banking data adapters
- DPDP Act data lifecycle
- Unit test coverage
- Observability (structured logging, metrics, tracing)

### Lower Impact / Lower Effort (Nice to Have)
- Dark/light theme improvements
- User preferences page
- Code quality (ruff, mypy, pre-commit)
- Architecture Decision Records
- Onboarding guide

### Lower Impact / Higher Effort (Deprioritize)
- Graph partitioning
- Database read replicas
- Multi-bank data federation
- Mutation testing

---

## Key Architectural Decisions for Future

1. **Neo4j over NetworkX** — NetworkX dies above 500K transactions; Neo4j persists to disk, runs native Cypher queries
2. **On-premise LLM over Claude API** — Banking data cannot leave the perimeter; Llama 3 or Mistral on bare-metal
3. **PostgreSQL over in-memory** — Feedback, audit logs, and scorer config need persistence
4. **Kafka over CSV** — Same pipeline at 1M transactions/day in production; just scale broker count
5. **GNN over rule-based** — Rules catch known patterns; GNNs catch novel fraud structures
6. **SHAP over black-box** — Regulators require explainability; SHAP shows which features drove each decision

---

*GraphSentinel Improvements Roadmap · Team Elida · MMIT Pune · PSBs Hackathon 2026*
*Built on Elida multi-agent framework — VOIS Innovation Marathon 2.0 Winners · ₹2,00,000*
