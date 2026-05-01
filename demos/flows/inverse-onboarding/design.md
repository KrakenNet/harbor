=============================================================================
                       THE INVERSE-ONBOARDING WORKFLOW
=============================================================================

A workflow that produces, for each person on a team, the document they'd
need if they vanished tomorrow — what they uniquely know, what would
break, who would be stuck on what. It runs by silently observing what
they touched, decided, and resolved over a window, and writes it back
in their voice as a "what would I forget if I left tomorrow" note.

The premise: most onboarding documentation is written *forward* — the
new person reads it. Most knowledge gaps are *backward* — they're what
the leaver carried out the door. Inverting the direction means the
record exists before the loss, instead of after.

[Trigger] (quarterly cron per active team member, OR on-demand for
 high-risk roles, OR fired the day a resignation is filed)
             │
             ▼
=============================================================================
            PHASE 1: SCOPE + WINDOW (BOUNDARY LAYER)
=============================================================================
[1. resolve_subject]
  (knowledge: `org-chart-kg` — role, tenure, reporting line, projects,
   on-call rotations, vendor relationships)
             │
             ▼
[2. governor: `compliance-scan`]
  (per-jurisdiction privacy rules — employee monitoring laws vary; the
   workflow halts in jurisdictions where this surveillance shape isn't
   permitted without consent)
             │
             ▼
[3. governor: `role-gate`]
  (the operator running the workflow must have HR-bless permission;
   peer-on-peer runs are blocked)
             │
             ▼
[4. resolve_window]  (rule: last N months, capped at tenure)
             │
             ▼
=============================================================================
            PHASE 2: SILENT OBSERVATION (TRACE-MINING LAYER)
=============================================================================
[5. parallel_collect]
  ├──► commits authored / reviewed
  ├──► PR comments (especially "blocking" ones — these signal taste)
  ├──► incidents on-call for, with resolution authorship
  ├──► tickets resolved + their threads
  ├──► docs authored or last-edited
  ├──► decisions in `decision-journal-kg` where this person is rationale_author
  ├──► meetings where this person spoke materially (transcript memory)
  ├──► vendor / external relationships from email metadata
  └──► tools/services where this person is sole admin
             │
             ▼
[6. governor: `pii-redactor`]
  (everything before the next step is scrubbed — the goal is the
   *pattern of expertise*, not the personal record)
             │
             ▼
=============================================================================
            PHASE 3: TACIT-KNOWLEDGE EXTRACTION (SYNTHESIS LAYER)
=============================================================================
[7. agent: `pattern-archaeologist`]
  (excavates this person's idioms — the way they review code, the
   phrases they use in incidents, the structures they repeat in docs)
             │
             ▼
