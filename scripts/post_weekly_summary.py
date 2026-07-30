"""
Post a weekly LLM rate limit summary to GitHub Discussions.

Reads the two most recent history snapshots, diffs them, and posts a
markdown summary via the GitHub GraphQL API using GH_TOKEN.

Requires the repo to have Discussions enabled with at least one category.
A "Weekly Summary" or "Announcements" category is preferred; falls back to
the first available category.
"""

from __future__ import annotations

import itertools
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
HISTORY_DIR = ROOT / "data" / "history"
DATA_FILE = ROOT / "data" / "rate-limits.json"

SITE_URL = "https://llerandi.github.io/llm-rate-limits-tracker/"
REPO_URL = "https://github.com/llerandi/llm-rate-limits-tracker"
CDN_BASE = "https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main"

LIMIT_FIELDS = ("rpm", "tpm", "rpd", "tpd", "itpm", "otpm")
FIELD_LABELS = {
    "rpm": "RPM",
    "tpm": "TPM",
    "rpd": "RPD",
    "tpd": "TPD",
    "itpm": "ITPM",
    "otpm": "OTPM",
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


def build_body(data: dict, old: dict[str, dict] | None, new: dict[str, dict], today: str) -> str:
    models = data["models"]
    n_models = len(models)
    n_providers = len({m["provider"] for m in models})

    lines = [
        f"## Weekly LLM Rate Limits Summary - {today}",
        "",
        f"Tracking **{n_models} models** across **{n_providers} providers**.",
        f"Data: [{SITE_URL}]({SITE_URL}) | [Raw JSON]({CDN_BASE}/data/rate-limits.json)",
        "",
    ]

    if old is None:
        lines += ["_Not enough history to show weekly changes yet._", ""]
    else:
        changes: list[dict] = []
        added: list[str] = []
        removed: list[str] = []

        for model_id, new_m in new.items():
            if model_id not in old:
                added.append(f"**{new_m['provider']}** {new_m['model_name']}")
                continue
            old_m = old[model_id]
            for tier_name, new_tier in new_m["limits"].items():
                old_tier = old_m["limits"].get(tier_name, {})
                for field in LIMIT_FIELDS:
                    old_val = old_tier.get(field)
                    new_val = new_tier.get(field)
                    if old_val != new_val and not (old_val is None and new_val is None):
                        changes.append(
                            {
                                "provider": new_m["provider"],
                                "model": new_m["model_name"],
                                "tier": tier_name,
                                "field": FIELD_LABELS.get(field, field.upper()),
                                "old": old_val,
                                "new": new_val,
                            }
                        )

        for model_id, old_m in old.items():
            if model_id not in new:
                removed.append(f"**{old_m['provider']}** {old_m['model_name']}")

        if not changes and not added and not removed:
            lines += ["### Changes this week", "", "_No rate limit changes detected this week._", ""]
        else:
            lines += ["### Changes this week", ""]
            if changes:
                lines += [
                    "| Provider | Model | Tier | Metric | Old | New |",
                    "|----------|-------|------|--------|-----|-----|",
                ]
                for c in changes:
                    lines.append(
                        f"| {c['provider']} | {c['model']} | {c['tier']} "
                        f"| {c['field']} | {fmt_num(c['old'])} | {fmt_num(c['new'])} |"
                    )
                lines.append("")
            if added:
                lines += ["**New models:**", ""]
                lines += [f"- {a}" for a in added]
                lines.append("")
            if removed:
                lines += ["**Removed models:**", ""]
                lines += [f"- {r}" for r in removed]
                lines.append("")

    # Provider snapshot table
    lines += ["### Current coverage", ""]
    by_provider: dict[str, list[dict]] = {}
    for m in models:
        by_provider.setdefault(m["provider"], []).append(m)

    lines += [
        "| Provider | Models | Tiers |",
        "|----------|--------|-------|",
    ]
    for provider, pmodels in sorted(by_provider.items()):
        tiers: set[str] = set()
        for pm in pmodels:
            tiers.update(pm["limits"].keys())
        lines.append(f"| {provider} | {len(pmodels)} | {', '.join(sorted(tiers))} |")

    lines += [
        "",
        "---",
        f"_Posted automatically every Monday after the weekly data update. "
        f"[Subscribe via Atom feed]({CDN_BASE}/data/feed.xml) or "
        f"[watch the repo]({REPO_URL}) for change alerts._",
    ]

    return "\n".join(lines)


def get_discussion_category_id(repo: str) -> str:
    owner, name = repo.split("/")
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        discussionCategories(first: 20) {
          nodes { id name }
        }
      }
    }
    """
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}",
         "-f", f"owner={owner}", "-f", f"name={name}"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    categories = data["data"]["repository"]["discussionCategories"]["nodes"]
    preferred = ("weekly summary", "announcements", "general")
    for pref in preferred:
        for cat in categories:
            if cat["name"].lower() == pref:
                return cat["id"]
    if categories:
        return categories[0]["id"]
    print("No Discussions categories found. Enable Discussions on the repo first.", file=sys.stderr)
    sys.exit(1)


def get_repo_id(repo: str) -> str:
    owner, name = repo.split("/")
    query = "query($owner: String!, $name: String!) { repository(owner: $owner, name: $name) { id } }"
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}",
         "-f", f"owner={owner}", "-f", f"name={name}"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)["data"]["repository"]["id"]


def create_discussion(repo_id: str, category_id: str, title: str, body: str) -> None:
    mutation = """
    mutation($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {
        repositoryId: $repoId,
        categoryId: $categoryId,
        title: $title,
        body: $body
      }) {
        discussion { url }
      }
    }
    """
    result = subprocess.run(
        ["gh", "api", "graphql",
         "-f", f"query={mutation}",
         "-f", f"repoId={repo_id}",
         "-f", f"categoryId={category_id}",
         "-f", f"title={title}",
         "-f", f"body={body}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        print(f"Failed to create discussion: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    resp = json.loads(result.stdout)
    url = resp["data"]["createDiscussion"]["discussion"]["url"]
    print(f"Discussion created: {url}")


def main() -> None:
    repo = os.environ.get("REPO", "llerandi/llm-rate-limits-tracker")
    today = datetime.now(tz=timezone.utc).date().isoformat()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    snapshots = sorted(HISTORY_DIR.glob("*.json"))

    new_snap = load_snapshot(snapshots[-1]) if snapshots else {}
    old_snap: dict[str, dict] | None = None
    if len(snapshots) >= 2:
        old_snap = load_snapshot(list(itertools.pairwise(snapshots))[-1][0])

    title = f"Weekly LLM Rate Limits Summary - {today}"
    body = build_body(data, old_snap, new_snap, today)

    repo_id = get_repo_id(repo)
    category_id = get_discussion_category_id(repo)
    create_discussion(repo_id, category_id, title, body)


if __name__ == "__main__":
    main()
