=============================================================================
                          BACKUP VERIFICATION
=============================================================================

[Trigger] (daily cron, or post-backup webhook from backup tooling)
             │
             ▼
[1. enumerate_backups]  (tool: cloud SDK list — S3, GCS, Azure Blob)
             │
             ▼
[2. check_freshness]  (rule: each protected resource has a backup
   within RPO window; missing → SEV1)
             │
             ▼
[3. check_integrity]  (parallel tool calls)
  ├──► checksum verification
  ├──► encryption-at-rest assertion
  └──► size-vs-historical sanity (gomlx_inference: `outlier-detector`)
             │
             ▼
[4. governor: `confidence-threshold`]
  (size anomalies routed to HITL queue — backups that are too small are
   silent corruption, backups that are too large may be runaway logging)
             │
             ▼
[5. spin_restore_sandbox]  (tool: ephemeral compute via cloud SDK)
             │
             ▼
[6. test_restore]  (tool: actually restore N% sampled backups into sandbox)
  → restore_succeeded, post_restore_row_counts, integrity_query_results
             │
             ▼
[7. governor: `cost-ceiling`]
  (sandbox spend capped per run; over-budget → halt + alert)
             │
             ▼
[8. classify_result]  (agent: `classifier`)
  → status: verified | partial | failed | inconclusive
             │
             ▼
[9. branch_action]  (conditional)
  ├──► verified     → record + carry on
  ├──► partial      → file ticket
  ├──► failed       → page on-call (this is the only test that matters)
  └──► inconclusive → re-run once with isolation flags
             │
             ▼
[10. teardown_sandbox]  (tool: cloud SDK delete; always runs even on failure)
             │
             ▼
[11. write_outcome]
  (memory: protected resource → verification history → MTTF;
   feeds RPO/RTO dashboard and audit reports)
=============================================================================

## Inputs

- protected resource list (databases, object stores, configs)
- RPO + RTO targets per resource

## Step types

| #  | Step               | Type             | Notes |
|----|--------------------|------------------|-------|
| 1  | enumerate_backups  | tool             | cloud SDK |
| 2  | check_freshness    | rule             | RPO window |
| 3  | check_integrity    | tool + ML        | parallel; `outlier-detector` on size |
| 4  | confidence_gate    | governor         | size-anomaly HITL |
| 5  | spin_sandbox       | tool             | ephemeral compute |
| 6  | test_restore       | tool             | actually restore samples |
| 7  | cost_ceiling       | governor         | sandbox spend cap |
| 8  | classify_result    | agent            | `classifier` |
| 9  | branch_action      | conditional      | per status |
| 10 | teardown_sandbox   | tool             | always runs |
| 11 | write_outcome      | memory           | feeds dashboards |

## Outputs

- verification record per resource
- pages / tickets per failure
- audit-ready restore-test trail

## Why it's a good demo

The unsexy workflow that everyone needs and almost nobody automates well.
Demonstrates `cost-ceiling` enforcement during ephemeral spin-up, ML-based
size anomaly detection, and a real "actually restore the bytes" verify
step. Pairs with `outlier-detector` and `cost-ceiling`.
