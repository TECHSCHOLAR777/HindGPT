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