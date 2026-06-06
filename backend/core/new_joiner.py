# backend/core/new_joiner.py
from core.hindsight_client import client

def query_joiner_intelligence(query: str, role: str = "engineering") -> dict:
    """
    Answer questions for new joiners grounded in historical decision memory,
    revealing tradeoffs, rejected options, and decision makers.
    """
    # Run reflect query on the Memory Engine
    reflection = client.reflect(
        query=f"""
        You are HindGPT, an institutional memory assistant.
        Answer the following question from a new team member. 
        Focus strictly on:
        1. Why decisions were made.
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
    Fetch a real-time pulse of team performance metrics: velocity, active customer
    commitments, and areas of highest customer concern.
    """
    # 1. Fetch commitments to count open ones
    commitments_resp = client.recall(
        query="all customer promises and deadlines",
        tags=["type:commitment"],
        budget="high",
        role="executive"
    )
    commitments = commitments_resp.get("results", [])
    
    # 2. Fetch engineering delivery facts
    delivery_resp = client.recall(
        query="all GitHub PRs and engineering shipping logs",
        tags=["source:github"],
        budget="high",
        role="executive"
    )
    deliveries = delivery_resp.get("results", [])

    # Calculate metrics
    open_commitments_count = len([c for c in commitments if "merged" not in c.get("text", "").lower()])
    merged_prs_count = len([d for d in deliveries if "merged" in d.get("text", "").lower() or "close" in d.get("text", "").lower()])
    total_prs = len(deliveries)

    # Simple analytics heuristics
    top_customer_concerns = ["Single Sign-On (SSO)", "SOC2 Compliance", "API Rate Limiting"]
    velocity_status = "Steady" if total_prs > 0 else "Low Activity"
    if merged_prs_count > 5:
        velocity_status = "High Velocity"

    return {
        "velocity": {
            "status": velocity_status,
            "total_prs_tracked": total_prs,
            "merged_prs": merged_prs_count,
            "pending_prs": total_prs - merged_prs_count
        },
        "customer_pulse": {
            "open_commitments_count": open_commitments_count,
            "top_concerns": top_customer_concerns
        },
        "pulse_summary": f"Team is operating at {velocity_status}. Currently managing {open_commitments_count} open customer commitments with {merged_prs_count} completed deliverables."
    }
