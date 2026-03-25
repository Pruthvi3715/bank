# GraphSentinel — Complete Project TODO

**Team Elida · MMIT Pune · PSBs Hackathon 2026 · PS3**  
**Competition:** PSBs Hackathon Series 2026 (GoI, Ministry of Finance, DFS)  
**Problem Statement:** PS3 — Tracking of Funds within Bank for Fraud Detection  
**Grand Finale:** March 27, 2026 · VIT Pune

---

## Progress Tracker

| Phase | Tasks | Priority |
|---|---|---|
| Phase 1 — Data & Graph Foundation | 7 tasks | 🔴 Critical |
| Phase 2 — Detection Algorithms | 7 tasks | 🔴 Critical |
| Phase 3 — ML Layer | 7 tasks | 🟠 High |
| Phase 4 — Privacy & Security | 6 tasks | 🟠 High |
| Phase 5 — SAR Chatbot + RAG | 6 tasks | 🟠 High |
| Phase 6 — Frontend & UX | 8 tasks | 🟠 High |
| Phase 7 — Demo Preparation | 7 tasks | 🟡 Demo |
| Phase 8 — Submission | 4 tasks | 🔴 Critical |
| **Total** | **52 tasks** | |

---

## Recommended Build Order

```
docker-compose.yml (t6)
  → IBM AMLSim data generation (t1, t2)
  → Neo4j migration (t3, t4, t5)
  → Detection algorithms (t8, t9, t10, t11, t12)
  → Feature extraction (t15)
  → ML models (t16, t17, t18)
  → TokenVault + privacy (t22, t23, t24)
  → SAR chatbot (t28, t29, t30, t31)
  → Frontend UX (t34, t35, t38, t39)
  → Demo prep (t42, t43, t44, t45, t46, t47, t48)
  → Submission (t49, t50, t51, t52)
```

---

## Phase 1 — Data & Graph Foundation 🔴

> Goal: Replace CSV + NetworkX with a real graph database and streaming ingestion. This is the foundation everything else builds on. Do not write any algorithm code until this phase is stable.

---

### T1 · Generate IBM AMLSim Dataset `CRITICAL`

**What to do:**  
Run the IBM AMLSim simulator to generate a realistic synthetic banking transaction dataset with embedded fraud patterns and ground-truth labels.

**Output files needed:**
- `accounts.csv` — account nodes with IDs, types, creation dates
- `transactions.csv` — directed edges with amounts, timestamps, channels
- `alert_patterns.csv` — fraud labels (which transactions are fraudulent)

**Commands:**
```bash
git clone https://github.com/IBM/AMLSim
cd AMLSim
# Edit conf.json: set n_accounts=10000, n_transactions=100000
python scripts/generate_data.py
java -jar target/AMLSim-1.0.jar conf.json
```

**Validation checklist:**
- [ ] At least 3 fraud pattern types present (cycle, hub-spoke, smurfing)
- [ ] Fraud labels in alert_patterns.csv match expected counts
- [ ] Timestamps span at least 6 months (for dormant activation testing)
- [ ] No null values in sender_id, receiver_id, amount, timestamp columns

**Alternative (faster):** Download pre-generated dataset from Kaggle:  
`kaggle datasets download ealtman2019/ibm-transactions-for-anti-money-laundering-aml`

---

### T2 · Validate Dataset Integrity `CRITICAL`

**What to do:**  
Before writing any detection code, verify the dataset is structurally sound.

```python
import pandas as pd

txns = pd.read_csv('transactions.csv')
accounts = pd.read_csv('accounts.csv')
alerts = pd.read_csv('alert_patterns.csv')

print(f"Transactions: {len(txns)}")
print(f"Accounts: {len(txns['sender_id'].nunique())} unique senders")
print(f"Fraud labels: {alerts['is_fraud'].sum()} flagged")
print(f"Null check: {txns.isnull().sum()}")
print(f"Date range: {txns['timestamp'].min()} → {txns['timestamp'].max()}")
print(f"Channels: {txns['channel'].value_counts()}")
```

**Pass criteria:**
- Zero null values in critical columns
- At least 500 fraud-labeled transactions
- Date range spans 180+ days
- Multiple channels present (UPI, NEFT, RTGS minimum)

---

### T3 · Replace NetworkX with Neo4j Community (Docker) `CRITICAL`

**What to do:**  
Pull Neo4j Community Edition via Docker. Rewrite `graph_builder.py` to use the bolt driver instead of in-memory NetworkX. NetworkX stays as a fallback for algorithm development only.

**Docker setup:**
```bash
docker pull neo4j:5-community
docker run \
  --name neo4j-graphsentinel \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/graphsentinel123 \
  -v $PWD/neo4j/data:/data \
  neo4j:5-community
```

**Updated graph_builder.py:**
```python
from neo4j import GraphDatabase

class GraphBuilder:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "graphsentinel123")
        )

    def build_from_transactions(self, transactions: list):
        with self.driver.session() as session:
            for txn in transactions:
                session.run("""
                    MERGE (a:Account {id: $sender_id})
                    MERGE (b:Account {id: $receiver_id})
                    CREATE (a)-[:TRANSFER {
                        txn_id: $txn_id,
                        amount: $amount,
                        timestamp: $timestamp,
                        channel: $channel
                    }]->(b)
                """, **txn.__dict__)
```

**Why Neo4j over NetworkX:**  
NetworkX loads entire graph into RAM — dies above 500K transactions. Neo4j persists to disk, runs native Cypher queries, and the visual browser (localhost:7474) lets judges interact with the graph directly during Q&A.

---

### T4 · Build Directed Graph Schema in Neo4j `CRITICAL`

**Node labels and properties:**

```cypher
// Account node
CREATE (a:Account {
  account_id: "ACC_0047",
  account_type: "Current",         // Savings | Current | Loan | FD
  created_date: date("2019-03-14"),
  last_active_date: date("2024-03-01"),
  last_txn_date: date("2024-03-01"),
  status: "Active",                // Active | Dormant | Frozen
  balance: 1250.00,
  kyc_status: "Verified",
  declared_income: 420000,
  risk_rating: "Low"
})

// Transaction edge
CREATE (sender)-[:TRANSFER {
  txn_id: "TXN_000123",
  amount: 50000.00,
  timestamp: datetime("2024-03-14T14:30:00"),
  channel: "UPI",                  // UPI | NEFT | RTGS | IMPS | SWIFT | ATM
  account_type: "Current",
  device_id: "DEV_abc123",
  ip_address: "192.168.1.1"        // hashed in production
}]->(receiver)
```

**Indexes to create:**
```cypher
CREATE INDEX account_id_idx FOR (a:Account) ON (a.account_id);
CREATE INDEX txn_timestamp_idx FOR ()-[t:TRANSFER]-() ON (t.timestamp);
CREATE INDEX txn_amount_idx FOR ()-[t:TRANSFER]-() ON (t.amount);
```

---

### T5 · Add last_active_date and last_txn_date to Account Node `CRITICAL`

**Why this is critical:**  
Dormant activation detection (Fraud Type 4) requires knowing how long an account was inactive. Without `last_txn_date`, you cannot compute dormancy window. This field is missing from the current schema and breaks one of the 6 PS3-required fraud patterns.

