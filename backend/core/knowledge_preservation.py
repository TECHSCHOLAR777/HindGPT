# backend/core/knowledge_preservation.py
from core.hindsight_client import client

# Track departed team members (defaulting to 'rahul' for demo)
DEPARTED_PEOPLE = {"rahul"}

def mark_person_departed(name: str) -> dict:
    """Mark a team member as departed to enable shadow routing for their domains."""
    name_clean = name.strip().lower()
    DEPARTED_PEOPLE.add(name_clean)
    return {
        "status": "success",
        "message": f"'{name.capitalize()}' is now marked as DEPARTED. Shadow routing enabled.",
        "departed_list": list(DEPARTED_PEOPLE)
    }

def generate_knowledge_transfer_report(author: str) -> dict:
    """
    Build a Knowledge Transfer Report for a departing employee
    summarizing key decisions they made, tradeoffs they chose, and outstanding commitments.
    """
    author_clean = author.strip().lower()
    
    # 1. Recall decisions & commitments by this author
    author_facts = client.recall(
        query=f"decisions made by {author_clean} or commitments assigned to {author_clean}",
        tags=[f"author:{author_clean}"],
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
        Compile a Knowledge Transfer Report for the departing engineer '{author_clean}'.
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

def query_shadow_persona(author: str, query: str) -> dict:
    """
    Shadow routing query: Emulate the mindset and context of a departed context holder
    to answer technical design questions based on their historical files.
    """
    author_clean = author.strip().lower()
    is_departed = author_clean in DEPARTED_PEOPLE

    # Query Hindsight specifically for this author's choices
    reflection = client.reflect(
        query=f"""
        You are HindGPT. You are emulating the retired context holder '{author_clean}'.
        Using only their decision log history:
        - Answer this question exactly as they would.
        - Adopt their technical perspective and reference the tradeoffs they accepted (e.g., ops overhead, speed vs security).
        - State clearly at the start of your response: '[Emulating {author_clean.capitalize()} - Departed Status: {is_departed}]'.
        
        Question: {query}
        """,
        role="engineering"
    )

    return {
        "author": author_clean,
        "is_departed": is_departed,
        "shadow_answer": reflection.get("answer", "Failed to generate emulated response."),
        "citations": [{"text": c.get("text"), "type": c.get("type")} for c in reflection.get("evidence", [])]
    }

def how_did_person_think(author: str, topic: str) -> dict:
    """
    Query HindGPT live to analyze a specific developer's decision-making style,
    design patterns, and tradeoff logic.
    """
    author_clean = author.strip().lower()
    
    reflection = client.reflect(
        query=f"""
        Analyze the decision logs of '{author_clean}' on the topic of '{topic}'.
        Describe:
        1. Their technical preferences or patterns.
        2. The specific tradeoffs they historically accepted (e.g. data sovereignty vs operational overhead).
        3. Their reasoning style: is it risk-averse, performance-driven, or velocity-driven?
        Provide a concise response grounded in their actual files.
        """,
        role="engineering"
    )

    return {
        "author": author_clean,
        "topic": topic,
        "thinking_profile": reflection.get("answer", "Could not reconstruct thinking profile."),
        "citations": [{"text": c.get("text"), "type": c.get("type")} for c in reflection.get("evidence", [])]
    }

def detect_succession_gaps() -> dict:
    """
    Identify components or design areas that have single-point-of-failure risks
    (i.e., only one person has historical context or decision logs in that domain).
    """
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
        author = d.get("author", "unknown").lower()
        
        domain = "General Platform"
        if "auth" in text or "sso" in text or "jwt" in text:
            domain = "Authentication & SSO"
        elif "s3" in text or "storage" in text:
            domain = "AWS Storage Pipeline"
        elif "billing" in text or "stripe" in text:
            domain = "Stripe Billing"
        elif "elasticsearch" in text:
            domain = "Search & Indexing"
        elif "vector" in text:
            domain = "Vector Memory Store"
        elif "langfuse" in text or "observability" in text:
            domain = "AI Observability"

        if domain not in domain_owners:
            domain_owners[domain] = set()
        domain_owners[domain].add(author)

    gaps = []
    for domain, authors in domain_owners.items():
        if len(authors) <= 1:
            sole_owner = list(authors)[0] if authors else "unknown"
            # Mark critical if the sole context holder is marked departed
            risk_level = "MEDIUM"
            if sole_owner in DEPARTED_PEOPLE:
                risk_level = "CRITICAL"
            elif sole_owner != "unknown":
                risk_level = "HIGH"
                
            gaps.append({
                "domain": domain,
                "risk_level": risk_level,
                "sole_context_holder": sole_owner.capitalize(),
                "reasons": f"Only {sole_owner.capitalize()} has recorded decision history for the '{domain}' module. " +
                           (f"CRITICAL: Context holder is departed!" if sole_owner in DEPARTED_PEOPLE else "Succession backup is missing.")
            })

    return {
        "status": "success",
        "gaps_found_count": len(gaps),
        "succession_gaps": gaps if gaps else [{"domain": "All", "risk_level": "NONE", "sole_context_holder": "None", "reasons": "No succession risks detected."}]
    }
