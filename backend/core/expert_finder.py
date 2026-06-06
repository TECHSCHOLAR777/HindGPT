# backend/core/expert_finder.py
from core.hindsight_client import client

def find_experts(topic: str) -> dict:
    """
    Expert Finder: query Hindsight for matching memories on a topic,
    aggregate by author tags, and rank the top experts in the domain.
    """
    # 1. Recall matching entries
    recall_resp = client.recall(
        query=f"design decisions, implementations, PRs and code changes regarding: {topic}",
        tags=[],
        budget="high",
        role="engineering"
    )
    results = recall_resp.get("results", [])

    if not results:
        return {
            "topic": topic,
            "experts": [],
            "summary": f"No expert records found in hindsight for topic '{topic}'."
        }

    # 2. Count author occurrences & map contributions
    author_counts = {}
    author_contributions = {}

    for item in results:
        # Extract author name from item details
        author = item.get("author")
        text = item.get("text", "")
        
        # Double check if author metadata is missing, look at tags
        if not author:
            for tag in item.get("tags", []):
                if tag.startswith("author:"):
                    author = tag.split(":")[-1]
                    break
        
        if not author or author.lower() in ["system", "unknown"]:
            continue
            
        author = author.lower()
        author_counts[author] = author_counts.get(author, 0) + 1
        if author not in author_contributions:
            author_contributions[author] = []
        # Store a snippet of their contribution
        author_contributions[author].append(text[:100] + "..." if len(text) > 100 else text)

    # 3. Sort experts by activity score
    sorted_experts = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)

    experts_list = []
    for name, count in sorted_experts:
        experts_list.append({
            "name": name.capitalize(),
            "score": count,
            "contributions": list(set(author_contributions[name]))[:3] # unique top 3 contributions
        })

    summary = f"Found {len(experts_list)} expert(s) for topic '{topic}'."
    if experts_list:
        summary += f" The top expert is {experts_list[0]['name']} with a contribution score of {experts_list[0]['score']}."

    return {
        "topic": topic,
        "experts": experts_list,
        "summary": summary
    }
