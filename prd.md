https://github.com/sickn33/antigravity-awesome-skills

use all skills for this project below 

**PRODUCT REQUIREMENTS DOCUMENT**

**GraphSentinel**

AI-Powered Fund Flow Fraud Detection System

*VIT Pune Grand Hackathon 2026 \| Problem Statement PS3 \| Track:
FinTech & Fraud Prevention*

  ----------------- -----------------------------------------------------
  **Document        v1.3 --- Third-Party Review Corrections Applied
  Version**         

  **Date**          March 13, 2026

  **Status**        **APPROVED FOR DEVELOPMENT**

  **Project Code**  PS3-GRAPHSENTINEL-2026

  **Competition**   VIT Pune Grand Hackathon --- Grand Finale, March 27,
                    2026

  **Submitted By**  Team Elida (MMIT, Pune) --- Winners, VOIS Innovation
                    Marathon 2.0
  ----------------- -----------------------------------------------------

*CONFIDENTIAL --- FOR HACKATHON EVALUATION ONLY*

**Table of Contents**

**1. Executive Summary**

GraphSentinel is an AI-powered, graph-based Fund Flow Fraud Detection
System designed to expose sophisticated money laundering patterns that
conventional banking systems systematically fail to detect. Built on a
modular detection pipeline inspired by the Elida multi-agent framework
--- validated by Team Elida\'s ₹2,00,000 prize-winning submission at the
VOIS Innovation Marathon 2.0 --- GraphSentinel transforms raw
transactional data into a living, queryable knowledge graph that enables
investigators to trace, visualize, and act on suspicious fund flows.

The global financial system loses an estimated \$800 billion to \$2
trillion annually to money laundering. Despite this scale, legacy
rule-based AML systems generate false-positive rates exceeding 90%,
meaning investigators spend the vast majority of their time clearing
legitimate transactions rather than pursuing genuine fraud.

+-----------------------------------------------------------------------+
| **Honest Value Proposition --- Time Accounting**                      |
|                                                                       |
| GraphSentinel does not compress 3--5 days of manual analysis into     |
| under a minute. Manual investigation includes reviewing KYC           |
| documents, verifying business premises, consulting relationship       |
| managers, and checking GST filings --- tasks no AI system can         |
| perform. What GraphSentinel actually delivers: (1) Graph pattern      |
| detection: 4 seconds. (2) AI-drafted SAR pre-population: 45 seconds.  |
| (3) Investigator review of AI draft vs. writing from scratch: 15--20  |
| minutes vs. 4+ hours. Total case preparation: approximately 20        |
| minutes vs. 3 days. That is a genuine 20x improvement --- stated      |
| honestly, without false precision.                                    |
+-----------------------------------------------------------------------+

**1.1 Problem at a Glance**

  ----------------------- ----------------------- -----------------------
  **Metric**              **Legacy Systems**      **GraphSentinel
                                                  Target**

  **False Positive Rate** 90--98%                 \< 40%

  **Multi-hop Detection   Not Supported           Up to 50 hops
  (\>3 hops)**                                    

  **Cross-channel         Siloed                  Unified
  Visibility**                                    

  **Explainability for    None                    LLM-Generated SAR
  Regulators**                                    

  **Temporal Fraud        30-day window only      3-year rolling graph
  (months/years)**                                
  ----------------------- ----------------------- -----------------------

**2. Problem Statement & Context**

**2.1 The AML Crisis in Indian Banking**

India\'s financial sector faces a systemic and growing challenge in
Anti-Money Laundering (AML) enforcement. Under the Prevention of Money
Laundering Act (PMLA) and RBI Master Directions on KYC, banks are
legally obligated to identify, monitor, and report suspicious
transactions to the Financial Intelligence Unit --- India (FIU-IND).
Non-compliance carries severe penalties including license revocation.

Despite this regulatory pressure, the tools available to compliance
teams have not kept pace with the sophistication of modern financial
crime. The result is a systemic enforcement gap with three critical
dimensions:

-   **Rule-based SQL systems only flag transactions that exceed static
    monetary thresholds or match predefined patterns. Criminal networks
    deliberately structure transactions to stay below these thresholds
    (structuring/smurfing) or distribute transfers across multiple
    accounts (layering) to avoid triggering any single rule.** The
    Detection Gap:

-   **A mid-size Indian bank processes millions of transactions daily
    across NEFT, IMPS, RTGS, UPI, and SWIFT channels. Relational
    database joins become computationally prohibitive when tracing money
    beyond 2--3 account hops, making deep-path analysis effectively
    impossible at production scale.** The Scale Gap:

-   **Even when modern ML models do flag suspicious activity, regulators
    require deterministic, step-by-step audit trails explaining why a
    transaction was flagged. Black-box AI outputs are legally
    inadmissible without this explainability layer.** The Explainability
    Gap:

**2.2 Real-World Fraud Scenarios GraphSentinel Targets**

The following documented fraud typologies represent the primary
detection targets for GraphSentinel:

**Fraud Type 1: Round-Tripping (Circular Fund Flow)**

+-----------------------------------------------------------------------+
| **Real Case Reference**                                               |
|                                                                       |
| Multiple cases investigated by ED India involve shell companies used  |
| to route funds in circular patterns to disguise beneficial ownership. |
| The Vijay Mallya case involved funds routed through 40+ entities      |
| before returning as \'consulting fees\'.                              |
+-----------------------------------------------------------------------+

Pattern: Account A transfers funds through a chain of intermediary
accounts (B, C, D) which eventually returns to Account A or a closely
associated beneficiary --- disguising the original funds as legitimate
revenue.

-   **Closed directed cycle: A → B → C → D → A** Graph Signature:

-   **Each individual leg of the transfer appears as a legitimate
    standalone payment** Why Banks Miss It:

-   **Depth-First Search cycle detection on directed transaction graph;
    flags within seconds of cycle completion** GraphSentinel Detection:

**Fraud Type 2: Smurfing / Structuring**

+-----------------------------------------------------------------------+
| **Real Case Reference**                                               |
|                                                                       |
| The 2016 Punjab National Bank fraud investigations revealed extensive |
| use of sub-threshold transfers split across hundreds of accounts to   |
| avoid PAN card and CTR (Cash Transaction Report) triggers.            |
+-----------------------------------------------------------------------+

Pattern: A large sum is broken into many smaller transfers (each below
₹50,000 reporting thresholds) distributed across multiple accounts ---
all ultimately converging on a single beneficiary.

-   **High fan-in pattern --- many small-weight edges from diverse
    source nodes converging on one destination node** Graph Signature:

-   **Each transaction is below the threshold that triggers a rule-based
    alert** Why Banks Miss It:

