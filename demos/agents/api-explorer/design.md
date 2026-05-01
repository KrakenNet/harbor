# Agent · `api-explorer`

Takes an OpenAPI spec or live endpoint and answers questions about it:
which endpoint to call, what payload, what to expect back.

## Purpose

The integrations companion. Used in `integration` setup flows and as a
helper for developers exploring third-party APIs. Pairs with
`http-fetch` for live exploration and `sql-writer` as a sister "ask
your system" agent.

## DSPy signature

```python
class ExploreAPI(dspy.Signature):
    spec: str = dspy.InputField(desc="OpenAPI doc, or 'live:base_url'")
    question: str = dspy.InputField()
    auth_context: str = dspy.InputField(
        desc="auth scheme + which credentials are available")
    endpoint: str = dspy.OutputField()
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = dspy.OutputField()
    request_body: dict = dspy.OutputField()
    expected_response_shape: dict = dspy.OutputField()
    confidence: float = dspy.OutputField()
```

## Recommended tools

- `http-fetch` — try a no-op call (HEAD, OPTIONS) to confirm reachability
- `json-jq` — extract response samples
- `vector-search` — retrieve prior calls against this API

## Recommended governors

- `tool-allowlist` — restrict to read-only HTTP verbs
- `cost-ceiling` — prevent accidental fan-out exploration
- `rate-limit` — honor the upstream API's published limits

## Demonstrations sketch

- "How do I list invoices?" against Stripe → GET /v1/invoices, with paging
- "Create a new contact" against HubSpot → POST /crm/v3/objects/contacts
- "What does the webhook for X look like?" → returns event schema only

## Why it's a good demo

Pairs naturally with the integrations primitive: an `api-explorer`
agent is what makes a fresh integration usable without reading docs.
The read-only governor configuration is the demo of "exploration
should never accidentally mutate."
