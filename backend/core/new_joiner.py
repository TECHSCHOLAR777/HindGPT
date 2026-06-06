# backend/core/new_joiner.py
from core.hindsight_client import client

def query_joiner_intelligence(query: str, role: str = "engineering") -> dict:
    """
    Answer questions for new joiners grounded in historical decision memory,
    revealing tradeoffs, rejected options, and decision makers.
    """
    reflection = client.reflect(
        query=f"""
        You are HindGPT, an institutional memory assistant.
        Answer the following question from a new team member. 
        Focus strictly on:
        1. Why decisions were made (e.g., Notion decision logs).
        2. What tradeoffs were accepted.
        3. Who made the final decision.
        4. What alternative solutions were rejected and why.
        
        Question: {query}
        """,
        role=role
    )

    return {
        "query": query,
        "answer": reflection.get("answer", "Failed to retrieve decision background details."),
        "citations": reflection.get("evidence", [])
    }

def get_performance_pulse() -> dict:
    """
    Performance Pulse: Calculate development velocity and commitment hit rate.
    Velocity = total merged PRs.
    Hit Rate = percentage of customer commitments successfully delivered.
    """
    # 1. Fetch commitments
    commitments_resp = client.recall(
        query="customer commitments, promises and customer requirements",
        tags=["type:commitment"],
        budget="high",
        role="executive"
    )
    commitments = commitments_resp.get("results", [])
    
    # 2. Fetch engineering delivery facts (git PRs)
    delivery_resp = client.recall(
        query="GitHub PR status, commits and engineering merge records",
        tags=["source:github"],
        budget="high",
        role="executive"
    )
    deliveries = delivery_resp.get("results", [])

    total_commitments = len(commitments)
    total_deliveries = len(deliveries)

    # Calculate delivered commitments (commitments linked to a merged PR or completed work)
    delivered_commitments = 0
    merged_prs = [d for d in deliveries if "merged" in d.get("text", "").lower() or "close" in d.get("text", "").lower()]
    total_merged = len(merged_prs)

    for c in commitments:
        text = c.get("text", "").lower()
        # Look if there is matching git evidence or if text indicates success/close
        if "completed" in text or "closed" in text or "live" in text:
            delivered_commitments += 1
        else:
            # Check if any merged PR title matches words in the commitment description
            words = set(text.split())
            for pr in merged_prs:
                pr_text = pr.get("text", "").lower()
                # If there's high semantic keyword overlap
                overlap = [w for w in ["sso", "saml", "export", "billing", "api", "limit"] if w in text and w in pr_text]
                if overlap:
                    delivered_commitments += 1
                    break

    # Guard bounds for hit rate calculation
    if total_commitments > 0:
        # Bound delivered count so it doesn't exceed total commitments
        delivered_commitments = min(delivered_commitments, total_commitments)
        hit_rate = round((delivered_commitments / total_commitments) * 100, 1)
    else:
        hit_rate = 100.0  # Default perfect hit rate if no active commitments exist

    velocity_status = "Moderate Velocity"
    if total_merged > 5:
        velocity_status = "High Velocity"
    elif total_merged == 0:
        velocity_status = "Maintenance Phase"

    return {
        "metrics": {
            "total_commitments_tracked": total_commitments,
            "delivered_commitments": delivered_commitments,
            "pending_commitments": total_commitments - delivered_commitments,
            "commitment_hit_rate_percentage": hit_rate,
            "engineering_velocity": {
                "status": velocity_status,
                "total_prs_tracked": total_deliveries,
                "merged_prs": total_merged,
                "pending_prs": total_deliveries - total_merged
            }
        },
        "pulse_summary": f"Operating at '{velocity_status}' with a commitment hit rate of {hit_rate}%. " +
                         f"Delivered {delivered_commitments}/{total_commitments} client promises successfully."
    }
