=============================================================================
                          STALE RECORD CLEANUP
=============================================================================

[Trigger] (weekly cron — Sunday 02:00, low-traffic window)
             │
             ▼
[1. load_retention_policy]
  (knowledge: `compliance-kb` — per-table retention, legal hold flags,
   tenant-level overrides)
             │
             ▼
[2. enumerate_candidates]  (tool: `sql-query`)
  → rows past retention, no legal hold, no recent reference
             │
             ▼
[3. governor: `compliance-scan`]
  (cross-checks against active legal holds, audit subpoenas, e-discovery
   tags — anything tripped is removed from the candidate set)
             │
             ▼
[4. classify_record]  (agent: `classifier`)
  → action: delete | archive-cold | tombstone | keep
             │
             ▼
[5. governor: `loop-breaker`]
  (refuses to act on the same record-set fingerprint twice in a week —
   prevents thrash from a misconfigured policy)
             │
             ▼
[6. governor: `approval-policy`]
  (tenant-wide deletes above N records require ops approval;
   single-record deletions auto-approved)
             │
             ▼
[7. HITL Approval Gate]  (conditional, with 48h timeout → defer to next run)
             │
             ▼
[8. snapshot_before]  (tool: warehouse export to cold object storage,
   keyed by run_id — irreversibility insurance)
             │
             ▼
[9. governor: `decision-diary`]
  (immutable rationale row per record-set before any DELETE fires)
             │
             ▼
[10. execute_action]  (tool dispatch)
  ├──► delete    → `sql-query` DELETE
  ├──► archive   → move to cold tier + tombstone
  ├──► tombstone → soft-delete with TTL
  └──► keep      → no-op
             │
             ▼
[11. verify_count]  (rule: actual deleted count must match planned)
             │
             ├──► [IF mismatch] ──► [Page on-call + auto-rollback from snapshot]
             │
             ▼
[12. write_outcome]
  (memory: run_id → records affected → snapshot URI → approver;
   feeds future retention-policy refinement)
=============================================================================

## Inputs

- target tables (default: all tagged with retention policy)
- dry-run flag

## Step types

| #  | Step                  | Type      | Notes |
|----|-----------------------|-----------|-------|
| 1  | load_retention_policy | knowledge | `compliance-kb` |
| 2  | enumerate_candidates  | tool      | `sql-query` |
| 3  | compliance_filter     | governor  | `compliance-scan` |
| 4  | classify_record       | agent     | `classifier` |
| 5  | loop_breaker          | governor  | thrash protection |
| 6  | approval_policy       | governor  | bulk-delete gate |
| 7  | hitl_approval         | approval  | 48h timeout |
| 8  | snapshot_before       | tool      | cold-storage export |
| 9  | decision_diary        | governor  | rationale before delete |
| 10 | execute_action        | tool      | dispatched action |
| 11 | verify_count          | rule      | sanity check |
| 12 | write_outcome         | memory    | run history |

## Outputs

- snapshot artifact per run
- delete/archive log
- audit-ready decision-diary trail

## Why it's a good demo

Irreversible actions are the highest-stakes test of governance, and this
workflow stacks every relevant safeguard: `loop-breaker`, `decision-diary`,
pre-action snapshot, post-action verification. Pairs with `compliance-kb`
and `decision-journal-kg`.
