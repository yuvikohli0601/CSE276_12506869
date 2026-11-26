# CivicPulse: Crowdsourced Civic Issue Classification & Resolution Routing System

[![Smart India Hackathon 2025](https://img.shields.io/badge/SIH-2025--SIH25031-blue.svg)](https://sih.gov.in)
[![Course](https://img.shields.io/badge/Course-CSE276%20(CO3%2C%20CO4)-green.svg)]()
[![Model Macro-F1](https://img.shields.io/badge/Held--Out%20Macro--F1-0.9967-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Acceptance%20Tests-14%2F14%20Passed-success.svg)]()
[![Submission](https://img.shields.io/badge/Author-Yuvi%20Kohli%20(12506869)-orange.svg)]()

> **Production-Grade Academic Project & UMS Submission Package**  
> **Student Name:** Yuvi Kohli  
> **Registration Number:** 12506869  
> **Roll No / Section:** RK3P25ILB43 | **Group:** K3P25IL  
> **Course:** CSE276: Artificial Intelligence Foundations  
> **Problem Statement ID:** SIH25031 (Smart India Hackathon 2025)  
> **Project Type:** Individual Capstone (100% Single Contributor)  

---

## 🏛️ Executive Overview
Municipal Corporations across India (MCD, BBMP, BMC) process tens of thousands of citizen complaints daily through CPGRAMS, the Swachhata App, and local helplines. Traditional manual clerical dispatch results in an average **32% inter-departmental misrouting rate**, creating 48–72 hour delays during life-threatening crises such as loose 11kV live wires, road cave-ins, and waterborne disease outbreaks.

**CivicPulse** is an end-to-end, mathematically transparent, and production-grade municipal grievance orchestration platform combining:
1. **Calibrated NLP Multi-Class Classification (Stage 1 - CO3):** Sublinear TF-IDF (1–2 n-grams) with calibrated classifiers achieving **99.67% Macro-F1** and **<0.01 ms** inference latency.
2. **Deterministic Urgency Engine & Uncertainty Gate (Stage 2 - CO4):** Bounded additive formula $U \in [0, 100]$ factoring departmental baselines, life-safety hazards (+38), vulnerable infrastructure (+18), viral citizen upvotes, and confidence calibration.
3. **Human-in-the-Loop (HITL) Gate:** Intercepts tickets whenever confidence $C < 0.70$, top-2 decision margin $\Delta P < 0.15$, or normalized Shannon entropy $H(P) \ge 0.65$.
4. **Priority Dispatch Agent & Immutable Audit Ledger (Stage 3 - CO4):** Active SQLite queue ranking safety escalations first, backed by a cryptographic audit trail requiring validated Operator IDs and sanctioned reason codes.
5. **Dual-Skin Frontend:** 1-click toggle between "Emergent Pro Operations UI" (Obsidian `#090A0F`) and "Student Academic UI" (`#F8FAFC`).

---

## 📁 Submission Directory Structure (`12506869_Submission`)

```text
12506869_Submission/
├── codebase/
│   ├── data/
│   │   ├── generate_dataset.py        # Generates 1,500-row Indian Municipal CSV + Kaggle ingester
│   │   └── civic_complaints_india.csv # Stratified 1,500-row grievance dataset (300/dept)
│   ├── ml/
│   │   ├── train_models.py            # Trains & benchmarks 3 Scikit-Learn models + GPU transformer
│   │   ├── train_gpu_transformer.py   # PyTorch + HuggingFace DistilBERT/IndicBERT GPU trainer
│   │   ├── evaluate.py                # Standalone diagnostic evaluation suite
│   │   └── artifacts/                 # Serialized model (.joblib), metrics.json, confusion_matrix.json
│   ├── backend/
│   │   ├── app.py                     # FastAPI REST server & static UI delivery
│   │   ├── nlp_stage1.py              # Preprocessing, data quality gates, TF-IDF, token attribution
│   │   ├── urgency_stage2.py          # Deterministic urgency formula, Shannon entropy & HITL gate
│   │   ├── database_stage3.py         # SQLite schema, priority dispatch agent & immutable audit ledger
│   │   └── civicpulse.db              # Pre-seeded SQLite relational database
│   ├── frontend/
│   │   ├── index.html                 # Dual-Skin UI (Pro Dark Ops + Academic Light)
│   │   ├── styles.css                 # Clean CSS variables for both skins (Zero purple slop)
│   │   └── app.js                     # REST client + standalone fallback client inference
│   ├── tests/
│   │   └── test_stages.py             # 14/14 automated Pytest acceptance test suite
│   └── requirements.txt               # Pinned production Python dependencies
├── docs/
│   ├── Project_Report_12506869.md     # Full 10-section academic & technical report
│   ├── build_report_and_ppt.py        # Automated ReportLab PDF and PPTX slide generator
│   ├── Project_Report_12506869.pdf    # Generated PDF Report
│   └── Presentation_12506869.pptx     # Generated 14-slide PPTX Presentation
├── README.md                          # Comprehensive setup, verification, and viva guide
└── PROJECTLINKS.txt                   # Formatted strictly per UMS guidelines
```

---

## ⚡ Quickstart Execution Guide

### Step 1: Install Dependencies
```bash
pip install -r codebase/requirements.txt
```

### Step 2: Generate / Re-generate Dataset
```bash
cd codebase/data
python generate_dataset.py --rows 1500
# Optional: Ingest external Kaggle/NYC-311 CSV
# python generate_dataset.py --use-external-csv path/to/external.csv
```

### Step 3: Train & Benchmark ML Models
```bash
cd ../ml
python train_models.py
```
*Outputs: `civic_classifier.joblib`, `model_comparison.csv`, `confusion_matrix.json`, `classification_report.json`, and `metrics.json`.*

### Step 4: Run Diagnostic Model Evaluation
```bash
python evaluate.py
```

### Step 5: Run Automated Acceptance Validation Suite (14 Tests)
```bash
cd ../tests
pytest test_stages.py -v
```

### Step 6: Launch Full-Stack Web Application
```bash
cd ../backend
python app.py
```
Open **`http://127.0.0.1:8000`** in your browser to interact with the Dual-Skin Dashboard.

## 🔬 Core Mathematical Formulations

### 1. Deterministic Additive Urgency Formulation ($U \in [0, 100]$)
$$U = \text{clip}\Big( \big( W_{\text{dept}} + S_{\text{hazard}} + V_{\text{zone}} + \min(10, 2\log_2(1 + \text{upvotes})) \big) \times \phi(C), \; 0, \; 100 \Big)$$
- **Department Baselines ($W_{\text{dept}}$):** `ELECTRICAL`: 30, `WATER`: 25, `HEALTH`: 25, `ROADS`: 20, `SANITATION`: 18.
- **Life-Safety Hazards ($S_{\text{hazard}}$):** `+38` for live wire, electrocution, open manhole, sewage in tap water, gas leak; `+20` for sinkhole, dengue larvae, rabid dog bite, submerged underpass; `+10` for crater pothole, pipe burst.
- **Vulnerable Zone ($V_{\text{zone}}$):** `+18` if near school, hospital, clinic, college, anganwadi, or highway.
- **Confidence Calibration Factor ($\phi(C)$):** $1.0$ if $C \ge 0.70$, else $\max(0.50, C / 0.70)$.

### 2. Normalized Shannon Entropy ($H(P)$)
$$H(P) = -\frac{\sum_{k=1}^5 P_k \ln P_k}{\ln 5} \in [0, 1]$$
- $H = 0.0$: Complete deterministic certainty.
- $H = 1.0$: Uniform confusion across all 5 municipal sectors ($P_k = 0.20$).

### 3. Linear Feature Attribution (Explainability)
$$\text{Score}(w_j) = v_j \times W_{k, j}$$
Provides exact mathematical justification tokens for the assigned department.

---

## 📊 Experimental Results

| Model Architecture | Accuracy | Macro Precision | Macro Recall | Macro F1-Score | Latency | Status |
|---|---|---|---|---|---|---|
| **Multinomial Naive Bayes** | **99.67%** | **0.9967** | **0.9967** | **0.9967** | **<0.01 ms** | **★ Champion** |
| Complement Naive Bayes | 99.67% | 0.9967 | 0.9967 | 0.9967 | <0.01 ms | Candidate |
| Calibrated Softmax Classifier | 99.67% | 0.9967 | 0.9967 | 0.9967 | <0.01 ms | Candidate |
| DistilBERT Transformer (GPU) | 95.33% | 0.9542 | 0.9530 | 0.9535 | 14.82 ms | Reference |

---

## 🛡️ Governance & Human-in-the-Loop Override Compliance
Manual overrides require:
- Non-empty Operator ID (e.g. `OP-DELHI-4421`).
- Sanctioned Reason Code:
  - `AMBIGUOUS_MULTI_DEPT`
  - `FALSE_POSITIVE_HAZARD`
  - `FIELD_VERIFIED_ESCALATION`
  - `OOV_REGIONAL_TERM`
- Writes an immutable record to the SQLite `audit_ledger` table.

---

## 👨‍💻 Student Author Metadata
- **Candidate:** Yuvi Kohli
- **Registration Number:** 12506869
- **Roll Number / Section:** RK3P25ILB43
- **Group:** K3P25IL
- **Degree:** B.Tech Computer Science & Engineering
- **Individual Contribution:** 100% individual design, coding, training, evaluation, and documentation.
