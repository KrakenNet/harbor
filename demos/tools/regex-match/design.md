# Tool · `regex-match`

Run a regular expression against a body of text and return matches with
groups and offsets. The boring, deterministic complement to LLM-based
extraction.

## Purpose

Some extraction problems don't need a model. Phone numbers, version
strings, ticket IDs — a regex is faster, cheaper, and exact. Exposing it
as a first-class tool lets agents (and the `extractor` agent) reach for
the right tool for the job.

## Inputs

| Field        | Type    | Required | Notes |
|--------------|---------|----------|-------|
| `text`       | string  | yes      |       |
| `pattern`    | string  | yes      | RE2 syntax by default |
| `flags`      | string  | no       | combinations of `i` (ignore case), `m` (multiline), `s` (dotall) |
| `find_all`   | bool    | no, true | else first match only |
| `max_matches`| int     | no, 1000 | hard cap |

## Outputs

| Field         | Type      | Notes |
|---------------|-----------|-------|
| `matches`     | []Match   | full text + groups + start/end offsets |
| `match_count` | int       |       |
| `truncated`   | bool      | true if `max_matches` capped result |

## Implementation kind

Python tool. Uses Go's RE2-equivalent (`google-re2` Python bindings) by
default to avoid catastrophic backtracking; opt-in to `re` for full PCRE.

## Dependencies

- `google-re2` — linear-time regex engine
- Standard `re` — opt-in for backreferences and lookaround

## Side effects

Pure. No network, no filesystem.

## Failure modes

- Invalid pattern → `error_kind="pattern"` with column
- Pattern would catastrophically backtrack (PCRE mode) → killed by timeout, `error_kind="regex_timeout"`
- No matches → `matches=[]`, `match_count=0`, not an error
- Match capped → `truncated=true`

## Why it's a good demo

It's the cheapest extraction primitive and the one that prevents agents
from using a 70B-param model to find an email address. Pairs with the
`extractor` agent as the "try regex first" fast path and with
`json-jq` as a sibling deterministic transform.
