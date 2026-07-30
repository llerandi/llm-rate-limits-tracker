"""
Generate an Atom feed of rate limit changes from weekly history snapshots.

Compares consecutive snapshot pairs; emits one <entry> per week that had
any additions, removals, or limit value changes.

Output: data/feed.xml
"""

from __future__ import annotations

import itertools
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
HISTORY_DIR = ROOT / "data" / "history"
FEED_FILE = ROOT / "data" / "feed.xml"

REPO_URL = "https://github.com/llerandi/llm-rate-limits-tracker"
SITE_URL = "https://llerandi.github.io/llm-rate-limits-tracker/"
CDN_BASE = "https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main"
LIMIT_FIELDS = ("rpm", "tpm", "rpd", "tpd", "itpm", "otpm")

MAX_ENTRIES = 52  # Keep up to one year of weekly entries


def load_snapshot(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {m["model_id"]: m for m in data["models"]}


def diff_snapshots(old: dict, new: dict) -> tuple[list[str], list[str], list[str]]:
    """Return (changes, added, removed) as lists of human-readable strings."""
    changes: list[str] = []
    added: list[str] = []
    removed: list[str] = []

    for model_id, new_m in new.items():
        if model_id not in old:
            added.append(f"{new_m['provider']} {new_m['model_name']} (new model)")
            continue
        old_m = old[model_id]
        for tier_name, new_tier in new_m["limits"].items():
            old_tier = old_m["limits"].get(tier_name, {})
            for field in LIMIT_FIELDS:
                old_val = old_tier.get(field)
                new_val = new_tier.get(field)
                if old_val != new_val and not (old_val is None and new_val is None):
                    changes.append(
                        f"{new_m['provider']} {new_m['model_name']}"
                        f" [{tier_name}] {field.upper()}: {old_val} -> {new_val}"
                    )

    for model_id, old_m in old.items():
        if model_id not in new:
            removed.append(f"{old_m['provider']} {old_m['model_name']} (removed)")

    return changes, added, removed


def build_html_summary(changes: list[str], added: list[str], removed: list[str]) -> str:
    parts: list[str] = []
    if changes:
        rows = "".join(f"<li>{c}</li>" for c in changes)
        parts.append(f"<h3>Limit changes</h3><ul>{rows}</ul>")
    if added:
        rows = "".join(f"<li>{a}</li>" for a in added)
        parts.append(f"<h3>New models</h3><ul>{rows}</ul>")
    if removed:
        rows = "".join(f"<li>{r}</li>" for r in removed)
        parts.append(f"<h3>Removed models</h3><ul>{rows}</ul>")
    parts.append(
        f'<p>Full data: <a href="{CDN_BASE}/data/rate-limits.json">rate-limits.json</a>'
        f' | <a href="{SITE_URL}">Live site</a></p>'
    )
    return "".join(parts)


def date_to_rfc3339(date_str: str) -> str:
    """Convert YYYY-MM-DD to RFC 3339 UTC timestamp."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    snapshots = sorted(HISTORY_DIR.glob("*.json"))
    if len(snapshots) < 2:
        # Not enough history to diff; write an empty feed
        entries: list[dict] = []
    else:
        entries = []
        pairs = list(itertools.pairwise(snapshots))
        for old_path, new_path in pairs[-MAX_ENTRIES:]:
            old = load_snapshot(old_path)
            new = load_snapshot(new_path)
            changes, added, removed = diff_snapshots(old, new)
            if not (changes or added or removed):
                continue
            date_str = new_path.stem  # YYYY-MM-DD
            total = len(changes) + len(added) + len(removed)
            entries.append(
                {
                    "date": date_str,
                    "title": f"{total} rate limit change{'s' if total != 1 else ''} ({date_str})",
                    "html": build_html_summary(changes, added, removed),
                    "id": f"{REPO_URL}/blob/main/data/history/{date_str}.json",
                }
            )

    # Build Atom XML
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated = entries[-1]["date"] if entries else now[:10]

    ET.register_namespace("", "http://www.w3.org/2005/Atom")
    feed = ET.Element("{http://www.w3.org/2005/Atom}feed")

    def sub(parent: ET.Element, tag: str, text: str | None = None, **attrs: str) -> ET.Element:
        el = ET.SubElement(parent, f"{{http://www.w3.org/2005/Atom}}{tag}", attrs)
        if text is not None:
            el.text = text
        return el

    sub(feed, "title", "LLM Rate Limits Tracker - Changes")
    sub(feed, "subtitle", "Weekly diffs of API rate limits across major LLM providers")
    sub(feed, "id", f"{REPO_URL}/")
    sub(feed, "updated", date_to_rfc3339(updated) if len(updated) == 10 else updated)
    sub(feed, "link", href=SITE_URL, rel="alternate", type="text/html")
    sub(feed, "link", href=f"{CDN_BASE}/data/feed.xml", rel="self", type="application/atom+xml")

    author = sub(feed, "author")
    sub(author, "name", "LLM Rate Limits Tracker")
    sub(author, "uri", REPO_URL)

    for entry in reversed(entries):  # Newest first
        e = sub(feed, "entry")
        sub(e, "title", entry["title"])
        sub(e, "id", entry["id"])
        sub(e, "updated", date_to_rfc3339(entry["date"]))
        sub(e, "link", href=entry["id"], rel="alternate")
        content = sub(e, "content", type="html")
        content.text = entry["html"]

    tree = ET.ElementTree(feed)
    ET.indent(tree, space="  ")

    with FEED_FILE.open("wb") as f:
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        tree.write(f, encoding="utf-8", xml_declaration=False)
        f.write(b"\n")

    print(f"Generated {FEED_FILE.relative_to(ROOT)} with {len(entries)} entries")


if __name__ == "__main__":
    main()
