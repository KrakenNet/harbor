# Knowledge · `customer-account-kg`

A knowledge graph of customer accounts — companies, contacts, contracts,
support tickets, product usage, and the relationships between them. The
substrate behind any CSM, support, or sales agent that needs the full
360 on an account before responding.

## Purpose

CRM gives you the customer record; product analytics gives you usage;
billing gives you contracts; support gives you tickets. None of them
talk to each other. The `customer-account-kg` joins them across stable
identity (account_id, contact email) so an agent answering one ticket
sees the whole relationship.

## Type

Knowledge Graph (Neo4j-backed via `internal/knowledge/`).

## Schema

```
Nodes:
  Account    { id, name, tier, mrr, status, region }
  Contact    { id, email, name, role, account_id }
  Contract   { id, start, end, plan, value, auto_renew }
  Ticket     { id, opened_at, status, priority, summary }
  UsageStat  { id, metric, value, period }
  Project    { id, name, status }     // customer-side projects/initiatives

Edges:
  (Contact)-[:WORKS_AT]->(Account)
  (Account)-[:HAS_CONTRACT]->(Contract)
  (Account)-[:OPENED]->(Ticket)
  (Contact)-[:OPENED]->(Ticket)
  (Account)-[:USES { period }]->(UsageStat)
  (Account)-[:RUNS]->(Project)
  (Account)-[:MANAGED_BY]->(Person)   // links to org-chart-kg
  (Account)-[:PARENT_OF]->(Account)   // group/subsidiary structure
```

## Ingest source

- CRM integration adapter (Salesforce / HubSpot) for accounts and contacts
- Billing system for contracts
- Support tool (Zendesk / Intercom / Front) for tickets
- Product analytics for `UsageStat` rollups (daily)

## Retrieval query example

> "before I reply to ticket #42819, what should I know about the account?"

```cypher
MATCH (t:Ticket { id: 42819 })<-[:OPENED]-(c:Contact)-[:WORKS_AT]->(a:Account)
OPTIONAL MATCH (a)-[:HAS_CONTRACT]->(con:Contract { auto_renew: true })
OPTIONAL MATCH (a)-[:USES]->(u:UsageStat { metric: "weekly_active_users" })
OPTIONAL MATCH (a)-[:OPENED]->(prev:Ticket { status: "closed" })
RETURN a, con, u, count(prev) AS prior_tickets
```

## ACLs

- **Read**: GTM org by default; PII fields gated by role; per-account ACLs honor CRM teams
- **Write**: ingestion automations; CSM updates flow back via the integration adapter
- **Public/customer access**: never

## Why it's a good demo

Joined customer data is the unsexy thing every GTM team wants and almost
none have. Wiring it into a `support-triage` or `meeting-prep` workflow
is an immediate adoption win. Composes with the `customer-faq-kb`,
`role-gate`, `redaction-on-egress`, and `customer-churn-outreach`.