**Add to ingestor.py:**
```python
from datetime import datetime, timedelta
import random

def compute_dormancy(account_id: str, transactions_df) -> dict:
    account_txns = transactions_df[
        (transactions_df['sender_id'] == account_id) |
        (transactions_df['receiver_id'] == account_id)
    ].sort_values('timestamp')

    if len(account_txns) == 0:
        return {'last_active_date': None, 'dormancy_days': None}

    last_txn = account_txns.iloc[-1]['timestamp']
    dormancy_days = (datetime.now() - pd.to_datetime(last_txn)).days

    return {
        'last_txn_date': last_txn,
        'last_active_date': last_txn,
        'dormancy_days': dormancy_days
    }
```

**Dormancy threshold:** 90 days (configurable in `config.yaml`)

---

### T6 · Set Up docker-compose.yml with All Services `CRITICAL`

**What to do:**  
Create a single `docker-compose.yml` that starts the entire GraphSentinel stack with one command. This is the most important infrastructure task — judges should be able to run the system in under 5 minutes.

```yaml
version: '3.9'

services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=graphsentinel123
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://gs:gs@postgres:5432/graphsentinel
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on: [neo4j, redis, postgres, kafka]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

  neo4j:
    image: neo4j:5-community
    ports: ["7474:7474", "7687:7687"]
    environment:
      - NEO4J_AUTH=neo4j/graphsentinel123
    volumes: ["./neo4j/data:/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=gs
      - POSTGRES_PASSWORD=gs
      - POSTGRES_DB=graphsentinel
    volumes: ["./postgres/data:/var/lib/postgresql/data"]

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      - ZOOKEEPER_CLIENT_PORT=2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports: ["9092:9092"]
    environment:
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
    depends_on: [zookeeper]
```

**Run command:**
```bash
cp .env.example .env          # add ANTHROPIC_API_KEY
docker-compose up --build     # first time
docker-compose up             # subsequent runs
```

---

### T7 · Set Up Kafka Producer (Replaces CSV Loader)

**What to do:**  
Replace the static CSV file loader with a Kafka producer that streams transactions. The ingestor becomes a Kafka consumer. Same code runs at 1M txns/day in production — just change broker count.

```python
# producer.py — reads IBM AMLSim CSV, publishes to Kafka
from kafka import KafkaProducer
import json, pandas as pd, time

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

df = pd.read_csv('data/transactions.csv')
for _, row in df.iterrows():
    producer.send('transactions', row.to_dict())
    time.sleep(0.05)  # 20 txns/second for demo

# consumer in ingestor.py
from kafka import KafkaConsumer
consumer = KafkaConsumer('transactions', bootstrap_servers=['localhost:9092'])
for message in consumer:
    txn = json.loads(message.value)
    process_transaction(txn)
```

**Demo pitch line:** *"Same pipeline runs at 1M transactions per day in production — we just scale the broker count."*

---

## Phase 2 — Detection Algorithms 🔴

> Goal: Replace raw DFS with production-grade algorithms. Each algorithm should be a standalone function in `pattern_detector.py` so they can be swapped independently.

---

### T8 · Replace DFS with Tarjan's SCC Cycle Detection `CRITICAL`

**What to do:**  
Replace the current raw DFS cycle detection with Tarjan's Strongly Connected Components algorithm. O(V+E) single pass — finds all cycles at once, no repeated traversal.

**NetworkX implementation:**
```python
import networkx as nx

def detect_cycles(G: nx.DiGraph) -> list:
    """
    Returns list of suspicious SCCs (cycles with 3+ nodes).
    Tarjan's SCC: O(V+E) — single pass, no stack overflow.
    """
    sccs = list(nx.strongly_connected_components(G))
    suspicious = [
        scc for scc in sccs
        if len(scc) >= 3  # minimum cycle size
    ]
    return suspicious
```

**Neo4j Cypher equivalent:**
```cypher
// Find all cycles up to 8 hops
MATCH path = (a:Account)-[:TRANSFER*3..8]->(a)
WHERE ALL(r IN relationships(path) WHERE r.timestamp > datetime() - duration({days: 90}))
RETURN a.account_id, length(path) as cycle_length,
       [n IN nodes(path) | n.account_id] as cycle_nodes
ORDER BY cycle_length
```

**Why better than DFS:**
- DFS from every node = O(V × (V+E)) — quadratic on large graphs
- Tarjan's = O(V+E) total — linear, single pass
- No recursive stack overflow on deep graphs
- Finds ALL cycles simultaneously

---

### T9 · Implement Louvain Community Detection `CRITICAL`

**What to do:**  
Add Louvain community detection to find fraud rings that are NOT perfect cycles — dense clusters of accounts moving money between each other.

```bash
pip install python-louvain networkx
```

```python
import community as community_louvain
import networkx as nx

def detect_fraud_rings(G: nx.DiGraph) -> list:
    """
    Louvain detects dense account clusters (mule networks, rings).
    O(n log n) — scales to 100K+ nodes.
    """
    G_undirected = G.to_undirected()
    partition = community_louvain.best_partition(G_undirected)

    # Group nodes by community
    communities = {}
    for node, comm_id in partition.items():
        communities.setdefault(comm_id, []).append(node)

    # Flag high-risk communities
    suspicious = []
    for comm_id, nodes in communities.items():
        subgraph = G.subgraph(nodes)
        density = nx.density(subgraph)
        if density > 0.3 and len(nodes) >= 4:
            suspicious.append({
                'community_id': comm_id,
                'nodes': nodes,
                'density': density,
                'pattern_type': 'HubAndSpoke'
            })

    return suspicious
```

**What Louvain catches that cycle detection misses:**  
A 10-account mule network where money flows irregularly between members — not a clean A→B→C→A cycle, but a dense web. Louvain sees the density and flags it.

---

### T10 · Implement Reverse BFS Backtracking

**What to do:**  
Start from a suspicious endpoint (large withdrawal, known high-risk account) and trace backwards through predecessors. Legitimate money traces back 1–3 hops. Fraudulent money explodes wide — 8–12 predecessor accounts.

```python
from collections import deque

def reverse_trace(G: nx.DiGraph, suspect_node: str, max_depth: int = 12) -> dict:
    """
    Backtrack from suspect node through incoming edges.
    Returns trace width at each depth level.
    Legit: depth 3 → 1-3 predecessors
    Fraud: depth 3 → 8-12 predecessors (fan-in)
    """
    visited = {suspect_node}
    queue = deque([(suspect_node, 0)])
    depth_counts = {}

    while queue:
        node, depth = queue.popleft()
        if depth >= max_depth:
            continue

        predecessors = list(G.predecessors(node))
        depth_counts[depth] = depth_counts.get(depth, 0) + len(predecessors)

        for pred in predecessors:
            if pred not in visited:
                visited.add(pred)
                queue.append((pred, depth + 1))

    # Flag if trace width > 5 at any depth level
    is_suspicious = any(count > 5 for count in depth_counts.values())

    return {
        'trace_width': depth_counts,
        'total_predecessors': len(visited) - 1,
        'is_suspicious': is_suspicious,
        'pattern_type': 'Layering' if is_suspicious else 'Normal'
    }
```

---

### T11 · Implement Temporal Motif Detector

**What to do:**  
Detect the dormant→ping→burst temporal motif — the early warning signal of a mule network activating. Can predict fraud 12–48 hours before the main layering begins.