-   **Edge density and velocity analysis --- aggregated flow to a single
    node triggers flag regardless of individual transaction size**
    GraphSentinel Detection:

**Fraud Type 3: Mule Networks (Hub-and-Spoke)**

+-----------------------------------------------------------------------+
| **Real Case Reference**                                               |
|                                                                       |
| A 2023 Enforcement Directorate operation in Hyderabad dismantled a    |
| network where 300+ mule accounts were used to route ₹200+ crore from  |
| cyber fraud victims through layered transfers.                        |
+-----------------------------------------------------------------------+

Pattern: A central hub account receives funds from many sources and
immediately redistributes to a final destination --- often recruited
individuals (mules) who keep a small fee.

-   **Hub node with high in-degree and high out-degree within a narrow
    time window; near-zero balance maintained throughout** Graph
    Signature:

-   **Each mule account has low individual transaction volume; no single
    account appears suspicious in isolation** Why Banks Miss It:

-   **In-degree/out-degree ratio analysis combined with temporal
    clustering identifies hub behavior** GraphSentinel Detection:

**Fraud Type 4: Dormant Account Activation**

Pattern: Bank accounts dormant for 6--36 months are suddenly activated
with large, rapid transactions --- often by insiders or via account
takeover --- and immediately transferred out before freezing mechanisms
trigger.

-   **Node with zero edge activity for extended period followed by
    sudden high-weight edge spike** Graph Signature:

-   **Node behavioral baseline scoring --- deviation from historical
    activity triggers maximum anomaly flag** GraphSentinel Detection:

**Fraud Type 5: Temporal Layering (Long-Horizon)**

Pattern: Criminal networks deliberately slow the pace of money movement
--- letting funds sit in intermediary accounts for months or years ---
to exhaust the 30-day monitoring windows of legacy systems before
executing the next transfer leg.

-   **Multi-hop path with long time gaps between edges but consistent
    directional flow toward a single terminal node** Graph Signature:

-   **3-year rolling temporal graph retains all edges with timestamps;
    cycle detection is applied independent of time gap between hops**
    GraphSentinel Detection:

**Fraud Type 6: Pass-Through / Hawala Accounts**

+-----------------------------------------------------------------------+
| **Real Case Reference**                                               |
|                                                                       |
| NIA and ED investigations into terror financing have repeatedly       |
| identified bank accounts used purely as pass-through nodes ---        |
| receiving and immediately forwarding funds while maintaining          |
| near-zero balances.                                                   |
+-----------------------------------------------------------------------+

Pattern: Accounts serve as pure financial relays --- funds arrive and
depart in near-matching amounts within hours, with no legitimate
economic activity explaining the flow.

-   **In-flow equals out-flow within narrow time window; in-degree to
    out-degree ratio approaches 1.0** Graph Signature:

-   **Flow-balance analysis on each node over rolling 24/48-hour
    windows** GraphSentinel Detection:

**3. Product Goals & Success Metrics**

**3.1 Hackathon Prototype Goals (MVP --- March 27, 2026)**

1.  Demonstrate end-to-end fraud detection on a synthetic dataset with
    embedded fraud patterns, showing the system correctly identifies all
    planted anomalies

2.  Render an interactive, real-time graph visualization where
    fraudulent nodes and edges are visually distinguishable from clean
    transaction flows

3.  Generate a Risk Score (0--100) for each flagged subgraph with a
    plain-English LLM explanation of why the pattern is suspicious

4.  Produce a downloadable mock Suspicious Activity Report (SAR)
    formatted for FIU-IND submission standards

5.  Demonstrate privacy-safe LLM integration through a tokenization
    layer that strips PII before any data leaves the local environment

**3.2 Enterprise Production Goals (Post-Hackathon Roadmap)**

6.  Process 1M+ transactions per day in real-time without degradation in
    detection latency

7.  Reduce total alert volume presented to investigators compared to
    pure rule-based thresholds, by surfacing structural patterns that
    require multi-signal confirmation rather than single-threshold
    triggers. No specific false-positive percentage is claimed for the
    prototype --- this metric is an operational outcome measured through
    investigator feedback over deployment time.

8.  Support multi-bank federated anomaly correlation via encrypted,
    anonymized graph sharing with FIU-IND

9.  Achieve full regulatory compliance with PMLA, RBI Master Directions,
    and DPDP Act data protection requirements

10. Provide RBAC (Role-Based Access Control) and complete audit trails
    for all investigator actions

**3.3 Key Performance Indicators**

  -------------------------- --------------- ----------------- ----------------------
  **KPI**                    **Prototype     **Enterprise      **Measurement**
                             Target**        Target**          

  Cycle Detection Accuracy   100% on         Validated via     Precision/Recall on
  (on embedded patterns)     embedded test   held-out test     labelled set
                             set             partition         

  Alert Response Time (hot   \< 5 seconds    \< 2s (hot        P99 latency
  layer only)                per batch       layer); cold      
                                             queries: 5--30s   

  Alert Volume Reduction vs. Demonstrated    Measured          Investigator-cleared
  Rule-Only Baseline         qualitatively   post-deployment   rate
                                             via feedback      

  SAR Draft Generation Time  45s pre-cached; \< 3 minutes with Time to
                             15--60s live    human review step investigator-ready
                             API                               draft

  Graph Load Time (10K nodes \< 15s NetworkX \< 1s Neo4j       Wall-clock load time
  / 100K edges)              in-memory       Enterprise        
                                             (indexed)         
  -------------------------- --------------- ----------------- ----------------------

**4. System Architecture**

**4.1 Architecture Overview**

GraphSentinel is built on a five-layer funnel architecture that
progressively filters billions of raw transactions down to a small set
of high-confidence fraud alerts for human review. Each layer is
independently scalable and replaceable.

+-----------------------------------------------------------------------+
| **Design Principle**                                                  |
|                                                                       |
| No layer performs final fraud determination. The system scores and    |
| explains; human investigators decide. This design satisfies both      |
| regulatory explainability requirements and operational due process    |
| obligations.                                                          |
+-----------------------------------------------------------------------+

**4.2 Layer-by-Layer Technical Design**

**Layer 1 --- Data Ingestion (Batch Replay Demo / Apache Kafka)**

Function: Ingests transaction events from banking source systems into
the processing pipeline.

-   **1M+ events per second via Apache Kafka with schema registry**
    Throughput Target (Enterprise):

-   **The prototype operates in two modes toggled via a UI switch:**
    Prototype Implementation --- Hybrid Demo Design:

