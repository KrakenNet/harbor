# Knowledge · `product-docs-kb`

A knowledge base of product documentation — user guides, feature pages,
tutorials, and how-tos. The retrievable substrate behind the
`support-agent`, the in-product helpbot, and any chatbot that needs to
answer "how do I X?" in your product's voice.

## Purpose

Product docs are usually authored in a docs site (Docusaurus, Mintlify,
Readme) and consumed only when users find their way to that site. The
`product-docs-kb` mirrors them into a RAG-ready store so agents can cite
the same prose the docs site serves, without a brittle scraping layer.

## Type

Knowledge Base (markdown documents) with chunked embeddings; one
embedding per H2/H3 section to keep retrieval granularity high.

## Schema

Each doc page carries frontmatter:

```yaml
---
title: <page title>
product: <product-id>
surface: <web|mobile|api|cli>
audience: <end-user|admin|developer>
last_verified: <date>
canonical_url: <https://docs.example.com/...>
---
```

Body is markdown — sections become chunks, code blocks are preserved,
front-of-page TL;DRs are weighted higher in retrieval.

## Ingest source

- Git repo backing the public docs site (canonical)
- CI hook on docs-repo merge republishes affected chunks
- Optional pull from the docs CMS via integration adapter

## Retrieval query example

> "how do I rotate an API key in the dashboard?"

→ retrieves: chunks where `audience in ["admin","developer"]`, ranked by
  semantic similarity, returns markdown excerpt + `canonical_url` for
  attribution.

## ACLs

- **Read**: public — same audience as the docs site
- **Write**: docs team via PR; the KB is a downstream consumer, not an authoring surface
- **Public/customer access**: yes (this is the customer-facing slice)

## Why it's a good demo

It's the most common RAG ask: "answer questions over our docs." Doing
it well — with section-level chunking, canonical-URL attribution, and a
cache-invalidation story tied to the docs repo — is the difference
between a demo that ships and one that drifts. Composes with
`conviction-tax` (citations required) and the `faq-answerer` agent.