```python
from datetime import datetime, timedelta

def detect_dormant_motif(G: nx.DiGraph, node: str,
                          account_data: dict) -> dict:
    """
    Dormant motif: inactive (>90d) → small test ping (<500) → burst (>10K)
    Triggers 12-48h early warning before main layering.
    """
    dormancy_days = account_data.get('dormancy_days', 0)

    if dormancy_days < 90:
        return {'motif_detected': False}

    # Get recent edges sorted by timestamp
    recent_edges = sorted([
        (u, v, d) for u, v, d in G.edges(node, data=True)
        if d.get('timestamp') > datetime.now() - timedelta(days=7)
    ], key=lambda x: x[2]['timestamp'])

    if len(recent_edges) < 2:
        return {'motif_detected': False}

    # Check for ping → burst pattern
    first_amount = recent_edges[0][2]['amount']
    latest_amount = recent_edges[-1][2]['amount']
    time_gap = (recent_edges[-1][2]['timestamp'] -
                recent_edges[0][2]['timestamp']).total_seconds() / 3600

    motif_detected = (
        first_amount < 500 and        # small test ping
        latest_amount > 10000 and     # large burst follows
        time_gap < 48                 # within 48 hours
    )

    return {
        'motif_detected': motif_detected,
        'dormancy_days': dormancy_days,
        'ping_amount': first_amount,
        'burst_amount': latest_amount,
        'hours_between': round(time_gap, 1),
        'pattern_type': 'DormantActivation',
        'risk_signal': 'EARLY_WARNING' if motif_detected else None
    }
```

---

### T12 · Add PageRank + Approximate Betweenness Centrality

**What to do:**  
PageRank identifies kingpin nodes (central to many fund flows). Betweenness centrality identifies bridge accounts (sitting between two fraud clusters). Use approximate betweenness — sampling 10% of nodes reduces complexity from O(V×E) to manageable.

```python
def compute_centrality(G: nx.DiGraph, sample_ratio: float = 0.1) -> dict:
    """
    PageRank: O(V+E × iterations). Identifies high-influence nodes.
    Approximate betweenness: O(k×E) where k = sample size.
    10% sample = 100x speedup with <5% accuracy loss.
    """
    pagerank = nx.pagerank(G, alpha=0.85, max_iter=100)

    # Approximate betweenness — sample k nodes as sources
    k = max(1, int(len(G.nodes()) * sample_ratio))
    betweenness = nx.betweenness_centrality(G, k=k, normalized=True)

    return {
        'pagerank': pagerank,
        'betweenness': betweenness,
        # Top 10 by each metric
        'top_pagerank': sorted(pagerank.items(), key=lambda x: -x[1])[:10],
        'top_betweenness': sorted(betweenness.items(), key=lambda x: -x[1])[:10]
    }
```

**Add as risk signals:**
- PageRank > 0.05 → +10 to structural score
- Betweenness > 0.1 → +15 (bridge account = pass-through indicator)

---

### T13 · Add Channel + Branch Color Coding to Graph Edges

**What to do:**  
PS3 explicitly requires tracking funds across channels and branches. Add channel as a visible property on every graph edge. This is a 10-line change that directly satisfies a PS3 requirement judges will check.

```python
# In graph_builder.py
CHANNEL_COLORS = {
    'UPI':   '#378ADD',   # blue
    'NEFT':  '#EF9F27',   # amber
    'RTGS':  '#1D9E75',   # teal
    'IMPS':  '#7F77DD',   # purple
    'SWIFT': '#D85A30',   # coral/red
    'ATM':   '#888780',   # gray
}

# Pass to frontend as edge property
edge_data['color'] = CHANNEL_COLORS.get(txn.channel, '#888780')
edge_data['channel'] = txn.channel
edge_data['width'] = min(10, txn.amount / 50000)  # thickness = amount
```

**Frontend legend (add to GraphVisualizer.tsx):**
```
UPI ■  NEFT ■  RTGS ■  IMPS ■  SWIFT ■  ATM ■
```

---

### T14 · Add Profile Mismatch Detection

**What to do:**  
Detect mismatches between declared customer income and actual transaction volume — a direct PS3 requirement. Add `declared_income` to synthetic data and flag accounts where monthly flow exceeds 3× declared income.

```python
def detect_profile_mismatch(node: str, account_data: dict,
                             G: nx.DiGraph) -> dict:
    declared_income = account_data.get('declared_income', 0)
    if not declared_income:
        return {'mismatch_detected': False}

    # Sum last 30 days of transactions
    cutoff = datetime.now() - timedelta(days=30)
    monthly_flow = sum(
        d['amount'] for _, _, d in G.edges(node, data=True)
        if d.get('timestamp', datetime.min) > cutoff
    )

    mismatch_ratio = monthly_flow / (declared_income / 12)

    return {
        'mismatch_detected': mismatch_ratio > 3.0,
        'declared_monthly': round(declared_income / 12, 2),
        'actual_monthly': round(monthly_flow, 2),
        'mismatch_ratio': round(mismatch_ratio, 2),
        'risk_signal': +25 if mismatch_ratio > 3.0 else 0
    }
```

---

## Phase 3 — ML Layer 🟠

> Goal: Add Isolation Forest (unsupervised) and XGBoost (supervised) as two independent ML scores alongside the existing rule-based risk score. Both scores show in every alert row.

---

### T15 · Extract Graph Feature Vectors for ML `CRITICAL`

**What to do:**  
Build a feature extraction function that converts each account node's graph properties into a numerical vector. This is the input to both ML models.

```python
import numpy as np

def extract_node_features(G: nx.DiGraph, node: str,
                           account_data: dict) -> np.ndarray:
    """
    Extracts 10 numerical features per account node.
    Same features used by both Isolation Forest and XGBoost.
    """
    in_deg = G.in_degree(node)
    out_deg = G.out_degree(node)
    total_deg = in_deg + out_deg

    in_amounts = [d['amount'] for _, _, d in G.in_edges(node, data=True)]
    out_amounts = [d['amount'] for _, _, d in G.out_edges(node, data=True)]

    total_in = sum(in_amounts)
    total_out = sum(out_amounts)
    in_out_ratio = total_in / (total_out + 1e-6)

    channels = set(d['channel'] for _, _, d in G.edges(node, data=True))
    channel_mix = len(channels)

    timestamps = [d['timestamp'] for _, _, d in G.edges(node, data=True)]
    off_hours_count = sum(
        1 for t in timestamps
        if hasattr(t, 'hour') and (t.hour < 6 or t.hour >= 22)
    )
    off_hours_ratio = off_hours_count / (len(timestamps) + 1e-6)

    dormancy_days = account_data.get('dormancy_days', 0) or 0

    return np.array([
        in_deg,            # 1. incoming connections
        out_deg,           # 2. outgoing connections
        in_out_ratio,      # 3. flow balance (1.0 = pass-through)
        total_in,          # 4. total incoming amount
        total_out,         # 5. total outgoing amount
        channel_mix,       # 6. number of unique channels used
        off_hours_ratio,   # 7. fraction of off-hours transactions
        dormancy_days,     # 8. days since last active
        len(in_amounts),   # 9. transaction count
        np.std(in_amounts) if in_amounts else 0  # 10. amount variance
    ])
```

---

### T16 · Train Isolation Forest (Unsupervised) `CRITICAL`

**What to do:**  
Train an Isolation Forest on normal transaction features. No fraud labels needed — it learns what normal looks like and flags deviations. Threshold 0.65 = suspicious.

