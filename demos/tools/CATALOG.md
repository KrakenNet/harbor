# Tools — Demo Catalog

Tool primitives for Railyard agents. Each entry will graduate into its own
folder with a config (Python / Shell / API / DSPy), example invocations, and
a smoke test.

## Generic

- `http-fetch` — typed HTTP client with retry/backoff
- `shell-exec` — sandboxed shell command runner
- `sql-query` — read-only Postgres/SQLite query
- `vector-search` — pgvector similarity search
- `embed-text` — single-text embedding helper
- `web-scrape` — readability-mode page → markdown
- `pdf-extract` — PDF → text + tables
- `ocr` — image → text
- `csv-read` / `csv-write`
- `json-jq` — jq-style query over JSON
- `regex-match`
- `git-ops` — clone / diff / blame / log
- `slack-post` / `discord-post` / `email-send`
- `dns-lookup`, `whois`, `tls-cert-info`
- `markdown-html` — both directions
- `token-count` — model-aware
- `code-format` — prettier / black / gofmt
- `lint-run` / `test-run`
- `aws-cli`, `gcloud`, `kubectl` thin wrappers

## Creative

- `provenance-tracer` — given a claim, walks the trace tree back to its source span
- `confidence-bettor` — asks the LLM to "bet" on its answer, returns calibrated probability
- `counterfactual-mutator` — minimally perturbs an input until the verdict flips
- `cargo-cult-detector` — finds copy-pasted patterns whose original justification is gone
- `embedding-cartographer` — clusters a corpus, auto-names regions, returns a 2D map
- `time-travel-replayer` — re-runs a span tree with one node swapped (model, prompt, tool)
- `chaos-payload` — fuzzes a tool's inputs to find brittle assumptions
- `schema-migration-synthesizer` — diffs two schemas and emits a safe migration
- `five-whys` — recursive "why?" until first-principles bedrock is hit
- `decision-diary` — writes an immutable rationale row before any irreversible verb fires
