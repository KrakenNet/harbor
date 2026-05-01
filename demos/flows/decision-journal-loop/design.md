=============================================================================
                       THE DECISION-JOURNAL LOOP
=============================================================================

A meta-workflow that wraps any multi-step plan with an immutable
decision journal: rationale captured before, outcome captured after,
both linked to the trace tree that produced them. Every consequential
plan in the platform inherits this scaffolding by composition. The
journal becomes a first-class institutional memory — replayable,
queryable, and used by every other learning workflow.

The premise: a decision without a recorded rationale is a guess; a
decision without a recorded outcome is a story. Railyard's persistent
runtime makes both ends cheap to capture in the same workflow object,
so neither half is left to human discipline.

[Trigger] (any caller workflow that opts in via `journal: true`,
 OR any decision above the stakes_threshold for the tenant)
             │
             ▼
=============================================================================
            PHASE 1: RATIONALE COMMIT (PRE-DECISION LAYER)
=============================================================================
[1. canonicalize_plan]
  (extracts: goal, alternatives_considered, chosen_alternative,
   inputs, expected_outcome, success_criteria, blast_radius,
   reversibility, plan_hash)
             │
             ▼
[2. retrieve_context]
  (knowledge: parallel pull from `decision-journal-kg` for related past
   decisions, `anti-pattern-kb` for known failure modes,
   `disagreement-archive` for unresolved debates touching this domain)
             │
             ▼
[3. agent: `extractor` → rationale_card]
  → fields:
      • why_this_alternative
      • why_not_each_other_alternative
      • assumptions_being_made
      • would_change_my_mind_if
      • who_we_are_betting_against (the implicit counter-position)
      • reversibility (one-way / two-way / unclear)
             │
             ▼
[4. governor: `show-your-work`]
  (every rationale field must cite evidence — bare claims rejected)
             │
             ▼
[5. governor: `conviction-tax`]
  (high-confidence claims with no priors in `past-decision-memory` are
   penalized — first-time confidence costs more)
             │
             ▼
[6. governor: `decision-diary`]
  (writes the rationale row to `decision-journal-kg` IMMUTABLY before
   any side-effecting verb fires; the workflow cannot proceed otherwise —
   this is the load-bearing pre-commit)
             │
             ▼
=============================================================================
            PHASE 2: REVERSIBILITY GATE (PRE-EXECUTION LAYER)
=============================================================================
[7. classify_reversibility]  (agent: `classifier`)
  → reversibility: one_way | two_way | unclear
             │
             ▼
[8. governor: `are-you-sure`]
  (one_way decisions trigger a mandatory self-doubt pass — the agent
   must produce a "what would make me NOT do this" paragraph; this
   pass is itself logged immutably)
             │
             ▼
[9. governor: `hitl-trigger`]
  (one_way + high blast_radius → human ack required;
   two_way auto-proceeds; unclear → escalate)
             │
             ▼
[10. governor: `pre-mortem-required`]
  (for one_way decisions, calls into `pre-mortem-first` workflow as a
   sub-flow before execution — composition between two creative
   workflows the platform encourages)
             │
             ▼
=============================================================================
            PHASE 3: EXECUTION (INSTRUMENTED LAYER)
=============================================================================
[11. execute_plan]
  (sub-workflow: the actual caller plan; runs inside the rationale
   row's plan_hash scope so every subsequent span is traceable back
   to the rationale)
             │
             ▼
[12. write_intermediate_signals]
  (loop: at each declared check_at offset, captures leading-indicator
   state from `forecast-then-score` watchers — these are mid-flight
   evidence, not the final outcome)
             │
             ▼
=============================================================================
            PHASE 4: SCHEDULED OUTCOME (TIME-SHIFTED LAYER)
=============================================================================
[13. schedule_outcome_capture]
  (loop step: sleep until `now + outcome_horizon`; horizon defaults
   to 7d, override per decision class — incidents 14d, hires 90d,
   contracts 1y)
             │
             ▼
        ─── workflow suspends here, persistent across restarts ───
             │
             ▼
[14. wake + fetch_actual]
  (parallel tool calls: metrics, follow-ups, tickets, customer signals,
   any human comments tagged to plan_hash)
             │
             ▼
[15. governor: `fact-half-life`]
  (refuses to use facts older than the rationale row — the scoring
   window is bounded)
             │
             ▼
[16. compute_outcome_delta]  (rule: per-criterion predicted vs actual)
             │
             ▼
[17. classify_outcome]  (agent: `classifier`)
  → verdict: confirmed | partial | wrong | hijacked-by-confound |
    inconclusive
             │
             ▼
[18. agent: `five-whys`] (only on wrong / partial)
  (recursive root-cause until first principles)
             │
             ▼
[19. governor: `anti-sycophancy`]
  (no celebratory framing on a "wrong" verdict)
             │
             ▼
=============================================================================
            PHASE 5: ARCHIVE + COMPOUND (FEEDBACK LAYER)
=============================================================================
[20. append_outcome_edge]
  (knowledge: outcome edge appended to the original
   `decision-journal-kg` node — never replaces, always appends; the
   rationale and the outcome both live forever)
             │
             ▼
