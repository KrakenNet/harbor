# Tool · `sql-query`

Read-only SQL query against a registered Postgres or SQLite datasource.
Parses the statement, rejects anything that isn't a `SELECT` (or a
`WITH ... SELECT`), runs it under a query-timeout, and returns rows in a
typed envelope.

## Purpose

Agents constantly need to look something up in a relational store —
revenue numbers, ticket counts, catalog rows. `sql-query` makes that a
first-class primitive without giving the agent a write capability.

## Inputs

| Field           | Type              | Required | Notes |
|-----------------|-------------------|----------|-------|
| `datasource`    | string            | yes      | references a registered credential |
| `sql`           | string            | yes      | parsed; must be read-only |
| `params`        | []any             | no       | bound positionally to `$1..$N` |
| `row_limit`     | int               | no, 1000 | enforced via `LIMIT` rewrite |
| `timeout_ms`    | int               | no, 5000 | statement timeout |

## Outputs

| Field         | Type              | Notes |
|---------------|-------------------|-------|
| `columns`     | []ColumnInfo      | name + inferred type |
| `rows`        | [][]any           | row-major |
| `row_count`   | int               | actual rows returned (post-limit) |
| `truncated`   | bool              | true if `row_limit` clipped result |
| `duration_ms` | int               |       |

## Implementation kind

Python tool (uses asyncpg / sqlite3). A Go-side variant is trivial; Python
is the canonical demo to keep parity with other read tools.

## Dependencies

- `asyncpg` / `sqlite3` — driver per datasource kind
- `sqlglot` — parses the statement to verify it's read-only
- `internal/credential/` — datasource credential resolution

## Side effects

Read-only network call to the datasource. No filesystem, no mutation.
Honors the datasource's own connection-pool limits.

## Failure modes

- Non-SELECT statement → rejected pre-execution, `error_kind="not_readonly"`
- Parse error → returned with parser diagnostics
- Statement timeout → cancelled, `error_kind="timeout"`
- Permission denied at the database level → surfaced as `error_kind="auth"`
- Result exceeds `row_limit` → silently truncated with `truncated=true`

## Why it's a good demo

It demonstrates Railyard's credential-resolution pattern, the read/write
split that good agent platforms enforce, and how typed-row results flow
back into downstream tool calls. Pairs naturally with `vector-search` (for
hybrid retrieval) and the `schema-validator` governor (which can verify
result shape against a declared schema).
