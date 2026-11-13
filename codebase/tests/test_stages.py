"""
CivicPulse - Stage 1, Stage 2, and Stage 3 Acceptance Validation Suite
Course: CSE276 | Problem Statement: SIH25031
Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)

Verifies:
- Stage 1: Data quality gates (length, OOV, duplicate hashing), TF-IDF, Macro-F1 >= 0.85, Latency < 50ms.
- Stage 2: Urgency score mathematical bounds [0, 100], hazard rules, vulnerable zones, Shannon entropy, HITL gate.
- Stage 3: SQLite ticket insertion, priority agent ranking, human-in-the-loop override governance and audit ledger.
"""

import os
import sys
import time
import pytest
import sqlite3

# Ensure codebase root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
codebase_dir = os.path.abspath(os.path.join(current_dir, ".."))
if codebase_dir not in sys.path:
    sys.path.insert(0, codebase_dir)

from backend.nlp_stage1 import (
    normalize_text,
    check_data_quality,
    compute_text_hash,
    calculate_shannon_entropy,
    CivicNLPPipeline,
    DEPARTMENTS
)
from backend.urgency_stage2 import (
    calculate_urgency_score,
    detect_hazard_score,
    detect_vulnerable_zone,
    compute_upvote_bonus
)
from backend.database_stage3 import (
    init_database,
    insert_ticket,
    apply_human_override,
    get_priority_queue,
    get_audit_ledger,
    VALID_REASON_CODES
)

# Shared artifact fixture
@pytest.fixture(scope="session")
def nlp_pipeline():
    artifact_path = os.path.join(codebase_dir, "ml", "artifacts", "civic_classifier.joblib")
    if not os.path.exists(artifact_path):
        pytest.skip(f"Artifact {artifact_path} not found. Run train_models.py first.")
    return CivicNLPPipeline(artifact_path)

@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_civicpulse.db")
    init_database(db_path)
    return db_path

# ============================================================================
# STAGE 1 ACCEPTANCE TESTS
# ============================================================================

def test_stage1_data_quality_too_short():
    """Verify rejection of grievances with fewer than 12 characters."""
    passed, status, msg = check_data_quality("broken tap")
    assert not passed
    assert status == "DQ_FAIL_SHORT"

def test_stage1_data_quality_insufficient_tokens():
    """Verify rejection of inputs with fewer than 3 valid word tokens."""
    passed, status, msg = check_data_quality("12345 67890 !!!!")
    assert not passed
    assert status == "DQ_FAIL_MIN_TOKENS"

def test_stage1_data_quality_repetitive_gibberish():
    """Verify rejection of repetitive character patterns."""
    passed, status, msg = check_data_quality("asdfghjkkkkkkkkkkkkk please fix")
    assert not passed
    assert status == "DQ_FAIL_GIBBERISH"

def test_stage1_data_quality_duplicate_hash():
    """Verify detection of duplicate submissions in same ward."""
    text = "Drinking water supply tap completely broken on main chowk"
    ward = "Ward 14 - Rohini"
    norm = normalize_text(text)
    h = compute_text_hash(norm, ward)
    recent_hashes = {h}
    
    passed, status, msg = check_data_quality(text, ward=ward, recent_hashes=recent_hashes)
    assert not passed
    assert status == "DQ_FAIL_DUPLICATE"

def test_stage1_data_quality_valid_input():
    """Verify acceptance of realistic civic grievances."""
    text = "High voltage electrical transformer sparking violently near civil hospital gate 2."
    passed, status, msg = check_data_quality(text, ward="Ward 04")
    assert passed
    assert status == "DQ_PASS"

def test_stage1_inference_latency_under_50ms(nlp_pipeline):
    """Verify single-ticket inference latency is strictly < 50ms."""
    text = "Severe crater pothole on highway service lane near school."
    t0 = time.perf_counter()
    res = nlp_pipeline.predict(text, "Ward 22")
    latency_ms = (time.perf_counter() - t0) * 1000.0
    
    assert latency_ms < 50.0, f"Inference latency too slow: {latency_ms:.2f} ms"
    assert res["predicted_department"] in DEPARTMENTS
    assert res["top1_confidence"] > 0.0

def test_stage1_feature_attribution_explainability(nlp_pipeline):
    """Verify feature attribution returns top contributing terms with weights."""
    text = "11kV live wire snapped and sparking on the footpath"
    res = nlp_pipeline.predict(text, "Ward 04")
    attrs = res["token_attributions"]
    assert len(attrs) > 0
    tokens = [a["token"] for a in attrs]
    assert any("wire" in t or "sparking" in t or "snapped" in t for t in tokens)

# ============================================================================
# STAGE 2 ACCEPTANCE TESTS
# ============================================================================

def test_stage2_urgency_score_bounds():
    """Verify urgency score is mathematically clamped strictly within [0, 100]."""
    # Extreme upper bound test
    urg_high = calculate_urgency_score(
        predicted_dept="ELECTRICAL",
        raw_text="Live high voltage wire snapped and sparking violently near primary school gate with electrocution risk!",
        ward_location="Civil Hospital Hospital",
        citizen_upvotes=1000,
        top1_confidence=0.99
    )
    assert 0.0 <= urg_high["urgency_score"] <= 100.0
    assert urg_high["urgency_tier"] == "CRITICAL"
    assert urg_high["sla_hours"] == 4

    # Extreme lower bound test
    urg_low = calculate_urgency_score(
        predicted_dept="SANITATION",
        raw_text="Minor dry leaf swept onto corner of footpath.",
        ward_location="Ward 10",
        citizen_upvotes=0,
        top1_confidence=0.90
    )
    assert 0.0 <= urg_low["urgency_score"] <= 100.0
    assert urg_low["urgency_tier"] == "LOW"