```{=html}
<!-- -->
```
-   Track A --- Guaranteed Path (main presentation): A curated
    500-transaction scenario covering all three embedded fraud patterns
    is replayed in batches of 20 transactions/second. Completes in
    approximately 25 seconds. All LLM explanations are pre-cached before
    the demo begins --- no live API call during the presentation. This
    is the primary demo path.

-   Track B --- Live Processing (judge Q&A): Three additional pre-loaded
    fraud scenarios (different from Track A) are available for judges to
    explore. The investigator selects a scenario, clicks \'Run
    Detection,\' and watches actual DFS traversal execute with a visible
    progress indicator. The UI honestly displays \'Loading 10K nodes\...
    9 seconds\' and \'Running cycle detection\... 2 seconds.\' LLM
    explanation is generated live (15--45 seconds depending on API
    response). This demonstrates genuine system capability, not scripted
    replay.

```{=html}
<!-- -->
```
-   **A single scripted demo creates a trap: if a judge asks \'show me a
    different pattern\' or \'run it on this modified scenario,\' the
    team has no answer. Track B eliminates that vulnerability by
    exposing real processing with honest latency display.** Why Two
    Tracks:

-   **txn.raw, txn.filtered, alerts.flagged, alerts.cleared** Enterprise
    Kafka Topics:

-   **JSON with schema: { txn_id, sender_id, receiver_id, amount,
    timestamp, channel, account_type, device_id, ip_address }** Data
    Format:

**Layer 2 --- Stream Processing & Pre-filtering (Apache Flink)**

Function: Discards low-risk transactions in real time before they reach
the graph layer --- dramatically reducing the compute burden on graph
algorithms.

-   **Transactions below ₹500 between known-good KYC-verified accounts
    with \>24 months of stable history are marked low-risk and archived
    without graph analysis** Filter Rules Applied:

-   **Each surviving transaction is enriched with account metadata
    (account type, creation date, KYC status, declared income bracket)
    from the Customer Data Store** Enrichment:

-   **Python-based pre-filter script applying simple threshold and
    account-age rules** Prototype Implementation:

**Layer 3 --- Graph Database (Neo4j / NetworkX)**

Function: Stores the transaction network as a native graph structure and
runs topology algorithms to detect fraud patterns.

-   **Account, Customer, Device, IP Address, Branch, External
    Counterparty** Node Types:

-   **Transaction (with amount, timestamp, channel), Session (login
    events), Shared Infrastructure (same device or IP across accounts)**
    Edge Types:

-   Core Algorithms:

```{=html}
<!-- -->
```
-   Depth-First Search cycle detection --- identifies round-tripping
    loops. DFS has O(V+E) time complexity; prototype targets cycles up
    to 8 hops before combinatorial explosion makes traversal impractical
    on a 10,000-node graph. Enterprise deployment using Neo4j\'s native
    cycle procedures supports deeper traversal with hardware-optimized
    graph engines.

-   Louvain Community Detection --- identifies tightly connected account
    clusters at O(n log n) complexity

-   In-degree / Out-degree ratio analysis --- detects pass-through and
    hub-and-spoke patterns at O(V) complexity

-   Temporal velocity analysis --- detects rapid multi-hop sequences
    using timestamp-sorted edge traversal

```{=html}
<!-- -->
```
-   **Python NetworkX for in-memory graph with up to 10,000 nodes; Neo4j
    Free for visual demo queries** Prototype Stack:

-   **Neo4j Enterprise or TigerGraph with distributed horizontal
    scaling** Enterprise Stack:

**Layer 4 --- Risk Scoring Engine**

Function: Converts raw graph anomaly signals into a normalized Risk
Score (0--100) per flagged subgraph, enabling investigators to
prioritize cases.

  ---------------------------------- ------------ -------------------------
  **Signal**                         **Weight**   **Detection Method**

  Directed cycle detected            **+40**      DFS cycle algorithm

  Transaction amount \> declared     **+25**      Customer income
  income baseline                                 comparison

  Off-hours transaction (10PM--6AM)  **+15**      Timestamp analysis

  Dormant account activated (\>90    **+15**      Node activity timeline
  days inactive)                                  

  Rapid multi-hop velocity (\<24hrs  **+20**      Temporal edge velocity
  across 3+ accounts)                             

  Shared device/IP across multiple   **+20**      Infrastructure node
  accounts                                        analysis

  In/out flow ratio approaching 1.0  **+18**      Node degree balance
  (pass-through)                                  

  Near-threshold amounts             **+15**      Amount histogram analysis
  (₹45K--₹49.9K pattern)                          
  ---------------------------------- ------------ -------------------------

Risk Score Thresholds: 0--39 = Monitor; 40--69 = Elevated Alert; 70--89
= High Priority; 90--100 = Critical --- Auto-Escalate to Senior
Investigator

**Layer 5 --- LLM Explanation & SAR Draft Generation**

Function: Converts graph anomaly signals into human-readable case
summaries and investigator-ready SAR drafts. The tokenization scheme is
pattern-aware --- it encodes topological role, not just a generic
positional label, so the LLM receives enough structural context to
generate genuinely meaningful explanations.

-   **Account IDs are replaced with role-based identifiers that encode
    their position in the detected fraud pattern, not just their
    sequential hop number. Examples by pattern type:** Step 1 ---
    Pattern-Aware Tokenization:

```{=html}
<!-- -->
```
-   Round-trip cycle: CYCLE_ORIGIN, CYCLE_INTERMEDIARY_1,
    CYCLE_INTERMEDIARY_2, CYCLE_CLOSURE \[with explicit annotation:
    CYCLE_CLOSURE maps back to CYCLE_ORIGIN, forming a directed loop\]

-   Hub-and-spoke: HUB_NODE, SPOKE_001 through SPOKE_N,
    TERMINAL_BENEFICIARY

-   Smurfing fan-in: AGGREGATION_TARGET, SOURCE_001 through SOURCE_N

-   Pass-through: PASSTHROUGH_NODE \[with in/out balance annotation\]

```{=html}
<!-- -->
```
-   **A naive sequential scheme (HOP_1, HOP_2, TERMINAL_NODE) destroys
    the cycle topology --- the LLM sees a linear chain with a
    disconnected return transfer and cannot identify the closed loop.
    Role-based labeling preserves the topological semantics the LLM
    needs to generate accurate explanations.** Why Role-Based Not
    Sequential:

-   **Each edge in the prompt includes a structural annotation alongside
    the amount and timestamp: \[CLOSURE_EDGE: connects CYCLE_CLOSURE
    back to CYCLE_ORIGIN completing directed cycle\] or \[FAN_IN_EDGE:
    one of 47 convergent transfers to AGGREGATION_TARGET within 72
    hours\].** Step 2 --- Edge Annotations:

