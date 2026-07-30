"""
Generate data/changelog.md by comparing all consecutive weekly snapshots
in data/history/ and recording rate limit changes, new models, and removals.

Run after snapshot.py so the current week's snapshot is already written.
The output file is regenerated from scratch on every run (idempotent).
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
HISTORY_DIR = ROOT / "data" / "history"
CHANGELOG_FILE = ROOT / "data" / "changelog.md"

LIMIT_FIELDS = ("rpm", "tpm", "rpd", "tpd", "itpm", "otpm")
FIELD_LABELS = {
    "rpm": "RPM", "tpm": "TPM", "rpd": "RPD",
    "tpd": "TPD", "itpm": "ITPM", "otpm": "OTPM",
}


def load_snapshot(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {m["model_id"]: m for m in data["models"]}


def fmt_num(v: int | None) -> str:
    if v is None:
        return "N/A"
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.0f}K"
    return str(v)


def compare(
    prev: dict[str, dict], curr: dict[str, dict]
) -> tuple[list[dict], list[dict], list[dict]]:
    """Return (limit_changes, new_models, removed_models)."""
    limit_changes: list[dict] = []
    new_models: list[dict] = []
    removed_models: list[dict] = []

    for model_id, curr_m in curr.items():
        prev_m = prev.get(model_id)
        if prev_m is None:
            new_models.append(curr_m)
            continue
        for tier_name, curr_tier in curr_m["limits"].items():
            prev_tier = prev_m["limits"].get(tier_name, {})
            for field in LIMIT_FIELDS:
                old_val = prev_tier.get(field)
                new_val = curr_tier.get(field)
                if old_val != new_val and not (old_val is None and new_val is None):
                    limit_changes.append(
                        {
                            "provider": curr_m["provider"],
                            "model_name": curr_m["model_name"],
                            "tier": tier_name,
                            "field": FIELD_LABELS.get(field, field.upper()),
                            "old": old_val,
                            "new": new_val,
                        }
                    )

    for model_id, prev_m in prev.items():
        if model_id not in curr:
            removed_models.append(prev_m)

    return limit_changes, new_models, removed_models


def render_entry(
    date_curr: str,
    limit_changes: list[dict],
    new_models: list[dict],
    removed_models: list[dict],
) -> str:
    lines = [f"## {date_curr}", ""]

    if limit_changes:
        lines += [
            "### Limit changes",
            "",
            "| Provider | Model | Tier | Metric | Old | New |",
            "|----------|-------|------|--------|-----|-----|",
        ]
        for c in limit_changes:
            lines.append(
                f"| {c['provider']} | {c['model_name']} | {c['tier']} "
                f"| {c['field']} | {fmt_num(c['old'])} | {fmt_num(c['new'])} |"
            )
        lines.append("")

    if new_models:
        lines += ["### New models", ""]
        for m in new_models:
            lines.append(f"- **{m['provider']}** {m['model_name']}")
        lines.append("")

    if removed_models:
        lines += ["### Removed models", ""]
        for m in removed_models:
            lines.append(f"- **{m['provider']}** {m['model_name']}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    snapshots = sorted(p for p in HISTORY_DIR.glob("*.json") if p.stem != "index")
    header = (
        "# Rate Limits Changelog\n\n"
        "All rate limit changes, new models, and removals detected by the weekly update workflow.\n"
        "Sorted by date (newest first). "
        "Source: [`data/history/`](data/history/)\n\n"
        "---\n\n"
    )

    if len(snapshots) < 2:
        CHANGELOG_FILE.write_text(header + "_No changes recorded yet._\n", encoding="utf-8")
        print("Not enough snapshots to compare (need at least 2). Empty changelog written.")
        return

    entries: list[str] = []
    for old_path, new_path in reversed(list(itertools.pairwise(snapshots))):
        date_curr = new_path.stem
        prev = load_snapshot(old_path)
        curr = load_snapshot(new_path)
        limit_changes, new_models, removed_models = compare(prev, curr)
        if limit_changes or new_models or removed_models:
            entries.append(render_entry(date_curr, limit_changes, new_models, removed_models))

    content = header + ("\n---\n\n".join(entries) if entries else "_No changes recorded yet._\n")
    CHANGELOG_FILE.write_text(content, encoding="utf-8")
    print(f"Changelog written: {len(entries)} entries from {len(snapshots)} snapshots.")


if __name__ == "__main__":
    main()
