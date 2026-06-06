# backend/ingest/github.py
from core.hindsight_client import client

# HARDCODE: Only watch this repo for demo
DEMO_REPO = "acme-corp/platform"

def handle_pr_event(payload: dict):
    pr = payload["pull_request"]
    action = payload["action"]  # opened, closed, merged

    content = f"""
    PR #{pr['number']}: {pr['title']}
    Status: {action}
    Author: {pr['user']['login']}
    Branch: {pr['head']['ref']}
    URL: {pr['html_url']}
    Description: {pr['body'] or 'No description'}
    """

    client.retain(
        content=content,
        type="event",
        source="github",
        author=pr['user']['login'],
        visibility="engineering",
        tags=[f"pr:{pr['number']}", "type:delivery"]
    )

# HARDCODE: Seed 3 fake PRs for demo to show full graph
SEED_PRS = [
    {"number": 441, "title": "feat: SSO SAML integration", "status": "open", "author": "dev-mike"},
    {"number": 398, "title": "feat: bulk export endpoint", "status": "merged", "author": "dev-priya"},
    {"number": 455, "title": "chore: raise API rate limit to 10k/min", "status": "open", "author": "dev-alex"},
]