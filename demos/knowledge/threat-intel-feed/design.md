# Knowledge · `threat-intel-feed`

A knowledge base of vulnerability and threat intelligence — NVD, OSV,
GitHub Advisory, CISA KEV, and vendor advisories — normalized into a
single retrievable feed. Joined to the `code-dependency-kg` and
`cmdb-asset-kg` so "is this CVE relevant to us?" is answerable in
seconds.

## Purpose

Security teams pay for feeds; engineering teams ignore feeds because
nothing joins the CVE to the affected line of code or asset. The
`threat-intel-feed` is the join key: each advisory is normalized to
package + version-range + severity, ready to graph-walk into the assets
that actually use it.

## Type

Knowledge Base (markdown + structured fields) with chunked embeddings
on prose, exact-match indexes on package + version-range fields.

## Schema

Each advisory record carries frontmatter:

```yaml
---
advisory_id: <CVE-NNNN-NNNN | GHSA-... | OSV-...>
sources: [<NVD|OSV|GHSA|KEV|vendor>]
package: <ecosystem>/<name>
affected_versions: <semver-range>
fixed_versions: [<version>, ...]
severity: <critical|high|medium|low>
cvss: <score>
cisa_kev: <true|false>
exploited_in_wild: <true|false>
published: <date>
last_modified: <date>
---
```

Body is the normalized prose: **Summary** · **Impact** · **Affected
configurations** · **Remediation** · **References**.

## Ingest source

- Pull jobs against NVD JSON feed, OSV API, GitHub Advisory GraphQL, CISA KEV CSV
- Optional vendor advisories via integration adapter
- Deduplication keyed on `advisory_id` aliases (CVE ↔ GHSA ↔ OSV)

## Retrieval query example

> "any new criticals affecting our services in the last 24 hours?"

→ filter: `severity=critical AND last_modified > now() - 24h`
→ join into `code-dependency-kg`:

```cypher
MATCH (r:Repo)-[d:DEPENDS_ON]->(p:Package)
WHERE p.name = $advisory.package AND semver_in_range(d.version_constraint, $advisory.affected_versions)
MATCH (r)<-[:OWNED_BY]-(t:Team)
RETURN r.url, t.name, $advisory.fixed_versions
```

## ACLs

- **Read**: all engineers (advisory data is non-sensitive); join-results inherit asset ACLs
- **Write**: ingestion automations only
- **Public/customer access**: trust portal can expose "fixed" advisories on a delay; raw feed is internal

## Why it's a good demo

It's the entry point to the `cve-remediation` workflow, which already
ships in the demo catalog. The feed plus the join into
`code-dependency-kg` plus a HITL approval is a credible "we close CVEs"
loop. Composes with `incident-response`, `pr-review`, and the
`pre-mortem-required` governor for irreversible patches.
