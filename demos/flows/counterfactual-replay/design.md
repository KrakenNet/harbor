=============================================================================
                       THE COUNTERFACTUAL REPLAY WORKFLOW
=============================================================================

A workflow that re-runs past decisions on alternative paths and grades
each. The system takes a closed past decision (with known outcome),
deliberately mutates the inputs or the chosen branch, replays the
workflow inside a sandbox, and produces a counterfactual grade: what
would have happened if we'd done it differently?

The premise: regret is information. Most platforms throw away every path
not taken. Railyard records the trace, so the path-not-taken is
reconstructible — and once reconstructible, it can be scored.

[Trigger] (closed decision in `decision-journal-kg` reaches outcome maturity,
 OR analyst-initiated "what if?" replay)
             │
             ▼
=============================================================================
            PHASE 1: ANCHOR THE ORIGINAL (DETERMINISTIC LAYER)
=============================================================================
[1. resolve_decision]
  (knowledge: `decision-journal-kg` — pull rationale, branch chosen,
   inputs, outcome, learnings, plan_hash)
             │
             ▼
[2. retrieve_trace]
  (tool: `provenance-tracer` walks the original span tree;
   model versions, prompt artifacts, tool calls all pinned)
             │
             ▼
[3. governor: `cost-ceiling`]
  (counterfactual replay is exploratory — caps spend per replay so a
   curiosity-driven sweep can't burn the budget)
             │
             ▼
=============================================================================
            PHASE 2: GENERATE COUNTERFACTUALS (DIVERGENT FAN-OUT)
=============================================================================
[4. propose_alternatives]  (agent: `extractor`)
  → ranked list of plausible alternatives:
      • alt_branches: paths the conditional could have taken
      • alt_inputs: minimal mutations to the input that would flip a gate
      • alt_models: same prompt, different model class
      • alt_prompts: prior prompt-artifact versions
      • alt_tools: tool-allowlist variants
             │
             ▼
[5. counterfactual_mutate]  (tool: `counterfactual-mutator`)
  (for each alt_input, perturbs minimally until the original verdict flips —
   surfaces the brittle threshold)
             │
             ▼
[6. spawn_replays]  (loop: parallel sub-workflows, one per alternative)
  each replay:
    │
    ├──► [tool: `time-travel-replayer` — re-runs span tree with the
    │    one chosen mutation; everything else identical]
    │
    ├──► [governor: `tool-allowlist` enforced per alt scenario]
    │
    └──► [emits: counterfactual_outcome row with full trace]
             │
             ▼
[7. governor: `loop-breaker`]
  (caps total replay count per original decision; refuses to keep
   re-replaying the same near-duplicate mutation)
             │
             ▼
=============================================================================
            PHASE 3: SCORE EACH PATH (LEARNING LAYER)
=============================================================================
[8. score_each]  (gomlx_inference: outcome scorer)
  (each replay's outcome scored against original metrics + side-effects:
   would it have hit the goal? blast radius? cost? latency? safety?)
             │
             ▼
[9. classify_each]  (agent: `classifier`)
  → verdict: dominated | tied | dominating | risky-but-better | unsafe
             │
             ▼
[10. governor: `show-your-work`]
  (every "dominating" verdict must cite the metric delta that justifies it —
   no narrative-only "it would have been better" claims)
             │
             ▼
[11. governor: `anti-sycophancy`]
  (kills "if only we had…" framing not backed by replay evidence)
             │
             ▼
=============================================================================
            PHASE 4: ARCHIVE + LEARN (FEEDBACK LAYER)
=============================================================================
[12. write_counterfactual_memory]
  (knowledge: `counterfactual-memory` row per alternative with grade,
   rationale, and link back to original `decision-journal-kg` node)
             │
             ▼
[13. propose_governor_update]  (agent: `extractor`)
  (if a dominating alternative reveals a brittle threshold, propose a
   CLIPS rule that would have caught the original mistake)
             │
             ▼
[14. ml_signal: `governor-rule-miner`]
  (over many replays, a recurring "would have been caught by rule X"
   pattern gets promoted into a permanent governor)
             │
             ▼
[15. notify_owner]  (tool: Slack — "your decision N had a dominating
   alternative; review the counterfactual?")
=============================================================================

## Inputs

- decision_id (from `decision-journal-kg`) OR replay-trigger criteria
- replay budget (count, $, time)
- mutation set (default: agent-proposed; analyst-overridable)

## Step types

| #     | Step                       | Type                |
|-------|----------------------------|---------------------|
| 1     | resolve_decision           | knowledge           |
| 2     | retrieve_trace             | tool                |
| 3     | cost_ceiling               | governor            |
| 4     | propose_alternatives       | agent               |
| 5     | counterfactual_mutate      | tool                |
| 6     | spawn_replays              | loop (sub-workflow) |
| 7     | loop_breaker               | governor            |
| 8     | score_each                 | gomlx_inference     |
| 9     | classify_each              | agent               |
| 10    | show_your_work             | governor            |
| 11    | anti_sycophancy            | governor            |
| 12    | write_counterfactual_memory| knowledge           |
| 13    | propose_governor_update    | agent               |
| 14    | governor_rule_miner_signal | gomlx_inference     |
| 15    | notify_owner               | tool                |

## Outputs

- counterfactual-memory rows per alternative path
- proposed governor rules from dominating paths
- Slack ping with replay summary

## Pairs naturally with

- `time-travel-replayer` (tool) — Phase 2 engine
- `counterfactual-mutator` (tool) — Phase 2 input perturbation
- `provenance-tracer` (tool) — Phase 1 span-tree walk
- `counterfactual-memory` (knowledge) — Phase 4 archive
- `decision-journal-kg` (knowledge) — Phase 1 source-of-truth
- `governor-rule-miner` (ML) — long-horizon learning loop
- `decision-journal-loop` (workflow) — provides the closed decisions to replay

## Why it's a good demo

Three reasons this workflow is more than the sum of its mutations:

1. **It turns traces into a learning corpus.** Most platforms record
   traces for debugging — read-once, then forgotten. Railyard's
   span-tree fidelity makes those traces *replayable* with one node
   swapped, which means every closed decision is the seed of N
   counterfactual training rows. The trace store stops being a debug
   log and becomes a regret database.

2. **It composes with `decision-journal-loop` to close a learning
   loop the platform itself owns.** `decision-journal-loop` writes the
   decision; this workflow scores the path-not-taken; `governor-rule-miner`
   promotes recurring wins. No human in the middle of the learning
   step — the platform earns its own policies.

3. **It demonstrates Railyard's governance stack on exploratory work.**
   Counterfactual exploration is the kind of work that quietly burns
   budgets and produces narrative without evidence. The `cost-ceiling`,
   `loop-breaker`, `show-your-work`, and `anti-sycophancy` governors
   keep the exploration honest — a memorable showcase of "governance
   isn't just for production."
