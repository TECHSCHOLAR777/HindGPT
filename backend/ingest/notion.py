# backend/ingest/notion.py
import os
from notion_client import Client
from core.hindsight_client import client

# Fetch notion token safely
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

# HARDCODE: Only index this one database for demo (engineering decisions DB)
DEMO_NOTION_DB = os.getenv("NOTION_DATABASE_ID", "your-notion-database-id-here")

def extract_text_from_blocks(blocks: dict) -> str:
    """Flatten Notion block contents into a single string"""
    text_parts = []
    results = blocks.get("results", []) if isinstance(blocks, dict) else blocks
    for block in results:
        b_type = block.get("type")
        if not b_type:
            continue
        rich_text = block.get(b_type, {}).get("rich_text", [])
        for rt in rich_text:
            plain_text = rt.get("plain_text")
            if plain_text:
                text_parts.append(plain_text)
    return "\n".join(text_parts)

def ingest_notion_page(page_id: str):
    try:
        if not notion:
            raise ValueError("Notion client not initialized (missing NOTION_TOKEN)")
            
        page = notion.pages.retrieve(page_id=page_id)
        blocks = notion.blocks.children.list(block_id=page_id)

        content = extract_text_from_blocks(blocks)
        title = page['properties']['Name']['title'][0]['text']['content']
    except Exception as e:
        print(f"⚠️ Notion fetch error, using fallback/demo content: {e}")
        content = DEMO_NOTION_CONTENT
        title = "Decision: Microservice Split — Auth Service"

    # Retain in Hindsight
    client.retain(
        content=content,
        type="decision",
        source="notion",
        author="CTO",
        visibility="engineering",
        tags=[]
    )

# HARDCODE: Seed this Notion "decision" for demo
DEMO_NOTION_CONTENT = """
# Decision: Microservice Split — Auth Service
Date: November 2023
Decision: Carve out auth into its own service
Tradeoff accepted: More ops overhead, better security boundary
Alternatives rejected: Monolith auth module (scaling concerns), third-party auth (data sovereignty)
Decision maker: CTO — Rahul Sharma
"""