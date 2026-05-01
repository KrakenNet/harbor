=============================================================================
                          WEEKLY ROLL-UP
=============================================================================

[Trigger] (cron: Friday 16:00 local per team)
             │
             ▼
[1. resolve_team_scope]
  (knowledge: `org-chart-kg` — team members, OKRs, repos, projects)
             │
             ▼
[2. parallel_collect]
  ├──► shipped: GitHub merged PRs + Linear closed issues
  ├──► in_flight: open PRs and active issues
  ├──► incidents: post-mortems closed this week
  ├──► metrics: KPI deltas vs previous week
  ├──► hires/departures: HRIS deltas
  └──► customer_signals: NPS / churn-risk score deltas
             │
             ▼
[3. dedupe_and_attribute]  (rule: roll up by sub-team + theme)
             │
             ▼
[4. classify_each]  (agent: `classifier`)
  → wins | risks | blockers | noise
             │
             ▼
[5. summarize]  (agent: `summarizer`, tiered)
  → tier1: leadership-headline (3 bullets)
  → tier2: per-section detail
  → tier3: links + raw rows
             │
             ▼
[6. governor: `confidence-threshold`]
  (low-confidence "risks" demoted to "watch list" to avoid alarmism;
   audit row preserved either way)
             │
             ▼
[7. governor: `anti-sycophancy`]
  (kills celebratory framing not supported by metric deltas — wins must
   show the number that supports them)
             │
             ▼
[8. governor: `output-length-cap`]
  (leadership doc <= one screen; eng-team doc <= one page)
             │
             ▼
[9. governor: `tone-calibrator`]
  (per-audience: leadership = headline-first, engineers = detail-first)
             │
             ▼
[10. render]  (tool: `markdown-html` per audience)
             │
             ▼
[11. branch_distribute]  (conditional)
  ├──► leadership digest → email
  ├──► team channel post → Slack
  └──► immutable archive → docs site + provenance edge to source items
             │
             ▼
[12. write_outcome]
  (memory: roll-up → which items got cited in next week's exec review;
   feeds future "what matters" classifier and `memory-utility-scorer`)
=============================================================================

## Inputs

- team_id + week boundary
- audience set (default: leadership + team)

## Step types

| #  | Step                    | Type        | Notes |
|----|-------------------------|-------------|-------|
| 1  | resolve_team_scope      | knowledge   | `org-chart-kg` |
| 2  | parallel_collect        | tool        | fan-out |
| 3  | dedupe_and_attribute    | rule        | sub-team + theme |
| 4  | classify_each           | agent       | `classifier` |
| 5  | summarize               | agent       | `summarizer` (tiered) |
| 6  | confidence_threshold    | governor    | demote low-confidence |
| 7  | anti_sycophancy         | governor    | requires metric backing |
| 8  | output_length_cap       | governor    | per-audience caps |
| 9  | tone_calibrator         | governor    | per audience |
| 10 | render                  | tool        | `markdown-html` |
| 11 | branch_distribute       | conditional | per audience |
| 12 | write_outcome           | memory      | trains relevance |

## Outputs

- audience-specific roll-up docs
- archived doc with provenance links to source items
- citation-feedback row

## Why it's a good demo

Almost every leader does this manually every Friday. The
`anti-sycophancy` governor refusing celebratory bullets without metric
backing is a memorable, polarizing demo moment. Pairs with
`anti-sycophancy`, `summarizer`, and `org-chart-kg`.
