# hanzo-tools-llm

Models through Hanzo as MCP tools. Every call goes to `api.hanzo.ai` with the
Hanzo credential `hanzo_tools.core.HanzoCloud` resolves (`HANZO_API_KEY`, then
`~/.hanzo/config.json`, then `hanzo auth token`).

## Tools

- `llm` — action-routed, default action `query`:
  - `query`: `POST /v1/chat/completions`. `model` defaults to `enso-auto`;
    `"auto"` lets Enso pick across the models your org can serve. `max_cost`
    (USD per 1,000 tokens) and `max_latency_ms` ride as `X-Max-Cost` and
    `X-Max-Latency-Ms`; `fallback: true` sends `X-Hanzo-Fallback: allow`, so the
    plan's fallback answers instead of a refusal. Returns `{id, model, content,
    finish_reason, usage, served, paid_by, usage_state, usage_class, fallback,
    fallback_reason}`, the last six read from the `X-Hanzo-*` headers (`None` when
    absent).
  - `models`: `GET /v1/models`, one row per model with family, class, what it
    supports, the catalog's per-million prices and `variable`; `search`, `class`
    (`premium`, `ours`, `free`), `family` and `capability` narrow it.
  - `limits`: `GET /v1/ai/limits` — plan, state, each class's percent, who pays,
    resets, paused models and the actions. Shares only, never an amount.
  - `feedback`: `POST /v1/ai/feedback` with `request_id`, `signal` and, for
    `signal: rating`, a `rating` of 1 to 3.
- `kai_decide` — `POST /v1/decisions`: a `state` (text, object or array) and
  named typed `questions` (`choice`, `score`, `noul`), answered by Kai with
  calibrated probabilities; `model` is `kai`, a trained `kai-<id>` or
  `typesafe/jev-1.13`.

A plan refusal (402 or 429 with `plan_allowance_used`, `paid_plan_required`,
`free_plan_cap`, `model_cap`, `usage_cap_exceeded` or `insufficient_balance`) is
an error whose `code` is that refusal, with `class`, `model`, `fallback`,
`window`, `resets_at` and `actions`; `hanzoai.usage` reads it.

## Install

```bash
pip install hanzo-tools-llm
```

`hanzo-mcp` loads both tools through the `hanzo.tools` entry point.
