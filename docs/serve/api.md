# HTTP API

Harbor's HTTP surface lives under `/v1/*`, mounted on a FastAPI app
constructed by `harbor.serve.api:create_app`. Every route runs through
the auth provider chain (profile-pinned), then the route-level capability
gate, then the handler. Authentication and capability decisions emit
audit events on every request.

The route surface is intentionally small: 5 POC routes plus the post-Phase-2
counterfactual + artifacts + listing routes. The OpenAPI 3.1 spec is the
canonical contract; see `docs/reference/openapi.json`.

## Topics

- TODO: route-by-route reference (POST /v1/runs, GET /v1/runs/{id}, ...).
- TODO: error-envelope shape (FastAPI default + Harbor `_redact_error`).
- TODO: capability-gate matrix (profile × route).
- TODO: rate-limit headers + retry-after semantics.
- TODO: OpenAPI client SDK generation (Python + TypeScript).
