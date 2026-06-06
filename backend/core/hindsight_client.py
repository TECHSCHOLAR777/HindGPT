# backend/core/hindsight_client.py
import os
import requests
from typing import List, Dict, Any, Optional

HINDSIGHT_ENGINE_URL = os.getenv("HINDSIGHT_ENGINE_URL", "http://localhost:8001")

class HindsightMemoryEngineClient:
    def __init__(self, base_url: str = HINDSIGHT_ENGINE_URL):
        self.base_url = base_url

    def retain(
        self,
        content: str,
        type: str,
        source: str,
        author: str,
        visibility: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        url = f"{self.base_url}/api/v1/memory/retain"
        payload = {
            "content": content,
            "type": type,
            "source": source,
            "author": author,
            "visibility": visibility,
            "tags": tags or [],
            "metadata": metadata or {}
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def recall(
        self,
        query: str,
        tags: List[str] = None,
        budget: str = "mid",
        role: str = "public"
    ):
        url = f"{self.base_url}/api/v1/memory/recall"
        payload = {
            "query": query,
            "tags": tags or [],
            "budget": budget
        }
        headers = {"X-User-Role": role}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def reflect(
        self,
        query: str,
        structured: bool = False,
        role: str = "public"
    ):
        url = f"{self.base_url}/api/v1/memory/reflect"
        payload = {
            "query": query,
            "structured": structured
        }
        headers = {"X-User-Role": role}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

client = HindsightMemoryEngineClient()
DEMO_BANK_ID = "company-brain"

def seed_rahuls_history():
    """Seed Rahul's decision history (5 decisions, 3 domains)"""
    try:
        # Check if already seeded
        existing = client.recall(query="decisions by rahul", tags=[], role="executive")
        results = existing.get("results", [])
        # Count items having author:rahul tag or containing rahul
        rahul_items = [r for r in results if "rahul" in r.get("text", "").lower()]
        if len(rahul_items) >= 5:
            print("ℹ️ Rahul's decision history is already seeded.")
            return
    except Exception as e:
        print(f"⚠️ Could not check seeding status: {e}. Attempting to seed...")

    decisions = [
        {
            "content": "Adopted OAuth2 standard for single sign-on integration to align with corporate security requirements.",
            "type": "decision",
            "source": "notion",
            "author": "rahul",
            "visibility": "engineering",
            "tags": ["auth", "sso"]
        },
        {
            "content": "Implemented JWT tokens for stateless session tracking across microservices, rejecting session database options to prevent scaling limits.",
            "type": "decision",
            "source": "notion",
            "author": "rahul",
            "visibility": "engineering",
            "tags": ["auth", "jwt"]
        },
        {
            "content": "Decided to use Redis cache to decrease database load for churn metrics and speed up dashboard latency.",
            "type": "decision",
            "source": "notion",
            "author": "rahul",
            "visibility": "engineering",
            "tags": ["database", "redis"]
        },
        {
            "content": "Migrated transaction logs to AWS S3 storage to comply with new compliance standards, accepting higher fetch latency.",
            "type": "decision",
            "source": "notion",
            "author": "rahul",
            "visibility": "engineering",
            "tags": ["database", "s3"]
        },
        {
            "content": "Adopted Langfuse observability layer to inspect LLM token consumption and trace drift in our prompt-cache pipelines.",
            "type": "decision",
            "source": "notion",
            "author": "rahul",
            "visibility": "engineering",
            "tags": ["ai", "observability"]
        }
    ]

    print("🌱 Seeding Rahul's decision history...")
    for d in decisions:
        try:
            client.retain(
                content=d["content"],
                type=d["type"],
                source=d["source"],
                author=d["author"],
                visibility=d["visibility"],
                tags=d["tags"]
            )
        except Exception as ex:
            print(f"❌ Failed to seed decision: {ex}")
    print("✅ Rahul's decision history seeded successfully.")
