"""
Compare the two most recent snapshots and report whether any rate limits changed.

Writes changed=true/false to GITHUB_OUTPUT.
If changes are detected, writes a markdown summary to /tmp/rate_limit_changes.md.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
HISTORY_DIR = ROOT / "data" / "history"
SUMMARY_FILE = os.environ.get("SUMMARY_FILE", "/tmp/rate_limit_changes.md")

LIMIT_FIELDS = ("rpm", "tpm", "rpd", "tpd", "itpm", "otpm")


def load_snapshot(path: Path) -> dict[str, dict]:
    """Return {model_id: model_dict} from a snapshot file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {m["model_id"]: m for m in data["models"]}


def main() -> None:
    snapshots = sorted(HISTORY_DIR.glob("*.json"))
    if len(snapshots) < 2:
        print("changed=false")
        return

    old_snap = load_snapshot(snapshots[-2])
    new_snap = load_snapshot(snapshots[-1])

    changes: list[str] = []
    added: list[str] = []
    removed: list[str] = []

    for model_id, new_m in new_snap.items():
        if model_id not in old_snap:
            added.append(f"- **{new_m['provider']}** {new_m['model_name']} (new)")
            continue
        old_m = old_snap[model_id]
        for tier_name, new_tier in new_m["limits"].items():
            old_tier = old_m["limits"].get(tier_name, {})
            for field in LIMIT_FIELDS:
                old_val = old_tier.get(field)
                new_val = new_tier.get(field)
                if old_val != new_val and not (old_val is None and new_val is None):
                    changes.append(
                        f"- **{new_m['provider']}** {new_m['model_name']} "
                        f"[{tier_name}] {field}: {old_val} -> {new_val}"
                    )

    for model_id, old_m in old_snap.items():
        if model_id not in new_snap:
            removed.append(f"- **{old_m['provider']}** {old_m['model_name']} (removed)")

    if not changes and not added and not removed:
        print("changed=false")
        return

    lines = ["## Rate limit changes detected", ""]
    if changes:
        lines += ["### Limit changes", ""] + changes + [""]
    if added:
        lines += ["### New models", ""] + added + [""]
    if removed:
        lines += ["### Removed models", ""] + removed + [""]

    Path(SUMMARY_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("changed=true")


if __name__ == "__main__":
    main()
