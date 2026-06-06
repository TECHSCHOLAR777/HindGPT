import os
import json
from pathlib import Path
from datetime import datetime, timezone

from hindsight_client import Hindsight

# ---------------- CONFIG ----------------

HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_KEY", "")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "company-brain")

client = Hindsight(
    base_url=HINDSIGHT_BASE_URL,
    api_key=HINDSIGHT_API_KEY,
    timeout=30.0,
)

# ---------------- RETAIN FUNCTION ----------------

def retain_item(item: dict):
    tags = list(set(item.get("tags", []) + [
        f"source:{item.get('source', 'unknown')}",
        f"author:{item.get('author', 'unknown')}",
        f"visibility:{item.get('visibility', 'public')}",
        f"type:{item.get('type', 'note')}",
    ]))

    client.retain(
        bank_id=BANK_ID,
        content=item.get("content", ""),
        context=f"{item.get('type', 'note').upper()} via {item.get('source')} by {item.get('author')}",
        timestamp=datetime.fromisoformat(
            item.get("timestamp", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")
        ),
        metadata=item.get("metadata", {}),
        tags=tags,
        retain_async=False,
    )


# ---------------- LOAD JSON ----------------

def load_json():
    file_path = Path("nexus_dummy_data.json")

    if not file_path.exists():
        print("❌ nexus_dummy_data.json not found")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = data.get("data", data.get("items", []))

    return data


# ---------------- MAIN SEED ----------------

def main():
    data = load_json()

    print(f"📦 Found {len(data)} records")

    success = 0
    failed = 0

    for i, item in enumerate(data):
        try:
            retain_item(item)
            success += 1
            print(f"✅ Seeded {i+1}/{len(data)}")
        except Exception as e:
            failed += 1
            print(f"❌ Failed {i+1}: {e}")

    print("\n====== SEED SUMMARY ======")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print("===========================")


# ---------------- RUN ----------------

if __name__ == "__main__":
    main()