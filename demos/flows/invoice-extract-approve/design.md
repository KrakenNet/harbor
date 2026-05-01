=============================================================================
                       INVOICE EXTRACT → APPROVE → ERP
=============================================================================

[Invoice Sources] (AP email inbox, vendor portal scrape, scanned upload)
             │
             ▼
[1. classify_doc]  (agent: `doc-classifier`)
  → doc_type: invoice | credit-note | statement | spam
             │
             ├──► [IF NOT invoice] ──► [Reroute or discard]
             │
             ▼
[2. extract_fields]  (agent: `extractor`)
  → vendor_name, vendor_id, invoice_number, issue_date, due_date,
    line_items[], subtotal, tax, total, currency, po_number
             │
             ▼
[3. governor: `schema-validator`]
  (extracted JSON must conform to invoice schema; on fail → step 2 with
   structured feedback, max 2 retries)
             │
             ▼
[4. match_po]  (tool: `sql-query` against ERP open POs)
  → po_match_status: matched | partial | no_po | mismatch
             │
             ▼
[5. duplicate_check]  (tool: `sql-query` — vendor + invoice_number)
             │
             ├──► [IF duplicate] ──► [Flag + halt]
             │
             ▼
[6. governor: `expense-policy-check`]
  (per-category caps, vendor allowlist, GL-code sanity)
             │
             ▼
[7. score_anomaly]  (gomlx_inference: `anomaly-detector`)
  (flags amounts that deviate from this vendor's historical range)
             │
             ▼
[8. route_approval]  (rule: amount + GL code + anomaly flag)
  → approver_chain: [manager, director?, CFO?]
             │
             ▼
[9. HITL Approval Gate]  (approval step with timeout escalation)
             │
             ├──► [IF rejected] ──► [Notify vendor + write outcome]
             │
             ▼
[10. post_to_erp]  (tool: integration adapter — NetSuite/QuickBooks/SAP)
             │
             ▼
[11. schedule_payment]  (tool: integration adapter for AP module)
             │
             ▼
[12. write_outcome]
  (memory: vendor → invoice → approval chain → days-to-pay; trains
   future anomaly model)
=============================================================================

## Inputs

- invoice file (PDF, image, or structured EDI)
- inbox metadata (sender, subject, received_at)

## Step types

| #  | Step              | Type             | Notes |
|----|-------------------|------------------|-------|
| 1  | classify_doc      | agent            | `doc-classifier` |
| 2  | extract_fields    | agent            | `extractor` (typed output) |
| 3  | schema_validator  | governor         | `schema-validator`, can loop to 2 |
| 4  | match_po          | tool             | `sql-query` |
| 5  | duplicate_check   | tool             | `sql-query` |
| 6  | policy_check      | governor         | `expense-policy-check` |
| 7  | score_anomaly     | gomlx_inference  | `anomaly-detector` |
| 8  | route_approval    | rule             | deterministic chain |
| 9  | hitl_approval     | approval         | conditional + timeout |
| 10 | post_to_erp       | tool             | ERP adapter |
| 11 | schedule_payment  | tool             | AP module |
| 12 | write_outcome     | memory           | trains anomaly model |

## Outputs

- approved/rejected invoice with full audit trail
- ERP entry + scheduled payment
- vendor-history row for future anomaly scoring

## Why it's a good demo

Classic high-value AP automation. Exercises retry-on-schema-failure
(governor → agent loop), anomaly-aware routing, and tiered HITL approval —
all primitives Railyard composes natively. Pairs with
`expense-policy-check` and `anomaly-detector`.
