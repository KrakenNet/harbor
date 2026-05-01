=============================================================================
                       THE AUTO-HYPOTHESIS WORKFLOW
=============================================================================

A workflow that scans the platform's own logs and traces for surprises,
turns each surprise into a hypothesis, and queues an experiment to test
it. The system mines its own operational substrate for unanswered "huh,
that's weird" moments — and then, instead of forgetting them, files them
as work.

The premise: the most valuable signal in any production system is the
moment a senior engineer says "huh." That signal is currently captured
nowhere. Railyard's trace store has every "huh" in it; this workflow
makes them findable, frame-able, and testable.

[Trigger] (hourly cron over recent traces, OR on-demand via /surprise)
             │
             ▼
=============================================================================
            PHASE 1: SURPRISE MINING (ANOMALY LAYER)
=============================================================================
[1. sample_recent_traces]
  (tool: trace store query — last N hours, weighted toward
   high-cost / high-latency / failed runs)
             │
             ▼
[2. ml: `trace-shape-anomaly`]
  (gomlx_inference — the "normal" span tree distribution per workflow
   class; flags shapes that are unusual without being errors)
             │
             ▼
[3. ml: `prompt-drift-classifier`]
  (gomlx_inference — agents that silently veered off-policy)
             │
             ▼
[4. ml: `cost-spike-forecaster` retro-check]
  (gomlx_inference — cost overshoots that the forecaster missed
   are interesting precisely because they were unpredictable)
             │
             ▼