-   **The role-annotated graph description is sent to the LLM. Amounts
    and timestamps are preserved unmodified as they carry no direct
    PII.** Step 3 --- LLM Prompt:

-   **After the LLM returns its explanation, a post-processing step
    substitutes role labels back to real account identifiers using the
    session token vault. Investigators see real account numbers in the
    final report. The vault never leaves the local environment.** Step 4
    --- Detokenization:

-   **AI-generated draft SAR pre-populated with case narrative, entity
    timeline, and risk signal justification. This is explicitly a DRAFT
    requiring mandatory investigator review, annotation, and attestation
    before FIU-IND submission. Automated filing without sign-off
    violates PMLA Section 12.** Output --- SAR Draft:

-   **Prototype uses Claude API. Tokenized structural data (role
    labels + amounts + timestamps --- no raw account IDs or names) is
    transmitted. The vault mapping is stored locally only. This is NOT
    an air-gapped deployment --- that applies to the enterprise roadmap
    in Section 13.** Prototype Privacy Boundary:

**5. Detection Pipeline Architecture (Elida-Inspired Modular Design)**

GraphSentinel\'s intelligence layer is organized as an orchestrated,
modular detection pipeline. Each stage is implemented as a discrete
Python module with defined inputs, outputs, and a single responsibility.
This design is inspired by the multi-agent Elida framework developed by
the team, adapted here to a sequential orchestration pattern appropriate
for the prototype scope.

+-----------------------------------------------------------------------+
| **Honest Architecture Note**                                          |
|                                                                       |
| The five stages below are Python modules called sequentially by an    |
| orchestrator script --- not independent microservices with            |
| message-passing or distributed coordination. They are labeled as      |
| \'agents\' to communicate their single-responsibility design and to   |
| illustrate the pathway to a true distributed agent architecture in    |
| production. Judges should understand this distinction: the value is   |
| in the modular logic, not the runtime topology.                       |
+-----------------------------------------------------------------------+

**5.1 Pipeline Stage Definitions**

  -------------- ---------------- --------------------- -------------------
  **Agent**      **Role**         **Input**             **Output**

  **Graph Agent  Ingests raw      transactions.csv /    Neo4j / NetworkX
  (Mapper)**     transactions and Kafka stream          graph object
                 constructs the                         
                 live knowledge                         
                 graph                                  

  **Pathfinder   Runs topology    Graph object +        List of flagged
  Agent          algorithms to    algorithm config      subgraphs with
  (Detector)**   detect                                 pattern type
                 suspicious                             
                 structural                             
                 patterns                               

  **Context      Compares         Flagged subgraph +    Behavioral anomaly
  Agent          transaction      customer profile      score + innocence
  (Profiler)**   behavior against                       signals
                 customer\'s                            
                 historical                             
                 baseline and KYC                       
                 data                                   

  **Scorer       Aggregates       Pattern flags +       Risk Score 0-100 +
  Agent**        signals from     behavioral anomaly    contributing
                 Pathfinder and   score                 factors
                 Context agents                         
                 into a unified                         
                 Risk Score                             

  **Report Agent Generates LLM    Scored subgraph +     Case summary + SAR
  (Compiler)**   explanations and tokenized metadata    PDF
                 formats SAR                            
                 documents for                          
                 investigators                          
  -------------- ---------------- --------------------- -------------------

**5.2 Scoring & Innocence Protocol --- Asymmetric Bands**

GraphSentinel uses a two-layer scoring model: a structural score
computed purely from graph topology, and an innocence discount applied
as a percentage reduction. These are intentionally kept separate to
avoid the mathematical collapse where maximum innocence signals reduce a
60-point structural flag to zero --- which previously caused both a
verified legitimate business and a suspicious fresh mule to both land in
the \'Monitor\' band.

**Layer A --- Structural Score (0--100)**

Computed by the graph algorithms. This score never changes based on
customer profile data. It reflects only what the transaction topology
says.

**Layer B --- Innocence Discount (0--30% reduction of structural
score)**

Applied by the Context Stage after structural scoring. Positive
innocence evidence reduces the structural score. Absence of innocence
evidence leaves the structural score unchanged --- it does not increase
it.

-   **-20% of structural score** GST-registered entity with active
    filings:

-   **-10% of structural score** Established transaction relationship
    (6+ months, recurring pattern):

-   **-10% of structural score** Declared income consistent with
    transaction amount:

-   **-25% of structural score** Prior investigator clearance on
    identical pattern:

-   **capped at 30% --- a score of 60 can floor to 42, not to 0**
    Maximum total discount:

**Threshold Gates After Discount Applied**

  ------------------ ------------------ ------------------ ----------------
  **Final Score**    **Innocence        **Disposition**    **Rationale**
                     Evidence**                            

  0--39              Any signal present **Auto-clear**     Structural
                                                           signal weak +
                                                           verified entity
                                                           = no
                                                           investigator
                                                           time needed

  0--39              No innocence       Monitor queue      Low structural
                     signals                               signal but
                                                           unverified ---
                                                           passive watch

  40--69             Strong (GST +      Deferred review (7 Elevated
                     history)           days)              structure but
                                                           strong
                                                           legitimacy ---
                                                           low urgency

  40--69             Weak or absent     **Immediate        Elevated
                                        review**           structure +
                                                           unverified
                                                           entity =
                                                           prioritize

  70--100            Any                **Immediate        High structural
                                        review**           signal always
                                                           requires human
                                                           eyes regardless
                                                           of innocence
  ------------------ ------------------ ------------------ ----------------

+-----------------------------------------------------------------------+
| **Why This Matters**                                                  |
|                                                                       |
| The \'trusted lane\' (auto-clear for score 0--39 with innocence       |
| signals) is the genuine alert volume reduction mechanism. Legitimate  |
| businesses with GST records and established transaction patterns that |
| trigger weak structural signals are automatically resolved without    |
| investigator time. This is the operationally significant improvement  |
| over legacy systems --- not detection accuracy, but investigator      |
| workload reduction.                                                   |
+-----------------------------------------------------------------------+

**6. Data Architecture**

