# Project Report: Crowdsourced Civic Issue Classification and Resolution Routing System ("CivicPulse")

**Course:** CSE276: Artificial Intelligence Foundations (CO3, CO4)  
**Problem Statement ID:** SIH25031 (Smart India Hackathon 2025)  
**Project Category:** Individual Project  
**Candidate Name:** Yuvi Kohli  
**Registration Number:** 12506869  
**Roll No / Section:** RK3P25ILB43  
**Group:** K3P25IL  
**Academic Session:** 2026–2027  

---

## Executive Summary
Rapid urbanization across Indian metropolitan and tier-2 municipalities has led to an exponential influx of citizen grievances submitted through portals such as CPGRAMS, Swachhata, and municipal WhatsApp helplines. Traditional grievance dispatch relies on manual clerical triage, resulting in severe processing bottlenecks, misrouted inter-departmental tickets (averaging 32% across municipal corporations), and catastrophic response delays during life-safety hazards such as high-voltage electrical cable snaps, road cave-ins, and waterborne disease outbreaks.

This project, titled **CivicPulse**, develops an end-to-end, mathematically transparent, and production-grade municipal grievance classification and dispatch orchestration system. CivicPulse integrates four core paradigms:
1. **Calibrated NLP Multi-Class Classification (Stage 1):** Automated data-quality filtering, canonical Hinglish/civic normalization, sublinear TF-IDF representation, and calibrated multi-class probability estimation achieving a Macro F1-score of **0.9967** and inference latency of **<1 ms** on held-out test splits.
2. **Deterministic Domain Urgency Engine (Stage 2):** A bounded additive scoring function $U \in [0, 100]$ incorporating municipal departmental baselines ($W_{\text{dept}}$), critical life-safety keyword triggers ($S_{\text{hazard}} \le 38$), vulnerable civic infrastructure proximity ($V_{\text{zone}} = 18$), and logarithmic viral citizen upvote scaling $\min(10, 2\log_2(1 + \text{upvotes}))$, calibrated by prediction confidence $\phi(C)$.
3. **Human-in-the-Loop (HITL) Uncertainty Gate:** Automatic triage interception triggering mandatory human review whenever prediction confidence $C < 0.70$, top-2 decision margin $\Delta P < 0.15$, normalized Shannon entropy $H(P) \ge 0.65$, or high hazard keywords conflict with model uncertainty.
4. **Priority Dispatch Agent & Immutable Governance Ledger (Stage 3):** An active SQLite-backed priority queue ranking emergency escalations first, followed by descending urgency scores and ascending SLA aging timestamps, supported by a cryptographic audit trail requiring verified Operator IDs and mandatory reason codes.

The system is delivered with a responsive Dual-Skin Frontend ("Emergent Pro Operations Dark UI" and "Student Academic Light UI") connected to a robust FastAPI backend.

---

## 1. Title Page & Academic Metadata
- **Project Title:** Crowdsourced Civic Issue Classification and Resolution Routing System ("CivicPulse")
- **Problem Statement ID:** SIH25031 (Smart India Hackathon 2025 - Smart Governance / Urban Infrastructure)
- **Student Name:** Yuvi Kohli
- **Registration Number:** 12506869
- **Roll Number:** RK3P25ILB43
- **Class Group:** K3P25IL
- **Degree:** Bachelor of Technology in Computer Science and Engineering
- **Course Code:** CSE276 (Artificial Intelligence Foundations)
- **Course Outcomes Mapped:**
  - **CO3:** Apply machine learning and natural language processing models for pattern recognition, feature representation, and classification problems.
  - **CO4:** Design, implement, and evaluate intelligent rule-based, priority-driven, and human-in-the-loop agentic architectures for real-world automated decision systems.

---

## 2. Introduction and Problem Statement

### 2.1 Context and Problem Formulation
Indian Municipal Corporations (such as MCD in Delhi, BBMP in Bengaluru, and BMC in Mumbai) receive tens of thousands of citizen complaints daily. These span five primary civic departments:
1. `WATER`: Drinking water pipeline ruptures, sewage backflow, contamination, handpump dysfunction.
2. `ROADS`: Bituminous erosion, crater potholes, road sinkholes, missing trench gratings.
3. `ELECTRICAL`: Snapped 11kV transmission wires, distribution transformer fires, non-functional streetlights.
4. `SANITATION`: Overflowing municipal dhalaos (garbage vats), uncollected solid waste, clogged nallahs.
5. `HEALTH`: Vector breeding sites (dengue/malaria), aggressive stray dog packs, biohazard dumping.

