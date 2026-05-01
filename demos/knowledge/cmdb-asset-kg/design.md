# Knowledge · `cmdb-asset-kg`

A knowledge graph of infrastructure and application assets — services,
hosts, databases, queues, buckets, and the dependency edges that connect
them. The substrate any incident, change-management, or capacity agent
walks to answer "what does this thing depend on?" and "what depends on
it?"

## Purpose

A traditional CMDB is a table of rows; the questions you actually want to
answer are graph-shaped. The `cmdb-asset-kg` makes blast-radius queries,
upstream-dependency walks, and ownership-chase trivial — and keeps the
graph fresh by sourcing from the systems of record, not a quarterly
manual sync.

## Type

Knowledge Graph (Neo4j-backed via `internal/knowledge/`).

## Schema

```
Nodes:
  Service     { id, name, tier, language, repo_url }
  Host        { id, hostname, region, env }
  Database    { id, engine, version, env }
  Queue       { id, kind, env }
  Bucket      { id, provider, name, env }
  Dependency  { id, name, kind: lib|saas|internal }

Edges:
  (Service)-[:DEPLOYED_ON]->(Host)
  (Service)-[:READS_FROM]->(Database|Queue|Bucket)
  (Service)-[:WRITES_TO]->(Database|Queue|Bucket)
  (Service)-[:CALLS]->(Service)
  (Service)-[:USES]->(Dependency)
  (Service)-[:OWNED_BY]->(Team)         // links to org-chart-kg
```

## Ingest source

- Cloud provider APIs (AWS Config / GCP Asset Inventory) for hosts and managed services
- Service registry (Backstage, internal manifest) for `Service` nodes
- OpenTelemetry traces post-processed nightly for `CALLS` edges
- `code-dependency-kg` provides `USES` edges for libraries

## Retrieval query example

> "if checkout-svc goes down, what else fails?"

```cypher
MATCH (s:Service { name: "checkout-svc" })<-[:CALLS*1..3]-(upstream:Service)
RETURN DISTINCT upstream.name, upstream.tier
ORDER BY upstream.tier
```

## ACLs

- **Read**: all engineers; production-credential fields gated to SRE
- **Write**: ingestion automations only; manual override requires SRE approval
- **Public/customer access**: never

## Why it's a good demo

Blast-radius queries are the single most-asked question during incidents
and changes, and almost no team has them in graph form. Composes with
`incident-response`, the `runbooks-kb`, and `threat-intel-feed` (joining
CVEs to affected services via `USES`).