**6.1 Data Schema --- Node Attributes**

  -------------------- ------------------- ------------------- -------------------
  **Node Type**        **Field**           **Data Type**       **Purpose**

  **Account**          account_id,         String, Enum, Date, Primary entity;
                       account_type,       Float, Date, Date   last_active_date
                       creation_date,                          and last_txn_date
                       status, balance,                        are required to
                       last_active_date,                       compute dormancy
                       last_txn_date                           window for Fraud
                                                               Type 4 detection
                                                               (\>90 days
                                                               inactivity
                                                               threshold)

  **Customer**         customer_id,        String, Enum, Int,  Establishes
                       kyc_status,         Enum                behavioral baseline
                       income_bracket,                         
                       occupation,                             
                       risk_rating                             

  **Device/Network**   device_id,          String, String,     Detects shared
                       mac_address,        String, Geo         infrastructure
                       ip_address,                             across accounts
                       geolocation                             

  **External Entity**  entity_id,          String, Enum,       Tracks offshore and
                       entity_type,        ISO-2, Bool         high-risk
                       country,                                counterparties
                       risk_jurisdiction                       
  -------------------- ------------------- ------------------- -------------------

**6.2 Data Schema --- Edge Attributes (Transactions)**

  ------------------ ------------------------------ ---------------------------------
  **Field**          **Type**                       **Purpose**

  txn_id             UUID                           Unique transaction identifier

  sender_id /        Foreign Key (Account)          Defines directed edge between
  receiver_id                                       nodes

  amount             Float (INR)                    Edge weight --- used in fan-in
                                                    and flow-balance analysis

  timestamp          DateTime (IST)                 Enables temporal graph analysis
                                                    and off-hours detection

  channel            Enum:                          Channel-switching patterns can
                     NEFT/IMPS/RTGS/UPI/SWIFT/ATM   indicate structuring

  account_type       Enum: Savings/Current/Loan/FD  Flags mismatches between account
                                                    type and transaction behavior

  device_id /        String                         Shared device/IP links across
  ip_address                                        accounts in the graph
  ------------------ ------------------------------ ---------------------------------

**6.3 Memory & Storage Strategy**

GraphSentinel implements a three-tier hot/warm/cold storage strategy.
Real-time alerting operates exclusively on the hot layer. Warm and cold
tiers serve investigative analysis. A critical design challenge
addressed in v1.3 is the detection bridge: without a mechanism
connecting hot-layer detection to cold historical patterns, long-horizon
fraud (months/years) would be entirely invisible to the alert system.

11. **Stored in native graph database RAM. Fully indexed. All real-time
    detection algorithms operate exclusively here. Target query latency:
    sub-2 seconds.** Hot Layer (Last 90 Days):

12. **Stored on SSD in compressed graph format. Queried during
    investigation mode or via historical fingerprint probes. Expected
    latency: 5--30 seconds.** Warm Layer (90 Days -- 1 Year):

13. **Stored in object storage (AWS S3). On-demand retrieval for deep
    investigation. Edge aggregation compresses repeated transfers into
    weighted edges. Expected latency: 30 seconds to several minutes.
    Investigator tool only.** Cold Layer (1--3 Years):

**The Detection Bridge --- Anomaly-Driven Historical Probes**

Without an active bridge, a criminal using 6-month layering would be
entirely invisible: the final hop appears in the hot layer without
structural context, no alert fires, and no investigator ever queries
warm storage. To close this gap, GraphSentinel runs lightweight
historical fingerprint probes on accounts that cross a significance
threshold in the hot layer:

-   **Any account with transaction volume exceeding ₹1 lakh in the
    current hot-layer window triggers an automatic background probe.**
    Trigger Condition:

-   **\'Has this account appeared in any 3+ hop directed path in the
    last 12 months?\' --- executed against warm storage (5--30s,
    background, non-blocking).** Probe Query:

-   **Account is elevated to \'Long-Horizon Suspect\' status, triggering
    full historical investigation mode and notifying the assigned
    investigator.** On Match:

-   **Probe result is cached for 7 days. No investigator action
    required.** On No Match:

-   **Probes run asynchronously and do not block the hot-layer detection
    stream. Probe latency (5--30s) is acceptable because long-horizon
    pattern confirmation is not time-critical in the same way real-time
    alerts are.** Performance Design:

+-----------------------------------------------------------------------+
| **Prototype Note**                                                    |
|                                                                       |
| The 100,000-edge synthetic dataset is split 80/20 for development and |
| validation. The 80,000-edge development partition contains the three  |
| manually embedded fraud patterns. The held-out 20,000-edge test       |
| partition contains independently generated fraud variants with        |
| different structures, amounts, and timing --- ensuring detection      |
| algorithms are validated beyond the patterns they were built against. |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| **Prototype Note**                                                    |
|                                                                       |
| The 100,000-edge synthetic dataset is split 80/20 for development and |
| validation. The 80,000-edge development partition contains the three  |
| manually embedded fraud patterns used during algorithm development.   |
| The held-out 20,000-edge test partition contains independently        |
| generated fraud variants with different graph structures, amounts,    |
| and timing --- used to validate that detection algorithms generalize  |
| beyond the patterns they were built against. Reporting 100% detection |
| accuracy on the development partition without testing the held-out    |
| partition would be training on the test set, which is                 |
| methodologically invalid.                                             |
+-----------------------------------------------------------------------+

**7. User Interface Requirements**

**7.1 Dashboard Overview**

The GraphSentinel dashboard is a Streamlit-based web application
designed for fraud investigation teams. It consists of three primary
screens accessible via a left navigation panel.

**7.2 Screen 1 --- Live Graph Visualization**

The primary investigative surface. Renders the complete transaction
graph with visual encoding of risk levels.

-   **Green = Low Risk; Yellow = Elevated; Red = High Risk/Flagged; Size
    proportional to total transaction volume** Node Encoding:

-   **Edge thickness proportional to transaction amount; Edge color
    indicates channel type** Edge Encoding:

-   **A live sidebar panel displays which Elida agent is currently
    executing and what it found --- e.g. \'Graph Agent: Ingesting batch
    47/100\', \'Pathfinder Agent: Cycle detected --- nodes A7F3 → B2D1 →
    C9E4 → A7F3\', \'Scorer Agent: Risk Score 87/100\'. This makes the
    multi-agent architecture visibly active to judges rather than
    theoretical.** Agent Activity Panel (Critical for Demo):

-   **Click any node to expand its 1-hop neighborhood; Hover shows
    account metadata tooltip; Right-click opens the full Case Panel for
    that node** Interactivity:

-   **Date range slider; Risk score threshold slider; Fraud pattern type
    filter (cycle, fan-in, hub-spoke); Channel filter** Filter Controls:

-   **Click \'Investigate\' on any flagged node to render only that
    subgraph and its connected components --- removing visual noise from
    the full graph** Subgraph Isolation:

**7.3 Screen 2 --- Alert Triage Table**

A sortable, filterable table of all active alerts for the investigation
team to prioritize and assign cases.

-   **Alert ID, Fraud Pattern Type, Primary Node, Risk Score, Amount
    Involved, First Detected, Assigned Investigator, Status** Columns:

