"""
CivicPulse - FastAPI Production Server
Course: CSE276 | Problem Statement: SIH25031
Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)

Exposes REST APIs for:
- Stage 1: Calibrated NLP inference, feature attribution & data quality gating
- Stage 2: Rule-based urgency scoring, confidence calibration & HITL review
- Stage 3: Priority dispatch queue, SQLite persistence & immutable human audit ledger
- Model telemetry, confusion matrices & static frontend delivery
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure codebase root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
codebase_dir = os.path.abspath(os.path.join(current_dir, ".."))
if codebase_dir not in sys.path:
    sys.path.insert(0, codebase_dir)

from backend.nlp_stage1 import CivicNLPPipeline, DEPARTMENTS
from backend.urgency_stage2 import calculate_urgency_score
from backend.database_stage3 import (
    init_database,
    insert_ticket,
    get_ticket_by_id,
    apply_human_override,
    get_priority_queue,
    get_audit_ledger,
    seed_database_from_csv,
    VALID_REASON_CODES
)

# Initialize FastAPI App
app = FastAPI(
    title="CivicPulse - AI Municipal Routing Command API",
    description="Smart India Hackathon SIH25031 | CSE276 Production Backend",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Paths
MODEL_ARTIFACT_PATH = os.path.join(codebase_dir, "ml", "artifacts", "civic_classifier.joblib")
METRICS_JSON_PATH = os.path.join(codebase_dir, "ml", "artifacts", "metrics.json")
DB_PATH = os.path.join(current_dir, "civicpulse.db")
FRONTEND_DIR = os.path.join(codebase_dir, "frontend")
CSV_PATH = os.path.join(codebase_dir, "data", "civic_complaints_india.csv")

# Initialize SQLite & Seed Data
init_database(DB_PATH)
if os.path.exists(CSV_PATH):
    try:
        seed_database_from_csv(CSV_PATH, DB_PATH, limit=30)
    except Exception as e:
        print(f"[WARN] Database seeding notice: {e}")

# Load ML Pipeline
nlp_pipeline = CivicNLPPipeline(MODEL_ARTIFACT_PATH if os.path.exists(MODEL_ARTIFACT_PATH) else None)

# --- Pydantic Request / Response Schemas ---
class PredictRequest(BaseModel):
    raw_text: str = Field(..., min_length=3, description="Citizen complaint narrative text")
    ward_location: str = Field(default="Ward 14 - Municipal Zone", description="Municipal Ward and landmark")
    citizen_upvotes: int = Field(default=0, ge=0, description="Community upvote count")

class TicketCreateRequest(PredictRequest):
    ticket_id: Optional[str] = Field(default=None, description="Optional custom ticket ID")

class OverrideRequest(BaseModel):
    operator_id: str = Field(..., min_length=2, description="Authenticated Operator Badge / ID")
    reason_code: str = Field(..., description="Mandatory governance reason code")
    new_dept: Optional[str] = Field(default=None, description="Corrected target department")
    new_urgency_tier: Optional[str] = Field(default=None, description="Corrected urgency tier (CRITICAL, HIGH, MEDIUM, LOW)")
    notes: Optional[str] = Field(default="", description="Operator diagnostic justification notes")

# --- API Endpoints ---

@app.get("/api/health")
def healthcheck():
    """System health telemetry and engine status."""
    return {
        "status": "HEALTHY",
        "service": "CivicPulse AI Municipal Command Engine",
        "version": "2.0.0",
        "author": "Yuvi Kohli (12506869 / RK3P25ILB43 / K3P25IL)",
        "model_loaded": nlp_pipeline.model is not None,
        "database_connected": os.path.exists(DB_PATH),
        "supported_departments": DEPARTMENTS,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/predict")
def predict_complaint(payload: PredictRequest):
    """
    Executes Stage 1 NLP and Stage 2 Urgency Engine on input text without DB persistence.
    Used for live interactive classification testing in the UI.
    Duplicate checks and hash registration are disabled for real-time live typing.
    """
    # Stage 1: NLP (preview mode: no duplicate blocking, no hash registration)
    nlp_res = nlp_pipeline.predict(
        raw_text=payload.raw_text,
        ward_location=payload.ward_location,
        check_duplicate=False,
        register_hash=False
    )
    
    # Stage 2: Urgency Engine
    urgency_res = calculate_urgency_score(
        predicted_dept=nlp_res["predicted_department"],
        raw_text=payload.raw_text,
        ward_location=payload.ward_location,
        citizen_upvotes=payload.citizen_upvotes,
        top1_confidence=nlp_res["top1_confidence"],
        top2_margin=nlp_res["top2_margin"],
        shannon_entropy=nlp_res["shannon_entropy"],
        dq_status=nlp_res["data_quality_status"]
    )
    
    return {
        "stage1_nlp": nlp_res,
        "stage2_urgency": urgency_res,
        "input_echo": {
            "raw_text": payload.raw_text,
            "ward_location": payload.ward_location,
            "citizen_upvotes": payload.citizen_upvotes
        }
    }

@app.post("/api/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreateRequest):
    """
    End-to-End Pipeline Ingestion:
    Executes Stage 1 + Stage 2, assigns priority ranking, and persists into SQLite queue.
    Formally enforces duplicate submission prevention and registers complaint hash.
    """
    nlp_res = nlp_pipeline.predict(
        raw_text=payload.raw_text,
        ward_location=payload.ward_location,
        check_duplicate=True,
        register_hash=True
    )
    urgency_res = calculate_urgency_score(
        predicted_dept=nlp_res["predicted_department"],
        raw_text=payload.raw_text,
        ward_location=payload.ward_location,
        citizen_upvotes=payload.citizen_upvotes,
        top1_confidence=nlp_res["top1_confidence"],
        top2_margin=nlp_res["top2_margin"],
        shannon_entropy=nlp_res["shannon_entropy"],
        dq_status=nlp_res["data_quality_status"]
    )
    
    combined = {
        "ticket_id": payload.ticket_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ward_location": payload.ward_location,
        "raw_text": payload.raw_text,
        "citizen_upvotes": payload.citizen_upvotes,
        "predicted_department": nlp_res["predicted_department"],
        "top1_confidence": nlp_res["top1_confidence"],
        "top2_margin": nlp_res["top2_margin"],
        "shannon_entropy": nlp_res["shannon_entropy"],
        "urgency_score": urgency_res["urgency_score"],
        "urgency_tier": urgency_res["urgency_tier"],
        "hazard_score": urgency_res["hazard_score"],
        "zone_bonus": urgency_res["zone_bonus"],
        "requires_hitl_review": urgency_res["requires_hitl_review"],
        "hitl_reasons": urgency_res["hitl_reasons"],
        "sla_hours": urgency_res["sla_hours"]
    }
    
    assigned_id = insert_ticket(combined, DB_PATH)
    combined["ticket_id"] = assigned_id
    combined["status"] = "PENDING_REVIEW" if urgency_res["requires_hitl_review"] else "DISPATCHED"
    combined["token_attributions"] = nlp_res["token_attributions"]
    
    return combined

@app.get("/api/tickets")
def list_tickets(
    dept: Optional[str] = Query(default=None, description="Department filter"),
    tier: Optional[str] = Query(default=None, description="Urgency tier filter"),
    hitl_only: bool = Query(default=False, description="Filter only tickets requiring human review"),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Retrieves ranked active queue from Priority Dispatch Agent."""
    tickets = get_priority_queue(
        dept_filter=dept,
        tier_filter=tier,
        hitl_only=hitl_only,
        limit=limit,
        db_path=DB_PATH
    )
    return {"total": len(tickets), "tickets": tickets}

