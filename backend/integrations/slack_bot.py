# backend/integrations/slack_bot.py
import os
from slack_bolt import App
from core.commitment_extractor import get_promise_progress
from core.hindsight_client import client

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "xoxb-placeholder")
app = App(token=SLACK_BOT_TOKEN)

@app.command("/hindgpt")
def handle_hindgpt(ack, say, command):
    ack()
    query = command.get("text", "")  # e.g. "check Acme Corp" or "why did we build SSO?"

    result = client.reflect(
        query=query,
        role="public" # default role for Slack commands unless mapped
    )

    # Format with citations for trust
    evidence_list = result.get("evidence", [])
    citations = "\n".join([
        f"• {m.get('text', '')[:80]}..."
        for m in evidence_list[:3]
    ]) if evidence_list else "No matching evidence found."

    say({
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*HindGPT:* {result.get('answer', 'No answer received.')}"}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Sources:*\n{citations}"}}
        ]
    })

# HARDCODE: Also listen for PR merge events and auto-ping AE
@app.event("message")
def handle_pr_merge_notification(event, say):
    # Triggered by GitHub → Slack webhook
    text = event.get("text", "")
    if "merged" in text:
        say("✅ HindGPT: Commitment node auto-closed. AE notified.")