-   **Assign to investigator; Mark as False Positive (feeds back to
    model); Escalate to Senior; Generate SAR; View in Graph** Actions:

-   **Select multiple alerts; Assign to team; Export for regulatory
    reporting** Bulk Operations:

**7.4 Screen 3 --- Case Report & SAR Generation**

The evidence packaging and regulatory reporting interface for a specific
fraud case.

-   **LLM-generated narrative explaining the fraud hypothesis in plain
    English; List of all contributing risk signals with individual
    weights; Timeline of suspicious transactions in chronological
    order** Case Summary Panel:

-   **Static snapshot of the flagged subgraph rendered as a PNG for
    inclusion in official reports** Evidence Graph:

-   **One-click generation of Suspicious Activity Report formatted to
    FIU-IND standards; Fields auto-populated from case data;
    Investigator can edit and annotate before finalizing** SAR
    Generator:

-   **All investigator actions logged with timestamp and user ID for
    regulatory compliance** Audit Trail:

**8. Privacy, Security & Compliance**

**8.1 Data Privacy Architecture**

GraphSentinel is designed to operate within the regulatory constraints
of the Digital Personal Data Protection Act (DPDP) 2023 and RBI data
localization requirements. All personal data remains within the bank\'s
secure perimeter.

14. **A local tokenization script replaces all PII (names, account
    numbers, phone numbers, addresses) with cryptographic tokens using
    SHA-256 hashing with per-session salts. Only tokenized data is
    passed to the LLM layer.** Tokenization Before LLM:

15. **The mapping table between real identifiers and tokens is stored in
    an isolated secure server that never connects to the internet. Even
    if the LLM communication is intercepted, the tokens are
    mathematically irreversible without the vault.** Air-Gapped Token
    Vault:

16. **Production deployment uses Llama 3 or Mistral running on
    bare-metal servers within the bank\'s data center. No transaction
    data transits the internet at any point.** Local LLM Deployment
    (Enterprise):

17. **Investigators can only view alerts in their assigned jurisdiction;
    senior investigators can override and escalate; all access is logged
    and auditable.** Role-Based Access Control:

18. **Hot graph data is retained for 90 days; warm for 1 year; cold for
    3 years --- aligned with PMLA record-keeping requirements of 5 years
    for reported entities.** Data Retention Policy:

**8.2 Regulatory Compliance Mapping**

  ---------------------- ----------------------- ------------------------
  **Regulation**         **Requirement**         **GraphSentinel
                                                 Implementation**

  **PMLA 2002**          Report suspicious       Automated SAR generation
                         transactions to FIU-IND formatted to FIU-IND
                                                 spec

  RBI Master Direction   Enhanced Due Diligence  Risk Score triggers EDD
  on KYC                 for high-risk accounts  workflow automatically

  DPDP Act 2023          Data minimization and   Tokenization; analysts
                         purpose limitation      see only risk signals,
                                                 not raw PII

  Basel III / RBI Pillar Operational risk        Full audit trails on all
  2                      management              detection and
                         documentation           investigator actions
  ---------------------- ----------------------- ------------------------

**9. Development & Build Plan**

**9.1 Hackathon Sprint Plan (March 13--27, 2026)**

  ---------------- ------------- ------------------------------ ----------------
  **Phase**        **Dates**     **Deliverables**               **Owner**

  **PPT Round 1**  Mar 13--15    6-slide deck: problem, gap,    Full Team
                                 solution, architecture, demo   
                                 preview, team credentials      

  **Round 1        Mar 16        PPT submission deadline --- NO ---
  Submission**                   CODE REQUIRED                  

  **Data + Graph** Mar 16--17    Day 1 (Mar 16): Synthetic data Backend Lead
                                 generation ONLY --- 10K nodes, 
                                 100K edges, fraud patterns     
                                 embedded. Validate dataset     
                                 integrity before touching      
                                 graph code. Day 2 (Mar 17):    
                                 Neo4j/NetworkX ingestion + DFS 
                                 cycle detection query only. Do 
                                 not attempt all 3 algorithms   
                                 on Day 2 --- get one working   
                                 perfectly first.               

  **Graph          Mar 18 AM     Fan-in and hub-spoke detection Backend Lead
  Algorithms**                   algorithms added after cycle   
                                 detection is stable. Debug     
                                 graph traversal bugs here ---  
                                 do NOT push to Day 3.          

  **Intelligence   Mar 18 PM     Risk scoring engine;           ML Lead
  Layer**                        tokenization layer; LLM        
                                 integration for case           
                                 explanations; streaming        
                                 simulator (replaces static     
                                 CSV)                           

  **Dashboard**    Mar 19        Streamlit app: 3 screens;      Frontend Lead
                                 pyvis graph visualization;     
                                 alert table; SAR PDF           
                                 generation                     

  **Round 2 Demo** Mar 20        Live evaluation --- working    Full Team
                                 prototype demonstration        

  **Polish +       Mar 21--26    Bug fixes; demo path           Full Team
  Pitch**                        rehearsal; architecture slide; 
                                 pitch narrative; Q&A prep      

  **Grand Finale** Mar 27        VIT Pune --- On-campus final   Full Team
                                 presentation and live demo     
  ---------------- ------------- ------------------------------ ----------------

**9.2 Technology Stack**

  ------------------ ---------------------- ------------------------------
  **Layer**          **Prototype            **Enterprise (Production)**
                     (Hackathon)**          

  **Data Ingestion** Python pandas + CSV    Apache Kafka + schema registry

  Stream Processing  Python pre-filter      Apache Flink
                     script                 

  Graph Database     Python NetworkX +      Neo4j Enterprise / TigerGraph
                     Neo4j Free             

  Graph Algorithms   NetworkX DFS, degree   PyTorch Geometric (GNNs),
                     analysis               GraphSAGE

  ML / Scoring       Weighted rule-based    Isolation Forest + Graph
                     scorer                 Neural Networks

  LLM Layer          Claude API (tokenized  On-premise Llama 3 / Mistral
                     inputs)                (air-gapped)

  Frontend           Streamlit + pyvis      React + D3.js + WebGL graph
                                            renderer

  SAR Generation     Python reportlab (PDF) Templated SAR system with
                                            FIU-IND API integration

  Synthetic Data     Python Faker + AMLSim  Live core banking data streams
                     dataset                
  ------------------ ---------------------- ------------------------------

