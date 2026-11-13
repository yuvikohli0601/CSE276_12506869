"""
Stage 3: SQLite Database Schema, Priority Dispatch Agent & Immutable Audit Ledger
Course: CSE276 | Problem Statement: SIH25031
Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)

Implements:
1. SQLite database initialization (complaints queue & immutable audit_ledger).
2. Priority-Based Agent ranking algorithm (Safety escalations, urgency score, SLA aging).
3. Human-in-the-Loop manual override with Operator ID and mandatory reason code validation.
4. Pre-population of seed grievances from generated CSV.
"""

import os
import sys
import sqlite3
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
codebase_dir = os.path.abspath(os.path.join(current_dir, ".."))
if codebase_dir not in sys.path:
    sys.path.insert(0, codebase_dir)

DB_FILE = "civicpulse.db"

VALID_REASON_CODES = [
    "AMBIGUOUS_MULTI_DEPT",
    "FALSE_POSITIVE_HAZARD",
    "FIELD_VERIFIED_ESCALATION",
    "OOV_REGIONAL_TERM"
]

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns an active SQLite database connection with row factory enabled."""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILE)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_database(db_path: Optional[str] = None):
    """Creates SQLite schema for priority tickets and immutable audit trail."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # 1. Complaints Dispatch Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        ward_location TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        citizen_upvotes INTEGER DEFAULT 0,
        predicted_dept TEXT NOT NULL,
        effective_dept TEXT NOT NULL,
        confidence REAL NOT NULL,
        top2_margin REAL NOT NULL,
        entropy REAL NOT NULL,
        urgency_score REAL NOT NULL,
        effective_urgency_tier TEXT NOT NULL,
        hazard_score INTEGER DEFAULT 0,
        zone_bonus INTEGER DEFAULT 0,
        requires_hitl INTEGER DEFAULT 0,
        hitl_reason TEXT DEFAULT '',
        status TEXT DEFAULT 'DISPATCHED',
        sla_deadline_hours INTEGER DEFAULT 24,
        created_at TEXT NOT NULL
    );
    """)
    
    # 2. Immutable Audit Ledger Table (Human-AI Collaboration Governance)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        operator_id TEXT NOT NULL,
        reason_code TEXT NOT NULL,
        previous_dept TEXT NOT NULL,
        new_dept TEXT NOT NULL,
        previous_urgency_tier TEXT NOT NULL,
        new_urgency_tier TEXT NOT NULL,
        notes TEXT DEFAULT '',
        FOREIGN KEY (ticket_id) REFERENCES complaints (ticket_id)
    );
    """)
    
    # Indexes for high-throughput query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_id ON complaints(ticket_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_urgency ON complaints(urgency_score DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hitl ON complaints(requires_hitl DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dept ON complaints(effective_dept);")
    
    conn.commit()
    conn.close()

def insert_ticket(ticket_data: Dict[str, Any], db_path: Optional[str] = None) -> str:
    """Inserts a newly classified ticket into the active queue."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    ticket_id = ticket_data.get("ticket_id")
    if not ticket_id:
        now_str = datetime.now().strftime("%Y%m%d%H%M%S")
        ticket_id = f"CP-TKT-{now_str}-{cursor.execute('SELECT COUNT(*) FROM complaints').fetchone()[0] + 1:03d}"
        
    created_at = datetime.now().isoformat()
    status = "PENDING_REVIEW" if ticket_data.get("requires_hitl_review") else "DISPATCHED"
    
    cursor.execute("""
    INSERT INTO complaints (
        ticket_id, timestamp, ward_location, raw_text, citizen_upvotes,
        predicted_dept, effective_dept, confidence, top2_margin, entropy,
        urgency_score, effective_urgency_tier, hazard_score, zone_bonus,
        requires_hitl, hitl_reason, status, sla_deadline_hours, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_id,
        ticket_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ticket_data.get("ward_location", "Municipal Ward"),
        ticket_data.get("raw_text", ""),
        int(ticket_data.get("citizen_upvotes", 0)),
        ticket_data.get("predicted_department", "SANITATION"),
        ticket_data.get("predicted_department", "SANITATION"),
        float(ticket_data.get("top1_confidence", 0.0)),
        float(ticket_data.get("top2_margin", 0.0)),
        float(ticket_data.get("shannon_entropy", 0.0)),
        float(ticket_data.get("urgency_score", 0.0)),
        ticket_data.get("urgency_tier", "LOW"),
        int(ticket_data.get("hazard_score", 0)),
        int(ticket_data.get("zone_bonus", 0)),
        1 if ticket_data.get("requires_hitl_review") else 0,
        " | ".join(ticket_data.get("hitl_reasons", [])) if isinstance(ticket_data.get("hitl_reasons"), list) else str(ticket_data.get("hitl_reasons", "")),
        status,
        int(ticket_data.get("sla_hours", 24)),
        created_at
    ))
    
    conn.commit()
    conn.close()
    return ticket_id

