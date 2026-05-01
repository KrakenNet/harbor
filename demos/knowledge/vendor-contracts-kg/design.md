# Knowledge · `vendor-contracts-kg`

A knowledge graph of vendor contracts — MSAs, order forms, DPAs, SOWs,
and the relationships between them, the parties, the obligations, and
the renewal/expiry dates that drag on the calendar. The substrate
behind procurement, legal-ops, and the `license-expiry-watch` workflow.

## Purpose

Contracts are usually filed as PDFs in a CLM (Ironclad, LinkSquares,
DocuSign Insight) or worse, a shared drive. Their structure — who signs,
what's promised, when it lapses, what supersedes what — is exactly the
shape of a graph. The `vendor-contracts-kg` makes obligations queryable
and dates trigger-able instead of slide-deck artifacts.

## Type

Knowledge Graph (Neo4j-backed via `internal/knowledge/`).

## Schema

```
Nodes:
  Vendor       { id, name, kind: saas|services|hardware|reseller }
  Contract     { id, doc_url, type: MSA|SOW|OF|DPA|NDA, signed_at, effective_from, effective_to }
  Party        { id, name, role: customer|vendor|signer }
  Obligation   { id, kind: payment|sla|data-handling|exclusivity|renewal, body, due }
  Cost         { id, amount, currency, cadence: monthly|annual|one-time }

Edges:
  (Contract)-[:WITH]->(Vendor)
  (Contract)-[:SIGNED_BY]->(Party)
  (Contract)-[:CONTAINS]->(Obligation)
  (Contract)-[:HAS_COST]->(Cost)
  (Contract)-[:SUPERSEDES]->(Contract)
  (Contract)-[:GOVERNED_BY]->(Contract)   // SOWs governed by an MSA
  (Vendor)-[:PROVIDES]->(Service)         // links to cmdb-asset-kg for SaaS
```

## Ingest source

- CLM integration adapter (Ironclad / LinkSquares / DocuSign Insight) for contract metadata
- The `extractor` agent + the `pdf-extract` tool to lift `Obligation` and `Cost` from contract PDFs
- HITL review queue for extracted obligations before they land on the graph

## Retrieval query example

> "what auto-renews in the next 60 days and what does it cost?"

```cypher
MATCH (c:Contract)-[:CONTAINS]->(o:Obligation { kind: "renewal" })
WHERE o.due <= date() + duration("P60D") AND o.body CONTAINS "auto"
MATCH (c)-[:HAS_COST]->(cost:Cost)
MATCH (c)-[:WITH]->(v:Vendor)
RETURN v.name, c.type, o.due, cost.amount, cost.cadence
ORDER BY o.due ASC
```

## ACLs

- **Read**: procurement + legal-ops unrestricted; cost fields gated to finance + the contract owner
- **Write**: ingestion automations + HITL extraction reviewers; no manual graph edits
- **Public/customer access**: never

## Why it's a good demo

"What's auto-renewing and what should we kill?" is a question every
finance team wants answered and almost no platform answers cleanly.
Composes with `license-expiry-watch`, `cost-spike-forecaster`, the
`time-bomb-scout` agent, and the `compliance-kb` for DPA-coverage
queries.