**10. Risks & Mitigations**

  --------------------- -------------- ----------------- ---------------------
  **Risk**              **Severity**   **Likelihood**    **Mitigation**

  **Demo fails during   **CRITICAL**   Medium            Pre-load a
  live presentation**                                    500-transaction demo
                                                         scenario that
                                                         completes reliably in
                                                         25 seconds. All LLM
                                                         explanations are
                                                         pre-cached locally so
                                                         no API call is needed
                                                         during the demo.
                                                         Video backup is last
                                                         resort only --- not
                                                         the primary plan.

  Graph visualization   **HIGH**       Medium            Show only the flagged
  too slow                                               subgraph (20--50
                                                         nodes), not the full
                                                         10K-node graph. Full
                                                         graph is available on
                                                         a separate tab.

  LLM API rate limiting **HIGH**       Low               Pre-generate and
  during demo                                            locally cache all LLM
                                                         explanations for the
                                                         3 demo fraud
                                                         scenarios before the
                                                         presentation begins

  Judges note graph DB  **HIGH**       Medium            Acknowledge this
  is already used by                                     directly in the
  banks                                                  pitch. Lead with LLM
                                                         explanation + SAR
                                                         draft as the genuine
                                                         differentiators, not
                                                         the graph layer
                                                         itself.

  Team capacity         **MEDIUM**     Medium            Cut SAR PDF if behind
  bottleneck on sprint                                   schedule.
                                                         Non-negotiable core:
                                                         graph visualization +
                                                         LLM explanation.
                                                         Everything else is
                                                         additive.
  --------------------- -------------- ----------------- ---------------------

**11. Competitive Differentiation**

Major Indian banks (SBI, HDFC, ICICI) and global institutions already
deploy Neo4j, TigerGraph, or Palantir for AML graph analytics. Graph
databases are no longer a differentiator in isolation --- they are table
stakes. GraphSentinel\'s genuine differentiators are the LLM explanation
layer and the SAR draft workflow, which are absent or early-stage in
most existing deployments.

  ------------------------- -------------------- --------------------------
  **Feature**               **Existing Graph AML **GraphSentinel Position**
                            Systems**            

  **Graph database core**   Already deployed at  NOT a differentiator ---
                            tier-1 banks         acknowledged as table
                                                 stakes

  Multi-hop cycle detection Standard in modern   NOT a differentiator ---
                            AML platforms        expected baseline
                                                 capability

  LLM plain-English case    Absent or            GENUINE DIFFERENTIATOR ---
  explanation               proprietary in most  compresses investigator
                            deployments          analysis time

  Investigator-ready SAR    Manual 3-5 day       GENUINE DIFFERENTIATOR ---
  draft (FIU-IND format)    process in all known pre-populated draft with
                            systems              mandatory human review
                                                 gate

  Tokenize-LLM-Detokenize   Not standard;        DIFFERENTIATOR --- cloud
  privacy loop              vendors use on-prem  LLM benefits without raw
                            models only          PII exposure
  ------------------------- -------------------- --------------------------

**11.1 The Pitch Narrative (30-Second Version)**

+-----------------------------------------------------------------------+
| **Judge-Ready Story**                                                 |
|                                                                       |
| Banks already use graph databases for AML. That is not the problem we |
| are solving. The problem is that when the graph flags a suspicious    |
| pattern, a compliance officer still spends 3 to 5 days manually       |
| writing a 20-page SAR report before it reaches the FIU. GraphSentinel |
| compresses that to under 3 minutes --- with an AI-drafted SAR, a      |
| plain-English explanation of the fraud pattern, and a full            |
| transaction timeline. We are not replacing the graph layer. We are    |
| making it actionable.                                                 |
+-----------------------------------------------------------------------+

**12. Known Limitations & Open Problems**

Intellectual honesty about system limitations is a design requirement,
not an afterthought. The following are acknowledged constraints that
inform the prototype scope and the enterprise roadmap.

**12.1 Adversarial Evasion**

Fraud patterns evolve. Once detection algorithms are deployed,
sophisticated criminal networks will study behavior and adapt ---
concept drift. GraphSentinel\'s current algorithms detect four known
structural topologies. Novel structures that do not match these
templates will not be flagged.

-   **No GAN-based adversarial testing is in prototype scope.**
    Prototype Limitation:

-   **The prototype includes an \'Adversarial Test Mode\' accessible
    from the dashboard. This mode generates synthetic evasion variants
    and shows detection failures honestly:** Prototype Mitigation ---
    Rule-Based Evasion Probe Mode:

```{=html}
<!-- -->
```
-   Cycle +1 hop test: extends a known 4-hop cycle to 5 hops, then 6, 7,
    8, and 9. Dashboard shows at which hop count detection degrades,
    with annotation \'DFS depth limit reached --- cycle not detected.\'

-   Split hub test: a single hub-and-spoke pattern is split into two
    smaller hubs sharing the same beneficiary. Dashboard shows
    \'Hub-spoke signature broken --- pattern falls below structural
    threshold.\'

-   Time-distributed smurfing test: transactions spread across 95 days
    instead of 72 hours. Dashboard shows \'Outside hot-layer detection
    window --- historical probe triggered.\'

```{=html}
<!-- -->
```
-   **Demonstrating known failure modes to judges is not a weakness ---
    it is security maturity. It validates that the team understands the
    threat model, and it creates concrete Phase 2 justification for
    GAN-based adversarial training.** Purpose:

-   **GAN-based Red Team module continuously generates novel fraud
    topologies to probe detection coverage. GNN-based detection replaces
    hardcoded topology matching with learned structural embeddings that
    generalize to unseen patterns.** Phase 2 Mitigation Path:

**12.2 Ground Truth Problem**

The prototype demonstrates that flagged patterns are structurally
suspicious --- but it cannot independently verify that a flagged
transaction is actually fraudulent. All flags are investigator leads,
not determinations.

-   **Detection accuracy metrics (precision, recall) can only be
    measured retroactively after investigators confirm or clear cases
    over deployment time.** Consequence:

-   **The prototype includes a concrete feedback loop, not aspirational
    roadmap vaporware:** Mitigation --- Feedback Infrastructure
    (implemented in prototype):

```{=html}
<!-- -->
```
-   investigator_decisions table: alert_id, decision (confirmed_fraud /
    false_positive / unclear), confidence (1--5), pattern_type, notes,
    timestamp

-   scorer_config table: pattern_type, signal_weights (JSON),
    model_version, last_updated

-   Demo cycle: A false positive is flagged (legitimate GST-registered
    business trips hub-spoke detector). Investigator marks it
    false_positive with confidence 5. The system recomputes the GST
    innocence discount weight for that pattern type from -20% to -28%.
    Score recalculates from 47 to 41, dropping to \'Deferred Review.\' A
    mock retraining round is triggered and model_version increments.

-   This is not real ML retraining --- it is weight adjustment based on
    feedback. Real GNN retraining is Phase 2. But demonstrating the
    feedback loop architecture is real and functional, even at this
    scale, is what makes \'continuous improvement\' credible to judges.

