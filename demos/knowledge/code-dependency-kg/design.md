# Knowledge · `code-dependency-kg`

A knowledge graph of source-code dependencies — packages, modules,
functions, and call edges across the org's repos. The substrate behind
the `pr-review` agent, the `cve-remediation` workflow, and any "where is
this used?" query that spans more than one repo.

## Purpose

`grep` works inside one repo; cross-repo blast radius does not. The
`code-dependency-kg` ingests language-aware ASTs from every repo and
materializes the call graph plus the package-level dependency graph, so
queries like "every caller of this deprecated function across all
services" become a single Cypher query.

## Type

Knowledge Graph (Neo4j-backed via `internal/knowledge/`).

## Schema

```
Nodes:
  Repo       { id, url, default_branch, language }
  Package    { id, name, version, ecosystem }   // npm, pypi, go-module, etc.
  Module     { id, repo_id, path }
  Symbol     { id, module_id, name, kind: func|class|method, signature }

Edges:
  (Repo)-[:CONTAINS]->(Module)
  (Module)-[:DECLARES]->(Symbol)
  (Symbol)-[:CALLS]->(Symbol)
  (Repo)-[:DEPENDS_ON { version_constraint }]->(Package)
  (Module)-[:IMPORTS]->(Module|Package)
  (Symbol)-[:DEPRECATED_AT { since }]->(Symbol)
```

## Ingest source

- Tree-sitter / language-server AST extraction in CI for every repo
- Lockfiles (`package-lock.json`, `go.sum`, `requirements.txt`) for `DEPENDS_ON` edges
- The `git-ops` tool for blame/last-touched annotations

## Retrieval query example

> "every caller of `legacy.UserAuth.verify_token` across all repos"

```cypher
MATCH (target:Symbol { name: "verify_token" })<-[:CALLS]-(caller:Symbol)
MATCH (caller)<-[:DECLARES]-(m:Module)<-[:CONTAINS]-(r:Repo)
RETURN r.url, m.path, caller.name, caller.signature
```

## ACLs

- **Read**: all engineers
- **Write**: CI ingestion automations only
- **Public/customer access**: never

## Why it's a good demo

Cross-repo refactor planning is one of the highest-value, lowest-supplied
agent capabilities. Pairs with the `cve-remediation` workflow (joining
`Package` nodes to `threat-intel-feed`), the `pr-review` agent, and the
`pattern-archaeologist` agent for dead-idiom excavation.