```python
from sklearn.ensemble import IsolationForest
import joblib
import numpy as np

def train_isolation_forest(feature_matrix: np.ndarray) -> IsolationForest:
    """
    Unsupervised — no labels needed.
    contamination=0.01 assumes ~1% of transactions are anomalous.
    Training time: ~30 seconds on 100K transactions.
    """
    model = IsolationForest(
        n_estimators=100,
        contamination=0.01,
        random_state=42,
        n_jobs=-1        # use all CPU cores
    )
    model.fit(feature_matrix)
    joblib.dump(model, 'models/isolation_forest.pkl')
    return model

def score_with_if(model: IsolationForest,
                   features: np.ndarray) -> float:
    """
    Returns anomaly score 0–1.
    >0.65 = suspicious. >0.85 = high risk.
    """
    raw_score = model.decision_function([features])[0]
    # Convert to 0-1 range (higher = more anomalous)
    normalized = 1 - (raw_score - model.offset_) / (
        model.decision_function([features * 0]).mean() - model.offset_ + 1e-6
    )
    return float(np.clip(normalized, 0, 1))
```

---

### T17 · Train XGBoost Classifier on IBM AMLSim Labels `CRITICAL`

**What to do:**  
Train XGBoost using the fraud labels from IBM AMLSim `alert_patterns.csv`. Outputs fraud probability 0–1 per account. Target: 85%+ accuracy on held-out test set.

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

def train_xgboost(X: np.ndarray, y: np.ndarray):
    """
    Supervised fraud classifier.
    X: feature matrix (n_accounts × 10 features)
    y: fraud labels from IBM AMLSim alert_patterns.csv
    Training time: 2-5 minutes on 100K samples.
    Target accuracy: 85%+
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=99,   # handles class imbalance (1% fraud)
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        early_stopping_rounds=20,
        verbose=False
    )

    # Evaluate
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred,
          target_names=['Normal', 'Fraud']))

    joblib.dump(model, 'models/xgboost_fraud.pkl')
    return model

def score_with_xgb(model, features: np.ndarray) -> float:
    """Returns fraud probability 0–1."""
    return float(model.predict_proba([features])[0][1])
```

---

### T18 · Wire Both ML Scores into risk_scorer.py `CRITICAL`

**What to do:**  
Integrate both ML models into the existing risk scoring pipeline. Final score combines structural rule-based score with both ML predictions. Show scores separately in the UI.

```python
import joblib

class RiskScorer:
    def __init__(self):
        self.if_model = joblib.load('models/isolation_forest.pkl')
        self.xgb_model = joblib.load('models/xgboost_fraud.pkl')

    def score(self, subgraph_data: dict) -> dict:
        features = extract_node_features(
            subgraph_data['graph'],
            subgraph_data['primary_node'],
            subgraph_data['account_data']
        )

        structural_score = self._compute_structural(subgraph_data)
        if_score = score_with_if(self.if_model, features)
        xgb_score = score_with_xgb(self.xgb_model, features)

        # Composite: structural 50%, IF 25%, XGB 25%
        composite = (
            structural_score * 0.50 +
            if_score * 100 * 0.25 +
            xgb_score * 100 * 0.25
        )

        # Apply innocence discount (max 30%)
        innocence_discount = self._compute_innocence(subgraph_data)
        final_score = composite * (1 - min(innocence_discount, 0.30))

        return {
            'final_score': round(final_score),
            'structural_score': round(structural_score),
            'if_score': round(if_score, 3),
            'xgb_score': round(xgb_score, 3),
            'innocence_discount': round(innocence_discount, 2),
            'threshold': self._get_threshold(final_score)
        }

    def _get_threshold(self, score: float) -> str:
        if score >= 90: return 'CRITICAL'
        if score >= 70: return 'HIGH'
        if score >= 40: return 'ELEVATED'
        return 'MONITOR'
```

---

### T19 · Add Feature Importance Display to ML Tab

Show XGBoost feature importances in the frontend ML tab so judges can see which signals matter most.

```python
# In /api/ml-info endpoint
def get_feature_importance():
    model = joblib.load('models/xgboost_fraud.pkl')
    feature_names = [
        'in_degree', 'out_degree', 'in_out_ratio',
        'total_in', 'total_out', 'channel_mix',
        'off_hours_ratio', 'dormancy_days',
        'txn_count', 'amount_variance'
    ]
    importances = model.feature_importances_
    return dict(zip(feature_names, importances.tolist()))
```

---

### T20 · Build Feedback Storage Tables in PostgreSQL

```sql
-- Investigator decisions
CREATE TABLE investigator_decisions (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(50) NOT NULL,
    decision VARCHAR(20) NOT NULL,  -- 'confirmed_fraud' | 'false_positive' | 'unclear'
    confidence INTEGER,              -- 1-5
    pattern_type VARCHAR(50),
    notes TEXT,
    investigator_id VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Scorer configuration (weights)
CREATE TABLE scorer_config (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,
    signal_weights JSONB NOT NULL,
    innocence_discounts JSONB NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trusted accounts (cleared false positives)
CREATE TABLE trusted_accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    reason TEXT,
    cleared_by VARCHAR(50),
    cleared_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ
);
```

---

### T21 · Implement Feedback → Weight Adjustment Loop

```python
def process_feedback(alert_id: str, decision: str,
                     confidence: int, pattern_type: str):
    """
    On false_positive with confidence 5:
    - Increase innocence discount weight for this pattern type
    - Recompute alert score
    - Increment model_version
    """
    if decision == 'false_positive' and confidence >= 4:
        # Increase GST innocence discount for this pattern
        current_config = db.get_scorer_config(pattern_type)
        current_discount = current_config['innocence_discounts']['gst_verified']

        # Gradual adjustment: +2% per confirmed false positive
        new_discount = min(0.30, current_discount + 0.02)

        db.update_scorer_config(
            pattern_type=pattern_type,
            innocence_discounts={'gst_verified': new_discount},
            model_version=increment_version(current_config['model_version'])
        )

        # Recompute affected alert score
        recompute_alert_score(alert_id)
```

---

## Phase 4 — Privacy & Security 🟠

> Goal: Implement production-grade PII protection. All data passed to the Claude API must be tokenized. No raw account IDs, names, or PAN numbers ever leave the local environment.

---

### T22 · Implement TokenVault with SHA-256 + Per-Session Salt `CRITICAL`

```python
import hashlib
import secrets
from typing import Optional

class TokenVault:
    """
    Per-session PII tokenization with SHA-256 + random salt.
    Vault mapping stored in memory only — never persisted.
    New salt generated every pipeline run.
    """
    def __init__(self):
        self.session_salt = secrets.token_hex(32)  # 256-bit random salt
        self._vault: dict[str, str] = {}           # token → real_id
        self._reverse: dict[str, str] = {}         # real_id → token

    def tokenize(self, account_id: str, role: str) -> str:
        """
        role: 'CYCLE_ORIGIN' | 'HUB_NODE' | 'SPOKE_001' | 'AGGREGATION_TARGET'
        Role-based NOT sequential (HOP_1, HOP_2) — preserves graph topology.
        """
        if account_id in self._reverse:
            return self._reverse[account_id]

        salted = f"{self.session_salt}:{account_id}"
        hash_val = hashlib.sha256(salted.encode('utf-8')).hexdigest()[:12]
        token = f"{role}_{hash_val}"

        self._vault[token] = account_id
        self._reverse[account_id] = token
        return token

    def detokenize(self, token: str) -> Optional[str]:
        return self._vault.get(token)

    def detokenize_text(self, text: str) -> str:
        """Replace all tokens in LLM output with real account IDs."""
        for token, real_id in self._vault.items():
            text = text.replace(token, real_id)
        return text

    def tokenize_subgraph(self, subgraph: dict,
                          pattern_type: str) -> dict:
        """
        Tokenize all account IDs in a subgraph using pattern-aware roles.
        Cycle: CYCLE_ORIGIN, CYCLE_INTERMEDIARY_N, CYCLE_CLOSURE
        Hub: HUB_NODE, SPOKE_001..N, TERMINAL_BENEFICIARY
        Smurfing: AGGREGATION_TARGET, SOURCE_001..N
        """
        tokenized_nodes = []
        tokenized_edges = []

        for i, node in enumerate(subgraph['nodes']):
            role = self._assign_role(node, subgraph, pattern_type, i)
            token = self.tokenize(node['account_id'], role)
            tokenized_nodes.append({**node, 'token': token, 'account_id': '[PROTECTED]'})

        for edge in subgraph['edges']:
            tokenized_edges.append({
                **edge,
                'sender_id': self._reverse.get(edge['sender_id'], edge['sender_id']),
                'receiver_id': self._reverse.get(edge['receiver_id'], edge['receiver_id']),
                'annotation': self._annotate_edge(edge, pattern_type)
            })

        return {'nodes': tokenized_nodes, 'edges': tokenized_edges}

    def _assign_role(self, node, subgraph, pattern_type, index) -> str:
        if pattern_type == 'Cycle':
            if index == 0: return 'CYCLE_ORIGIN'
            if index == len(subgraph['nodes']) - 1: return 'CYCLE_CLOSURE'
            return f'CYCLE_INTERMEDIARY_{index}'
        elif pattern_type == 'HubAndSpoke':
            if node.get('is_hub'): return 'HUB_NODE'
            return f'SPOKE_{str(index).zfill(3)}'
        elif pattern_type == 'Smurfing':
            if node.get('is_target'): return 'AGGREGATION_TARGET'
            return f'SOURCE_{str(index).zfill(3)}'
        return f'NODE_{str(index).zfill(3)}'

    def _annotate_edge(self, edge, pattern_type) -> str:
        if pattern_type == 'Cycle' and edge.get('is_closure'):
            return '[CLOSURE_EDGE: completes directed cycle back to CYCLE_ORIGIN]'
        if pattern_type == 'Smurfing':
            return '[FAN_IN_EDGE: one of N convergent transfers to AGGREGATION_TARGET]'
        return ''
```

**Why per-session salt is non-negotiable:**  
Without salt: SHA-256("ACC_0047") always = same hash. Attacker who intercepts two API calls can correlate tokens across sessions. With `secrets.token_hex(32)`, same account produces completely different token every run. Mathematically irreversible without the vault.

---

### T23 · Implement detokenize_text() for LLM Responses `CRITICAL`

**Already covered in TokenVault class above. Key rule:**  
Always call `vault.detokenize_text(llm_response)` before rendering any LLM output in the frontend. Investigators see real account numbers. The vault never touches the network.

---

### T24 · Add Edge Annotations to LLM Prompt

**What to do:**  
Include structural annotations in the Claude prompt so the LLM understands the topology without needing raw account IDs.

```python
def build_llm_prompt(tokenized_subgraph: dict, risk_score: int,
                     pattern_type: str, vault: TokenVault) -> str:
    return f"""You are a senior AML investigator assistant.
