=============================================================================
                          LEAD ENRICHMENT
=============================================================================

[Lead Sources] (form fill, CSV import, CRM webhook, business card OCR)
             │
             ▼
[1. normalize_input]  (rule: trim, lowercase email, parse name)
             │
             ▼
[2. dedupe_check]  (tool: `sql-query` over CRM)
             │
             ├──► [IF existing lead] ──► [Merge path: enrich gaps only]
             │
             ▼
[3. domain_lookup]  (tool: `dns-lookup` + `whois`)
  → domain age, registrar, MX provider
             │
             ▼
[4. company_enrich]  (tool: `http-fetch` to enrichment provider)
  → industry, employee count, revenue band, tech stack
             │
             ▼
[5. person_enrich]  (tool: `http-fetch` to people-data provider)
  → title, seniority, LinkedIn handle, location
             │
             ▼
[6. governor: `compliance-scan`]
  (GDPR/CCPA jurisdiction check; halts enrichment for protected geos
   without a documented basis)
             │
             ▼
[7. score_lead]  (gomlx_inference: `risk-scorer` repurposed as fit-scorer)
  → fit score 0–100 + reasons
             │
             ▼
[8. classify_segment]  (agent: `classifier`)
  → segment: enterprise | mid-market | smb | consumer
             │
             ▼
[9. governor: `confidence-threshold`]
  (low-confidence segments routed to HITL review queue instead of CRM)
             │
             ▼
[10. write_crm]  (tool: integration adapter — Salesforce/HubSpot/Pipedrive)
             │
             ▼
[11. assign_owner]  (rule: territory + segment routing)
             │
             ▼
[12. write_outcome]
  (memory: `past-decision-memory` — lead → score → eventual close/no-close,
   feeds back into next training cycle of `churn-predictor` / fit-scorer)
=============================================================================

## Inputs

- raw lead payload (name, email, company, optional phone)
- source channel
- campaign/UTM metadata

## Step types

| #  | Step             | Type             | Notes |
|----|------------------|------------------|-------|
| 1  | normalize_input  | rule             | deterministic |
| 2  | dedupe_check     | tool             | `sql-query` |
| 3  | domain_lookup    | tool             | `dns-lookup` + `whois` |
| 4  | company_enrich   | tool             | external API |
| 5  | person_enrich    | tool             | external API |
| 6  | compliance       | governor         | `compliance-scan` for GDPR/CCPA |
| 7  | score_lead       | gomlx_inference  | fit-scorer model |
| 8  | classify_segment | agent            | `classifier` |
| 9  | confidence_gate  | governor         | `confidence-threshold` → HITL |
| 10 | write_crm        | tool             | integration adapter |
| 11 | assign_owner     | rule             | territory/segment |
| 12 | write_outcome    | memory           | feeds future scoring |

## Outputs

- enriched CRM record with fit score, segment, owner
- compliance audit row
- outcome edge after eventual disposition

## Why it's a good demo

Familiar GTM workflow that exercises external tools, ML scoring,
compliance gating, and outcome writeback. Shows how a `risk-scorer` model
can be repurposed for fit prediction. Pairs with `customer-account-kg` and
`churn-predictor`.