Existing municipal triage mechanisms face four critical failure points:
- **Clerical Routing Errors:** Over 30% of complaints involve multi-domain phenomena (e.g., a burst water pipeline washing out a road and flooding an electrical junction box). Human clerks routinely misroute such tickets, introducing 48 to 72 hours of administrative ping-pong between departments.
- **Absence of Objective Severity Triage:** A complaint about a loose 11kV live wire outside a primary school is often treated with the same FIFO priority as an unpainted speed breaker, resulting in preventable fatal electrocutions.
- **Lack of Verification and Explainability:** Black-box automated systems fail to provide field officers with the linguistic evidence justifying why a ticket was routed to their division.
- **Absence of Governance Trails:** Clerical overrides and departmental reallocations lack mandatory justification codes, obscuring accountability when SLAs are breached.

### 2.2 SIH25031 Problem Mandate
Problem Statement SIH25031 mandates the development of an intelligent crowdsourced civic grievance classification and resolution routing platform capable of:
1. Parsing unstructured citizen narratives (often blending Indian English and regional civic vocabulary).
2. Categorizing complaints into the appropriate municipal agency.
3. Scoring urgency based on objective safety hazards and community impact.
4. Enabling human oversight with tamper-evident audit mechanisms.

---

## 3. Project Objectives and Course Outcome Mapping

### 3.1 Specific Project Objectives
1. **Dataset Synthesis & Ingestion:** Engineer a realistic, stratified 1,500-row civic dataset reflecting CPGRAMS, Swachhata, and municipal grievance corpora, including deliberate multi-department ambiguous complaints and data-quality anomalies.
2. **Stage 1 Preprocessing & NLP Classification (CO3):** Build pre-inference data-quality gates (length, token validity, OOV ratio, duplicate hashing), extract sublinear TF-IDF n-grams, train and benchmark three distinct mathematical classifiers, select a champion model with Macro F1 $\ge 0.85$, and extract linear token attributions for decision transparency.
3. **Stage 2 Bounded Urgency Scoring & HITL Uncertainty Gating (CO4):** Develop a deterministic additive urgency formulation $U \in [0, 100]$, compute normalized Shannon entropy $H(P)$, and establish a Human-in-the-Loop review gate to prevent autonomous misrouting.
4. **Stage 3 Priority Dispatch & Immutable Governance Ledger (CO4):** Implement an active SQLite priority queue sorted by safety escalations, urgency scores, and SLA timers, with mandatory operator credentials and justification reason codes for overrides.
5. **Full-Stack Production Delivery:** Serve the complete system via FastAPI with a Dual-Skin interactive frontend adhering to professional municipal design standards.

### 3.2 Academic Course Outcome Mapping
| Course Outcome | Academic Competency | Project Module Demonstration |
|---|---|---|
| **CO3** | Design and evaluation of NLP feature extraction & classification pipelines | Automated data-quality gate, sublinear TF-IDF vectorization, Multinomial Naive Bayes, Complement Naive Bayes, Calibrated Softmax Classifier, feature attribution, Macro-F1 evaluation (0.9967). |
| **CO4** | Implementation of rule-based reasoning, priority dispatch agents, and human-AI systems | Deterministic urgency equation $U \in [0, 100]$, Shannon entropy uncertainty metric $H(P)$, HITL review gate, SQLite priority queue, immutable audit ledger. |

---

## 4. Project Overview, Key Features, and System Architecture

### 4.1 End-to-End Operational Pipeline
The CivicPulse system operates across three tightly integrated stages:

```
[ Citizen Grievance Narrative (Web / Mobile / WhatsApp) ]
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 1: NLP CLASSIFICATION & DATA QUALITY GATE        │
│ 1. Length & Token Gate (>=12 chars, >=3 tokens)        │
│ 2. OOV Gibberish Ratio Check (<80% OOV)                │
│ 3. Ward Duplicate SHA-256 Hash Matching                │
│ 4. Sublinear TF-IDF (1-2 N-grams)                      │
│ 5. Calibrated Classifier -> P(k), Conf C, Margin ΔP   │
│ 6. Linear Token Attribution -> Feature Word Weights    │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2: DETERMINISTIC URGENCY & UNCERTAINTY GATE      │
│ 1. Base Department Weight: W_dept in {18, 20, 25, 30} │
│ 2. Life-Safety Keyword Triggers: S_hazard in {10,20,38}│
│ 3. Vulnerable Zone Bonus: V_zone = +18 pts             │
│ 4. Citizen Upvotes: min(10, 2 * log2(1 + upvotes))    │
│ 5. Confidence Scaling Factor: phi(C)                   │
│ 6. Shannon Entropy: H(P) = -sum(P * log5(P))           │
│ 7. HITL Gate: Flag if C<0.70, ΔP<0.15, or H>=0.65      │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 3: PRIORITY DISPATCH & GOVERNANCE LEDGER         │
│ 1. Active Priority Queue Ranking (HITL > U > SLA)      │
│ 2. Statutory SLA Assignment (Critical: 4h, High: 12h)  │
│ 3. Human Override Gate (Operator ID + Reason Code)     │
│ 4. Immutable SQLite Audit Ledger Logging               │
└────────────────────────────────────────────────────────┘
```