Analyze this flagged transaction pattern and draft a SAR narrative.

PATTERN TYPE: {pattern_type}
RISK SCORE: {risk_score}/100

TRANSACTION GRAPH (all account IDs are tokenized for privacy):
{format_subgraph(tokenized_subgraph)}

STRUCTURAL ANNOTATIONS:
{format_annotations(tokenized_subgraph['edges'])}

RISK SIGNALS:
{format_risk_signals(tokenized_subgraph)}

Write a 3-paragraph SAR narrative explaining:
1. What suspicious pattern was detected and why it is suspicious
2. The timeline and amounts involved
3. Recommended investigator actions

Use only the token labels (CYCLE_ORIGIN, HUB_NODE etc.) — do not invent account numbers."""
```

---

### T25 · Add JWT Authentication to FastAPI

```python
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")  # 'investigator' | 'senior_analyst'
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401)

# Protect endpoints
@app.get("/api/sar/{alert_id}")
async def get_sar(alert_id: str, user=Depends(get_current_user)):
    log_action(user['user_id'], 'SAR_VIEW', alert_id)
    return generate_sar(alert_id)
```

---

### T26 · Build Audit Log Table in PostgreSQL

```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    -- e.g. ALERT_VIEW | SAR_GENERATE | SAR_EXPORT | FEEDBACK_SUBMIT | PIPELINE_RUN
    alert_id VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    details JSONB
);

CREATE INDEX audit_user_idx ON audit_log(user_id);
CREATE INDEX audit_timestamp_idx ON audit_log(timestamp);
CREATE INDEX audit_alert_idx ON audit_log(alert_id);
```

---

### T27 · Move All Secrets to .env with python-dotenv

```bash
# .env.example
ANTHROPIC_API_KEY=your_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graphsentinel123
POSTGRES_URL=postgresql://gs:gs@localhost:5432/graphsentinel
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=generate_a_strong_random_key_here
```

```python
# In every config file
from dotenv import load_dotenv
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
```

---

## Phase 5 — SAR Chatbot + RAG 🟠

> Goal: Build a conversational investigation interface where investigators can interrogate SAR documents and fraud cases using plain English. This is GraphSentinel's primary differentiator.

---

### T28 · Build /api/sar-chat Endpoint in FastAPI `CRITICAL`

```python
from fastapi.responses import StreamingResponse
from anthropic import Anthropic

client = Anthropic()

@app.post("/api/sar-chat")
async def sar_chat(request: SARChatRequest):
    """
    request.alert_id: which case to discuss
    request.message: investigator's question
    request.history: previous conversation turns
    """
    # Fetch case context
    alert = db.get_alert(request.alert_id)
    sar_draft = db.get_sar_draft(request.alert_id)
    subgraph = db.get_subgraph(request.alert_id)

    # Tokenize before sending
    vault = TokenVault()
    tokenized_subgraph = vault.tokenize_subgraph(subgraph, alert.pattern_type)

    system_prompt = f"""You are a senior AML investigator assistant for GraphSentinel.
You have access to the following fraud case:

ALERT ID: {request.alert_id}
PATTERN: {alert.pattern_type}
RISK SCORE: {alert.risk_score}/100
ML SCORES: Isolation Forest {alert.if_score} · XGBoost {alert.xgb_score}

SAR DRAFT:
{sar_draft}

GRAPH DATA (tokenized):
{format_subgraph(tokenized_subgraph)}

