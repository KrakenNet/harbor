=============================================================================
                       API CONTRACT DIFF ALERT
=============================================================================

[Trigger] (CI hook on `openapi.yaml` change, or scheduled probe of partner APIs)
             │
             ▼
[1. fetch_specs]  (parallel tool calls)
  ├──► current spec from this repo
  ├──► previous spec from prior commit / last successful run
  └──► partner specs via `http-fetch` to their docs URLs
             │
             ▼
[2. parse_specs]  (tool: OpenAPI / GraphQL / gRPC schema parser)
             │
             ▼
[3. structural_diff]  (rule: deterministic schema diff)
  → added | removed | renamed | type-changed | required-flipped | enum-changed
             │
             ▼
[4. classify_breakage]  (agent: `classifier`)
  → breaking | non-breaking | semantic-only | unknown
             │
             ▼
[5. resolve_consumers]
  (knowledge: `code-dependency-kg` — which services / clients call which
   endpoints; produces blast-radius set)
             │
             ▼
[6. governor: `show-your-work`]
  (the breakage classification must include which spec rule triggered it
   and which consumer the call signature would break)
             │
             ▼
[7. propose_compat_strategy]  (agent: `extractor` → migration plan)
  → strategies: add deprecation header | dual-publish | versioned route |
    coordinated cutover
             │
             ▼
[8. governor: `approval-policy`]
  (any breaking change to a public-facing endpoint requires API-council
   sign-off; internal-only breaks need just the consumer team's owner)
             │
             ▼
[9. branch_action]  (conditional)
  ├──► non-breaking   → record + ship
  ├──► semantic-only  → ping consumers + ship
  ├──► breaking       → file ADR + open coordination thread
  └──► unknown        → HITL review
             │
             ▼
[10. notify_consumers]  (tool: per-team Slack + GitHub mention)
             │
             ▼
[11. write_outcome]
  (memory: spec_hash → diff → strategy → eventual breakage incidents;
   trains future breakage classifier)
=============================================================================

## Inputs

- spec source (repo path or URL)
- baseline ref (previous commit or last sync run)

## Step types

| #  | Step                      | Type        | Notes |
|----|---------------------------|-------------|-------|
| 1  | fetch_specs               | tool        | parallel |
| 2  | parse_specs               | tool        | schema parser |
| 3  | structural_diff           | rule        | deterministic |
| 4  | classify_breakage         | agent       | `classifier` |
| 5  | resolve_consumers         | knowledge   | `code-dependency-kg` |
| 6  | show_your_work            | governor    | requires evidence |
| 7  | propose_compat_strategy   | agent       | `extractor` |
| 8  | approval_policy           | governor    | per scope |
| 9  | branch_action             | conditional | per category |
| 10 | notify_consumers          | tool        | Slack + GitHub |
| 11 | write_outcome             | memory      | trains classifier |

## Outputs

- per-endpoint diff report with blast radius
- migration plan
- approval and notification trail

## Why it's a good demo

Platform / API teams immediately recognize the pain. Combines deterministic
diff with KG-based consumer resolution to produce blast radius — the
expensive-to-maintain piece every team builds badly themselves. Pairs with
`code-dependency-kg` and `show-your-work`.
