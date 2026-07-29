"use strict";

/**
 * llm-rate-limits-tracker
 * Weekly-updated LLM API rate limits, served via jsDelivr CDN.
 * No dependencies - uses the global fetch (Node >= 18, all modern browsers).
 *
 * @example
 * const { fetchRateLimits, getModel, getProvider } = require("llm-rate-limits-tracker");
 *
 * const { models } = await fetchRateLimits();
 * const model = await getModel("openai/gpt-5.5");
 * const { models: anthropicModels } = await getProvider("anthropic");
 */

const BASE_URL =
  "https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main";

async function _get(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`llm-rate-limits-tracker: HTTP ${res.status} for ${url}`);
  return res.json();
}

/**
 * Fetch the full rate limits dataset (all providers and models).
 * @returns {Promise<{last_updated: string, models: object[]}>}
 */
async function fetchRateLimits() {
  return _get(`${BASE_URL}/data/rate-limits.json`);
}

/**
 * Fetch a single model by its identifier.
 * @param {string} modelId - e.g. "openai/gpt-5.5", "anthropic/claude-sonnet-5"
 * @returns {Promise<object|null>} The model object, or null if not found.
 */
async function getModel(modelId) {
  const data = await fetchRateLimits();
  return data.models.find((m) => m.model_id === modelId) ?? null;
}

/**
 * Fetch all models for a single provider.
 * @param {string} providerSlug - lowercase hyphenated slug, e.g. "anthropic",
 *   "openai", "google", "groq", "together-ai", "fireworks-ai", "amazon-bedrock"
 * @returns {Promise<{last_updated: string, provider: string, provider_id: string, models: object[]}>}
 */
async function getProvider(providerSlug) {
  return _get(`${BASE_URL}/data/providers/${providerSlug}.json`);
}

module.exports = { fetchRateLimits, getModel, getProvider, BASE_URL };
