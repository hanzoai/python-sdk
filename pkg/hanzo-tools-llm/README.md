# hanzo-tools-llm

Models through Hanzo as MCP tools. Every call goes to `api.hanzo.ai` with the
Hanzo credential `hanzo_tools.core.HanzoCloud` resolves (`HANZO_API_KEY`, then
`~/.hanzo/config.json`, then `hanzo auth token`).

## Tools

- `llm` — action-routed, default action `query`:
  - `query`: `POST /v1/chat/completions`. `model` defaults to `enso-auto`;
    `"auto"` lets Enso pick across the models your org can serve. `max_cost`
    (USD per 1,000 tokens) and `max_latency_ms` ride as `X-Max-Cost` and
    `X-Max-Latency-Ms`. Returns `{id, model, content, finish_reason, usage}`.
  - `models`: `GET /v1/models`, one row per model with family, class and the
    catalog's per-million prices; `family` narrows it (`enso`, `kai`).
  - `feedback`: `POST /v1/ai/feedback` with `request_id`, `signal` and, for
    `signal: rating`, a `rating` of 1 to 3.
- `kai_decide` — `POST /v1/decisions`: a `state` (text, object or array) and
  named typed `questions` (`choice`, `score`, `noul`), answered by Kai with
  calibrated probabilities.

## Install

```bash
pip install hanzo-tools-llm
```

`hanzo-mcp` loads both tools through the `hanzo.tools` entry point.