Answer the investigator's questions using only this case data.
Be specific, cite node tokens and amounts.
If asked to draft FIU content, use formal regulatory language."""

    async def generate():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=request.history + [
                {"role": "user", "content": request.message}
            ]
        ) as stream:
            for text in stream.text_stream:
                # Detokenize before sending to frontend
                safe_text = vault.detokenize_text(text)
                yield f"data: {safe_text}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

### T29 · Set Up ChromaDB for SAR Vector Store

```bash
pip install chromadb sentence-transformers
```

```python
import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('all-MiniLM-L6-v2')  # local, free, fast
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("sar_reports")

def index_sar(alert_id: str, sar_text: str):
    """
    Called every time a SAR is generated.
    Chunks SAR into 4 sections and embeds each.
    """
    sections = {
        'summary': extract_section(sar_text, 'EXECUTIVE SUMMARY'),
        'entities': extract_section(sar_text, 'ENTITY TIMELINE'),
        'signals': extract_section(sar_text, 'RISK SIGNALS'),
        'actions': extract_section(sar_text, 'INVESTIGATOR ACTIONS')
    }

    for section_name, content in sections.items():
        embedding = embedder.encode(content).tolist()
        collection.add(
            embeddings=[embedding],
            documents=[content],
            ids=[f"{alert_id}_{section_name}"],
            metadatas=[{'alert_id': alert_id, 'section': section_name}]
        )
```

---

### T30 · Implement RAG Retrieval for Multi-Report Chat

```python
def retrieve_relevant_context(query: str, current_alert_id: str,
                               top_k: int = 3) -> list[str]:
    """
    Enables: "Compare this with last week's hub-spoke case"
    or: "Has ACC_0047 appeared in other reports?"
    """
    query_embedding = embedder.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"alert_id": {"$ne": current_alert_id}}  # exclude current case
    )

    return results['documents'][0] if results['documents'] else []

# Inject into chatbot system prompt
def build_rag_context(query: str, alert_id: str) -> str:
    similar_cases = retrieve_relevant_context(query, alert_id)
    if not similar_cases:
        return ""
    return f"""
SIMILAR CASES FROM HISTORY:
{chr(10).join(similar_cases)}

Use these only if directly relevant to the investigator's question."""
```

---

### T31 · Build LangChain Agent with 4 Tools

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool

@tool
def get_alert_details(alert_id: str) -> str:
    """Get full details of a fraud alert including risk score and pattern type."""
    return json.dumps(db.get_alert(alert_id))

@tool
def get_subgraph(alert_id: str) -> str:
    """Get the transaction subgraph for a specific alert."""
    return json.dumps(db.get_subgraph(alert_id))

@tool
def get_sar_draft(alert_id: str) -> str:
    """Get the pre-generated SAR draft for an alert."""
    return db.get_sar_draft(alert_id)

@tool
def query_similar_cases(pattern_type: str) -> str:
    """Find similar fraud cases by pattern type from history."""
    return json.dumps(db.get_alerts_by_pattern(pattern_type, limit=5))

tools = [get_alert_details, get_subgraph, get_sar_draft, query_similar_cases]
llm = ChatAnthropic(model="claude-sonnet-4-6")
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

---

### T32 · Add 4 Pre-Written Question Buttons to Chatbot UI

**In SAR tab (React component):**
```tsx
const QUICK_QUESTIONS = [
  { label: "Why was this flagged?", prompt: "Explain in plain English why this alert was flagged and what makes it suspicious." },
  { label: "Who is the key node?", prompt: "Which account is the most central to this fraud pattern and why?" },
  { label: "Show money trail", prompt: "Describe the complete path the money took, with amounts and timestamps." },
  { label: "Draft FIU note", prompt: "Draft a formal one-paragraph FIU-IND submission note for this case." },
];

{QUICK_QUESTIONS.map(q => (
  <button key={q.label} onClick={() => sendMessage(q.prompt)}
    style={{fontSize:'11px', padding:'4px 10px', marginRight:'6px', marginBottom:'6px'}}>
    {q.label}
  </button>
))}
```

---

### T33 · Implement Streaming Response in Chatbot UI

```tsx
// In SAR chatbot component
async function sendMessage(message: string) {
  setIsStreaming(true);
  const response = await fetch('/api/sar-chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({alert_id: selectedAlert, message, history: chatHistory})
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let fullResponse = '';

  while (true) {
    const {done, value} = await reader!.read();
    if (done) break;
    const chunk = decoder.decode(value).replace('data: ', '');
    fullResponse += chunk;
    setCurrentResponse(fullResponse);  // updates live as tokens stream
  }

  setChatHistory(prev => [...prev,
    {role: 'user', content: message},
    {role: 'assistant', content: fullResponse}
  ]);
  setIsStreaming(false);
}
```

---

## Phase 6 — Frontend & UX 🟠

> Goal: Every feature that judges will directly see and interact with. Prioritize node click panel and SAR report — these are the two most visually impactful additions.

---

### T34 · Node Click → Account Detail Panel `CRITICAL`

**In GraphVisualizer.tsx:**
```tsx
const [selectedNode, setSelectedNode] = useState(null);

<ForceGraph2D
  onNodeClick={(node) => {
    fetch(`/api/node/${node.id}`)
      .then(r => r.json())
      .then(data => setSelectedNode(data));
  }}
/>

{selectedNode && (
  <div style={{position:'absolute', right:0, top:0, width:'280px',
    height:'100%', background:'var(--bg)', borderLeft:'0.5px solid var(--border)',
    padding:'16px', overflowY:'auto'}}>

    <div style={{display:'flex', justifyContent:'space-between', marginBottom:'12px'}}>
      <span style={{fontWeight:500}}>{selectedNode.account_id}</span>
      <button onClick={() => setSelectedNode(null)}>✕</button>
    </div>

    <RiskBadge score={selectedNode.risk_score} />

    <DetailRow label="Account type" value={selectedNode.account_type} />
    <DetailRow label="Created" value={selectedNode.created_date} />
    <DetailRow label="Last active" value={selectedNode.last_active_date} />
    <DetailRow label="Dormant days" value={selectedNode.dormancy_days} />
    <DetailRow label="KYC status" value={selectedNode.kyc_status} />
    <DetailRow label="Declared income" value={`₹${selectedNode.declared_income?.toLocaleString()}`} />

    <Divider label="Transaction stats" />
    <DetailRow label="Total in" value={`₹${selectedNode.total_in?.toLocaleString()}`} />
    <DetailRow label="Total out" value={`₹${selectedNode.total_out?.toLocaleString()}`} />
    <DetailRow label="In/out ratio" value={selectedNode.in_out_ratio?.toFixed(2)} />
    <DetailRow label="Transactions" value={selectedNode.txn_count} />

    <Divider label="ML scores" />
    <MLScoreBar label="Isolation Forest" score={selectedNode.if_score} />
    <MLScoreBar label="XGBoost" score={selectedNode.xgb_score} />

    <div style={{display:'flex', gap:'8px', marginTop:'16px'}}>
      <button onClick={() => investigateNode(selectedNode.account_id)}>Investigate</button>
      <button onClick={() => generateSAR(selectedNode.account_id)}>Generate SAR</button>
    </div>
  </div>
)}
```

---

### T35 · Add Channel Color Coding to Graph Edges

```tsx
// In GraphVisualizer.tsx
const CHANNEL_COLORS = {
  'UPI':   '#378ADD',
  'NEFT':  '#EF9F27',
  'RTGS':  '#1D9E75',
  'IMPS':  '#7F77DD',
  'SWIFT': '#D85A30',
  'ATM':   '#888780',
};

<ForceGraph2D
  linkColor={(link) => CHANNEL_COLORS[link.channel] || '#888780'}
  linkWidth={(link) => Math.min(5, link.amount / 100000)}
  linkDirectionalArrowLength={4}
  linkDirectionalArrowRelPos={1}
/>

// Legend below graph
<div style={{display:'flex', gap:'12px', marginTop:'8px', fontSize:'11px'}}>
  {Object.entries(CHANNEL_COLORS).map(([channel, color]) => (
    <span key={channel}>
      <span style={{background:color, width:'10px', height:'10px',
        borderRadius:'2px', display:'inline-block', marginRight:'4px'}}/>
      {channel}
    </span>
  ))}
</div>
```

---

### T36 · Add Zustand for State Management

```bash
npm install zustand
```

```tsx
// store/useGraphStore.ts
import { create } from 'zustand';

interface GraphStore {
  selectedAlert: Alert | null;
  graphData: GraphPayload | null;
  pipelineStatus: 'idle' | 'running' | 'complete' | 'error';
  chatHistory: ChatMessage[];
  filterState: FilterState;
  setSelectedAlert: (alert: Alert | null) => void;
  setGraphData: (data: GraphPayload) => void;
  setPipelineStatus: (status: string) => void;
  addChatMessage: (msg: ChatMessage) => void;
  updateFilter: (filter: Partial<FilterState>) => void;
}

export const useGraphStore = create<GraphStore>((set) => ({
  selectedAlert: null,
  graphData: null,
  pipelineStatus: 'idle',
  chatHistory: [],
  filterState: { riskThreshold: 40, patternType: 'all' },
  setSelectedAlert: (alert) => set({ selectedAlert: alert }),
  setGraphData: (data) => set({ graphData: data }),
  setPipelineStatus: (status) => set({ pipelineStatus: status as any }),
  addChatMessage: (msg) => set(state => ({
    chatHistory: [...state.chatHistory, msg]
  })),
  updateFilter: (filter) => set(state => ({
    filterState: { ...state.filterState, ...filter }
  })),
}));
```

---

### T37 · Add WebSocket for Live Pipeline Progress

```python
# FastAPI backend
from fastapi import WebSocket

@app.websocket("/ws/pipeline")
async def pipeline_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send agent activity updates
            await websocket.send_json({
                "agent": "PatternDetector",
                "status": "running",
                "message": "Cycle detected — nodes ACC_012 → ACC_031 → ACC_047",
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
```

```tsx
// Frontend AgentActivityPanel.tsx
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/pipeline');
  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    setAgentLogs(prev => [...prev.slice(-50), update]);  // keep last 50
  };
  return () => ws.close();
}, []);
```

---

### T38 · Add ML Scores Column to Alert Feed

```tsx
// In AlertFeed.tsx — add to each alert row
<div style={{display:'flex', gap:'4px', marginTop:'2px'}}>
  <MLChip label="IF" score={alert.if_score} />
  <MLChip label="XGB" score={alert.xgb_score} />
