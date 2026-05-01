# Knowledge · `provenance-graph`

A knowledge graph in which every fact in the platform is linked to its
sources, and every source is linked to *its* sources, all the way back
to ground truth. The trust path of every claim is a query, not a
guess.

Most platforms can answer "what does the agent believe?" Some can
answer "where did the agent get that?" Almost none can answer "what is
the *full* trust path from this claim back to a primary source, and is
any link in that path stale, low-trust, or contradicted?" The
`provenance-graph` answers exactly that, structurally, on every fact
the platform commits to.

## Purpose

Provenance is the load-bearing primitive behind every other epistemic
demo in the catalog. Stale facts, hallucinated citations,
laundered-through-summarization claims — all of them collapse if the
trust path is materialized. The graph is the substrate that makes the
trust path materialized rather than implied.

The load-bearing innovations:

1. **Every fact has at least one `DERIVED_FROM` edge** — claims with
   no provenance can exist in the graph but are flagged
   `unsourced` and refused by the retrieval layer for high-stakes
   queries.
2. **Provenance is transitive and decaying.** Trust along a path
   composes multiplicatively: a trustworthy summary of a low-trust
   source is still low-trust, and the graph computes this on read.
3. **Sources are themselves nodes**, not opaque URLs. A source has its
   own trust score, its own freshness, and its own upstream sources
   — a citation to a Wikipedia article whose own citations are stale
   is detectable as such, several hops away from the original claim.

## Type

Knowledge Graph (Neo4j-backed via `internal/knowledge/`).

## Schema

```
Nodes:
  Fact         { id, body, asserted_at, asserted_by, status, embedding }
  Source       { id, kind, url, trust_score, last_verified }
  Span         { id, trace_id, kind: tool-call|agent-output|governor }
  Document     { id, kb_id, doc_id, version }
  Person       { id, role }                    // human-attested facts
  Integration  { id, name, system_of_record_for }

Edges:
  (Fact)-[:DERIVED_FROM { confidence }]->(Fact|Source|Span|Document|Person)
  (Source)-[:CITES]->(Source|Document)
  (Span)-[:READ_FROM]->(Source|Document)
  (Span)-[:PRODUCED]->(Fact)
  (Fact)-[:CONTRADICTS]->(Fact)
  (Fact)-[:REINFORCED_BY]->(Source)
  (Source)-[:EMITTED_BY]->(Integration|Person)
  (Document)-[:HAS_VERSION]->(Document)        // version chain
```

The retrieval layer can compute, for any `Fact`, the **trust path**:
the shortest weighted path back to a primary `Source` (or set of them),
with composed trust = product of edge confidences * source trust *
freshness decay.

## Ingest source

- Every other catalog item that produces facts writes provenance edges
  here as a side effect: `half-life-kb` writes `REINFORCED_BY`,
  `decision-journal-kg` writes `DERIVED_FROM` to priors,
  `disagreement-archive` writes `DERIVED_FROM` from positions to their
  evidence, `anti-pattern-kb` writes `CONTRADICTS` from outcomes
- `internal/tracing/` populates `Span` nodes and `READ_FROM` edges
  automatically — every tool call's read of a source becomes a graph
  edge
- Integrations register themselves as `Integration` nodes with their
  trust scores at deploy time
- The `provenance-tracer` tool is the canonical query interface

## Retrieval query example

> An agent has just produced the fact: "the customer's plan auto-renews
  on 2026-07-01."

```cypher
MATCH (f:Fact { id: $fact_id })
CALL { WITH f
  MATCH path = (f)-[:DERIVED_FROM*1..6]->(s:Source)
  RETURN path, reduce(t = 1.0, r IN relationships(path) | t * r.confidence) * s.trust_score AS composed_trust
  ORDER BY composed_trust DESC LIMIT 5
}
RETURN [n IN nodes(path) | { id: n.id, kind: labels(n)[0] }] AS hop_chain, composed_trust
```

→ returns the top 5 trust paths from the claim back to primary
  sources. Composed trust < 0.4 → governor refuses egress without
  HITL. Composed trust ≥ 0.8 → fact is "well-grounded" and goes out
  unflagged. Anything in between gets a "based on" qualifier.

## ACLs

- **Read**: workspace-wide for the graph; some `Source` and
  `Document` nodes inherit ACLs from their underlying KB; trust paths
  that *cross* a restricted node are returned with the restricted node
  redacted but the path-length and composed-trust preserved (so
  callers can still reason about grounding without being granted the
  redacted content)
- **Write**: append-only — provenance edges can be added but never
  silently rewritten; a contradiction is a new `CONTRADICTS` edge,
  not a deletion
- **Audit**: every read of a trust path produces a span (which itself
  becomes a node in the graph — the graph is self-describing)

## Why it's a good demo

1. **It is the substrate the platform's "no hallucination" claim
   actually rests on.** Conviction taxes, citation requirements, and
   freshness governors all depend on a graph that *can answer* "where
   did this come from?" without hand-waving. Without this primitive,
   each of those governors is checking surface signals (does a string
   look like a citation?). With it, they're checking real structure
   (does the trust path compose to >0.7?). Pull this out and the
   platform's epistemic guarantees collapse to vibes.

2. **It is the data substrate for `provenance-tracer`,
   `conviction-tax`, `fact-half-life`, `cargo-cult-registry`, and
   the `anti-cargo-cult` workflow.** Every one of those reads from
   this graph in a different way: the tool walks paths, the governor
   composes trust, the freshness governor reads source freshness, the
   registry detects orphaned facts, the workflow re-runs the
   composition. That's five separate consumers, none of which is
   plausible without a real provenance graph underneath.

3. **The "redact but preserve path-shape" ACL behavior is the
   distinctive constraint.** Most graph systems either show you the
   node or hide the edge. This one preserves the *shape* of the
   trust path even when the contents are redacted, so a downstream
   caller without read access to a sensitive source can still tell
   that the claim is or isn't well-grounded. That separation —
   between *grounding-shape* and *grounding-content* — is exactly
   what regulated buyers want and almost nobody implements.

## Sample read

> An agent's output: "the SOC 2 audit window for FY26 closed on
  2026-03-15."

→ trust path for the claim:
  `Fact(soc2-window-fy26)` →[DERIVED_FROM, 0.9]→
  `Document(compliance-kb/soc2-audit-narrative.md, v3)` →[CITES, 1.0]→
  `Source(auditor-portal-export, trust=0.95, last_verified=2026-03-20)` →[EMITTED_BY]→
  `Integration(drata)`
→ composed trust = 0.9 * 1.0 * 0.95 * exp(-tiny) ≈ 0.85 → well-grounded.
→ the `conviction-tax` governor lets the high-confidence claim
  through. The audit log records the trust path. Six months from
  now, when a new auditor asks how the agent knew, the answer is
  one Cypher query — not a Slack archaeology expedition.

→ contrast: the same agent says "the FY26 audit was clean."
  Provenance trace: no `DERIVED_FROM` edge to anything verifiable.
  The fact is `unsourced`. Egress refused; `redaction-on-egress`
  rewrites the response to "I don't have grounding for the audit
  outcome — let me check Drata directly." That's the difference
  between "the platform doesn't hallucinate" as a slogan and as a
  guarantee.
