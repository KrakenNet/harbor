=============================================================================
                       THE ANTI-CARGO-CULT WORKFLOW
=============================================================================

A workflow that periodically re-justifies every governance rule, runtime
policy, and operational ritual older than X — or removes it. The system
treats its own accumulated rules as suspect. A rule that cannot articulate,
in current language, why it still exists is a rule waiting to be deleted.

The premise: most policies in any platform are inherited. They were
written for a world that no longer exists, then forgotten by the people
who wrote them, then defended by the people who only know they exist. The
half-life of a rule's *justification* is shorter than the half-life of
the rule. Pruning that gap is everyone's job and therefore no one's.

[Trigger] (monthly cron OR on-demand /cargo-cult-sweep OR triggered by
 `cargo-cult-registry` reaching capacity)
             │
             ▼
=============================================================================
            PHASE 1: ENUMERATE LEGACY RULES (DECAY LAYER)
=============================================================================
[1. enumerate_targets]
  (parallel knowledge pulls)
  ├──► CLIPS governor rules (every active governor + its install date)
  ├──► tool allowlists per workflow class
  ├──► HITL approval thresholds
  ├──► retention / expiry rules from `compliance-kb`
  ├──► escalation ladders, on-call routing rules
  └──► coding-style rules, lint configs, code-review checklists
             │
             ▼
[2. compute_age_signals]  (rule)
  ├──► install_date age
  ├──► last_fired age (CLIPS rules track this natively)
  ├──► last_modified age
  └──► last_explicitly_justified age (from `decision-journal-kg`)
             │
             ▼
[3. ml: `cargo-cult-detector`]
  (gomlx_inference + tool: identifies rules that fire rarely, were never
   explicitly cited, or whose original-issue links 404 — the silent
   majority of rules)
             │
             ▼
[4. governor: `fact-half-life`]
  (rules whose justification age exceeds class half-life are auto-flagged
   for re-justification, regardless of activity)
             │
             ▼
=============================================================================
            PHASE 2: TRACE BACK TO ORIGIN (PROVENANCE LAYER)
=============================================================================
[5. tool: `provenance-tracer`]
  (for each flagged rule, walks back through `decision-journal-kg`,
   git history, and `disagreement-archive` to find the original
   motivating incident, ADR, or thread)
             │
             ▼
[6. classify_origin]  (agent: `classifier`)
  → origin: clear-incident | clear-policy | hand-me-down | lost |
    apocryphal
             │
             ▼