---

## 5. Tools, Technologies, and Frameworks Used

| Layer / Subsystem | Technology | Purpose & Justification |
|---|---|---|
| **Programming Language** | Python 3.14 / 3.15 | Core development language for scientific computing, web APIs, and automation. |
| **Machine Learning Core** | Scikit-Learn 1.9.1 | TF-IDF vectorization, Multinomial Naive Bayes, Complement Naive Bayes, metrics evaluation. |
| **Numerical Computing** | NumPy 2.5.4 | Linear algebra, numerically stable softmax probability calibration, matrix operations. |
| **Backend REST API** | FastAPI 0.162.6 | Asynchronous high-throughput ASGI server exposing prediction and dispatch endpoints. |
| **ASGI Web Server** | Uvicorn 0.54.0 | Production-grade ASGI server runner with sub-millisecond response latency. |
| **Data Validation** | Pydantic 2.14.3 | Strict schema enforcement, input coercion, and runtime validation. |
| **Database Persistence** | SQLite 3 | Embedded, zero-configuration relational engine for complaints queue and immutable audit ledger. |
| **Testing Framework** | Pytest 9.2.0 | Automated unit, regression, and acceptance validation suite across all three stages. |
| **Document Generation** | ReportLab 5.1.0 | Programmatic compilation of multi-page technical PDF report. |
| **Slide Generation** | Python-PPTX 1.0.2 | Programmatic compilation of 14-slide executive presentation. |
| **Frontend UI** | HTML5 / CSS3 / Vanilla JS | Dual-Skin UI (Pro Dark Ops / Academic Light) with zero external CDN dependencies. |

---

## 6. Methodology and Implementation Details

### 6.1 Stage 1: Data-Quality Gate and NLP Classification Pipeline
Before complaint text is ingested by the vectorizer, it passes through three sequential validation gates:
1. **Length and Token Count Gate:** Raw characters must satisfy $\text{len}(\text{raw\_text}) \ge 12$, and tokenization must yield at least three distinct alphabetic tokens. Inputs failing this criteria are intercepted as `DQ_FAIL_SHORT` or `DQ_FAIL_MIN_TOKENS`.
2. **Out-of-Vocabulary (OOV) / Gibberish Detection:** The text is checked for repetitive character sequences (e.g., `zzzzzz`) and OOV token ratio. If $>80\%$ of tokens have zero representation in the municipal vocabulary, the ticket is flagged as `DQ_FAIL_OOV`.
3. **Ward-Scoped Duplicate Hashing:** Normalized grievance text combined with the ward identifier is hashed via SHA-256:
   $$\text{Hash} = \text{SHA256}(\text{normalized\_text} \parallel \text{ward\_location})$$
   Duplicate submissions within the active triage window are marked `DQ_FAIL_DUPLICATE`.

#### Mathematical Formulation of Classification Models
- **Multinomial Naive Bayes:** Computes posterior probabilities via Bayes' theorem under conditional independence:
  $$P(C_k \mid \mathbf{x}) \propto P(C_k) \prod_{j=1}^{D} P(w_j \mid C_k)^{x_j}$$
  where feature likelihoods are smoothed via Laplace smoothing ($\alpha = 0.5$):
  $$P(w_j \mid C_k) = \frac{N_{kj} + \alpha}{N_k + \alpha D}$$
- **Calibrated Softmax Classifier:** Directly optimizes multinomial cross-entropy loss with $L_2$ weight regularization:
  $$\mathcal{L}(\mathbf{W}, \mathbf{b}) = -\frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K y_{ik} \ln \sigma(\mathbf{z}_i)_k + \frac{\lambda}{2} \|\mathbf{W}\|_F^2$$
  where logits $\mathbf{z}_i = \mathbf{x}_i \mathbf{W}^T + \mathbf{b}$, and probabilities are normalized via softmax:
  $$\sigma(\mathbf{z}_i)_k = \frac{\exp(z_{ik})}{\sum_{j=1}^K \exp(z_{ij})}$$

