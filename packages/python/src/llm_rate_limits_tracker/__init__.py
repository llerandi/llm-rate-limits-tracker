"""
llm-rate-limits-tracker: weekly-updated LLM API rate limits.

Wraps the llm-rate-limits-tracker JSON API served via jsDelivr CDN.
No dependencies - uses the Python standard library only (urllib.request).

Usage::

    from llm_rate_limits_tracker import fetch_rate_limits, get_model, get_provider

    data = fetch_rate_limits()
    for m in data["models"]:
        for tier, limits in m["limits"].items():
            print(m["provider"], m["model_name"], tier, limits["rpm"])

    model = get_model("openai/gpt-5.5")
    anthropic = get_provider("anthropic")
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

__all__ = ["fetch_rate_limits", "get_model", "get_provider", "BASE_URL"]

BASE_URL = "https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main"


def _get(url: str) -> Any:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())


def fetch_rate_limits() -> dict[str, Any]:
    """Fetch the full rate limits dataset (all providers and models).

    Returns a dict with keys:

    - ``last_updated`` (str): ISO date of the last weekly update.
    - ``models`` (list[dict]): all models across all providers.

    Each model dict contains: ``provider``, ``provider_id``, ``model_id``,
    ``model_name``, ``docs_url``, ``notes``, and ``limits`` (a dict keyed
    by tier name, each containing ``rpm``, ``tpm``, ``rpd``, ``tpd``,
    ``spend_threshold_usd``, and optionally ``itpm``/``otpm`` for Anthropic).
    """
    return _get(f"{BASE_URL}/data/rate-limits.json")


def get_model(model_id: str) -> dict[str, Any] | None:
    """Return a single model by its identifier, or ``None`` if not found.

    Args:
        model_id: The model identifier, e.g. ``"openai/gpt-5.5"``,
            ``"anthropic/claude-sonnet-5"``, or ``"groq/llama-4-scout"``.
    """
    data = fetch_rate_limits()
    for m in data["models"]:
        if m["model_id"] == model_id:
            return m
    return None


def get_provider(provider_slug: str) -> dict[str, Any]:
    """Fetch all models for a single provider.

    Args:
        provider_slug: Lowercase hyphenated provider name, e.g. ``"anthropic"``,
            ``"openai"``, ``"google"``, ``"groq"``, ``"mistral"``, ``"cohere"``,
            ``"together-ai"``, ``"fireworks-ai"``, ``"deepseek"``,
            ``"xai"``, ``"perplexity"``, ``"amazon-bedrock"``.

    Returns a dict with ``last_updated``, ``provider``, ``provider_id``,
    and ``models``.

    Raises:
        urllib.error.HTTPError: If the provider slug is not recognised.
    """
    return _get(f"{BASE_URL}/data/providers/{provider_slug}.json")
