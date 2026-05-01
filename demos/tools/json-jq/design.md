# Tool · `json-jq`

jq-style query over a JSON document. Useful when an agent has a big JSON
blob and only needs a slice of it.

## Purpose

LLMs are bad at navigating large JSON. Asking them to extract `data.items[].id`
from a 200KB response wastes tokens and goes wrong on nesting. `json-jq`
does the projection deterministically and returns just what was asked
for.

## Inputs

| Field        | Type            | Required | Notes |
|--------------|-----------------|----------|-------|
| `data`       | json \| string  | yes      | string is parsed first |
| `query`      | string          | yes      | jq expression |
| `multiple`   | bool            | no, true | return all matches vs. just first |
| `raw_output` | bool            | no, false| strip JSON quoting from string results |

## Outputs

| Field        | Type     | Notes |
|--------------|----------|-------|
| `result`     | any      | scalar / array / object depending on query |
| `match_count`| int      | number of matches before slicing |
| `query_ok`   | bool     | false on parse error |

## Implementation kind

Python tool. Uses `pyjq` (CFFI binding to libjq) so the semantics match
canonical jq exactly.

## Dependencies

- `pyjq` — jq language bindings
- libjq system library

## Side effects

Pure function. No network, no filesystem.

## Failure modes

- Invalid JSON input → `error_kind="parse"` with byte offset
- Invalid jq expression → `error_kind="query"` with column hint
- Query returns nothing → `match_count=0`, `result=null`, not an error
- Result exceeds size cap → truncated with a warning

## Why it's a good demo

It's the canonical "save tokens by computing instead of prompting" tool
and the example most useful for showing why a real agent platform should
ship deterministic transforms alongside LLM calls. Pairs with
`http-fetch` (slice an API response) and with the `schema-validator`
governor (validate the slice).
