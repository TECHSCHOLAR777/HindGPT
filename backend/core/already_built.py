# backend/core/already_built.py
from core.hindsight_client import client

def detect_already_built(feature_query: str) -> dict:
    """
    Search historical records to verify if a requested feature was already built in the past.
    Returns details of original implementation, authors, PRs, and current status.
    """
    # Recall matching facts
    search_resp = client.recall(
        query=f"GitHub PRs, commits, code changes or structural decisions related to: {feature_query}",
        tags=[],
        budget="high",
        role="engineering"  # Needs engineering visibility to see codebase changes
    )
    results = search_resp.get("results", [])

    if not results:
        return {
            "already_built": False,
            "details": f"No historical records found indicating '{feature_query}' has been built.",
            "original_author": "N/A",
            "pr_reference": "N/A",
            "merged_at": "N/A",
            "evidence": []
        }

    # Reflect to extract structural details
    reflection = client.reflect(
        query=f"""
        Analyze these engineering records to check if '{feature_query}' was already built.
        Answer:
        1. Was it built (Yes/No)?
        2. Who was the primary author/developer?
        3. What was the exact PR/commit reference (e.g. PR #441)?
        4. When was it built (estimate timestamp based on records)?
        5. Explain the details of the match in a brief sentence.
        """,
        role="engineering"
    )

    answer_text = reflection.get("answer", "")
    citations = reflection.get("evidence", [])

    # Parse yes/no flag from LLM answer
    already_built = "yes" in answer_text.lower() or "built: yes" in answer_text.lower() or "was built: yes" in answer_text.lower()

    # Extract author name (simple regex fallback)
    author_match = next((item.get("author") for item in results if item.get("author")), "Unknown")
    
    # Extract PR reference
    pr_match = next((tag.split(":")[-1] for item in results for tag in item.get("tags", []) if tag.startswith("pr:")), "N/A")
    if pr_match == "N/A" and "pr #" in answer_text.lower():
        # Fallback keyword extract
        import re
        m = re.search(r'pr\s*#?\s*(\d+)', answer_text, re.IGNORECASE)
        if m:
            pr_match = m.group(1)

    return {
        "already_built": already_built,
        "details": answer_text,
        "original_author": author_match,
        "pr_reference": f"PR #{pr_match}" if pr_match != "N/A" else "N/A",
        "merged_at": next((item.get("timestamp") for item in results if item.get("timestamp")), "N/A"),
        "evidence": [{"text": c.get("text"), "type": c.get("type")} for c in citations]
    }