</div>

const MLChip = ({label, score}) => {
  const color = score > 0.8 ? 'var(--color-text-danger)'
              : score > 0.6 ? 'var(--color-text-warning)'
              : 'var(--color-text-success)';
  return (
    <span style={{fontSize:'10px', padding:'1px 5px', borderRadius:'4px',
      border:'0.5px solid var(--color-border-tertiary)', color}}>
      {label}: {score.toFixed(2)}
    </span>
  );
};
```

---

### T39 · Build Detailed SAR Report Viewer `CRITICAL`

**10 mandatory sections in every SAR:**

```
1.  CASE HEADER         — Alert ID, pattern, risk score, date, assigned investigator
2.  EXECUTIVE SUMMARY   — 2-3 sentences, plain English, written by LLM
3.  ENTITY TIMELINE     — Chronological table: date | from | to | amount | channel
4.  SUBGRAPH EVIDENCE   — Static PNG export of flagged subgraph
5.  RISK SIGNAL BREAKDOWN — Each contributing signal with weight and explanation
6.  ML MODEL SCORES     — IF score, XGB score, composite calculation shown
7.  INNOCENCE ASSESSMENT — Signals checked, discounts applied, final adjusted score
8.  INVESTIGATOR ACTIONS — Specific next steps: "Verify GST status", "Check device ID"
9.  AUDIT TRAIL         — Who accessed when, what actions taken
10. FIU-IND SUBMISSION  — Pre-formatted fields ready for filing
```

---

### T40 · Add config.yaml for Threshold Management

```yaml
# config.yaml — all detection thresholds in one place
# Changes here require no code deployment

detection:
  dormancy_threshold_days: 90
  smurfing_min_transactions: 6
  smurfing_max_amount: 49999
  cycle_max_hops: 8
  hub_min_degree: 5
  temporal_window_hours: 24
  pass_through_ratio_threshold: 0.95

risk_weights:
  cycle_detected: 40
  amount_exceeds_income: 25
  rapid_multi_hop: 20
  shared_device_ip: 20
  pass_through_ratio: 18
  dormant_activation: 15
  off_hours_transaction: 15
  near_threshold_amount: 15

innocence_discounts:
  gst_verified: 0.20
  established_relationship: 0.10
  declared_income_consistent: 0.10
  prior_investigator_clearance: 0.25
  max_total_discount: 0.30

risk_thresholds:
  monitor: 39
  elevated: 69
  high: 89
  critical: 90
```

---

### T41 · Export SAR as PDF (reportlab)

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table

def export_sar_pdf(alert_id: str) -> bytes:
    """Generate downloadable FIU-IND formatted SAR PDF."""
    alert = db.get_alert(alert_id)
    sar = db.get_sar_draft(alert_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    # Header
    story.append(Paragraph(f"SUSPICIOUS ACTIVITY REPORT — {alert_id}", title_style))
    story.append(Paragraph(f"GraphSentinel · Generated: {datetime.now()}", subtitle_style))

    # All 10 sections...
    # (build each section as Paragraph + Table)

    doc.build(story)
    return buffer.getvalue()

@app.get("/api/sar/{alert_id}/pdf")
async def download_sar(alert_id: str):
    pdf_bytes = export_sar_pdf(alert_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=SAR_{alert_id}.pdf"}
    )
```

---

## Phase 7 — Demo Preparation 🟡

> Goal: A flawless 5-minute demo is worth more than 10 unfinished features. Every task here is about making the system bulletproof for the judges.

---

### T42 · Pre-Cache All LLM Responses for Track A `CRITICAL`

**What to do:**  
Before the presentation starts, run the full pipeline on Track A and cache all LLM-generated SAR narratives in Redis. The demo never makes a live API call during the presentation.

```python
def pre_cache_demo_responses():
    """Run before entering the presentation room."""
    for alert_id in TRACK_A_ALERT_IDS:
        sar_text = generate_sar_with_llm(alert_id)  # live API call
        redis_client.setex(
            f"sar_cache:{alert_id}",
            86400,  # cache for 24 hours
            sar_text
        )
    print(f"Pre-cached {len(TRACK_A_ALERT_IDS)} SAR responses")
    print("Demo is ready. No live API calls will occur during presentation.")
```

**In sar_generator.py:**
```python
def generate_sar(alert_id: str) -> str:
    # Check cache first
    cached = redis_client.get(f"sar_cache:{alert_id}")
    if cached:
        return cached.decode('utf-8')  # instant, no API call
    # Fall back to live API
    return generate_sar_with_llm(alert_id)
```

---

### T43 · Build Track B Live Processing Mode

**What to do:**  
Track B is for judge Q&A — 3 additional fraud scenarios that run live with real detection and honest latency display.

```tsx
// In frontend — Track B mode
const [trackBStatus, setTrackBStatus] = useState('');

async function runTrackB(scenario: string) {
  setTrackBStatus('Loading transaction graph...');
  const result = await fetch(`/api/run-pipeline?track=B&scenario=${scenario}`);
  setTrackBStatus('Running Tarjan cycle detection...');
  // Show real progress, real latency
  // Display: "Cycle detected in 2.1 seconds"
}
```