[7. governor: `show-your-work`]
  (every "lost" or "apocryphal" verdict must show what was searched and
   what wasn't found — null result is itself evidence)
             │
             ▼
[8. write_to_cargo_cult_registry]
  (knowledge: `cargo-cult-registry` row per rule with origin verdict,
   last-fired timestamp, blast radius if removed)
             │
             ▼
=============================================================================
            PHASE 3: RE-JUSTIFICATION ATTEMPT (REASONING LAYER)
=============================================================================
[9. agent: `naive-newcomer`]
  (asks "why does this rule exist *today*?" — not "why was it written"
   but "what current threat would re-create it"; deliberately ignores
   the original motivation)
             │
             ▼
[10. agent: `pattern-archaeologist`]
  (excavates: has this rule's underlying problem been solved by other
   means? has the system that needed it been deprecated? is the rule
   protecting a path that no longer exists?)
             │
             ▼
[11. agent: `extractor` → re_justification_card]
  → fields:
      • current_threat_addressed
      • evidence_threat_still_exists
      • cost_of_rule (false positives, latency, friction)
      • alternative_mitigations (if any)
      • verdict: justified | redundant | obsolete | unknown
             │
             ▼
[12. governor: `conviction-tax`]
  (high-confidence "justified" verdicts must cite a fired-in-anger event
   from `decision-journal-kg` within the half-life window — abstract
   justifications are penalized)
             │
             ▼
[13. agent: `devils-advocate`]
  (governed by `must-disagree`: argues that the rule should be removed,
   *especially* if step 11 said "justified"; the disagreement record is
   itself written to `disagreement-archive`)
             │
             ▼
=============================================================================
            PHASE 4: PROPOSE ACTION (DECISION LAYER)
=============================================================================
[14. classify_disposition]  (agent: `classifier`)
  → action: keep_as_is | re_justify_record_only | sunset_with_notice |
    remove_now | replace_with_simpler
             │
             ▼
[15. governor: `approval-policy`]
  (remove_now and replace_with_simpler always require HITL — irreversible
   policy changes get human eyes; sunset_with_notice can auto-proceed)
             │
             ▼
[16. governor: `decision-diary`]
  (immutable row written before any rule modification — what we removed,
   why we removed it, who signed off, and what we predicted would happen
   as a result)
             │
             ▼
[17. branch_action]  (conditional)
  ├──► keep_as_is             → step 18 (record only)
  ├──► re_justify_record_only → step 19 (refresh the journal)
  ├──► sunset_with_notice     → step 20 (deprecation timer)
  ├──► remove_now             → step 21 (HITL + remove)
  └──► replace_with_simpler   → step 22 (HITL + swap)
             │
             ▼
[18. record_no_action]  (knowledge: registry timestamp updated)
[19. refresh_justification]  (knowledge: re_justification_card linked
     into `decision-journal-kg`)
[20. sunset_with_notice]  (governor compiled with TTL; auto-removes in
     N days unless reaffirmed)
[21. remove_now]  (tool: governor un-install + git PR removing the rule)
[22. replace_with_simpler]  (tool: governor swap + git PR; old rule
     archived in `intentional-non-features-kb` with reason)
             │
             ▼
=============================================================================
            PHASE 5: WATCH FOR FALLOUT (SCHEDULED VERIFICATION LAYER)
=============================================================================
[23. schedule_fallout_watch]  (loop: sleep N days, then check for
   incidents tagged to the removed rule's domain)
             │
             ▼
        ─── workflow suspends here ───
             │
             ▼
[24. wake + classify_fallout]  (agent: `classifier`)
  → fallout: none | minor | regression | catastrophic
             │
             ▼
[25. branch_fallout]  (conditional)
  ├──► none / minor      → write win to `past-decision-memory`
  ├──► regression        → re-install rule + write to `anti-pattern-kb`
  └──► catastrophic      → page on-call + emergency rollback
             │
             ▼
[26. ml_signal: rule-removal calibrator]
  (gomlx_inference: per-rule-class, what fraction of removals turned
   into regressions? sets future caution levels at step 14)
             │
             ▼
[27. notify_owners]
  (tool: Slack — monthly "we removed N rules, M came back, here are
   the survivors" digest; the visible attrition is the demo)
=============================================================================

## Inputs

- rule scope (default: all governance rules + tool allowlists +
  approval thresholds)
- minimum age (default: 180d — rules younger than this are exempt)
- aggression flag (conservative / standard / pruning)

## Step types

| #     | Step                          | Type                  |
|-------|-------------------------------|-----------------------|
| 1     | enumerate_targets             | knowledge (parallel)  |
| 2     | compute_age_signals           | rule                  |
| 3     | cargo_cult_detector           | gomlx_inference + tool|
| 4     | fact_half_life                | governor              |
| 5     | provenance_tracer             | tool                  |
| 6     | classify_origin               | agent                 |
| 7     | show_your_work                | governor              |
| 8     | write_to_registry             | knowledge             |
| 9     | naive_newcomer                | agent                 |
| 10    | pattern_archaeologist         | agent                 |
| 11    | re_justification_card         | agent                 |
| 12    | conviction_tax                | governor              |
| 13    | devils_advocate               | agent + governor      |
| 14    | classify_disposition          | agent                 |
| 15    | approval_policy               | governor              |
| 16    | decision_diary                | governor              |
| 17    | branch_action                 | conditional           |
| 18-22 | per-disposition actions       | knowledge / tool      |
| 23    | schedule_fallout_watch        | loop (sleep)          |
| 24    | classify_fallout              | agent                 |
| 25    | branch_fallout                | conditional           |
| 26    | rule_removal_calibrator       | gomlx_inference       |
| 27    | notify_owners                 | tool                  |

## Outputs

- per-rule re-justification card or removal record
- updated `cargo-cult-registry`
- scheduled fallout-watch sub-workflow per removal
- self-tuning aggression parameter at step 14

## Pairs naturally with

- `cargo-cult-detector` (tool) — Phase 1 ML detection
- `cargo-cult-registry` (knowledge) — Phase 2 archive
- `provenance-tracer` (tool) — Phase 2 origin walk
- `naive-newcomer` (agent) — Phase 3 first-principles voice
- `pattern-archaeologist` (agent) — Phase 3 dead-idiom excavation
- `devils-advocate` (agent) — Phase 3 forced removal argument
- `intentional-non-features-kb` (knowledge) — Phase 4 tombstone
- `disagreement-archive` (knowledge) — Phase 3 dissent record
- `decision-journal-kg` (knowledge) — Phase 4 immutable rationale
- `past-decision-memory` / `anti-pattern-kb` (knowledge) — Phase 5 outcomes
- `knowledge-half-life-sweep` (workflow) — sister workflow; same shape
  applied to KB articles instead of rules

## Why it's a good demo

Three reasons:

1. **It treats *the platform's own governance* as a corpus to be
   pruned.** Every other workflow in the catalog uses governors;
   this is the one that asks whether each governor still earns its
   keep. The platform turns its own immune system inward. That
   level of self-skepticism is rare in agent platforms and memorable
   in a demo.

2. **It composes the catalog's most contrarian primitives.**
   `naive-newcomer`, `pattern-archaeologist`, `devils-advocate`, the
   `cargo-cult-detector`, and the `must-disagree` governor all live
   in the same five steps. This is the workflow they were each
   written for; together they perform a function — durable
   anti-bureaucracy — that no single agent could do alone.

3. **It closes the loop on its own removals.** The
   schedule_fallout_watch step at 23 makes deletion a reversible
   experiment: if removing a rule causes regressions, the workflow
   re-installs it and writes the lesson to `anti-pattern-kb`. The
   rule-removal calibrator at step 26 then adjusts how aggressive
   the *next* sweep is. The system *learns to prune* — not just
   prunes once.
