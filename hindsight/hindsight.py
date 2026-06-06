import os
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from hindsight_client import Hindsight

# ---------------- CONFIG ----------------

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_KEY", "")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "company-brain")

client: Optional[Hindsight] = None

app = FastAPI(title="Hindsight Memory Engine", version="1.0.0")

# ---------------- MODELS ----------------

class MemoryRetainRequest(BaseModel):
    content: str
    type: Literal["decision", "event", "promise", "note", "alert"]
    source: str
    author: str
    visibility: Literal["public", "engineering", "sales", "finance", "executive"]
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryRecallRequest(BaseModel):
    query: str
    tags: List[str] = []
    budget: str = "mid"


class MemoryReflectRequest(BaseModel):
    query: str
    structured: bool = False


# ---------------- ROLE CONTROL ----------------

ROLE_MAP = {
    "public": ["public"],
    "engineering": ["engineering", "public"],
    "sales": ["sales", "public"],
    "finance": ["finance", "public"],
    "executive": ["public", "engineering", "sales", "finance", "executive"],
}


def verify_role_access(x_user_role: str = Header(default="public")):
    role = x_user_role.lower()
    if role not in ROLE_MAP:
        raise HTTPException(status_code=403, detail="Invalid role")
    return role


# ---------------- STARTUP ----------------

@app.on_event("startup")
def startup():
    global client

    if not HINDSIGHT_API_KEY:
        raise Exception("❌ HINDSIGHT_API_KEY not set")

    client = Hindsight(
        base_url=HINDSIGHT_BASE_URL,
        api_key=HINDSIGHT_API_KEY,
        timeout=30.0,
    )

    print("✅ Hindsight client initialized")


@app.on_event("shutdown")
def shutdown():
    global client
    if client:
        client.close()


# ---------------- CORE RETAIN FUNCTION ----------------

def _retain_item(
    content: str,
    type_: str,
    source: str,
    author: str,
    visibility: str,
    extra_tags: List[str],
    timestamp: str,
    metadata: Dict[str, Any],
):
    global client

    if client is None:
        raise Exception("Hindsight client not initialized")

    tags = list(set(extra_tags + [
        f"source:{source}",
        f"author:{author}",
        f"visibility:{visibility}",
        f"type:{type_}",
    ]))

    client.retain(
        bank_id=BANK_ID,
        content=content,
        context=f"{type_.upper()} via {source} by {author}",
        timestamp=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
        metadata={
            "type": type_,
            "source": source,
            "author": author,
            "visibility": visibility,
            **metadata,
        },
        tags=tags,
        retain_async=False,
    )


# ---------------- API ----------------

@app.post("/api/v1/memory/retain")
def retain(payload: MemoryRetainRequest):
    try:
        timestamp = datetime.now(timezone.utc).isoformat()

        _retain_item(
            content=payload.content,
            type_=payload.type,
            source=payload.source,
            author=payload.author,
            visibility=payload.visibility,
            extra_tags=payload.tags,
            timestamp=timestamp,
            metadata=payload.metadata,
        )

        return {"status": "success", "timestamp": timestamp}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/memory/recall")
def recall(payload: MemoryRecallRequest, role: str = Depends(verify_role_access)):
    try:
        if client is None:
            raise HTTPException(status_code=500, detail="Client not initialized")

        tags = list(payload.tags)

        if role != "executive":
            tags.append(f"visibility:{role}")

        response = client.recall(
            bank_id=BANK_ID,
            query=payload.query,
            budget=payload.budget,
            max_tokens=2000,
            tags=tags if tags else None,
        )

        results = response.results if hasattr(response, "results") else response

        return {
            "results": [
                {"text": r.text, "type": r.type}
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/memory/reflect")
def reflect(payload: MemoryReflectRequest, role: str = Depends(verify_role_access)):
    try:
        if client is None:
            raise HTTPException(status_code=500, detail="Client not initialized")

        tags = [] if role == "executive" else [f"visibility:{role}"]

        answer = client.reflect(
            bank_id=BANK_ID,
            query=payload.query,
            budget="mid",
            tags=tags,
        )

        evidence = []
        if hasattr(answer, "based_on") and answer.based_on:
            for m in getattr(answer.based_on, "memories", []):
                evidence.append({"text": m.text, "type": m.type})

        return {
            "answer": answer.text,
            "evidence": evidence,
            "structured": getattr(answer, "structured_output", None)
            if payload.structured else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))