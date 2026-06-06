# backend/core/after_action.py
from core.hindsight_client import client

def generate_after_action_report(feature_name: str = "SSO integration") -> dict:
    """
    Generate an After-Action Review (AAR) report for a completed or missed commitment topic.
    Grabs timelines, delivery PRs, and summarizes alignment/drift.
    """
    # 1. Recall historical records about this feature
    hindsight_facts = client.recall(
        query=f"promises, emails, tickets and PRs related to {feature_name}",
        tags=[],
        budget="high",
        role="executive"
    )
    facts_list = hindsight_facts.get("results", [])

    # 2. Reflect on timeline/drift
    reflection = client.reflect(
        query=f"""
        Analyze the commitment and execution history for '{feature_name}'.
        Construct a detailed After-Action Report containing:
        1. INITIAL PROMISE: What was committed, when, to whom, and by which author?
        2. ACTUAL OUTCOME: What was built/merged (cite PR numbers and git authors)?
        3. DRIFT ANALYSIS: Did delivery drift from initial promise (timeline delays, feature scope changes)? Why?
        4. LESSONS LEARNED: Technical or communication recommendations for next sprint.
        Format the output clearly as a structured Markdown document.
        """,
        role="executive"
    )

    report_markdown = reflection.get("answer", "Failed to generate report analysis.")
    citations = reflection.get("evidence", [])

    return {
        "feature_name": feature_name,
        "report_markdown": report_markdown,
        "citations": citations,
        "source_facts_count": len(facts_list)
    }