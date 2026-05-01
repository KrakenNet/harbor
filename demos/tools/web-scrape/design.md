# Tool · `web-scrape`

Fetch a URL, run it through a readability extractor, return clean
markdown plus structured metadata. The "give me the actual article, not
the boilerplate" tool.

## Purpose

LLMs do a lot worse with raw HTML than with clean markdown. `web-scrape`
collapses fetch + readability + markdown conversion into one call so
agents can read web content without burning tokens on navigation chrome.

## Inputs

| Field         | Type    | Required | Notes |
|---------------|---------|----------|-------|
| `url`         | string  | yes      | https only by default |
| `mode`        | enum    | no       | readability / raw / metadata-only |
| `timeout_ms`  | int     | no, 15000|       |
| `render_js`   | bool    | no, false| if true, uses a headless browser path |

## Outputs

| Field         | Type              | Notes |
|---------------|-------------------|-------|
| `markdown`    | string            | empty in metadata-only mode |
| `title`       | string            |       |
| `byline`      | string            | best-effort author/site |
| `published_at`| string \| null    | ISO 8601 if extractable |
| `links`       | []string          | absolute URLs found in body |
| `lang`        | string            | language code |

## Implementation kind

Python tool. Uses `httpx` for fetch and `readability-lxml` +
`markdownify` for extraction. Optional Playwright path when JS rendering
is required.

## Dependencies

- `httpx` — fetch
- `readability-lxml` — boilerplate removal
- `markdownify` — HTML → markdown
- Optional `playwright` — JS rendering
- Sibling tool `http-fetch` — used in non-JS mode for retry semantics

## Side effects

Network egress. With `render_js=true`, spins up a short-lived headless
browser process. No filesystem writes.

## Failure modes

- Fetch failure → returns the underlying `http-fetch` error envelope
- Readability finds no main content → falls back to raw, `mode_used="raw"`
- JS rendering required but disabled → `error_kind="js_required"`
- Robots.txt disallows path → `error_kind="robots_disallow"` if config opts in to honoring it

## Why it's a good demo

It's the canonical example of "compose a primitive on top of another
primitive": `web-scrape` is `http-fetch` plus extraction. Pairs with the
`pdf-extract` and `markdown-html` tools to form a uniform "any document
to clean text" pipeline.
