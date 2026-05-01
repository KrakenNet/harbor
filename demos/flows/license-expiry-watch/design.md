=============================================================================
                          LICENSE EXPIRY WATCH
=============================================================================

[Trigger] (daily cron + on-demand for vendor onboarding)
             │
             ▼
[1. load_license_inventory]
  (knowledge: `vendor-contracts-kg` + TLS cert inventory + domain registrar
   exports + SaaS subscriptions)
             │
             ▼
[2. enrich_each]  (parallel tool calls)
  ├──► `tls-cert-info` for certs
  ├──► `whois` for domains
  ├──► `http-fetch` to vendor admin APIs for SaaS seats
  └──► `pdf-extract` over contract PDFs (renewal clauses, opt-out windows)
             │
             ▼
[3. extract_expiry]  (agent: `extractor`)
  → fields: expires_at, auto_renew, opt_out_deadline, renewal_owner
             │
             ▼
[4. compute_alert_tiers]  (rule: 90 / 60 / 30 / 7 / 0 days out → tier)
             │
             ▼
[5. governor: `compliance-scan`]
  (any expiring artifact tied to a regulatory commitment — SOC2 control
   evidence, PCI cert — promoted one tier upward)
             │
             ▼
[6. classify_renewal_intent]  (agent: `classifier`)
  → renew | drop | renegotiate | unknown
             │
             ▼
[7. governor: `confidence-threshold`]
  (unknown intent forces HITL routing rather than silent decay)
             │
             ▼
[8. draft_renewal_brief]  (agent: `summarizer`)
  → for each renewal: usage trend, cost trend, alternative options
             │
             ▼
[9. branch_action]  (conditional)
  ├──► tier 90 → email owner
  ├──► tier 60 → email + Slack
  ├──► tier 30 → file ticket + ping manager
  ├──► tier 7  → page renewal owner
  └──► tier 0  → page incident channel
             │
             ▼
[10. notify]  (tool: per-channel send)
             │
             ▼
[11. write_outcome]
  (memory: license → expiry → renewal decision → cost delta;
   feeds future cost-trend and `forecast-then-score` workflows)
=============================================================================

## Inputs

- inventory sources (KG + integrations)
- alert-tier thresholds (override per category)

## Step types

| #  | Step                     | Type        | Notes |
|----|--------------------------|-------------|-------|
| 1  | load_license_inventory   | knowledge   | `vendor-contracts-kg` |
| 2  | enrich_each              | tool        | parallel |
| 3  | extract_expiry           | agent       | `extractor` |
| 4  | compute_alert_tiers      | rule        | day-buckets |
| 5  | compliance_scan          | governor    | promotes tiers |
| 6  | classify_renewal_intent  | agent       | `classifier` |
| 7  | confidence_gate          | governor    | HITL on unknown |
| 8  | draft_renewal_brief      | agent       | `summarizer` |
| 9  | branch_action            | conditional | per tier |
| 10 | notify                   | tool        | per channel |
| 11 | write_outcome            | memory      | feeds forecasts |

## Outputs

- renewal brief per expiring item
- tiered notifications
- outcome row after eventual disposition

## Why it's a good demo

Cross-cuts security (TLS certs), legal (contracts), and finance (SaaS
spend) — three audiences usually never on the same dashboard. Pairs with
`vendor-contracts-kg`, `compliance-scan`, and `forecast-then-score`.