@app.get("/api/tickets/{ticket_id}")
def fetch_single_ticket(ticket_id: str):
    """Retrieves a single complaint record by ticket_id for citizen tracking."""
    record = get_ticket_by_id(ticket_id, db_path=DB_PATH)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Ticket '{ticket_id}' not found in municipal grievance database."
        )
    return record

@app.post("/api/tickets/{ticket_id}/override")
def override_ticket(ticket_id: str, payload: OverrideRequest):
    """
    Stage 3 Human-in-the-Loop Override Workflow:
    Updates ticket routing and logs an immutable record into audit_ledger.
    """
    if payload.reason_code not in VALID_REASON_CODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reason_code '{payload.reason_code}'. Must be one of: {VALID_REASON_CODES}"
        )
        
    try:
        result = apply_human_override(
            ticket_id=ticket_id,
            operator_id=payload.operator_id,
            reason_code=payload.reason_code,
            new_dept=payload.new_dept,
            new_urgency_tier=payload.new_urgency_tier,
            notes=payload.notes or "",
            db_path=DB_PATH
        )
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/audit-log")
def fetch_audit_log(limit: int = Query(default=50, ge=1, le=200)):
    """Retrieves chronological entries from the immutable human audit ledger."""
    records = get_audit_ledger(limit=limit, db_path=DB_PATH)
    return {"total": len(records), "audit_trail": records}

@app.get("/api/metrics")
def get_model_metrics():
    """Serves model comparison tables, confusion matrix, and accuracy reports."""
    if os.path.exists(METRICS_JSON_PATH):
        with open(METRICS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "status": "Artifacts not compiled yet. Run train_models.py to build metrics."
    }

# Mount static frontend directory and direct root routes
STATIC_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend_root():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file, headers=STATIC_HEADERS)
        return {"message": "Frontend index.html not found"}

    @app.get("/citizen")
    @app.get("/report")
    @app.get("/citizen/")
    @app.get("/report/")
    def serve_citizen_portal():
        citizen_file = os.path.join(FRONTEND_DIR, "citizen.html")
        if os.path.exists(citizen_file):
            return FileResponse(citizen_file, headers=STATIC_HEADERS)
        # Fallback to index.html if citizen.html not present
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), headers=STATIC_HEADERS)

    @app.get("/styles.css")
    @app.get("/citizen/styles.css")
    @app.get("/report/styles.css")
    def serve_root_css():
        css_file = os.path.join(FRONTEND_DIR, "styles.css")
        if os.path.exists(css_file):
            return FileResponse(css_file, media_type="text/css", headers=STATIC_HEADERS)
        raise HTTPException(status_code=404, detail="styles.css not found")

    @app.get("/app.js")
    @app.get("/citizen/app.js")
    @app.get("/report/app.js")
    def serve_root_js():
        js_file = os.path.join(FRONTEND_DIR, "app.js")
        if os.path.exists(js_file):
            return FileResponse(js_file, media_type="application/javascript", headers=STATIC_HEADERS)
        raise HTTPException(status_code=404, detail="app.js not found")

if __name__ == "__main__":
    import uvicorn
    default_port = 7860 if os.environ.get("SPACE_ID") else 8000
    port = int(os.environ.get("PORT", default_port))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting CivicPulse Server on http://{host}:{port} ...")
    uvicorn.run(app, host=host, port=port)