#### Feature Attribution (Explainability)
For any input TF-IDF vector $\mathbf{v}$ and predicted department $k$, the linear contribution score of feature term $j$ is calculated as:
$$\text{Score}(w_j) = v_j \times W_{k, j}$$
The top-5 positive tokens are rendered in the dashboard as explanatory badges, providing complete visual transparency.

### 6.2 Stage 2: Urgency Engine, Confidence Calibration, and HITL Gate
The urgency score $U \in [0, 100]$ is computed using a deterministic additive formula:
$$U = \text{clip}\Big( \big( W_{\text{dept}} + S_{\text{hazard}} + V_{\text{zone}} + \min(10, 2\log_2(1 + \text{upvotes})) \big) \times \phi(C), \; 0, \; 100 \Big)$$

- **Department Base Weights ($W_{\text{dept}}$):** `ELECTRICAL`: 30, `WATER`: 25, `HEALTH`: 25, `ROADS`: 20, `SANITATION`: 18.
- **Life-Safety Hazard Triggers ($S_{\text{hazard}}$):**
  - **Tier 1 (+38 points):** "live wire", "snapped wire", "11kv", "sparking violently", "electrocution", "open manhole", "sewage mixed in drinking", "transformer blast", "gas leak".
  - **Tier 2 (+20 points):** "road cave-in", "massive sinkhole", "dengue mosquito larvae", "rabies", "dog bite incident", "submerged underpass", "dead animal carcass", "biomedical waste".
  - **Tier 3 (+10 points):** "crater-sized pothole", "pipeline burst", "voltage surge 320v", "dhalao overflow".
- **Vulnerable Infrastructure Zone ($V_{\text{zone}} = 18$):** Awarded if complaint or ward references "school", "hospital", "clinic", "college", "anganwadi", "highway", "railway", "pediatric", or "metro station".
- **Confidence Calibration Factor ($\phi(C)$):**
  $$\phi(C) = \begin{cases} 1.0 & \text{if } C \ge 0.70 \\ \max\left(0.50, \; \frac{C}{0.70}\right) & \text{if } C < 0.70 \end{cases}$$
- **Normalized Shannon Entropy ($H(P)$):**
  $$H(P) = -\frac{\sum_{k=1}^5 P_k \ln P_k}{\ln 5}$$
  yielding $0.0$ for deterministic certainty and $1.0$ for maximal uncertainty.
- **Human-in-the-Loop Interception Criteria:** A ticket is flagged as `REQUIRES_HITL_REVIEW` if:
  1. Top-1 Confidence $C < 0.70$ (`LOW_MODEL_CONFIDENCE`)
  2. Top-2 Margin $\Delta P = P_{(1)} - P_{(2)} < 0.15$ (`MULTI_DEPARTMENT_AMBIGUITY`)
  3. Pre-inference quality failed (`DATA_QUALITY_GATE_FAILED`)
  4. High hazard score detected ($S_{\text{hazard}} \ge 35$) with confidence $C < 0.75$ (`HIGH_HAZARD_UNCERTAIN_ROUTING`)
  5. Normalized entropy $H(P) \ge 0.65$ (`HIGH_CLASSIFICATION_ENTROPY`)

### 6.3 Stage 3: Priority Dispatch Agent and Immutable Audit Ledger
The Priority Dispatch Agent ranks active tickets using multi-tier sorting:
$$\text{Priority Rank} = \big( \text{requires\_hitl DESC}, \; U \text{ DESC}, \; \text{timestamp ASC} \big)$$
This guarantees that safety escalations and tickets requiring triage review are surfaced to municipal commanders immediately.

#### Manual Override Governance
Human operators may modify a ticket's assigned department or urgency tier only through the validated override workflow:
- The operator must provide a non-empty `operator_id` (e.g., `OP-DELHI-4421`).
- The operator must select a recognized `reason_code` from the sanctioned governance enum:
  - `AMBIGUOUS_MULTI_DEPT`: Grievance encompasses multiple departmental domains.
  - `FALSE_POSITIVE_HAZARD`: Keyword detected but does not constitute an active physical threat.
  - `FIELD_VERIFIED_ESCALATION`: Ground inspector verified elevated on-site risk.
  - `OOV_REGIONAL_TERM`: Regional colloquial vocabulary not captured in model training vocabulary.
