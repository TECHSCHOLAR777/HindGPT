# backend/main.py
import os
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Core product imports
from core.commitment_extractor import get_promise_progress
from core.risk_score import calculate_risk_score
from core.after_action import generate_after_action_report
from core.already_built import detect_already_built
from core.new_joiner import query_joiner_intelligence, get_performance_pulse
from core.expert_finder import find_experts
from core.knowledge_preservation import (
    generate_knowledge_transfer_report,
    detect_succession_gaps,
    mark_person_departed,
    query_shadow_persona,
    how_did_person_think
)
from core.hindsight_client import seed_rahuls_history

# Ingest imports
from ingest.github import handle_pr_event
from ingest.gmail import ingest_gmail_thread
from ingest.notion import ingest_notion_page
from ingest.zoom import ingest_zoom_meeting
from ingest.calendar import ingest_calendar_event

app = FastAPI(title="HindGPT Backend", version="1.0.0")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Event
@app.on_event("startup")
def startup_event():
    # Seed Rahul's decision history (5 decisions, 3 domains)
    seed_rahuls_history()

# Request Models
class GmailIngestRequest(BaseModel):
    thread_id: str

class NotionIngestRequest(BaseModel):
    page_id: str

class ZoomIngestRequest(BaseModel):
    meeting_title: str
    transcript_text: str
    host: str = "unknown"

class CalendarIngestRequest(BaseModel):
    event_title: str
    description: str
    attendees: str
    date_str: str

class DepartRequest(BaseModel):
    name: str

@app.get("/")
def read_root():
    return {"message": "Welcome to HindGPT B2B Decision Tracking & Commitment Verification API"}

# --- 1. Promise-to-Progress ---
@app.get("/api/v1/promise-progress")
def api_promise_progress(customer: str = "Acme Corp"):
    try:
        return get_promise_progress(customer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. Commitment Risk Score ---
@app.get("/api/v1/risk-score")
def api_risk_score(customer: str = "Acme Corp"):
    try:
        return calculate_risk_score(customer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. Auto After-Action Reports ---
@app.get("/api/v1/after-action-report")
def api_after_action_report(feature_name: str = "SSO integration"):
    try:
        return generate_after_action_report(feature_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 4. Already Built Detection ---
@app.get("/api/v1/already-built")
def api_already_built(feature_query: str = "SSO SAML"):
    try:
        return detect_already_built(feature_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 5. New Joiner Intelligence & Pulse ---
@app.get("/api/v1/new-joiner/query")
def api_new_joiner_query(query: str, x_user_role: str = Header(default="engineering")):
    try:
        return query_joiner_intelligence(query, role=x_user_role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/new-joiner/pulse")
def api_performance_pulse():
    try:
        return get_performance_pulse()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 6. Expert Finder ---
@app.get("/api/v1/expert-finder")
def api_expert_finder(topic: str):
    try:
        return find_experts(topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 7. Institutional Knowledge Preservation ---
@app.get("/api/v1/knowledge/transfer")
def api_knowledge_transfer(author: str):
    try:
        return generate_knowledge_transfer_report(author)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/knowledge/succession-gaps")
def api_succession_gaps():
    try:
        return detect_succession_gaps()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/knowledge/depart")
def api_depart_person(payload: DepartRequest):
    try:
        return mark_person_departed(payload.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/knowledge/shadow")
def api_shadow_query(author: str, query: str):
    try:
        return query_shadow_persona(author, query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/knowledge/how-did-think")
def api_how_did_think(author: str, topic: str):
    try:
        return how_did_person_think(author, topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Ingestion Endpoints ---
@app.post("/api/v1/ingest/github")
def webhook_github(payload: dict, background_tasks: BackgroundTasks):
    background_tasks.add_task(handle_pr_event, payload)
    return {"status": "enqueued", "source": "github"}

@app.post("/api/v1/ingest/gmail")
def trigger_gmail_ingest(payload: GmailIngestRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_gmail_thread, payload.thread_id)
    return {"status": "enqueued", "source": "gmail"}

@app.post("/api/v1/ingest/notion")
def trigger_notion_ingest(payload: NotionIngestRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_notion_page, payload.page_id)
    return {"status": "enqueued", "source": "notion"}

@app.post("/api/v1/ingest/zoom")
def trigger_zoom_ingest(payload: ZoomIngestRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_zoom_meeting, payload.meeting_title, payload.transcript_text, payload.host)
    return {"status": "enqueued", "source": "zoom"}

@app.post("/api/v1/ingest/calendar")
def trigger_calendar_ingest(payload: CalendarIngestRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_calendar_event, payload.event_title, payload.description, payload.attendees, payload.date_str)
    return {"status": "enqueued", "source": "calendar"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)