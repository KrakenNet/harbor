# Knowledge · `codebase-semantic-index`

A knowledge base of source code, chunked semantically and embedded for
similarity search. The retrieval substrate behind the `code-reviewer`,
`bug-reproducer`, and `pr-describer` agents — the place an agent goes
when the question is "where in the codebase is X?"

## Purpose

`grep` finds string matches; engineers ask intent-shaped questions
("where do we handle Stripe webhook idempotency?"). The
`codebase-semantic-index` makes those answerable. It complements — does
not replace — the structural `code-dependency-kg`: this index is for
"what does this code mean?", that graph is for "what calls what?"

## Type

Knowledge Base (code chunks + metadata) with embeddings; one chunk per
function / class / top-level block, deduplicated across forks.

## Schema

Each chunk record carries:

```yaml
---
chunk_id: <repo>:<path>:<symbol>:<sha>
repo: <repo-id>
path: <relative path>
language: <python|go|typescript|...>
symbol: <function or class name, or null for top-level>
start_line: <int>
end_line: <int>
last_modified: <date>
last_author: <handle>
test_coverage: <0..1 or null>
---
```

Body is the raw code chunk plus a generated docstring summary used as an
additional embedding seed.

## Ingest source

- CI hook on every default-branch merge re-embeds changed files
- Tree-sitter chunker for symbol-level granularity
- The `git-ops` tool provides last-author / last-modified annotations
- Optional periodic full re-embed when the embedding model changes

## Retrieval query example

> "where do we handle Stripe webhook idempotency?"

→ retrieves: top-K chunks by semantic similarity, filtered by `language
  in ["python","go"]`, ranked by recency of `last_modified`, returns
  symbol + path + line range plus a snippet for grounding.

## ACLs

- **Read**: all engineers; private repos enforce repo-level ACL
- **Write**: CI ingestion automations only
- **Public/customer access**: never

## Why it's a good demo

It's the "your codebase, searchable" demo that every engineering org
asks for. The structural pairing with `code-dependency-kg` (semantic
to find a starting point, structural to walk callers) is what makes
this version distinctive. Composes with `pr-review`, `bug-reproducer`,
and the `kintsugi` agent.
