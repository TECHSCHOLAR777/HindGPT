# backend/core/knowledge_preservation.py
from core.hindsight_client import client

def generate_knowledge_transfer_report(author: str) -> dict:
    """
    Build a Knowledge Transfer Report for a departing employee
    summarizing key decisions they made, tradeoffs they chose, and outstanding commitments.
    """
    # 1. Recall decisions & commitments by this author
    author_facts = client.recall(
        query=f"decisions made by {author} or commitments assigned to {author}",
        tags=[f"author:{author}"],
        budget="high",
        role="executive"
    )
    facts_list = author_facts.get("results", [])

    if not facts_list:
        return {
            "author": author,
            "report_markdown": f"No historical records found for author '{author}'.",
            "decisions_count": 0,
            "citations": []
        }

    # 2. Reflect on decision footprint
    reflection = client.reflect(
        query=f"""
        Compile a Knowledge Transfer Report for the departing engineer '{author}'.
        Based on the history:
        1. KEY ARCHITECTURAL DOMAINS: What domains or modules did they design/own?
        2. CRITICAL DECISIONS & TRADEOFFS: What major engineering choices did they make, and what compromises were accepted?
        3. OPEN COMMITMENTS: Are there active promises or tasks still pending under their name?
        Format the report in clean Markdown.
        """,
        role="executive"
    )

    return {
        "author": author,
        "report_markdown": reflection.get("answer", "Failed to compile report."),
        "decisions_count": len(facts_list),
        "citations": [{"text": c.get("text"), "type": c.get("type")} for c in reflection.get("evidence", [])]
    }

def detect_succession_gaps() -> dict:
    """
    Identify components or design areas that have single-point-of-failure risks
    (i.e., only one person has historical context or decision logs in that domain).
    """
    # 1. Retrieve all architectural decisions
    decisions_resp = client.recall(
        query="architectural decisions and microservice configurations",
        tags=["type:decision"],
        budget="high",
        role="executive"
    )
    decisions = decisions_resp.get("results", [])

    # Group components by unique authors
    domain_owners = {}
    for d in decisions:
        text = d.get("text", "").lower()
        author = d.get("author", "unknown")
        
        # Simple extraction of domain name from text
        domain = "General Platform"
        if "auth" in text:
            domain = "Authentication & SSO"
        elif "s3" in text or "storage" in text:
            domain = "AWS Storage Pipeline"
        elif "billing" in text or "stripe" in text:
            domain = "Stripe Billing"
        elif "elasticsearch" in text:
            domain = "Search & Indexing"
        elif "vector" in text:
            domain = "Vector Memory Engine"

        if domain not in domain_owners:
            domain_owners[domain] = set()
        domain_owners[domain].add(author)

    gaps = []
    for domain, authors in domain_owners.items():
        if len(authors) <= 1:
            sole_owner = list(authors)[0] if authors else "Unknown"
            gaps.append({
                "domain": domain,
                "risk_level": "CRITICAL" if sole_owner != "Unknown" else "MEDIUM",
                "sole_context_holder": sole_owner,
                "reasons": f"Only {sole_owner} has recorded decision history for the '{domain}' module. Succession backup is missing."
            })

    return {
        "status": "success",
        "gaps_found_count": len(gaps),
        "succession_gaps": gaps if gaps else [{"domain": "All", "risk_level": "NONE", "sole_context_holder": "None", "reasons": "No succession risks detected. Multiple developers own each domain."}]
    }
