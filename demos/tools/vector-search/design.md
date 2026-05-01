# Tool · `vector-search`

pgvector similarity search over a chosen embedding column. Given a query
vector (or a query string the tool will embed), returns the top-K nearest
rows along with cosine/L2 distances.

## Purpose

The retrieval primitive every RAG agent leans on. Decoupled from any
specific knowledge base so it can search documents, memories, code chunks,
or arbitrary embedded rows.

## Inputs

| Field          | Type      | Required | Notes |
|----------------|-----------|----------|-------|
| `table`        | string    | yes      | must be in the tool's allowlist |
| `vector_column`| string    | yes      | the pgvector column name |
| `query`        | string \| []float | yes | string is embedded via `embed-text` |
| `top_k`        | int       | no, 10   | hard cap 200 |
| `metric`       | enum      | no       | cosine / l2 / inner (default cosine) |
| `filter_sql`   | string    | no       | optional `WHERE` clause, parameterized |

## Outputs

| Field      | Type             | Notes |
|------------|------------------|-------|
| `hits`     | []SearchHit      | rows + distance + payload |
| `latency_ms`| int             |       |
| `embed_ms` | int              | only if input was a string |

## Implementation kind

Python tool. Calls `embed-text` internally if the query is a string, then
issues an `ORDER BY <col> <op> $1 LIMIT k` against Postgres.

## Dependencies

- `asyncpg` — Postgres driver
- `pgvector` — distance operators
- Sibling tool `embed-text` — for string queries
- `internal/rag/` and `0096-rag_schema.sql` — table conventions

## Side effects

Read-only Postgres query. May trigger one embedding call.

## Failure modes

- Table not in allowlist → rejected pre-query, `error_kind="not_allowed"`
- Vector dimension mismatch → surfaced from Postgres as `error_kind="dim_mismatch"`
- `filter_sql` parse error → rejected with parser diagnostics
- No hits → returns empty `hits` array, not an error
- Embedding failure (string query) → returned as `error_kind="embed_failed"`

## Why it's a good demo

It shows Railyard's pgvector-native retrieval working without bolting on
an external vector store. Pairs naturally with `embed-text`, with the
`fact-half-life` governor (filtering stale rows), and with knowledge
catalog items like `provenance-graph` and `codebase-semantic-index`.
