"""
Generate shields.io endpoint JSON badge files for each model/tier/metric.

Output structure:
  data/badges/{provider_id}/{model_id}/{tier_slug}/rpm.json
  data/badges/{provider_id}/{model_id}/{tier_slug}/tpm.json
  data/badges/{provider_id}/{model_id}/{tier_slug}/rpd.json

Embed in a README or docs page:
  https://img.shields.io/endpoint?url=https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main/data/badges/{provider_id}/{model_id}/{tier_slug}/rpm.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "rate-limits.json"
BADGES_DIR = ROOT / "data" / "badges"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def fmt_num(v: int | None) -> str:
    if v is None:
        return "N/A"
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.0f}K"
    return str(v)


def make_badge(label: str, value: int | None) -> dict:
    if value is None:
        return {"schemaVersion": 1, "label": label, "message": "N/A", "color": "inactive"}
    return {"schemaVersion": 1, "label": label, "message": fmt_num(value), "color": "blue"}


def main() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    total = 0

    for m in data["models"]:
        pid = m["provider_id"]
        mid = m["model_id"]
        for tier_name, tier in m["limits"].items():
            tier_slug = slugify(tier_name)
            badge_dir = BADGES_DIR / pid / mid / tier_slug
            badge_dir.mkdir(parents=True, exist_ok=True)

            # Effective TPM: prefer tpm, fall back to itpm (Anthropic uses itpm/otpm)
            effective_tpm = tier.get("tpm") or tier.get("itpm")

            badges = {
                "rpm": make_badge("RPM", tier.get("rpm")),
                "tpm": make_badge("TPM", effective_tpm),
                "rpd": make_badge("RPD", tier.get("rpd")),
            }

            for metric, badge in badges.items():
                (badge_dir / f"{metric}.json").write_text(
                    json.dumps(badge, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                total += 1

    print(f"Generated {total} badge files in {BADGES_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
