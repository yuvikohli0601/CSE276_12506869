"""
Stage 2: Deterministic Rule-Based Urgency Engine & Human-in-the-Loop Gate
Course: CSE276 | Problem Statement: SIH25031
Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)

Implements:
1. Deterministic additive urgency scoring function U in [0, 100].
2. Critical life-safety keyword detection & department baseline weights.
3. Vulnerable civic zone proximity bonus (schools, hospitals, transit).
4. Citizen viral upvote scaling: min(10, 2 * log2(1 + upvotes)).
5. Confidence calibration scaling factor phi(C).
6. Multi-criteria Human-in-the-Loop (HITL) review gate.
7. Statutory SLA deadline calculation.
"""

import math
from typing import Dict, List, Tuple, Any

# Base Municipal Department Weights (W_dept)
DEPT_WEIGHTS = {
    "ELECTRICAL": 30,  # Immediate electrocution / fire hazard potential
    "WATER": 25,       # Potable contamination / critical infrastructure stoppage
    "HEALTH": 25,      # Vector epidemic / pathogen transmission risk
    "ROADS": 20,       # Vehicular accidents / severe transit bottlenecks
    "SANITATION": 18   # Environmental hygiene / municipal solid waste backlog
}

# Critical Life-Safety Hazard Rules (S_hazard)
CRITICAL_HAZARDS = [
    # Tier 1 (+38 points: Imminent fatality / catastrophe hazard)
    (["live wire", "snapped wire", "electric wire snapped", "11kv", "bare copper", "electrocution", "sparking violently"], 38),
    (["open manhole", "manhole cover missing", "uncovered manhole"], 38),
    (["sewage mixed in drinking", "sewage pipeline leaking directly into drinking", "toxic chemical discharge", "gas leak"], 38),
    (["transformer blast", "explosive popping sounds", "transformer smoke"], 38),
    
    # Tier 2 (+20 points: Severe public health & structural failure)
    (["road cave-in", "massive sinkhole", "sinkhole formed"], 20),
    (["dengue", "dengue mosquito", "mosquito larvae", "chikungunya", "rabies", "dog bite incident", "pack of 8-10 stray dogs"], 20),
    (["underpass severely waterlogged", "underpass submerged", "3 feet of water"], 20),
    (["dead animal carcass", "biomedical waste", "medical waste dumped"], 20),
    (["overflowing open nallah", "sludge overflowing"], 20),
    
    # Tier 3 (+10 points: Significant civic hindrance)
    (["crater-sized pothole", "flying gravel", "sunken road slab", "deep ruts"], 10),
    (["potable drinking water pipeline burst", "main water distribution pipe cracked"], 10),
    (["voltage surges up to 320v", "all streetlights completely dysfunctional"], 10),
    (["overflowing garbage dump", "dhalao", "dhalao spilling"], 10)
]

# Vulnerable Infrastructure Proximity Keywords (V_zone)
VULNERABLE_ZONE_TERMS = [
    "school", "hospital", "clinic", "dispensary", "college", "anganwadi",
    "highway", "railway", "nursing home", "kindergarten", "pediatric",
    "metro station", "bus stop", "blind school", "elderly"
]

# Statutory SLA Response Timers (Hours)
SLA_HOURS_MAP = {
    "CRITICAL": 4,   # Immediate emergency dispatch
    "HIGH": 12,      # Same-day resolution
    "MEDIUM": 24,    # Next-day action
    "LOW": 48        # Standard municipal queue
}

def detect_hazard_score(text: str) -> Tuple[int, List[str]]:
    """Scans text for life-safety hazard triggers, returning max score and matched terms."""
    text_lower = text.lower()
    highest_score = 0
    detected_terms = []
    
    for keywords, score in CRITICAL_HAZARDS:
        for kw in keywords:
            if kw in text_lower:
                detected_terms.append(kw)
                if score > highest_score:
                    highest_score = score
                    
    return highest_score, list(set(detected_terms))

def detect_vulnerable_zone(text: str, ward_location: str = "") -> Tuple[int, List[str]]:
    """Detects proximity to high-vulnerability infrastructure (+18 points)."""
    combined = f"{text.lower()} {ward_location.lower()}"
    matched_zones = [z for z in VULNERABLE_ZONE_TERMS if z in combined]
    
    if matched_zones:
        return 18, list(set(matched_zones))
    return 0, []

