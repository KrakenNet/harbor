# Knowledge · `org-chart-kg`

A knowledge graph of the organization's people, teams, and reporting
structure. The substrate behind any agent that needs to answer "who
owns this?", "who's on-call for X?", or "who should approve this?"

## Purpose

Org charts in HRIS systems are flat and reporting-line-oriented; real
ownership is a richer graph (functional teams, on-call rotations, code
ownership, project membership). The `org-chart-kg` unifies these so an
agent looking for the right human can walk the relationships rather than
guess from titles.

## Type

Knowledge Graph (Neo4j-backed via `internal/knowledge/`).

## Schema

```
Nodes:
  Person   { id, email, display_name, title, location, status }
  Team     { id, name, kind: functional|squad|guild|rotation }
  Role     { id, name, scope }
  Project  { id, name, status }

Edges:
  (Person)-[:REPORTS_TO]->(Person)
  (Person)-[:MEMBER_OF { since }]->(Team)
  (Person)-[:HOLDS]->(Role)
  (Person)-[:WORKS_ON]->(Project)
  (Team)-[:OWNS]->(Project)
  (Team)-[:RESPONSIBLE_FOR]->(Service)   // links to cmdb-asset-kg
  (Person)-[:ON_CALL_FOR { window }]->(Team)
```

## Ingest source

- HRIS integration adapter (Workday / BambooHR / Rippling) for `Person` and `REPORTS_TO`
- PagerDuty / Opsgenie integration for `ON_CALL_FOR`
- GitHub CODEOWNERS sync for `Team`-`OWNS`-`Service` edges
- Manual authoring in the KB UI for `Role` and `Project` membership

## Retrieval query example

> "who should approve a deploy to the payments service right now?"

```cypher
MATCH (s:Service { name: "payments" })<-[:RESPONSIBLE_FOR]-(t:Team)
MATCH (p:Person)-[:ON_CALL_FOR { window: $now }]->(t)
RETURN p.display_name, p.email
```

## ACLs

- **Read**: workspace-wide for non-sensitive fields; comp/HR fields gated to HR + manager-of-record
- **Write**: HRIS sync for upstream nodes; team leads for their own `Team` membership
- **Public/customer access**: never

## Why it's a good demo

Almost every workflow eventually needs to find a human, and most platforms
fake it with a config map. A real KG version supports HITL routing, on-call
escalation, and approval gates for free. Composes with `hitl-trigger`,
`approval-policy`, and the `incident-response` workflow.
