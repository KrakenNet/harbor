=============================================================================
                          DOC INGEST → RAG INDEX
=============================================================================

[Drop Sources] (S3 prefix watch, Drive folder, email-to-inbox, manual upload)
             │
             ▼
[1. detect_format]  (rule: extension + magic-byte sniff)
  → format: pdf | docx | md | html | image | csv | unknown
             │
             ├──► [IF unknown] ──► [Quarantine + notify owner]
             │
             ▼
[2. extract_text]
  (tool dispatch by format:
   • pdf  → `pdf-extract`
   • docx → `pandoc` wrapper
   • md/html → `markdown-html`
   • image → `ocr`
   • csv → `csv-read`)
             │
             ▼
[3. governor: `pii-redactor`]
  (mask PII before anything is embedded; the index must never carry raw PII)
             │
             ▼
[4. chunk]  (rule: semantic-aware splitter, ~800 tok with 100 tok overlap)
             │
             ▼
[5. governor: `output-length-cap`]
  (drops chunks above N tokens — usually a parser bug)
             │
             ▼
[6. embed]  (tool: `embed-text`, batched)
             │
             ▼
[7. extract_entities]  (agent: `extractor`)
  → people, orgs, products, dates — for hybrid retrieval filters
             │
             ▼
[8. write_index]
  (knowledge: pgvector row + entity rows + provenance edge to source doc)
             │
             ▼
[9. write_provenance]
  (knowledge: `provenance-graph` — chunk ↔ source ↔ ingest_run_id ↔ trust score)
             │
             ▼
[10. notify]  (tool: `slack-post` — "indexed N chunks from <doc>")
=============================================================================

## Inputs

- file blob or URI
- optional knowledge-base ID and tags
- optional trust-score override (default: derived from source channel)

## Step types

| #  | Step              | Type      | Notes |
|----|-------------------|-----------|-------|
| 1  | detect_format     | rule      | deterministic |
| 2  | extract_text      | tool      | dispatched by format |
| 3  | redact            | governor  | `pii-redactor` runs pre-embed |
| 4  | chunk             | tool      | semantic splitter |
| 5  | length_cap        | governor  | `output-length-cap` |
| 6  | embed             | tool      | `embed-text`, batched |
| 7  | extract_entities  | agent     | `extractor` for hybrid filters |
| 8  | write_index       | knowledge | pgvector + entities |
| 9  | write_provenance  | knowledge | `provenance-graph` |
| 10 | notify            | tool      | `slack-post` |

## Outputs

- N indexed chunks attached to a knowledge base
- entity rows for hybrid retrieval
- provenance row per chunk

## Why it's a good demo

The "table-stakes" RAG ingest pipeline — every Railyard deployment needs
one. Demonstrates redaction-before-embed (a safety property most off-the-
shelf RAG stacks miss) and the provenance write that makes downstream
`provenance-tracer` work. Pairs with `vector-search`, `pii-redactor`, and
`provenance-graph`.
