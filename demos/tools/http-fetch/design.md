# Tool · `http-fetch`

Typed HTTP client with retry / backoff. The default network primitive other
tools and agents call when they need an external HTTP resource.

## Purpose

Make outbound HTTP calls with sensible defaults: timeouts, retries on
transient failures, redact-on-log for headers, response parsing into a
stable envelope. Anything more elaborate (auth, pagination) wraps this.

## Inputs

| Field          | Type                            | Required | Notes |
|----------------|---------------------------------|----------|-------|
| `url`          | string (https only by default)  | yes      | http allowed via flag |
| `method`       | enum: GET/POST/PUT/PATCH/DELETE | no, GET  |       |
| `headers`      | map[string]string               | no       | Authorization redacted in logs |
| `body`         | bytes \| json                   | no       | mime inferred |
| `timeout_ms`   | int                             | no, 10000|       |
| `max_retries`  | int                             | no, 3    | retries on 5xx + connection err |

## Outputs

| Field           | Type              | Notes |
|-----------------|-------------------|-------|
| `status`        | int               |       |
| `headers`       | map[string]string |       |
| `body`          | bytes             |       |
| `parsed`        | json \| null      | populated when content-type json |
| `latency_ms`    | int               |       |
| `attempt_count` | int               | retries used |

## Implementation kind

Python tool. (A Shell variant via `curl` is trivial; the Python flavor is
the canonical demo.)

## Dependencies

- `httpx` — async-capable HTTP client with sane defaults
- `tenacity` — retry / backoff
- Project-internal: `internal/api/responses.go` envelope shape (for parity)

## Side effects

Network egress. No filesystem. No state mutations.

## Failure modes

- Timeout → returns partial envelope with `status=0`, `error_kind="timeout"`
- DNS failure → `error_kind="dns"`
- TLS error → `error_kind="tls"`
- 4xx → returned as-is, **not** retried
- 5xx / connection-reset → retried up to `max_retries` with exponential backoff + jitter

## Why it's a good demo

It's the smallest tool that touches every important Railyard tool concern:
typed inputs/outputs, timeouts, retries, error envelopes, and credential
redaction. Every other tool inherits from it conceptually. Pairs naturally
with the `cost-ceiling` and `rate-limit` governors as a first-touch
end-to-end demo.