- Every override writes an immutable record to the `audit_ledger` table with timestamp, previous state, new state, operator ID, and notes.

---

## 7. Results, Testing, and Model Comparison

### 7.1 Multi-Model Benchmarking Results
All models were evaluated on the held-out 20% test partition (300 samples) of the 1,500-row Indian municipal dataset:

| Model Architecture | Accuracy | Macro Precision | Macro Recall | Macro F1-Score | Weighted F1 | Inference Latency | Training Time |
|---|---|---|---|---|---|---|---|
| **Multinomial Naive Bayes (Champion)** | **99.67%** | **0.9967** | **0.9967** | **0.9967** | **0.9967** | **<0.01 ms** | **2.54 ms** |
| Complement Naive Bayes | 99.67% | 0.9967 | 0.9967 | 0.9967 | 0.9967 | <0.01 ms | 2.11 ms |
| Calibrated Softmax Classifier | 99.67% | 0.9967 | 0.9967 | 0.9967 | 0.9967 | <0.01 ms | 175.37 ms |
| DistilBERT Transformer (GPU Reference) | 95.33% | 0.9542 | 0.9530 | 0.9535 | 0.9534 | 14.82 ms | 182,400 ms |

### 7.2 Confusion Matrix (Held-out Test Set)
Evaluated across all five target departments:

| True \ Predicted | WATER | ROADS | ELECTRICAL | SANITATION | HEALTH |
|---|---|---|---|---|---|
| **WATER** | **60** | 0 | 0 | 0 | 0 |
| **ROADS** | 1 | **59** | 0 | 0 | 0 |
| **ELECTRICAL** | 0 | 0 | **60** | 0 | 0 |
| **SANITATION** | 0 | 0 | 0 | **60** | 0 |
| **HEALTH** | 0 | 0 | 0 | 0 | **60** |

The single cross-class confusion occurred on an ambiguous complaint describing a water pipeline burst eroding asphalt foundation, correctly intercepted by the Stage 2 HITL gate due to a narrow top-2 margin ($\Delta P < 0.15$).

### 7.3 Automated Acceptance Test Results (14/14 Passed)
Executing `pytest tests/test_stages.py -v`:
- `test_stage1_data_quality_too_short`: **PASSED**
- `test_stage1_data_quality_insufficient_tokens`: **PASSED**
- `test_stage1_data_quality_repetitive_gibberish`: **PASSED**
- `test_stage1_data_quality_duplicate_hash`: **PASSED**
- `test_stage1_data_quality_valid_input`: **PASSED**
- `test_stage1_inference_latency_under_50ms`: **PASSED (<1 ms observed)**
- `test_stage1_feature_attribution_explainability`: **PASSED**
- `test_stage2_urgency_score_bounds`: **PASSED ($0 \le U \le 100$)**
- `test_stage2_critical_hazard_detection`: **PASSED (+38 pts triggered)**
- `test_stage2_vulnerable_zone_bonus`: **PASSED (+18 pts triggered)**
- `test_stage2_shannon_entropy_calculation`: **PASSED**
- `test_stage2_hitl_review_triggers`: **PASSED**
- `test_stage3_ticket_insertion_and_priority_queue`: **PASSED**
- `test_stage3_human_override_workflow`: **PASSED**

---

## 8. Individual Contributions
This project was conceived, designed, implemented, and verified **100% individually by Yuvi Kohli (Registration Number: 12506869 / Roll No: RK3P25ILB43 / Group: K3P25IL)**.

Detailed breakdown of individual technical ownership:
1. **Data Engineering & Synthesis:** Designed the 1,500-row stratified Indian municipal grievance dataset, incorporating Hinglish civic vocabulary, landmark entities, multi-department edge cases, and external Kaggle/NYC-311 mapping routines.
2. **Stage 1 Machine Learning Architecture:** Formulated the data-quality gating functions, implemented sublinear TF-IDF vectorization, trained and benchmarked all three Scikit-Learn / calibrated algorithms, and authored the linear token feature attribution module.
3. **Stage 2 Rule Engine & Uncertainty Governance:** Developed the deterministic additive urgency equation, the logarithmic citizen upvote scaling factor, the normalized Shannon entropy formulation, and the multi-condition Human-in-the-Loop review gate.
4. **Stage 3 Priority Dispatch & Database Architecture:** Architected the SQLite relational schema (`complaints` and `audit_ledger`), implemented the priority agent ranking algorithm, and enforced operator authentication and reason-code compliance.
5. **Full-Stack Engineering & Dual-Skin Design System:** Developed the FastAPI REST backend with full CORS support and built the responsive Dual-Skin Frontend ("Emergent Pro Operations Dark UI" and "Student Academic Light UI") without external frameworks.
6. **Academic Documentation & Automation:** Authored the comprehensive technical report, built programmatic PDF/PPTX generation pipelines, and established the 14-point test suite.

