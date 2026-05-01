# Knowledge · `compliance-kb`

A knowledge base of compliance content — the controls, evidence, audit
narratives, and regulatory mappings that prove your org meets SOC 2 /
HIPAA / PCI / ISO / GDPR obligations. Retrieved by the `compliance-scan`
governor, the `expense-policy-check` workflow, and any agent that has to
answer "is this allowed?"

## Purpose

Compliance content lives in three places that never agree: the GRC tool
(Vanta, Drata, Secureframe), the policy PDFs, and the auditors' shared
folder. The `compliance-kb` is the unified retrieval layer so agents can
ground answers in the version of the policy that the auditor signed off
on, not the draft a teammate wrote in 2022.

## Type

Knowledge Base (markdown documents) with chunked embeddings; controls
and evidence linked by `control_id`.

## Schema

Each compliance document carries frontmatter:

```yaml
---
doc_id: <unique id>
doc_type: <policy|control|evidence|narrative|mapping>
framework: [<SOC2|HIPAA|PCI-DSS|ISO-27001|GDPR>]
control_id: <e.g. CC6.1, 164.312(a)(1)>
status: <draft|active|retired>
review_due: <date>
owner: <compliance-team-handle>
---
```

Body sections vary by `doc_type` but always include **Scope**,
**Statement / evidence**, and **Last reviewed**.

## Ingest source

- GRC tool via integration adapter (Vanta / Drata / Secureframe)
- Git repo for policies under version control
- HITL review queue for evidence collected from system scans

## Retrieval query example

> "can we store unredacted CHD in the analytics warehouse?"

→ retrieves: docs with `framework contains PCI-DSS` and embedded text
  matching "cardholder data" + "storage" + "encryption", returns the
  active policy statement and the relevant control mapping.

## ACLs

- **Read**: compliance team unrestricted; engineers see active policies; auditors see scoped subsets via time-bound tokens
- **Write**: compliance team only; framework-mapping changes require auditor sign-off
- **Public/customer access**: trust-portal subset only — public summaries, never raw evidence

## Why it's a good demo

Compliance is the place agents most often go wrong (hallucinating
policies that don't exist, missing controls that do) and where the cost
of being wrong is highest. A grounded `compliance-kb` plus
`compliance-scan` plus `redaction-on-egress` is a credible, sellable
package for any regulated buyer. Composes with the `audit-archive` and
the `provenance-graph` for evidence chains.
