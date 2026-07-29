"""
Generate per-provider JSON files in data/providers/{provider_id}.json.

Each file contains only the models for that provider, making it easy
to fetch a single provider's limits without downloading the full dataset.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "rate-limits.json"
PROVIDERS_DIR = ROOT / "data" / "providers"


def main() -> None:
    PROVIDERS_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    by_provider: dict[str, list[dict]] = {}
    for m in data["models"]:
        pid = m["provider_id"]
        by_provider.setdefault(pid, []).append(m)

    # Remove stale provider files
    expected = {f"{pid}.json" for pid in by_provider}
    for f in PROVIDERS_DIR.glob("*.json"):
        if f.name not in expected:
            f.unlink()

    for provider_id, models in by_provider.items():
        out = PROVIDERS_DIR / f"{provider_id}.json"
        payload = {
            "last_updated": data["last_updated"],
            "provider": models[0]["provider"],
            "provider_id": provider_id,
            "models": models,
        }
        out.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"Generated {len(by_provider)} provider files.")


if __name__ == "__main__":
    main()
