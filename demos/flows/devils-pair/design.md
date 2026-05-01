=============================================================================
                       THE DEVIL'S PAIR WORKFLOW
=============================================================================

A workflow that runs a primary strategy and an explicit opposing strategy
in parallel, scores both on the same evidence, and only then commits to
one. The two paths share inputs but cannot share state — they reason
independently. A judge layer, governed against agreement-bias, picks the
winner.

The premise: a single agent's plan is one sample from a distribution.
Pairing it with a deliberate adversary turns "the model said so" into
"the model and its opponent both saw the same evidence and one won." The
audit trail is the disagreement, not the verdict.

[Trigger] (high-stakes decision: deploy plan, contract change, model swap,
 architecture call — anything where being wrong is expensive)
             │
             ▼
=============================================================================
            PHASE 1: STRATEGIC FORK (PARALLEL DIVERGENCE)
=============================================================================
[1. canonicalize_inputs]
  (extract decision frame: goal, constraints, knowns, unknowns)
             │
             ▼
[2. governor: `cost-ceiling`]
  (paired execution roughly doubles spend; carve a cap up front and
   refuse the workflow if budget can't cover both branches plus the judge)
             │
             ▼
                                  │
                  ┌───────────────┴────────────────┐
                  ▼                                ▼
         ───── PRIMARY BRANCH ─────       ───── DEVIL BRANCH ─────
[3a. retrieve_priors]                 [3b. retrieve_anti_priors]
  (knowledge: `decision-journal-kg`)    (knowledge: `anti-pattern-kb` +
                                         `disagreement-archive` +
                                         `counterfactual-memory`)
                  │                                │
                  ▼                                ▼
[4a. plan_primary]                    [4b. plan_devil]
  (agent: domain planner)               (agent: `devils-advocate`,
                                         governed by `must-disagree` —
                                         concession=null enforced)
                  │                                │
                  ▼                                ▼
[5a. governor:                        [5b. governor:
     `show-your-work`]                     `show-your-work`]
                  │                                │
                  ▼                                ▼
[6a. agent: `steel-manner`]           [6b. agent: `steel-manner`]
  (rebuilds the OTHER branch's          (rebuilds the OTHER branch's
   strongest case before refuting)       strongest case before refuting)
                  │                                │
                  └───────────────┬────────────────┘
                                  ▼
=============================================================================
            PHASE 2: EVIDENCE-BOUND ADJUDICATION (JUDGE LAYER)
=============================================================================
[7. gather_shared_evidence]  (tool: `vector-search` against same corpus
   for both branches; the judge sees a fixed evidence set and the two
   plans only)
             │
             ▼
[8. agent: `panel-of-five`]
  (PM, SRE, Sec, IC, Exec critique each branch on the same evidence;
   each panelist outputs ranked verdict with reasoning)
             │
             ▼
[9. governor: `anti-sycophancy`]
  (rejects judge prose that compliments without committing — the judge
   must commit to a verdict, not punt to "both have merit")
             │
             ▼
[10. governor: `conviction-tax`]
  (penalizes high-confidence claims without citation in the judge
   output; uncertainty must be priced)
             │
             ▼
[11. score_branches]  (gomlx_inference: outcome predictor)
  → expected outcome per branch + delta
             │
             ▼
[12. classify_verdict]  (agent: `classifier`)
  → verdict: primary-wins | devil-wins | tied | both-flawed
             │
             ▼
=============================================================================
            PHASE 3: COMMIT + RECORD DISAGREEMENT (LEARNING LAYER)
=============================================================================
[13. branch_action]  (conditional)
  ├──► primary-wins → execute primary
  ├──► devil-wins   → execute devil (and write a high-priority record)
  ├──► tied         → escalate to HITL with both plans
  └──► both-flawed  → halt + open `disagreement-archive` thread
             │
             ▼
[14. governor: `decision-diary`]
  (immutable rationale row before execution)
             │
             ▼
[15. execute_winner]  (sub-workflow: the chosen branch's plan runs)
             │
             ▼
[16. write_disagreement_record]
  (knowledge: `disagreement-archive` row with both plans, the evidence
   set, the panel verdicts, and the chosen branch — kept *especially*
   when the verdict was close)
             │
             ▼
[17. ml_signal: branch-quality calibrator]
  (gomlx_inference: tracks which branch tends to win in which decision
   class; over time, branches that *never* win in a class get pruned
   from that class's `devil-pair` template)
             │
             ▼
[18. schedule_retro]  (calls `trial-and-retro` on the chosen branch —
   we still want to know if the winner was actually right)
=============================================================================

## Inputs

- decision frame (goal, constraints, knowns/unknowns)
- domain (drives which planner agents are spawned)
- stakes (gates whether the workflow is even allowed — low-stakes
  decisions skip pairing to save budget)

## Step types

| #         | Step                       | Type                |
|-----------|----------------------------|---------------------|
| 1         | canonicalize_inputs        | rule                |
| 2         | cost_ceiling               | governor            |
| 3a / 3b   | retrieve priors / anti     | knowledge           |
| 4a / 4b   | plan primary / devil       | agent               |
| 5a / 5b   | show_your_work             | governor            |
| 6a / 6b   | steel-manner pass          | agent               |
| 7         | gather_shared_evidence     | tool                |
| 8         | panel-of-five              | agent               |
| 9         | anti_sycophancy            | governor            |
| 10        | conviction_tax             | governor            |
| 11        | score_branches             | gomlx_inference     |
| 12        | classify_verdict           | agent               |
| 13        | branch_action              | conditional         |
| 14        | decision_diary             | governor            |
| 15        | execute_winner             | sub-workflow        |
| 16        | write_disagreement_record  | knowledge           |
| 17        | branch_quality_calibrator  | gomlx_inference     |
| 18        | schedule_retro             | sub-workflow        |

## Outputs

- chosen plan + execution
- `disagreement-archive` record with both branches preserved
- scheduled retro on the winner

## Pairs naturally with

- `devils-advocate` (agent) — Phase 1 devil branch
- `steel-manner` (agent) — both Phase 1 branches
- `panel-of-five` (agent) — Phase 2 judge
- `anti-pattern-kb` (knowledge) — feeds the devil branch's priors
- `disagreement-archive` (knowledge) — Phase 3 archive
- `decision-journal-kg` (knowledge) — receives the decision row
- `trial-and-retro` (workflow) — schedules the post-execution scoring

## Why it's a good demo

Three reasons:

1. **It models adversarial review as workflow structure, not prompt
   hygiene.** Most platforms try to get adversarial thinking by adding
   phrases to a prompt. Here, the adversary is a separate branch with
   its own retrieval, its own steel-manner pass, and its own evidence
   path. The audit trail is the disagreement.

2. **It composes the agent catalog into one shape.** `devils-advocate`,
   `steel-manner`, and `panel-of-five` are designed to live together
   here — this is the workflow they were built for. Showing all three
   firing on the same decision is a tour of Railyard's "creative
   agent" thinking.

3. **It writes value even when it loses.** The `disagreement-archive`
   row is the demo: most platforms forget the path-not-taken; this
   one keeps it on purpose, *especially* when verdicts were close.
   Six months later, when the chosen branch fails, the devil branch
   is sitting there waiting to be re-examined — a free, durable
   second opinion the org can actually find.