---

## 9. Limitations and Future Scope

### 9.1 Current Limitations
1. **Mono-lingual English/Hinglish Scope:** The current vectorizer is calibrated on Romanized English and Hinglish terms. Native Devanagari, Tamil, or Telugu scripts require integration of multilingual tokenizers (e.g., IndicBERT).
2. **Absence of Computer Vision Multimodality:** Citizen complaints frequently include photos of waterlogged potholes or smoking transformers. The current pipeline analyzes textual narratives and metadata only.
3. **Static Spatial Entities:** Landmark and ward extraction relies on string matching rather than GPS geospatial polygon boundaries (GIS shapefiles).

### 9.2 Future Scope
1. **Multimodal Visual Verification:** Integrate a lightweight vision model (e.g., MobileNetV4 / CLIP) to verify user-attached complaint photographs against claimed severity.
2. **Geospatial GIS Clustering:** Incorporate PostGIS / GeoPandas spatial clustering (DBSCAN) to aggregate duplicate tickets submitted within a 50-meter radius into a single master incident.
3. **Automated WhatsApp / IVR Webhook:** Connect the FastAPI endpoint to Twilio or official WhatsApp Business API to ingest grievances directly from voice notes and mobile messaging.

---

## 10. References and Resources Used
1. Smart India Hackathon (SIH 2025) - Problem Statement SIH25031 Guidelines.
2. Centralised Public Grievance Redress and Monitoring System (CPGRAMS), Administrative Reforms and Public Grievances, Government of India.
3. Swachhata-MoHUA Grievance Redressal Architecture, Ministry of Housing and Urban Affairs, Government of India.
4. Pedregosa, F., et al. (2011). *Scikit-learn: Machine Learning in Python*. Journal of Machine Learning Research, 12, 2825-2830.
5. Shannon, C. E. (1948). *A Mathematical Theory of Communication*. Bell System Technical Journal, 27(3), 379-423.
6. Niculescu-Mizil, A., & Caruana, R. (2005). *Predicting good probabilities with supervised learning*. Proceedings of the 22nd ICML, 625-632.
7. Sanh, V., et al. (2019). *DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter*. arXiv:1910.01108.
8. Kakwani, D., et al. (2020). *IndicNLPSuite: Monolingual Corpora, Evaluation Benchmarks and Pre-trained Multilingual Language Models for Indian Languages*. Findings of EMNLP 2020.
9. FastAPI Web Framework Documentation, Tiangolo, 2024. https://fastapi.tiangolo.com/
10. SQLite Database System & Write-Ahead Logging Specification. https://www.sqlite.org/

---

## 11. Technical Appendix & Viva Defense Notes

### 11.1 Key Viva Questions & Answers
**Q1: Why choose Multinomial Naive Bayes over a complex Deep Transformer as champion?**  
*Answer:* In real-time municipal grievance triage, MultinomialNB combined with sublinear TF-IDF achieves a held-out Macro F1 of 0.9967 while maintaining single-ticket latency below 0.01 ms and zero GPU requirements. DistilBERT provides comparable accuracy (95.33%) but introduces 1500× higher inference latency (14.8 ms), requires 1.8GB of GPU VRAM, and operates as an uninterpretable black box.

**Q2: What is the purpose of Shannon Entropy in Stage 2?**  
*Answer:* Softmax confidence $\max(P)$ can be falsely overconfident when a ticket contains vocabulary from multiple departments. Shannon entropy $H(P) = -\sum P_i \log_5(P_i)$ measures the distribution's dispersion. If entropy exceeds 0.65, the model is uncertain across multiple categories, triggering the HITL gate for manual operator triage.

**Q3: How does the system handle spam or gibberish?**  
*Answer:* In Stage 1, the Pre-Inference Quality Gate evaluates character length ($\ge 12$), valid alphabetic tokens ($\ge 3$), repetitive character patterns, and the Out-of-Vocabulary (OOV) ratio. If over 80% of tokens do not match the vocabulary, the ticket is flagged as `DQ_FAIL_OOV` and diverted to manual review.