def apply_human_override(
    ticket_id: str,
    operator_id: str,
    reason_code: str,
    new_dept: Optional[str] = None,
    new_urgency_tier: Optional[str] = None,
    notes: str = "",
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stage 3 Mandatory Human Override Workflow:
    Updates active ticket routing and writes an immutable record into audit_ledger.
    Requires validated Operator ID and sanctioned reason code.
    """
    if not operator_id or not operator_id.strip():
        raise ValueError("Operator ID is required for governance compliance.")
    if reason_code not in VALID_REASON_CODES:
        raise ValueError(f"Invalid reason code. Must be one of: {VALID_REASON_CODES}")
        
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Fetch current state
    cursor.execute("SELECT * FROM complaints WHERE ticket_id = ?", (ticket_id,))
    ticket = cursor.fetchone()
    if not ticket:
        conn.close()
        raise KeyError(f"Ticket {ticket_id} not found in complaints database.")
        
    prev_dept = ticket["effective_dept"]
    prev_tier = ticket["effective_urgency_tier"]
    
    target_dept = new_dept if new_dept else prev_dept
    target_tier = new_urgency_tier if new_urgency_tier else prev_tier
    
    # Recalculate SLA hours if tier altered
    sla_map = {"CRITICAL": 4, "HIGH": 12, "MEDIUM": 24, "LOW": 48}
    new_sla = sla_map.get(target_tier, ticket["sla_deadline_hours"])
    
    now_iso = datetime.now().isoformat()
    
    # 1. Update complaints table
    cursor.execute("""
    UPDATE complaints
    SET effective_dept = ?,
        effective_urgency_tier = ?,
        sla_deadline_hours = ?,
        status = 'OVERRIDDEN',
        requires_hitl = 0
    WHERE ticket_id = ?
    """, (target_dept, target_tier, new_sla, ticket_id))
    
    # 2. Append immutable record to audit_ledger
    cursor.execute("""
    INSERT INTO audit_ledger (
        ticket_id, timestamp, operator_id, reason_code,
        previous_dept, new_dept, previous_urgency_tier, new_urgency_tier, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_id,
        now_iso,
        operator_id.strip(),
        reason_code,
        prev_dept,
        target_dept,
        prev_tier,
        target_tier,
        notes.strip()
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "status": "SUCCESS",
        "ticket_id": ticket_id,
        "operator_id": operator_id,
        "reason_code": reason_code,
        "previous_dept": prev_dept,
        "new_dept": target_dept,
        "previous_urgency_tier": prev_tier,
        "new_urgency_tier": target_tier,
        "audit_timestamp": now_iso
    }

def get_ticket_by_id(ticket_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a single complaint record by ticket_id."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_priority_queue(
    dept_filter: Optional[str] = None,
    tier_filter: Optional[str] = None,
    hitl_only: bool = False,
    limit: int = 50,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Priority Agent Ranking Query:
    1. Safety Escalations & requires_hitl items ranked highest.
    2. Urgency Score U descending.
    3. Aging tickets (timestamp ascending) prioritized.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    query = "SELECT * FROM complaints WHERE 1=1"
    params = []
    
    if dept_filter and dept_filter != "ALL":
        query += " AND effective_dept = ?"
        params.append(dept_filter.upper())
    if tier_filter and tier_filter != "ALL":
        query += " AND effective_urgency_tier = ?"
        params.append(tier_filter.upper())
    if hitl_only:
        query += " AND requires_hitl = 1"
        
    query += " ORDER BY requires_hitl DESC, urgency_score DESC, timestamp ASC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

def get_audit_ledger(limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves chronological entries from the immutable audit ledger."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_ledger ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

def seed_database_from_csv(csv_path: str, db_path: Optional[str] = None, limit: int = 30):
    """Pre-populates the database with initial classified records from generated CSV."""
    init_database(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Check if complaints table already has data
    count = cursor.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    if count >= limit:
        conn.close()
        return count
        
    conn.close()
    
    from backend.nlp_stage1 import CivicNLPPipeline
    from backend.urgency_stage2 import calculate_urgency_score
    
    # Initialize Stage 1 model pipeline
    artifact_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml", "artifacts", "civic_classifier.joblib")
    nlp = CivicNLPPipeline(artifact_path)
    
    print(f"[SEED DB] Ingesting initial {limit} records from {csv_path}...")
    seeded_count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            # Predict Stage 1
            pred = nlp.predict(row["raw_text"], row["ward_location"])
            # Predict Stage 2
            urg = calculate_urgency_score(
                predicted_dept=pred["predicted_department"],
                raw_text=row["raw_text"],
                ward_location=row["ward_location"],
                citizen_upvotes=int(row["citizen_upvotes"]),
                top1_confidence=pred["top1_confidence"],
                top2_margin=pred["top2_margin"],
                shannon_entropy=pred["shannon_entropy"],
                dq_status=pred["data_quality_status"]
            )
            
            combined_payload = {
                "ticket_id": row["complaint_id"],
                "timestamp": row["timestamp"],
                "ward_location": row["ward_location"],
                "raw_text": row["raw_text"],
                "citizen_upvotes": int(row["citizen_upvotes"]),
                "predicted_department": pred["predicted_department"],
                "top1_confidence": pred["top1_confidence"],
                "top2_margin": pred["top2_margin"],
                "shannon_entropy": pred["shannon_entropy"],
                "urgency_score": urg["urgency_score"],
                "urgency_tier": urg["urgency_tier"],
                "hazard_score": urg["hazard_score"],
                "zone_bonus": urg["zone_bonus"],
                "requires_hitl_review": urg["requires_hitl_review"],
                "hitl_reasons": urg["hitl_reasons"],
                "sla_hours": urg["sla_hours"]
            }
            insert_ticket(combined_payload, db_path)
            seeded_count += 1
            
    print(f"[SEED DB] Successfully populated {seeded_count} records into SQLite database.")
    return seeded_count

if __name__ == "__main__":
    db_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILE)
    init_database(db_p)
    csv_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "civic_complaints_india.csv")
    if os.path.exists(csv_p):
        seed_database_from_csv(csv_p, db_p, limit=30)
