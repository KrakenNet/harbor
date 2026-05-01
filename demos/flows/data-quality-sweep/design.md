=============================================================================
                          DATA QUALITY SWEEP
=============================================================================

[Trigger] (nightly cron over warehouse + production OLTP replicas)
             │
             ▼
[1. load_rules]
  (knowledge: data-quality-rules KB — null-rate, range, FK integrity,
   uniqueness, freshness, schema-drift contracts)
             │
             ▼
[2. select_targets]  (rule: tables tagged for sweep, sampled by criticality tier)
             │
             ▼
[3. run_checks]  (parallel tool calls per table)
  ├──► null-rate query
  ├──► distribution query
  ├──► FK orphan query
  ├──► duplicate-key query
  └──► freshness (max(updated_at) age)
             │
             ▼
[4. score_each]  (gomlx_inference: `outlier-detector` over historical baselines)
             │
             ▼
[5. classify_severity]  (agent: `classifier`)
  → SEV1 (broken contract) | SEV2 (drift) | SEV3 (warning) | SEV4 (noise)
             │
             ▼
[6. governor: `confidence-threshold`]
  (low-confidence severities flagged for HITL review rather than paged)
             │
             ▼
[7. propose_remediation]  (agent: `extractor` → remediation_card)
  → SQL fix, owner team, blast radius, rollback note
             │
             ▼
[8. governor: `decision-diary`]
  (any auto-applied fix gets an immutable rationale row first)
             │
             ▼
[9. branch_action]  (conditional)
  ├──► SEV1 → page on-call + open ticket
  ├──► SEV2 → file ticket + ping owner
  ├──► SEV3 → append to weekly digest
  └──► SEV4 → suppress
             │
             ▼
[10. notify]  (tool: PagerDuty / Linear / Slack per severity)
             │
             ▼
[11. write_outcome]
  (memory: rule → trip → remediation → time-to-fix; trains future
   severity classifier and outlier baselines)
=============================================================================

## Inputs

- warehouse + replica connection strings
- ruleset selection (default: all tagged tables)

## Step types

| #  | Step                | Type             | Notes |
|----|---------------------|------------------|-------|
| 1  | load_rules          | knowledge        | DQ rules KB |
| 2  | select_targets      | rule             | tagged + sampled |
| 3  | run_checks          | tool             | parallel `sql-query` |
| 4  | score_each          | gomlx_inference  | `outlier-detector` |
| 5  | classify_severity   | agent            | `classifier` |
| 6  | confidence_gate     | governor         | HITL on low confidence |
| 7  | propose_remediation | agent            | structured output |
| 8  | decision_diary      | governor         | rationale before action |
| 9  | branch_action       | conditional      | per severity |
| 10 | notify              | tool             | per channel |
| 11 | write_outcome       | memory           | trains baselines |

## Outputs

- DQ scorecard per table
- tickets / pages per SEV
- baseline updates for next run

## Why it's a good demo

Data engineers immediately get it. Demonstrates parallel fan-out, ML
baseline scoring, and the decision-diary governor pattern that protects
auto-remediation from blame ambiguity. Pairs with `outlier-detector` and
`anomaly-detector`.
