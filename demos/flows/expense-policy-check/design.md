=============================================================================
                          EXPENSE POLICY CHECK
=============================================================================

[Trigger] (expense-tool webhook on submit; bulk replay for backfill audits)
             │
             ▼
[1. extract_receipt]  (agent: `extractor` over `pdf-extract` / `ocr` output)
  → vendor, amount, currency, category, date, location
             │
             ▼
[2. governor: `schema-validator`]
  (extracted JSON conforms to receipt schema; loops back to step 1 with
   feedback on parse failure, max 2 retries)
             │
             ▼
[3. fetch_employee_context]
  (knowledge: `org-chart-kg` — role, level, location, project codes)
             │
             ▼
[4. load_policy]
  (knowledge: `compliance-kb` + per-role expense caps — meal limits,
   travel class, alcohol policy by jurisdiction, prohibited categories)
             │
             ▼
[5. governor: `expense-policy-check`]
  (deterministic rule firing: per-category caps, frequency limits,
   prohibited-vendor checks; emits violation list + severity)
             │
             ▼
[6. score_anomaly]  (gomlx_inference: `anomaly-detector`)
  (per-employee baseline; flags out-of-pattern spends even when policy-clean)
             │
             ▼
[7. classify_disposition]  (agent: `classifier`)
  → auto-approve | needs-receipt-clarity | needs-manager-review |
    needs-finance-review | reject
             │
             ▼
[8. governor: `approval-policy`]
  (manager review required above $X; finance review above $Y;
   prohibited-category violations → reject regardless)
             │
             ▼
[9. HITL Approval Gate]  (conditional, with reminder cadence)
             │
             ├──► [IF approved]  ──► step 10
             ├──► [IF rejected]  ──► [Notify employee + write outcome]
             ├──► [IF clarify]   ──► [Send back to employee with specific ask]
             │
             ▼
[10. post_to_erp]  (tool: integration adapter — Concur / Expensify / NetSuite)
             │
             ▼
[11. write_outcome]
  (memory: expense → violations → resolution → days-to-reimburse;
   trains future policy classifier and anomaly baselines)
=============================================================================

## Inputs

- receipt file + employee_id + claimed amount/category

## Step types

| #  | Step                     | Type             | Notes |
|----|--------------------------|------------------|-------|
| 1  | extract_receipt          | agent            | over OCR output |
| 2  | schema_validator         | governor         | retry loop |
| 3  | fetch_employee_context   | knowledge        | `org-chart-kg` |
| 4  | load_policy              | knowledge        | `compliance-kb` |
| 5  | policy_check             | governor         | `expense-policy-check` |
| 6  | score_anomaly            | gomlx_inference  | per-employee baseline |
| 7  | classify_disposition     | agent            | `classifier` |
| 8  | approval_policy          | governor         | tiered review |
| 9  | hitl_approval            | approval         | with clarify path |
| 10 | post_to_erp              | tool             | adapter |
| 11 | write_outcome            | memory           | trains future runs |

## Outputs

- decision per receipt with reason chain
- ERP entry on approval
- baseline + classifier training row

## Why it's a good demo

The deterministic governor (`expense-policy-check`) and the ML anomaly
score do different jobs: the governor catches policy violations, the model
catches *legal but suspicious* patterns. Showing both fire on the same
record is a clean demo of complementary primitives. Pairs with
`anomaly-detector` and `compliance-kb`.