[21. branch_archive_writes]  (parallel)
  ├──► confirmed       → `past-decision-memory` win row
  ├──► wrong / partial → `anti-pattern-kb` row + `five-whys` chain
  ├──► inconclusive    → `disagreement-archive` (kept open on purpose)
  └──► hijacked        → `open-questions-kb` (the confound is a question)
             │
             ▼
[22. ml_signal: cross-loop calibrators]
  ├──► `governor-rule-miner` (recurring confirmed patterns → CLIPS rules)
  ├──► forecast calibrator (per-class confidence curves)
  ├──► `memory-utility-scorer` (which past decisions were retrieved
       most usefully at step 2)
             │
             ▼
[23. enqueue_replay]  (conditional, only on wrong / partial)
  (calls `counterfactual-replay` to score the path-not-taken — the
   loop closes by feeding the next learning workflow)
             │
             ▼
[24. notify_stakeholders]
  (tool: Slack — original decision-makers tagged with the verdict
   they unknowingly committed to N days ago; "your rationale survived /
   didn't survive contact with reality")
=============================================================================

## Inputs

- caller plan (free-form)
- decision class (drives outcome_horizon and gate thresholds)
- stakes flag (low / medium / high)

## Step types

| #     | Step                          | Type                  |
|-------|-------------------------------|-----------------------|
| 1     | canonicalize_plan             | rule                  |
| 2     | retrieve_context              | knowledge             |
| 3     | rationale_card                | agent                 |
| 4     | show_your_work                | governor              |
| 5     | conviction_tax                | governor              |
| 6     | decision_diary                | governor              |
| 7     | classify_reversibility        | agent                 |
| 8     | are_you_sure                  | governor              |
| 9     | hitl_trigger                  | governor              |
| 10    | pre_mortem_required           | sub-workflow          |
| 11    | execute_plan                  | sub-workflow          |
| 12    | write_intermediate_signals    | loop                  |
| 13    | schedule_outcome_capture      | loop (sleep)          |
| 14    | fetch_actual                  | tool (parallel)       |
| 15    | fact_half_life                | governor              |
| 16    | compute_outcome_delta         | rule                  |
| 17    | classify_outcome              | agent                 |
| 18    | five_whys                     | agent (creative)      |
| 19    | anti_sycophancy               | governor              |
| 20    | append_outcome_edge           | knowledge             |
| 21    | branch_archive_writes         | conditional + knowledge|
| 22    | cross_loop_calibrators        | gomlx_inference       |
| 23    | enqueue_replay                | sub-workflow          |
| 24    | notify_stakeholders           | tool                  |

## Outputs

- immutable rationale row (Phase 1)
- pre-execution self-doubt artifact (Phase 2)
- intermediate-signal trail (Phase 3)
- appended outcome edge with verdict (Phase 4)
- archive writes across four KGs (Phase 5)
- triggered counterfactual replay on misses

## Pairs naturally with

- `decision-journal-kg` (knowledge) — the load-bearing archive
- `decision-diary` (governor) — Phase 1 enforcement
- `are-you-sure` (governor) — Phase 2 self-doubt enforcement
- `pre-mortem-first` (workflow) — Phase 2 sub-flow on irreversibles
- `forecast-then-score` (workflow) — sister workflow; can be composed in
- `trial-and-retro` (workflow) — sister workflow; this is its more
  structured, multi-archive cousin
- `counterfactual-replay` (workflow) — Phase 5 trigger on misses
- `governor-rule-miner` (ML) — consumes Phase 5 patterns into rules
- `past-decision-memory` (knowledge) — Phase 5 win archive
- `anti-pattern-kb` (knowledge) — Phase 5 loss archive
- `disagreement-archive` (knowledge) — Phase 5 inconclusive archive
- `open-questions-kb` (knowledge) — Phase 5 confound archive

## Why it's a good demo

Three reasons:

1. **It is the *mechanism* the platform uses to remember.** Every other
   creative workflow in the catalog reads from or writes to
   `decision-journal-kg`. This is the workflow that puts rows in it —
   rationally, with rationale and outcome as opposite ends of a single
   persistent workflow object. If a customer is going to internalize
   one Railyard idea, this is it.

2. **It is meta-composable.** It wraps any other workflow. `incident-
   response`, `invoice-extract-approve`, `cve-remediation` — all of
   them can be wrapped by `decision-journal-loop` as a sub-flow,
   inheriting rationale capture, reversibility gating, scheduled
   scoring, and four-archive feedback. One workflow, every other
   workflow gets institutional memory for free.

3. **It models the rationale ↔ outcome edge as a graph relation.**
   Most "decision logging" tools produce flat rows. Railyard's KG
   model lets the rationale node and the outcome edge be queried
   together, replayed against alternatives (`counterfactual-replay`),
   mined for rules (`governor-rule-miner`), and decayed by half-life
   (`knowledge-half-life-sweep`). The journal isn't passive storage —
   it's the substrate the rest of the platform learns on.
