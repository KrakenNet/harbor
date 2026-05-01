# Tool · `csv-rw` (`csv-read` / `csv-write`)

Read and write CSV (and TSV) files with header inference, type coercion,
and streaming for large files. Two operations, one tool group.

## Purpose

CSV is still the lingua franca of data exchange. Agents need to load a
spreadsheet, transform it, and emit a new one. This tool handles both
sides without leaking pandas-isms into every caller.

## Inputs

### `csv-read`

| Field         | Type    | Required | Notes |
|---------------|---------|----------|-------|
| `source`      | url \| bytes \| storage_ref | yes | one-of |
| `delimiter`   | string  | no, ","  | "\t" for TSV |
| `has_header`  | bool    | no, true |       |
| `infer_types` | bool    | no, true | int/float/bool/date detection |
| `max_rows`    | int     | no, 100000 | hard cap |

### `csv-write`

| Field         | Type    | Required | Notes |
|---------------|---------|----------|-------|
| `rows`        | [][]any | yes      | row-major |
| `header`      | []string| no       | omitted = no header row |
| `delimiter`   | string  | no, ","  |       |
| `dest`        | storage_ref | yes  | sandboxed write path |

## Outputs

### `csv-read`

| Field      | Type        | Notes |
|------------|-------------|-------|
| `header`   | []string    | empty if `has_header=false` |
| `rows`     | [][]any     | typed if `infer_types=true` |
| `row_count`| int         |       |
| `truncated`| bool        | true if `max_rows` clipped |

### `csv-write`

| Field      | Type        | Notes |
|------------|-------------|-------|
| `dest`     | storage_ref | echo of input |
| `bytes`    | int         | total written |
| `row_count`| int         |       |

## Implementation kind

Python tool. Uses `csv` module for streaming and a thin type-inference
layer; avoids pandas to keep the dependency surface small.

## Dependencies

- Python `csv` — streaming I/O
- `dateutil` — flexible date parsing on infer
- `internal/credential/` — only when reading/writing remote storage refs

## Side effects

`csv-read` is read-only. `csv-write` writes inside the sandbox or to a
configured object store; never to arbitrary filesystem paths.

## Failure modes

- Inconsistent column count per row → `error_kind="ragged"` with offending row index
- Type inference disagrees within a column → falls back to string for that column with a warning
- Source larger than `max_rows` → silently truncated, `truncated=true`
- Write path outside sandbox → rejected pre-write

## Why it's a good demo

It demonstrates the "read primitive + write primitive in one tool group"
pattern and the streaming/truncation discipline that protects agents from
loading 10GB into context. Pairs with `sql-query` (CSV → table loads) and
with the `data-quality-sweep` workflow.
