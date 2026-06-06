# backend/ingest/calendar.py
from core.hindsight_client import client

def ingest_calendar_event(event_title: str, description: str, attendees: str, date_str: str):
    """
    Ingest a Google or Outlook Calendar event, preserving metadata of who met and what
    was scheduled.
    """
    content = f"""
    Calendar Event: {event_title}
    Date: {date_str}
    Attendees: {attendees}
    Description: {description}
    """

    client.retain(
        content=content,
        type="event",
        source="calendar",
        author="system",
        visibility="public",
        tags=["type:schedule", "source:calendar"]
    )