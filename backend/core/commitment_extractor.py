# backend/core/commitment_extractor.py
from core.hindsight_client import client

def get_promise_progress(customer: str = "Acme Corp"):
    """
    The money shot: trace promise → PR for the demo.
    """
    # Step 1: Get all commitments made to this customer
    commitments = client.recall(
        query=f"commitments and promises made to {customer}",
        tags=["type:commitment"],
        budget="high",
        role="executive"
    )

    # Step 2: Get all engineering delivery facts
    delivery = client.recall(
        query=f"GitHub PRs and engineering work related to {customer} features",
        tags=["source:github"],
        budget="mid",
        role="executive"
    )

    # Step 3: Use reflect to trace causal chain
    analysis = client.reflect(
        query=f"""
        For each commitment made to {customer}:
        1. What exactly was promised?
        2. What is the current PR/ticket status?
        3. Is it on track, at risk, or missed?
        4. Cite exact sources for every claim.
        """,
        role="executive"
    )

    return {
        "commitments": commitments.get("results", []),
        "delivery": delivery.get("results", []),
        "analysis": analysis.get("answer", ""),
        "citations": analysis.get("evidence", [])
    }