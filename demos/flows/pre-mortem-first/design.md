=============================================================================
                       THE PRE-MORTEM-FIRST WORKFLOW
=============================================================================

A workflow whose first phase is structured failure-imagination. Before any
plan executes, the system spends a budgeted slice of time and tokens
*hunting for the ways this will fail*, ranks the failure modes, and only
then proceeds — with the top failure modes converted into runtime guards.

The premise: the system that imagines its failures earnestly performs
better than the system that doesn't. The pre-mortem is not a ritual; it
generates concrete instrumentation.

[Caller-Provided Plan] (e.g. "deploy v2 of payments service to production")
             │
             ▼
=============================================================================
                  PHASE 1: FAILURE IMAGINATION (BUDGETED)
=============================================================================
[1. allocate_budget]
  (governor: `cost-ceiling` carves N% of run budget for the pre-mortem,
   typically 15–25%; remainder reserved for execution)
             │
             ▼
[2. retrieve_priors]
  (tool: `vector-search` over `decision-journal-kg` + `anti-pattern-kb`
   + `past-decision-memory`; pulls failures of plans that *looked* like this)
             │
             ▼
[3. spawn_panel]  (agent: `panel-of-five` — PM, SRE, Sec, IC, Exec critiques)
             │
             ▼
[4. devils_advocate_pass]  (agent: `devils-advocate`)
  (governed by `must-disagree` — concession=null is enforced)
             │
             ▼
[5. counterfactual_mutate]  (tool: `counterfactual-mutator`)
  (perturbs the plan's stated assumptions, surfaces brittle dependencies)
             │
             ▼
[6. synthesize_failure_modes]  (agent: classifier + extractor)
  → ranked list:
      { scenario, probability, blast_radius, early_warning_signal,
        proposed_guard, would_change_my_mind_if }
             │
             ▼
[7. governor: `pre-mortem-required`]
  (refuses to advance if fewer than N high-severity scenarios identified
   OR if any lacks an early_warning_signal — the demand for instrumentation
   is the point)
             │
             ▼
=============================================================================
              PHASE 2: GUARD INSTALLATION (DETERMINISTIC LAYER)
=============================================================================
[8. compile_guards]
  (each top-K failure mode becomes a runtime governor:
   • `early_warning_signal` → CLIPS rule that watches for it
   • `blast_radius` → tool-allowlist or rate-limit narrowing
   • `would_change_my_mind_if` → rollback trigger condition)
             │
             ▼
[9. install_guards]
  (governors are loaded into the run scope, not the global scope —
   they expire when the workflow does)
             │
             ▼
[10. write_pre_mortem_record]
  (knowledge: appended to `decision-journal-kg` immutably with plan hash)
             │
             ▼
=============================================================================
                  PHASE 3: EXECUTION (INSTRUMENTED)
=============================================================================
[11. execute_plan]
  (the original caller-plan now runs, but inside the guards installed
   in Phase 2; any guard tripping triggers compensating action)
             │
             ├──► [IF guard trips] ──► [11a. handle_per_guard_route]
             │                          (rollback / pause / escalate per guard)
             │
             └──► [IF clean]
                         │
                         ▼
=============================================================================
                  PHASE 4: SCORING (LEARNING LAYER)
=============================================================================
[12. score_pre_mortem]
  (which predicted failure modes happened? which surprises weren't predicted?)
             │
             ▼
[13. update_anti_pattern_kb]
  (knowledge: `anti-pattern-kb` ← outcome row;
   `decision-journal-kg` ← outcome edge appended)
             │
             ▼
[14. ml_signal: `governor-rule-miner`]
  (over time, repeated successful guards from pre-mortems get promoted
   into permanent CLIPS rules — the system learns its own policies)
=============================================================================

## Inputs

- caller plan (free-form)
- run budget ($, tokens, time)
- caller stakes (low / medium / high — affects pre-mortem budget %)

## Step types

| #     | Step                       | Type        |
|-------|----------------------------|-------------|
| 1     | allocate_budget            | governor    |
| 2     | retrieve_priors            | tool        |
| 3     | spawn_panel                | agent       |
| 4     | devils_advocate_pass       | agent + governor |
| 5     | counterfactual_mutate      | tool        |
| 6     | synthesize_failure_modes   | agent       |
| 7     | pre-mortem-required        | governor    |
| 8–9   | compile + install guards   | tool (CLIPS bootstrapper) |
| 10    | write_pre_mortem_record    | knowledge   |
| 11    | execute_plan               | sub-workflow (caller's plan) |
| 12–13 | score + update             | conditional + knowledge |
| 14    | governor-rule-miner signal | gomlx_inference (async) |

## Outputs

- executed plan with full pre-mortem record
- N installed run-scope governors (with provenance back to imagined failures)
- scoring row that closes the loop after execution

## Why it's a good demo

Three reasons it's worth more than its weight in tokens:

1. **It's the workflow that uses every other primitive deliberately.** Tools
   (`counterfactual-mutator`, `vector-search`), agents (`panel-of-five`,
   `devils-advocate`), governors (`pre-mortem-required`, plus
   dynamically-compiled ones), knowledge (`anti-pattern-kb`,
   `decision-journal-kg`), and ML (`governor-rule-miner`) all appear here,
   each doing real work. It is a single-page tour of the platform.

2. **It demonstrates *runtime governor compilation*.** Most platforms
   treat governance as static config. Here, the workflow generates
   governance from imagined failures. That capability — turn failure
   imagination into runtime instrumentation, automatically — is unusual
   enough to be a memorable showcase.

3. **It closes the loop.** The pre-mortem isn't just hand-wringing.
   Failure modes get scored against actual outcomes, and the
   `governor-rule-miner` ML model promotes durable wins into permanent
   rules. The system gets *less surprising over time*, and the demo shows
   the mechanism.

## Pairs naturally with

- `devils-advocate` (agent) — used inside Phase 1
- `pre-mortem-required` (governor) — enforces Phase 1's exit condition
- `decision-journal-kg` (knowledge) — receives Phase 2's record and Phase 4's outcome
- `governor-rule-miner` (ML) — closes the long-horizon learning loop