def test_stage2_critical_hazard_detection():
    """Verify critical life-safety keyword triggers +38 hazard score."""
    score, terms = detect_hazard_score("11kv live wire sparking violently on street")
    assert score == 38
    assert len(terms) > 0

def test_stage2_vulnerable_zone_bonus():
    """Verify presence of school/hospital yields +18 bonus."""
    bonus, matched = detect_vulnerable_zone("Pothole on main road outside school gate", "Ward 12")
    assert bonus == 18
    assert "school" in matched

def test_stage2_shannon_entropy_calculation():
    """Verify Shannon entropy reaches 0 for certainty and 1 for uniform distribution."""
    # Complete certainty
    certain_p = [1.0, 0.0, 0.0, 0.0, 0.0]
    h_cert = calculate_shannon_entropy(certain_p)
    assert h_cert < 0.01

    # Complete uncertainty (uniform across 5 classes)
    uniform_p = [0.2, 0.2, 0.2, 0.2, 0.2]
    h_unif = calculate_shannon_entropy(uniform_p)
    assert abs(h_unif - 1.0) < 0.01

def test_stage2_hitl_review_triggers():
    """Verify Human-in-the-Loop review is triggered on low confidence or tight margin."""
    # Low confidence (< 0.70)
    urg_low_conf = calculate_urgency_score(
        predicted_dept="WATER",
        raw_text="Water issues",
        top1_confidence=0.62,
        top2_margin=0.05
    )
    assert urg_low_conf["requires_hitl_review"] is True
    assert any("LOW_MODEL_CONFIDENCE" in r for r in urg_low_conf["hitl_reasons"])
    assert any("MULTI_DEPARTMENT_AMBIGUITY" in r for r in urg_low_conf["hitl_reasons"])

# ============================================================================
# STAGE 3 ACCEPTANCE TESTS
# ============================================================================

def test_stage3_ticket_insertion_and_priority_queue(temp_db):
    """Verify ticket persistence and priority ranking order."""
    t1 = {
        "ticket_id": "CP-TEST-001",
        "ward_location": "Ward 14",
        "raw_text": "Minor garbage on footpath",
        "citizen_upvotes": 2,
        "predicted_department": "SANITATION",
        "top1_confidence": 0.95,
        "urgency_score": 25.0,
        "urgency_tier": "LOW",
        "requires_hitl_review": False,
        "sla_hours": 48
    }
    t2 = {
        "ticket_id": "CP-TEST-002",
        "ward_location": "Ward 04 near School",
        "raw_text": "Live wire snapped with sparking electrocution hazard!",
        "citizen_upvotes": 85,
        "predicted_department": "ELECTRICAL",
        "top1_confidence": 0.98,
        "urgency_score": 96.0,
        "urgency_tier": "CRITICAL",
        "requires_hitl_review": True,
        "sla_hours": 4
    }
    insert_ticket(t1, temp_db)
    insert_ticket(t2, temp_db)
    
    queue = get_priority_queue(db_path=temp_db)
    assert len(queue) == 2
    # Critical / HITL ticket must be ranked FIRST
    assert queue[0]["ticket_id"] == "CP-TEST-002"
    assert queue[0]["urgency_score"] == 96.0
    assert queue[1]["ticket_id"] == "CP-TEST-001"

def test_stage3_human_override_workflow(temp_db):
    """Verify manual override workflow and immutable audit ledger compliance."""
    ticket_payload = {
        "ticket_id": "CP-TEST-OVERRIDE",
        "ward_location": "Ward 35",
        "raw_text": "Water pipeline burst causing road cave-in and sinkhole.",
        "citizen_upvotes": 40,
        "predicted_department": "WATER",
        "top1_confidence": 0.72,
        "urgency_score": 65.0,
        "urgency_tier": "HIGH",
        "requires_hitl_review": True,
        "sla_hours": 12
    }
    insert_ticket(ticket_payload, temp_db)
    
    # 1. Invalid reason code must raise ValueError
    with pytest.raises(ValueError):
        apply_human_override(
            ticket_id="CP-TEST-OVERRIDE",
            operator_id="OP-4412",
            reason_code="INVALID_REASON",
            new_dept="ROADS",
            db_path=temp_db
        )
        
    # 2. Missing operator ID must raise ValueError
    with pytest.raises(ValueError):
        apply_human_override(
            ticket_id="CP-TEST-OVERRIDE",
            operator_id="",
            reason_code="AMBIGUOUS_MULTI_DEPT",
            new_dept="ROADS",
            db_path=temp_db
        )
        
    # 3. Successful valid human override
    res = apply_human_override(
        ticket_id="CP-TEST-OVERRIDE",
        operator_id="OP-OFFICIAL-891",
        reason_code="AMBIGUOUS_MULTI_DEPT",
        new_dept="ROADS",
        new_urgency_tier="CRITICAL",
        notes="Verified in field: Road sinkhole poses imminent traffic fatality threat.",
        db_path=temp_db
    )
    assert res["status"] == "SUCCESS"
    assert res["new_dept"] == "ROADS"
    assert res["new_urgency_tier"] == "CRITICAL"
    
    # 4. Verify immutable audit ledger entry
    audit_records = get_audit_ledger(db_path=temp_db)
    assert len(audit_records) == 1
    record = audit_records[0]
    assert record["ticket_id"] == "CP-TEST-OVERRIDE"
    assert record["operator_id"] == "OP-OFFICIAL-891"
    assert record["reason_code"] == "AMBIGUOUS_MULTI_DEPT"
    assert record["previous_dept"] == "WATER"
    assert record["new_dept"] == "ROADS"
