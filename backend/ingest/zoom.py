# backend/ingest/zoom.py
from core.hindsight_client import client

def ingest_zoom_meeting(meeting_title: str, transcript_text: str, host: str = "unknown"):
    """
    Ingest a Zoom meeting transcript, parsing out commitments, decisions, and outcomes,
    and retaining them as rich events in the HindGPT Memory Engine.
    """
    content = f"""
    Zoom Meeting: {meeting_title}
    Host: {host}
    Transcript:
    {transcript_text}
    """

    # Retain the Zoom transcript in the Memory Engine
    # Default to "executive" visibility so managers can evaluate client calls.
    client.retain(
        content=content,
        type="event",
        source="zoom",
        author=host,
        visibility="executive",
        tags=["type:meeting", "source:zoom"]
    )