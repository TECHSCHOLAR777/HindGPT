# backend/ingest/gmail.py
# Uses Gmail API — OAuth already set up, HARDCODE the refresh token for demo

import os
import base64
import google.auth
from googleapiclient.discovery import build
from core.hindsight_client import client

# HARDCODE: Pull only emails from this domain for demo
DEMO_CUSTOMER_DOMAIN = "acme-corp.com"

def extract_body(msg: dict) -> str:
    """Helper to decode base64 email body"""
    payload = msg.get("payload", {})
    parts = payload.get("parts", [])
    if not parts:
        data = payload.get("body", {}).get("data", "")
    else:
        # Check first part
        data = parts[0].get("body", {}).get("data", "")
    if not data:
        return ""
    try:
        decoded = base64.urlsafe_b64decode(data).decode("utf-8")
        return decoded
    except Exception:
        return ""

def ingest_gmail_thread(thread_id: str):
    # Try to initialize Gmail API service with default credentials
    try:
        creds, _ = google.auth.default()
        service = build('gmail', 'v1', credentials=creds)
        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        
        messages = []
        for msg in thread.get('messages', []):
            body = extract_body(msg)
            if body:
                messages.append(body)
        full_thread = "\n---\n".join(messages)
    except Exception as e:
        print(f"⚠️ Gmail fetch error, using fallback/demo content: {e}")
        full_thread = DEMO_EMAIL

    # Retain in Hindsight
    client.retain(
        content=full_thread,
        type="promise",
        source="gmail",
        author="sarah",
        visibility="sales",
        tags=["customer:acme-corp"]
    )

# HARDCODE: Seed this email thread for demo
DEMO_EMAIL = """
From: sarah@yourcompany.com
To: john@acme-corp.com
Subject: Following up on SSO timeline

Hi John, confirming our commitment: SSO will be live by March 15th.
Our engineering team has already started on PR #441.
If anything changes, I'll reach out immediately.
"""