def compute_upvote_bonus(upvotes: int) -> float:
    """
    Logarithmic viral citizen engagement factor:
    bonus = min(10.0, 2.0 * log2(1 + upvotes))
    """
    safe_upvotes = max(0, int(upvotes))
    bonus = 2.0 * math.log2(1.0 + safe_upvotes)
    return float(min(10.0, round(bonus, 2)))

def calculate_urgency_score(
    predicted_dept: str,
    raw_text: str,
    ward_location: str = "",
    citizen_upvotes: int = 0,
    top1_confidence: float = 1.0,
    top2_margin: float = 0.5,
    shannon_entropy: float = 0.0,
    dq_status: str = "DQ_PASS"
) -> Dict[str, Any]:
    """
    Stage 2 Deterministic Additive Urgency Formula:
    U = clip( (W_dept + S_hazard + V_zone + min(10, 2 * log2(1 + upvotes))) * phi(C), 0, 100 )
    
    Plus Multi-Condition Human-in-the-Loop Collaboration Gate.
    """
    # 1. Base Department Weight
    w_dept = DEPT_WEIGHTS.get(predicted_dept.upper(), 20)
    
    # 2. Hazard Keywords
    s_hazard, matched_hazards = detect_hazard_score(raw_text)
    
    # 3. Vulnerable Zone Bonus
    v_zone, matched_zones = detect_vulnerable_zone(raw_text, ward_location)
    
    # 4. Citizen Upvote Bonus
    upvote_bonus = compute_upvote_bonus(citizen_upvotes)
    
    # 5. Confidence Calibration Factor phi(C)
    if top1_confidence >= 0.70:
        phi_c = 1.0
    else:
        # Confidence penalty scaling factor
        phi_c = max(0.50, round(top1_confidence / 0.70, 3))
        
    # Raw Additive Sum
    raw_sum = (w_dept + s_hazard + v_zone + upvote_bonus) * phi_c
    urgency_score = float(max(0.0, min(100.0, round(raw_sum, 1))))
    
    # Urgency Tier
    if urgency_score >= 75.0:
        tier = "CRITICAL"
    elif urgency_score >= 55.0:
        tier = "HIGH"
    elif urgency_score >= 35.0:
        tier = "MEDIUM"
    else:
        tier = "LOW"
        
    sla_hours = SLA_HOURS_MAP[tier]
    
    # 6. Human-AI Collaboration Gate (HITL Verification)
    requires_hitl = False
    hitl_reasons = []
    
    # Condition A: Low Confidence
    if top1_confidence < 0.70:
        requires_hitl = True
        hitl_reasons.append(f"LOW_MODEL_CONFIDENCE (Confidence: {top1_confidence*100:.1f}% < 70.0%)")
        
    # Condition B: Multi-Department Ambiguity (Tight Top-2 Margin)
    if top2_margin < 0.15:
        requires_hitl = True
        hitl_reasons.append(f"MULTI_DEPARTMENT_AMBIGUITY (Top-2 Margin: {top2_margin*100:.1f}% < 15.0%)")
        
    # Condition C: Data Quality Failure
    if dq_status != "DQ_PASS":
        requires_hitl = True
        hitl_reasons.append(f"DATA_QUALITY_GATE_FAILED ({dq_status})")
        
    # Condition D: High Hazard Conflict (High life hazard detected but low confidence)
    if s_hazard >= 35 and top1_confidence < 0.75:
        requires_hitl = True
        hitl_reasons.append(f"HIGH_HAZARD_UNCERTAIN_ROUTING (Hazard: +{s_hazard} with Confidence < 75%)")
        
    # Condition E: High Shannon Entropy
    if shannon_entropy >= 0.65:
        requires_hitl = True
        hitl_reasons.append(f"HIGH_CLASSIFICATION_ENTROPY (Entropy: {shannon_entropy:.2f} >= 0.65)")
        
    return {
        "urgency_score": urgency_score,
        "urgency_tier": tier,
        "sla_hours": sla_hours,
        "base_dept_weight": w_dept,
        "hazard_score": s_hazard,
        "hazard_triggers": matched_hazards,
        "zone_bonus": v_zone,
        "zone_triggers": matched_zones,
        "upvote_bonus": upvote_bonus,
        "confidence_calibration_factor": phi_c,
        "requires_hitl_review": requires_hitl,
        "hitl_reasons": hitl_reasons
    }
