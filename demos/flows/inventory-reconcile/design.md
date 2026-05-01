=============================================================================
                       INVENTORY RECONCILIATION
=============================================================================

[Trigger] (nightly cron, or on-demand from ops)
             │
             ▼
[1. snapshot_systems]  (parallel tool calls)
  ├──► WMS / ERP system of record
  ├──► barcode-scanner activity log
  ├──► shipping carrier API (in-transit)
  └──► returns queue
             │
             ▼
[2. align_skus]  (rule: SKU normalization across vendor codes)
             │
             ▼
[3. compute_diffs]  (tool: `sql-query` — set diff per SKU per location)
  → expected_qty vs counted_qty vs in_transit
             │
             ▼
[4. classify_variance]  (agent: `classifier`)
  → cause: shrinkage | mis-scan | timing-skew | system-bug | unknown
             │
             ▼
[5. governor: `confidence-threshold`]
  (unknown causes auto-escalated to HITL queue rather than auto-adjusted)
             │
             ▼
[6. score_anomaly]  (gomlx_inference: `anomaly-detector`)
  (per-SKU baseline; flags SKUs whose variance is unprecedented)
             │
             ▼
[7. propose_adjustments]  (agent: structured-output extractor → adjustment_journal)
             │
             ▼
[8. governor: `approval-policy`]
  (adjustments above $X or above N units require manager sign-off)
             │
             ▼
[9. HITL Approval Gate]
             │
             ├──► [IF rejected] ──► [Open investigation ticket]
             │
             ▼
[10. post_adjustments]  (tool: integration adapter to WMS/ERP)
             │
             ▼
[11. notify_ops]  (tool: `slack-post` — daily summary, anomalies highlighted)
             │
             ▼
[12. write_outcome]
  (memory: SKU → variance → cause → adjustment; feeds future
   anomaly thresholds and shrinkage forecasting)
=============================================================================

## Inputs

- list of warehouses/locations
- snapshot timestamp (default: now)

## Step types

| #  | Step                 | Type             | Notes |
|----|----------------------|------------------|-------|
| 1  | snapshot_systems     | tool             | parallel |
| 2  | align_skus           | rule             | normalization |
| 3  | compute_diffs        | tool             | `sql-query` |
| 4  | classify_variance    | agent            | `classifier` |
| 5  | confidence_gate      | governor         | `confidence-threshold` |
| 6  | score_anomaly        | gomlx_inference  | `anomaly-detector` |
| 7  | propose_adjustments  | agent            | structured output |
| 8  | approval_policy      | governor         | dollar/unit gate |
| 9  | hitl_approval        | approval         | conditional |
| 10 | post_adjustments     | tool             | WMS/ERP adapter |
| 11 | notify_ops           | tool             | `slack-post` |
| 12 | write_outcome        | memory           | trains anomaly model |

## Outputs

- adjustment journal entries (approved or queued)
- daily variance summary
- per-SKU history row

## Why it's a good demo

Operations-heavy workflow that maps cleanly onto Railyard's primitives
without contortion. Shows ML-assisted classification combined with
deterministic dollar-threshold approval gating. Pairs with
`anomaly-detector` and `cmdb-asset-kg` (analogous KG pattern).
