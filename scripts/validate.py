"""
Validate data/rate-limits.json against the expected schema.

Run manually or via CI. Exits with code 1 if validation fails.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "rate-limits.json"

REQUIRED_TOP = {"last_updated", "schema_version", "models"}
REQUIRED_MODEL = {"provider", "provider_id", "model_id", "model_name", "docs_url", "limits"}
REQUIRED_TIER = {"rpm", "tpm", "rpd", "tpd"}
NUMBER_OR_NULL = (int, float, type(None))

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def validate_tier(tier_name: str, tier: object, path: str) -> None:
    if not isinstance(tier, dict):
        err(f"{path}: tier must be an object")
        return
    if "spend_threshold_usd" not in tier:
        err(f"{path}: missing spend_threshold_usd")
    for field in REQUIRED_TIER:
        if field not in tier:
            err(f"{path}: missing field '{field}'")
        elif not isinstance(tier[field], NUMBER_OR_NULL):
            err(f"{path}.{field}: must be a number or null, got {type(tier[field]).__name__}")
    if "notes" in tier and tier["notes"] is not None and not isinstance(tier["notes"], str):
        err(f"{path}.notes: must be a string or null")


def validate_model(m: object, idx: int) -> None:
    path = f"models[{idx}]"
    if not isinstance(m, dict):
        err(f"{path}: must be an object")
        return
    for field in REQUIRED_MODEL:
        if field not in m:
            err(f"{path}: missing required field '{field}'")
    provider = m.get("provider", "")
    model_id = m.get("model_id", "")
    if not isinstance(provider, str) or not provider:
        err(f"{path}.provider: must be a non-empty string")
    if not isinstance(model_id, str) or not model_id:
        err(f"{path}.model_id: must be a non-empty string")
    limits = m.get("limits")
    if not isinstance(limits, dict) or not limits:
        err(f"{path}.limits: must be a non-empty object")
        return
    for tier_name, tier in limits.items():
        validate_tier(tier_name, tier, f"{path}.limits.{tier_name}")


def main() -> None:
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("ERROR: root must be a JSON object", file=sys.stderr)
        sys.exit(1)

    for field in REQUIRED_TOP:
        if field not in data:
            err(f"Missing top-level field: '{field}'")

    models = data.get("models", [])
    if not isinstance(models, list):
        err("'models' must be an array")
    else:
        for i, m in enumerate(models):
            validate_model(m, i)

    if errors:
        print(f"Validation failed: {len(errors)} error(s)", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {len(models)} models validated.")


if __name__ == "__main__":
    main()
