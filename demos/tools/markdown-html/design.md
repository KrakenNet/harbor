# Tool · `markdown-html`

Convert in either direction: markdown → HTML for rendering, HTML →
markdown for ingestion. Two thin operations under one tool.

## Purpose

Agents produce markdown; UIs render HTML; ingested content arrives as
HTML. This tool collapses both translations into one primitive so callers
don't depend on a specific markdown flavor.

## Inputs

| Field        | Type    | Required | Notes |
|--------------|---------|----------|-------|
| `direction`  | enum    | yes      | md_to_html / html_to_md |
| `text`       | string  | yes      | source content |
| `flavor`     | enum    | no       | gfm (default) / commonmark |
| `sanitize`   | bool    | no, true | md_to_html: strip script/iframe |
| `keep_tables`| bool    | no, true |       |

## Outputs

| Field        | Type    | Notes |
|--------------|---------|-------|
| `output`     | string  | converted body |
| `title`      | string  | extracted h1 if present |
| `links`      | []string | absolute URLs found |
| `warnings`   | []string | e.g. dropped raw HTML during sanitize |

## Implementation kind

Python tool. `markdown-it-py` (with the GFM plugin) for md→html,
`markdownify` + `bleach` for html→md.

## Dependencies

- `markdown-it-py` — CommonMark/GFM parsing
- `markdownify` — HTML → markdown
- `bleach` — HTML sanitization

## Side effects

Pure. No network, no filesystem.

## Failure modes

- Malformed HTML → best-effort parse with `warnings` populated
- Disallowed tag in sanitize mode → stripped silently, recorded in `warnings`
- Empty input → returns empty `output`, not an error
- Conversion produces lossy output (e.g. complex inline styles) → noted in `warnings`

## Why it's a good demo

It demonstrates the platform's "small bidirectional transforms as one
tool" pattern, mirroring `csv-rw`. Pairs with `web-scrape` (which already
emits markdown via this conversion path), `pdf-extract`, and the
`doc-ingest-rag` workflow.