[5. cluster_surprises]  (tool: `embedding-cartographer`)
  (groups individual anomalies into themes; deduplicates "the same
   surprise observed 40 times")
             │
             ▼
[6. governor: `loop-breaker`]
  (refuses to file a hypothesis on a cluster that already has an open
   experiment; suppresses re-investigation thrash)
             │
             ▼
=============================================================================
            PHASE 2: HYPOTHESIS FORMATION (FRAMING LAYER)
=============================================================================
[7. retrieve_priors]
  (knowledge: `open-questions-kb`, `past-decision-memory`, and
   `disagreement-archive` for similar surprises previously catalogued)
             │
             ▼
[8. agent: `naive-newcomer`]
  (asks "why?" recursively until the surprise reduces to a first-
   principles question — the unflinching outsider voice)
             │
             ▼
[9. agent: `extractor` → hypothesis_card]
  → fields:
      • surprise_summary
      • candidate_explanations[] (with prior probability)
      • predicted_distinguishing_observation
      • cheapest_test
      • would_change_my_mind_if
      • expected_value_of_information
             │
             ▼
[10. governor: `show-your-work`]
  (every candidate explanation must cite the trace evidence that motivates
   it; speculation without evidence is rejected)
             │
             ▼
[11. governor: `conviction-tax`]
  (the prior probability column gets penalized for high values without
   precedent in `past-decision-memory`)
             │
             ▼
=============================================================================
            PHASE 3: EXPERIMENT DESIGN + QUEUE (PLANNING LAYER)
=============================================================================
[12. agent: `extractor` → experiment_plan]
  → fields: design (A/B, replay-with-mutation, dark-launch, log-only),
    sample_size, instrumentation, stopping_rule, blast_radius, cost_cap
             │
             ▼
[13. governor: `cost-ceiling`]
  (caps experiment spend; high-cost experiments require approval before
   they can be queued)
             │
             ▼
[14. governor: `approval-policy`]
  (high-blast-radius experiments held for HITL; cheap log-only
   experiments auto-approved)
             │
             ▼
[15. branch_route]  (conditional)
  ├──► auto-runnable → enqueue as a `counterfactual-replay` job
  ├──► needs HITL    → file Linear ticket + Slack ping
  └──► record-only   → write to `open-questions-kb`, no experiment
             │
             ▼
[16. enqueue_experiment]  (tool: workflow scheduler — creates a
   `counterfactual-replay` or `devils-pair` run pointing at the
   surprise's plan_hash)
             │
             ▼
=============================================================================
            PHASE 4: ARCHIVE + LEARN (FEEDBACK LAYER)
=============================================================================
[17. write_hypothesis_record]
  (knowledge: row in `open-questions-kb` linked to the trace IDs and
   any queued experiment; immutable until the experiment closes)
             │
             ▼
[18. wait_for_experiment_outcome]  (loop: signal listener)
             │
             ▼
[19. score_hypothesis]
  (when the experiment closes, score the candidate explanations against
   results; emit `confirmed | refuted | partial | inconclusive`)
             │
             ▼
[20. write_to_archives]
  (knowledge: confirmed → `decision-journal-kg` learning edge;
   refuted → `anti-pattern-kb`; inconclusive → kept open in
   `disagreement-archive` on purpose)
             │
             ▼
[21. ml_signal: hypothesis-yield calibrator]
  (gomlx_inference: tracks which surprise-clusters are worth investigating
   per outcome; over time, low-yield clusters get suppressed at step 5)
=============================================================================

## Inputs

- scan window (default: last 1h)
- workflow scope (which workflow classes to mine)
- surprise sensitivity threshold

## Step types

| #     | Step                          | Type                  |
|-------|-------------------------------|-----------------------|
| 1     | sample_recent_traces          | tool                  |
| 2     | trace_shape_anomaly           | gomlx_inference       |
| 3     | prompt_drift_classifier       | gomlx_inference       |
| 4     | cost_spike_retro_check        | gomlx_inference       |
| 5     | cluster_surprises             | tool                  |
| 6     | loop_breaker                  | governor              |
| 7     | retrieve_priors               | knowledge             |
| 8     | naive_newcomer                | agent                 |
| 9     | hypothesis_card               | agent                 |
| 10    | show_your_work                | governor              |
| 11    | conviction_tax                | governor              |
| 12    | experiment_plan               | agent                 |
| 13    | cost_ceiling                  | governor              |
| 14    | approval_policy               | governor              |
| 15    | branch_route                  | conditional           |
| 16    | enqueue_experiment            | tool (sub-workflow)   |
| 17    | write_hypothesis_record       | knowledge             |
| 18    | wait_for_outcome              | loop (signal)         |
| 19    | score_hypothesis              | rule + agent          |
| 20    | write_to_archives             | knowledge             |
| 21    | yield_calibrator              | gomlx_inference       |

## Outputs

- queued experiments tied to specific surprise clusters
- `open-questions-kb` rows with provenance back to traces
- archive writes on outcome (confirmed / refuted / inconclusive)

## Pairs naturally with

- `trace-shape-anomaly` (ML) — Phase 1 anomaly source
- `prompt-drift-classifier` (ML) — Phase 1 drift source
- `embedding-cartographer` (tool) — Phase 1 clustering
- `naive-newcomer` (agent) — Phase 2 first-principles voice
- `open-questions-kb` (knowledge) — Phase 4 archive
- `disagreement-archive` (knowledge) — Phase 4 archive for inconclusive
- `counterfactual-replay` (workflow) — Phase 3 experiment runner
- `devils-pair` (workflow) — alternative Phase 3 runner

## Why it's a good demo

Three reasons:

1. **It mines value from data the platform already has.** Traces, span
   trees, and cost streams are produced as a side-effect of operation;
   most platforms throw them at observability dashboards and stop.
   Railyard turns them into a hypothesis pipeline. The substrate is
   already there — the workflow is the value extractor.

2. **It is the platform doing science on itself.** Every other learning
   loop in the catalog (calibration, retros, counterfactuals) acts on
   decisions humans made. This one acts on decisions the *agents* made
   that surprised humans. It's the auto-self-debugger.

3. **It composes the ML catalog into one shape.** `trace-shape-anomaly`,
   `prompt-drift-classifier`, `cost-spike-forecaster`, and
   `embedding-cartographer` were each built to do one job; this
   workflow shows the four firing in series to produce a single
   queueable experiment. It's the demo that makes the ML catalog
   feel like a system.
