# Knowledge · `api-reference-kb`

A knowledge base of API reference material — endpoint specs, request and
response schemas, error codes, auth modes, and idiomatic usage examples.
Consumed by the `api-explorer` agent and any code-writing agent that
needs to call your APIs correctly.

## Purpose

OpenAPI specs are great for codegen and lousy for retrieval — they're
JSON-shaped and lose all the surrounding "when do I use this?" prose.
The `api-reference-kb` denormalizes the spec into one document per
operation, with usage notes, gotchas, and example calls, so an agent
asking "how do I X?" gets back working code rather than schema fragments.

## Type

Knowledge Base (markdown documents) with chunked embeddings; primary key
is `operation_id`.

## Schema

Each operation document carries frontmatter:

```yaml
---
operation_id: <unique id from OpenAPI>
method: <GET|POST|PUT|PATCH|DELETE>
path: </resource/{id}>
service: <service-name>
auth: <bearer|oauth2|api-key|none>
stability: <stable|beta|deprecated>
deprecated_after: <date-or-null>
---
```

Body sections: **Summary** · **Request** · **Response** · **Errors** ·
**Examples (curl, Python, TypeScript)** · **Gotchas** · **See also**.

## Ingest source

- OpenAPI / AsyncAPI spec in the service repo (machine-generated skeleton)
- Hand-written prose layered on top in a sibling `.md` file per operation
- CI republishes on spec change; drift between spec and prose surfaces in `kb-sync`

## Retrieval query example

> "create a webhook that fires on invoice.paid"

→ retrieves: operations with `path` matching `/webhooks*` and request schema
  containing an `event_types` field, plus the `Examples` section showing the
  exact JSON shape for the `invoice.paid` event.

## ACLs

- **Read**: public for documented APIs; internal for unreleased / beta
- **Write**: service-owning team via spec PR + prose PR
- **Public/customer access**: matches the API's own visibility

## Why it's a good demo

A code-writing agent that hallucinates endpoints is worse than no agent
at all. Grounding it in a structured per-operation KB is the cleanest
fix and an obvious "we know what we're doing" demo. Pairs with the
`schema-validator` governor and the `api-contract-diff-alert` workflow
to keep the KB honest as the API evolves.