**Three Track B scenarios:**
1. Long-horizon temporal layering (funds move over 6 months)
2. Multi-bank hop simulation (funds exit + suspicious re-entry)
3. Dormant account activation motif (90+ day dormancy → burst)

---

### T44 · Prepare Adversarial Test Demo Script

**Script for adversarial test panel:**

```
DEMO SEQUENCE:

1. "Let me show you where our system fails — and why that's a strength."

2. Run cycle+hop test:
   - 4 hops → DETECTED (green)
   - 6 hops → DETECTED (green)
   - 8 hops → DEGRADED (orange) — "DFS depth limit"
   - 9+ hops → NOT DETECTED (red) — annotation appears

3. "We show this honestly because Phase 2 adds GNN detection
   that doesn't rely on hardcoded hop limits."

4. Run time-distributed smurfing:
   - 72 hours → DETECTED
   - 95 days → HISTORICAL PROBE TRIGGERED
   "The hot layer doesn't catch it — but the bridge to warm
   storage fires automatically. Investigator gets flagged."

5. "A team that hides its failure modes isn't ready for production.
   We are."
```

---

### T45 · Prepare 30-Second Pitch Narrative

```
"Banks already use graph databases for AML. That's table stakes.

The problem is what happens AFTER the graph flags something.
A compliance officer opens a blank Word document and spends
3 to 5 days manually writing a 20-page SAR report.

GraphSentinel compresses that to under 20 minutes.
AI-drafted SAR pre-populated to FIU-IND standards.
Plain-English explanation of exactly why the pattern is suspicious.
And a conversational chatbot — so investigators can interrogate
the evidence like a conversation, not read a static report.

We're not replacing the graph layer. We're making it actionable."
```

---

### T46 · Prepare Q&A Answers for 5 Likely Judge Questions

**Q1: How does this scale to millions of transactions?**  
"On a laptop: 100K transactions in 3 seconds. Same docker-compose file runs on a Kafka + Neo4j Enterprise cluster — handles 1M+ transactions per day. Stack swap, not redesign."

**Q2: What about cross-bank hops?**  
"Acknowledged limitation. We flag high-velocity outflows automatically and file a pre-formatted alert to FIU-IND, which holds the cross-bank master database. We become a contributor to the national intelligence layer."

**Q3: How is PII protected when using Claude API?**  
"Pattern-aware tokenization replaces all account IDs with role-based labels before any data leaves the system. SHA-256 with per-session salt. Token vault lives in memory only. Claude never sees raw account IDs."

**Q4: How do you handle false positives?**  
"Two-layer scoring separates structural suspicion from contextual innocence. Investigator marks false positive → innocence discount weight adjusts automatically → same pattern scores lower next time. Demonstrated live in the feedback demo."

**Q5: What makes this different from what banks already use?**  
"Banks have graph DBs. They don't have: (1) conversational SAR chatbot, (2) investigator-ready SAR draft in 45 seconds vs 3–5 days, (3) privacy-preserving LLM integration. We're not competing with the graph layer. We're replacing the Word document."

---

### T47 · Test Full docker-compose Startup on Clean Machine `CRITICAL`

```bash
# On a fresh machine (or after docker system prune):
git clone <your-repo>
cd GraphSentinel
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env

time docker-compose up --build
# Target: all services healthy within 60 seconds

# Then run full demo pipeline:
curl -X POST http://localhost:8000/api/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{"track": "A"}'

# Expected: 12 alerts, first SAR in <5 seconds (cached)
```

**Pass criteria:**
- [ ] All 7 services start cleanly
- [ ] No port conflicts
- [ ] Pipeline completes in under 30 seconds on Track A
- [ ] Graph renders in browser
- [ ] SAR chatbot responds
- [ ] Adversarial tests run

---

### T48 · Create Video Backup of Working Demo

**Record a complete screen capture:**
1. `docker-compose up` → services starting
2. Frontend loading at localhost:3000
3. Click "Run Pipeline" on Track A
4. Alerts appearing with risk scores + ML scores
5. Click on a red hub node → account detail panel
6. Click "Investigate" → subgraph isolation
7. Click "Generate SAR" → SAR report with all 10 sections
8. Open SAR chatbot → ask "Why was this flagged?"
9. See streaming response
10. Open Adversarial Tests → run cycle+hop test

**Storage:** Upload to Google Drive as unlisted video. Have URL ready on phone. Last resort only.

---

## Phase 8 — Submission 🔴

---

### T49 · Upload One-Page Summary PDF to Google Drive `CRITICAL`

1. Upload `GraphSentinel_OnePage_Summary.pdf` to Google Drive
2. Right-click → Share → Change to "Anyone with the link can view"
3. Copy link
4. Paste into Slide 10 (Research & References) under "Mandatory Submission"
5. Test link in incognito window — confirm it opens without login

---

### T50 · Delete Submission Guidelines Slide (Slide 2) `CRITICAL`

The template includes a "SUBMISSION GUIDELINES" slide (Slide 2) that must be deleted before final submission. Easy to forget under pressure. **Check this last before PDF export.**

---

### T51 · Export PPT as PDF for Submission `CRITICAL`

1. File → Export → PDF (not Print → Save as PDF)
2. Check all 9 slides render correctly
3. Verify: fonts didn't change, diagrams intact, tables formatted
4. Check file size — should be under 10MB
5. Submit via hackathon portal

---

### T52 · Final README with docker-compose Run Instructions

```markdown
# GraphSentinel — Quick Start

## Prerequisites
- Docker + Docker Compose
- Anthropic API key (for SAR generation)

## Setup (5 minutes)
git clone https://github.com/team-elida/graphsentinel
cd graphsentinel
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY

## Generate demo data
cd data
python generate_amlsim.py --transactions 50000
cd ..

## Start all services
docker-compose up --build

## Access
Frontend:     http://localhost:3000
Neo4j browser: http://localhost:7474 (neo4j / graphsentinel123)
API docs:     http://localhost:8000/docs

## Run demo pipeline
Click "Run Pipeline" → Select "Track A" → Watch alerts generate
```

---

## Quick Reference — Critical Tasks Only

These 15 tasks are the absolute minimum for a strong submission:

| Task | Phase | Why Critical |
|---|---|---|
| T1 — IBM AMLSim dataset | Data | Everything depends on this |
| T3 — Neo4j migration | Data | Foundation of the graph layer |
| T6 — docker-compose | Data | Judges need one-command setup |
| T8 — Tarjan SCC | Detection | Replaces DFS, more impressive |
| T9 — Louvain | Detection | Catches what cycles miss |
| T15 — Feature extraction | ML | Required by both models |
| T16 — Isolation Forest | ML | Unsupervised, easy to add |
| T17 — XGBoost | ML | Supervised with IBM labels |
| T18 — Wire ML scores | ML | Shows in every alert row |
| T22 — TokenVault | Security | Privacy differentiator |
| T28 — SAR chatbot | Chatbot | Primary differentiator |
| T34 — Node click panel | Frontend | Most visible demo feature |
| T39 — SAR report viewer | Frontend | PS3 evidence package requirement |
| T42 — Pre-cache responses | Demo | Zero API call risk during demo |
| T47 — Clean machine test | Demo | Catch setup issues before finals |

---

*GraphSentinel PRD v1.3 · Team Elida · MMIT Pune · PSBs Hackathon 2026*  
*Built on Elida multi-agent framework — VOIS Innovation Marathon 2.0 Winners · ₹2,00,000*
