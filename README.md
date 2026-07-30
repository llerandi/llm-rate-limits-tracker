# LLM Rate Limits Tracker

[![CI](https://img.shields.io/github/actions/workflow/status/llerandi/llm-rate-limits-tracker/ci.yaml?label=CI&logo=github)](https://github.com/llerandi/llm-rate-limits-tracker/actions/workflows/ci.yaml)
[![License](https://img.shields.io/github/license/llerandi/llm-rate-limits-tracker)](LICENSE)
[![Stars](https://img.shields.io/github/stars/llerandi/llm-rate-limits-tracker?style=social)](https://github.com/llerandi/llm-rate-limits-tracker/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/llerandi/llm-rate-limits-tracker)](https://github.com/llerandi/llm-rate-limits-tracker/commits/main)
[![Updated weekly](https://img.shields.io/badge/last--updated-2026--07--29-brightgreen)](https://github.com/llerandi/llm-rate-limits-tracker/actions/workflows/update.yaml)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue?logo=python)](https://www.python.org/)
[![Live site](https://img.shields.io/badge/live%20site-GitHub%20Pages-0969da)](https://llerandi.github.io/llm-rate-limits-tracker/)

Weekly-updated API rate limits for all major LLM providers. RPM, TPM, RPD by tier - structured as JSON so you can consume it programmatically. No API key required.

**Live site:** [llerandi.github.io/llm-rate-limits-tracker](https://llerandi.github.io/llm-rate-limits-tracker/) - filterable by provider and tier, sortable.

> [!TIP]
> Looking for token prices instead? See the sister project: [LLM Price Tracker](https://github.com/llerandi/llm-price-tracker)

---

## Providers covered

| Provider | Models | Tiers |
|---|---|---|
| OpenAI | GPT-5.5, GPT-4.5 nano | Tier 1-5 |
| Anthropic | Claude Opus 4.8, Sonnet 5, Haiku 4.5 | Tier 1-4 |
| Google | Gemini 3.1 Pro, Flash-Lite | Pay-as-you-go |
| Mistral | Mistral Large, Medium | Console-only |
| Cohere | Command R+ | Trial, Production |
| Groq | Llama 4 Scout, Maverick | Free, Developer |
| Together AI | Various | Dynamic |
| Fireworks AI | Various | Free, Paid |
| DeepSeek | DeepSeek R2 | Dynamic |
| xAI | Grok 3 | Tier 0-4 |
| Perplexity | Sonar, Sonar Pro | Tier 0, 1, 3 |
| Amazon Bedrock | Various | On-demand, Provisioned |

Providers that don't publish numerical limits appear with `null` values and a note linking to their docs.

---

## API

Static JSON served via jsDelivr CDN. CORS enabled, no auth.

| Endpoint | Description |
|---|---|
| [`/data/rate-limits.json`](https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main/data/rate-limits.json) | All providers and models |
| `/data/providers/{provider_id}.json` | Single provider (e.g. `anthropic`, `openai`, `groq`) |
| `/data/history/YYYY-MM-DD.json` | Weekly snapshot |
| `/data/badges/{provider_id}/{model_id}/{tier}/rpm.json` | shields.io endpoint badge (also `tpm`, `rpd`) |

### Embeddable badges

Use any badge file as a [shields.io endpoint](https://shields.io/badges/endpoint-badge):

```
https://img.shields.io/endpoint?url=https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main/data/badges/openai/gpt-5.5/tier-1/rpm.json
```

Replace `openai`, `gpt-5.5`, `tier-1`, and `rpm` with your target provider, model, tier, and metric (`rpm`, `tpm`, or `rpd`). Badge values update weekly.

**Base URL:** `https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main`

### Schema

Each model entry in `models[]`:

| Field | Type | Description |
|---|---|---|
| `provider` | string | Provider display name |
| `provider_id` | string | Provider slug used in per-provider endpoint |
| `model_id` | string | Unique model identifier |
| `model_name` | string | Human-readable name |
| `docs_url` | string | Link to provider rate limit docs |
| `limits` | object | Keys are tier names (e.g. `"free"`, `"tier-1"`) |

Each tier in `limits`:

| Field | Type | Description |
|---|---|---|
| `rpm` | int or null | Requests per minute |
| `tpm` | int or null | Tokens per minute |
| `itpm` | int or null | Input tokens/min (Anthropic only) |
| `otpm` | int or null | Output tokens/min (Anthropic only) |
| `rpd` | int or null | Requests per day |
| `tpd` | int or null | Tokens per day |
| `spend_threshold_usd` | int or null | Minimum spend to unlock this tier |
| `notes` | string or null | Caveats or link to source |

`null` means not published. Check `notes` for context.

### Example

```python
import urllib.request, json

url = "https://cdn.jsdelivr.net/gh/llerandi/llm-rate-limits-tracker@main/data/rate-limits.json"
with urllib.request.urlopen(url) as r:
    data = json.loads(r.read())

# Print RPM for every model and tier
for m in data["models"]:
    for tier, limits in m["limits"].items():
        print(f"{m['provider']:15} {m['model_name']:25} {tier:15} RPM={limits['rpm']}")
```

---

## Client Libraries

Installable wrappers around the jsDelivr JSON API. Both are zero-dependency and read-only.

### JavaScript / TypeScript (Node >= 18 and browsers)

```bash
npm install llm-rate-limits-tracker
```

```js
const { fetchRateLimits, getModel, getProvider } = require("llm-rate-limits-tracker");

const { models } = await fetchRateLimits();
const model = await getModel("openai/gpt-5.5");
const { models: anthropicModels } = await getProvider("anthropic");
```

Source: [`packages/npm/`](packages/npm/)

### Python (>= 3.9, no dependencies)

```bash
pip install llm-rate-limits-tracker
```

```python
from llm_rate_limits_tracker import fetch_rate_limits, get_model, get_provider

data = fetch_rate_limits()
model = get_model("openai/gpt-5.5")
anthropic = get_provider("anthropic")
```

Source: [`packages/python/`](packages/python/)

---

## Contributing

If you spot stale data, open an issue or PR with the corrected values and a link to the provider's docs page.

1. Edit `data/rate-limits.json`
2. Run `python scripts/validate.py`
3. Update `last_updated` at the top of the JSON

---

## How it works

A GitHub Actions workflow runs every Monday at 07:00 UTC. It validates the JSON, writes a weekly snapshot, generates per-provider files, and opens a GitHub Issue if any limits changed.

To trigger a manual update: Actions -> Weekly Rate Limit Update -> Run workflow.

---

## Roadmap

### Phase 1 - Foundation

- [x] Nested JSON schema (`provider > model > tiers > limits`)
- [x] Initial data: 12 providers, 19 models
- [x] Validation and CI pipeline (ruff + schema check)
- [x] Weekly update workflow with auto issue on changes
- [x] Weekly snapshots and per-provider endpoint files

### Phase 2 - Interface

- [x] GitHub Pages site with provider/tier filters, sort, dark mode
- [x] JSON API via jsDelivr CDN with CORS
- [x] SEO: Open Graph, JSON-LD structured data, sitemap, Twitter card

### Phase 3 - CDN and Automation

- [x] Auto-purge jsDelivr CDN after every weekly update
- [x] Embeddable badges: RPM, TPM and RPD per model/tier (shields.io endpoint)
- [x] Shareable URLs: query params preserve active filters

### Phase 4 - Expand Coverage

- [ ] More models per provider
- [ ] Free-tier providers: Cerebras, SambaNova, Nvidia NIM
- [ ] Per-region limits for Amazon Bedrock and Azure OpenAI

### Phase 5 - Community

- [ ] RSS/Atom feed of rate limit changes
- [ ] Weekly summary posted to GitHub Discussions
- [x] npm / PyPI package wrapping the JSON endpoint

### Phase 6 - Insights

- [ ] Rate limit history chart on the live site
- [ ] Provider comparison view: side-by-side tier diff
- [x] Calculator: enter RPM/TPM/RPD requirements and see which tiers cover them

---

## License

[MIT](LICENSE)
