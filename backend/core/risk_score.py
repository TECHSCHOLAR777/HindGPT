# backend/core/risk_score.py
from core.hindsight_client import client
import re

def calculate_risk_score(customer: str = "Acme Corp") -> dict:
    """
    Calculate a commitment risk score (0.0 to 1.0) for a given customer.
    Analyzes promises, alerts, and drift notifications.
    """
    # Query Hindsight for commitments
    commitments_resp = client.recall(
        query=f"commitments, deadlines and promises made to {customer}",
        tags=["type:commitment"],
        budget="high",
        role="executive"
    )
    commitments = commitments_resp.get("results", [])

    # Query Hindsight for alerts and drifts
    alerts_resp = client.recall(
        query=f"alerts, drifts, anomalies, delays or risks related to {customer}",
        tags=[],
        budget="high",
        role="executive"
    )
    alerts = alerts_resp.get("results", [])

    risk_factors = []
    base_score = 0.1  # start with a clean health baseline

    # Analyze alerts & drifts
    for item in alerts:
        text = item.get("text", "").lower()
        # Look for indicators of risk
        if "drift" in text or "not aligned" in text:
            base_score += 0.25
            risk_factors.append(f"Commitment Drift: {item.get('text')}")
        elif "alert" in text or "high risk" in text or "missed deadline" in text:
            base_score += 0.35
            risk_factors.append(f"Risk Warning: {item.get('text')}")
        elif "anomaly" in text or "leak" in text or "failure" in text:
            base_score += 0.20
            risk_factors.append(f"System Anomaly: {item.get('text')}")

    # Analyze commitments for tentative/unresolved state
    for item in commitments:
        text = item.get("text", "").lower()
        if "tentative" in text or "might be able to" in text or "hopefully" in text:
            base_score += 0.1
            risk_factors.append(f"Unresolved Promise: '{item.get('text')[:80]}...' is still tentative.")

    # Bound risk score between 0.0 and 1.0
    score = min(max(round(base_score, 2), 0.0), 1.0)

    if score < 0.4:
        status = "LOW"
    elif score < 0.7:
        status = "MEDIUM"
    else:
        status = "HIGH"

    return {
        "customer": customer,
        "score": score,
        "status": status,
        "risk_factors": risk_factors[:5] if risk_factors else ["No high risk indicators found. Commitments are tracking normally."]
    }