[8. agent: `kintsugi`]
  (finds the load-bearing legacy code the subject maintains; produces
   appreciation/care notes for it — what only they remember about why
   it's the way it is)
             │
             ▼
[9. agent: `constraint-surfacer`]
  (turns implicit assumptions in the subject's PR comments and decisions
   into explicit specs — "they always reject X because Y" patterns)
             │
             ▼
[10. agent: `extractor` → bus_factor_card]
  → fields:
      • sole_admin_systems[]
      • frequently_asked_about_topics[]
      • decisions_only_they_made[]
      • idioms_only_they_use[]
      • legacy_code_only_they_understand[]
      • vendor_relationships_owned[]
      • opinions_others_implicitly_defer_to[]
             │
             ▼
[11. governor: `show-your-work`]
  (every claim links to the trace, commit, ticket, or message that
   evidences it — no narrative prose untethered from records)
             │
             ▼
[12. governor: `conviction-tax`]
  (high-confidence claims about "only they know X" require >= N
   independent evidence pieces; reduces over-attribution)
             │
             ▼
=============================================================================
            PHASE 4: VOICED REWRITE (HUMANIZE LAYER)
=============================================================================
[13. agent: `dialect-translator`]
  (rewrites the bus_factor_card from third-person observation into
   first-person "what I would forget if I left tomorrow" voice;
   matches the subject's actual writing idiom from step 7)
             │
             ▼
[14. governor: `tone-calibrator`]
  (matches subject's prior writing tone; demands self-aware, not
   self-aggrandizing — calibrated to "honest hand-off note" register)
             │
             ▼
[15. governor: `anti-sycophancy`]
  (kills hagiography — "valued contributor" prose with nothing
   load-bearing under it is rejected)
             │
             ▼
=============================================================================
            PHASE 5: HITL CONSENT + ARCHIVE (PUBLICATION LAYER)
=============================================================================
[16. HITL Subject-Review Gate]
  (the subject themselves reviews and edits the document — they accept,
   amend, or redact; cannot be skipped; document is THEIRS)
             │
             ▼
[17. governor: `decision-diary`]
  (archive of which sections the subject edited / removed is itself
   informative and immutable)
             │
             ▼
[18. write_to_archives]
  (knowledge:
   • `folklore-kb` ← the subject-approved final document
   • `intentional-non-features-kb` ← any "we don't do X because Y"
     items the subject surfaced
   • `open-questions-kb` ← any "I don't know why we do X" the subject
     flagged during review)
             │
             ▼
[19. schedule_refresh]  (loop: reschedules itself for next quarter)
             │
             ▼
[20. ml_signal: bus-factor scorer]
  (gomlx_inference: per-team rollup of where bus-factor risk concentrates;
   feeds capacity / hiring / cross-training planning)
=============================================================================

## Inputs

- subject_id (the person to invert-onboard)
- window (default: last 6 months, capped at tenure)
- consent flag (per jurisdiction)

## Step types

| #     | Step                       | Type                |
|-------|----------------------------|---------------------|
| 1     | resolve_subject            | knowledge           |
| 2     | compliance_scan            | governor            |
| 3     | role_gate                  | governor            |
| 4     | resolve_window             | rule                |
| 5     | parallel_collect           | tool (fan-out)      |
| 6     | pii_redactor               | governor            |
| 7     | pattern_archaeologist      | agent               |
| 8     | kintsugi                   | agent               |
| 9     | constraint_surfacer        | agent               |
| 10    | bus_factor_card            | agent               |
| 11    | show_your_work             | governor            |
| 12    | conviction_tax             | governor            |
| 13    | dialect_translator         | agent               |
| 14    | tone_calibrator            | governor            |
| 15    | anti_sycophancy            | governor            |
| 16    | hitl_subject_review        | approval            |
| 17    | decision_diary             | governor            |
| 18    | write_to_archives          | knowledge           |
| 19    | schedule_refresh           | loop                |
| 20    | bus_factor_scorer          | gomlx_inference     |

## Outputs

- subject-approved "what I'd forget" document
- `folklore-kb`, `intentional-non-features-kb`, `open-questions-kb` writes
- bus-factor risk score per team

## Pairs naturally with

- `pattern-archaeologist` (agent) — Phase 3 idiom excavation
- `kintsugi` (agent) — Phase 3 legacy-code appreciation
- `constraint-surfacer` (agent) — Phase 3 assumption extraction
- `dialect-translator` (agent) — Phase 4 voiced rewrite
- `folklore-kb` (knowledge) — Phase 5 archive
- `intentional-non-features-kb` (knowledge) — Phase 5 archive
- `decision-journal-kg` (knowledge) — Phase 2 source
- `employee-onboarding` (workflow) — feeds the *next* hire's onboarding

## Why it's a good demo

Three reasons:

1. **It captures folklore before the carrier leaves.** Every org has a
   "you should ask Priya about this" — and one day Priya is gone.
   Inverse-onboarding writes Priya's hand-off note while she's still
   here to correct it. The HITL subject-review gate at step 16 is the
   ethical centerpiece: the document is hers, by design.

2. **It composes the "creative agent" catalog into one humanizing
   shape.** `pattern-archaeologist`, `kintsugi`, `constraint-surfacer`,
   and `dialect-translator` are each odd standalone curiosities; here
   they form a pipeline that produces something an executive would
   actually pay for. The workflow is what makes those agents feel
   load-bearing.

3. **It demonstrates Railyard's most uncomfortable governance
   surface.** Surveillance-shaped workflows are the place governance
   actually matters. `compliance-scan` halts in restrictive
   jurisdictions, `pii-redactor` runs before any synthesis,
   `role-gate` blocks peer-on-peer runs, and the subject themselves
   gates publication. A workflow that *could* go wrong, but which is
   structurally prevented from doing so, is a more honest demo of the
   governor stack than any benign one would be.
