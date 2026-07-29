"""
Write a daily snapshot of rate-limits.json to data/history/YYYY-MM-DD.json.

Snapshots are compact (no schema_version, no docs_url) to keep history small.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "rate-limits.json"
HISTORY_DIR = ROOT / "data" / "history"


def main() -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(tz=timezone.utc).date().isoformat()
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    snapshot = {
        "date": today,
        "models": [
            {
                "provider": m["provider"],
                "provider_id": m["provider_id"],
                "model_id": m["model_id"],
                "model_name": m["model_name"],
                "limits": m["limits"],
            }
            for m in data["models"]
        ],
    }

    out = HISTORY_DIR / f"{today}.json"
    out.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Snapshot written: {out.name} ({len(snapshot['models'])} models)")


if __name__ == "__main__":
    main()
