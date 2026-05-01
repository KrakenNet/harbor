# Tool · `embed-text`

Single-text embedding helper. Takes a string (or short batch), returns the
embedding vector(s) using a configured embedding model.

## Purpose

The smallest possible primitive for "turn this text into a vector." Other
tools (`vector-search`, knowledge ingestion flows) call it. Exists as a
standalone tool so embedding-model choice is centralized and swappable.

## Inputs

| Field         | Type     | Required | Notes |
|---------------|----------|----------|-------|
| `text`        | string \| []string | yes | batch up to 64 |
| `model`       | string   | no       | defaults to tenant's configured model |
| `normalize`   | bool     | no, true | L2-normalize the result vector |
| `truncate`    | bool     | no, true | truncate to model's max input tokens |

## Outputs

| Field        | Type        | Notes |
|--------------|-------------|-------|
| `vectors`    | [][]float32 | one per input |
| `model`      | string      | resolved model name |
| `dim`        | int         | vector dimensionality |
| `input_tokens`| int        | summed across batch |

## Implementation kind

Python tool. Provider-agnostic: dispatches to OpenAI / local / Bedrock per
the resolved model's provider.

## Dependencies

- `internal/credential/` — API key resolution
- LLM-model registry (per `0010-agent_schema.sql` and the LLM-model skill)
- Provider SDKs (OpenAI / etc.) loaded lazily

## Side effects

One outbound API call per resolved provider. No filesystem, no DB writes.

## Failure modes

- Input over model limit, `truncate=false` → `error_kind="too_long"`
- Provider rate limit → surfaced as `error_kind="rate_limit"`, retried by caller
- Model not configured for tenant → `error_kind="model_unknown"`
- Empty string → returns zero vector with a warning, not an error

## Why it's a good demo

Embedding is the connective tissue between text and Railyard's vector
store. Showing it as its own tool — rather than buried inside RAG —
demonstrates the platform's stance that every primitive is observable,
substitutable, and governable. Pairs with `vector-search`, `token-count`,
and the `cost-ceiling` governor.