**12.3 Infrastructure Cost Reality**

The enterprise architecture described in this PRD represents significant
infrastructure investment. A rough order-of-magnitude estimate:

-   **Approximately \$50,000--\$200,000 per year depending on cluster
    size** Neo4j Enterprise License:

-   **Approximately \$3,000--\$15,000 per month for 1M
    transactions/day** Kafka + Flink cluster (cloud):

-   **Approximately \$20,000--\$80,000 capital expenditure** On-premise
    GPU server for Llama 3:

-   **Approximately \$150,000--\$500,000 --- justified against the \$64M
    average annual AML compliance spend for mid-tier banks, but
    prohibitive for small banks** Total Year 1:

**12.4 Business Model --- Tiered SaaS**

A flat enterprise-only pricing model excludes small banks that cannot
afford \$500K deployments, while large banks (SBI, HDFC, ICICI) already
have Palantir or Neo4j and have little incentive to switch.
GraphSentinel addresses this with a tiered model designed to create
network effects across the Indian banking ecosystem:

  ---------------- ------------------ ------------------------------------
  **Tier**         **Target**         **Model & Pricing**

  **Community      Small banks, UCBs, Open-source, NetworkX-based, no LLM
  Edition**        NBFCs              layer, manual SAR writing. Free.
                                      Builds adoption and generates
                                      training data via investigator
                                      feedback.

  **Professional   Mid-tier private   Cloud-hosted Neo4j + LLM API.
  Edition**        banks              Per-alert pricing at ₹500 per
                                      processed alert cluster. Self-serve
                                      onboarding. Estimated 200--500
                                      alerts/month = ₹1--2.5L MRR per
                                      bank.

  **Enterprise     Large banks, PSBs  On-premise deployment, fixed annual
  Edition**                           license (\$150K/year). Air-gapped
                                      LLM. Dedicated integration support
                                      for core banking connectors.

  **FIU-IND        Regulator          Aggregated, anonymized cross-bank
  Analytics        (non-revenue)      fraud pattern dashboard provided
  Layer**                             free to FIU-IND. Creates network
                                      effects: banks join because
                                      detection improves as more
                                      participate. FIU-IND endorsement
                                      becomes the key sales mechanism.
  ---------------- ------------------ ------------------------------------

**12.5 Core Banking Integration Complexity**

Core banking systems use varied and proprietary formats: ISO 8583 (card
networks), XML/SOAP (RTGS/NEFT via RBI), FIX protocol (treasury), and
proprietary formats (Finacle, Temenos, BaNCS). GraphSentinel\'s
ingestion layer assumes normalized JSON input.

-   **Connectors for each source system format are required before
    production and are out of scope for the prototype.** Gap:

-   **Phase 1 roadmap includes connectors for Finacle, Temenos T24, and
    Oracle FLEXCUBE --- the top 3 core banking platforms at Indian
    banks.** Mitigation:

**13. Future Roadmap (Post-Hackathon)**

**Phase 1 --- Production Hardening (Month 1--3)**

19. Replace NetworkX with Neo4j Enterprise for production-scale graph
    processing

20. Build ISO 8583 and XML/SOAP connectors for core banking system
    integration

21. Deploy on-premise Llama 3 for air-gapped LLM inference --- replacing
    prototype Claude API usage

22. Integrate with FIU-IND API for direct SAR draft submission workflow

**Phase 2 --- Intelligence Upgrade (Month 3--6)**

23. Implement Graph Neural Networks via PyTorch Geometric for
    pattern-agnostic anomaly detection beyond the 4 hardcoded topologies

24. Build GAN-based Red Team module to continuously generate novel fraud
    topologies and probe detection coverage

25. Add behavioral biometrics layer (typing rhythm, device tilt, mouse
    velocity) to detect account takeover preceding transfers

26. Implement investigator feedback retraining pipeline --- confirmed
    frauds and false positives feed model updates

**Phase 3 --- Ecosystem Integration (Month 6--12)**

27. Federated anomaly correlation with participating banks via FIU-IND
    coordinated encrypted graph sharing

28. Integration with CIBIL, MCA21, and GST databases for counterparty
    verification and innocence signal enrichment

29. Implement Apache Kafka ingestion pipeline replacing the batch-replay
    prototype approach

30. RBI regulatory sandbox certification for production deployment
    authorization under PMLA framework

**Appendix A: Glossary**

  ------------------ ----------------------------------------------------
  **Term**           **Definition**

  **AML**            Anti-Money Laundering --- regulatory framework and
                     operational practices to detect and prevent
                     financial crime

  CTR                Cash Transaction Report --- mandatory report filed
                     with FIU-IND for cash transactions above ₹10 lakh

  DFS                Depth-First Search --- graph traversal algorithm
                     used to detect cycles (round-tripping patterns)

  FIU-IND            Financial Intelligence Unit --- India --- the nodal
                     agency under the Ministry of Finance receiving STRs
                     and SARs

  GNN                Graph Neural Network --- deep learning architecture
                     that learns patterns directly from graph topology

  Layering           The second stage of money laundering --- obscuring
                     the origin of funds through complex transfers

  PMLA               Prevention of Money Laundering Act 2002 --- primary
                     Indian legislation governing AML obligations

  SAR                Suspicious Activity Report --- formal regulatory
                     document filed with FIU-IND when suspicious
                     transactions are identified

  Smurfing           Breaking large amounts into smaller transactions to
                     avoid reporting thresholds --- also called
                     structuring

  STR                Suspicious Transaction Report --- specific type of
                     SAR focused on individual suspicious transactions

  Tokenization       Replacing sensitive identifiers with cryptographic
                     tokens before processing --- enables AI analysis
                     without PII exposure
  ------------------ ----------------------------------------------------

**Appendix B: References**

-   UNODC World Drug Report --- Global money laundering estimates
    (\$800B--\$2T annually)

-   RBI Master Direction on Know Your Customer (KYC) --- 2016 (updated
    2023)

-   Prevention of Money Laundering Act 2002 and Amendment Rules 2023

-   FIU-IND Annual Report 2022--23 --- STR and SAR filing statistics

-   ACAMS --- AML False Positive Rate Industry Benchmarks (2023)

-   IBM AMLSim --- Synthetic AML transaction dataset for research

-   PyTorch Geometric Documentation --- GNN implementation for fraud
    detection

-   Neo4j Graph Data Science Library --- Cycle detection and community
    algorithms

*--- END OF DOCUMENT ---*

GraphSentinel PRD v1.3 \| Team Elida \| VIT Pune Hackathon 2026