# Tool · `cargo-cult-detector`

Scans a corpus — code, configs, runbooks, governor rules, agent prompts
— for patterns that have been copy-pasted forward through generations of
edits but whose original justification has been lost. Finds the magic
incantations everyone preserves but no one can explain.

Every long-lived system collects these: a sleep before a network call
that someone added in 2019 to fix a flake nobody can reproduce, a
governor rule whose author has left, a `try/except: pass` whose
swallowed exception used to matter. They're load-bearing in unknown
proportions. This tool surfaces them so they can be either justified
or removed.

## Purpose

Make tribal knowledge auditable. Once a pattern is identified as cargo
cult, it gets a row in the `cargo-cult-registry` knowledge base and a
TTL: re-justify within N days or get scheduled for removal. Either
outcome is better than the current "no one remembers."

## Inputs

| Field           | Type    | Required | Notes |
|-----------------|---------|----------|-------|
| `corpus`        | enum    | yes      | code-repo / governor-rules / agent-prompts / runbooks |
| `scope`         | string  | no       | path or KB selector to limit scan |
| `min_repeats`   | int     | no, 3    | how many copies make a pattern |
| `min_age_days`  | int     | no, 180  | only flag patterns older than this |
| `mode`          | enum    | no       | structural / semantic (default both) |

## Outputs

| Field           | Type             | Notes |
|-----------------|------------------|-------|
| `patterns`      | []CargoPattern   | the suspicious recurrences |
| `evidence`      | map[id][]Locator | per-pattern source locations |
| `last_justified`| map[id]ts \| null| commit/PR/decision-journal entry, if any |
| `confidence`    | map[id]float     | how cargo-cult-y this looks (1.0 = textbook) |

`CargoPattern` carries: `signature` (normalized form), `representative`
(canonical instance), `first_seen`, `instances`, `proposed_owner` (best
guess from blame).

## Implementation kind

DSPy tool. Structural pass uses tree-sitter / AST hashing; semantic pass
uses embeddings to cluster near-duplicate prompt fragments and rule
bodies. The "is this actually cargo cult or just normal repetition?"
classification step is what makes it DSPy.

## Dependencies

- `tree-sitter` — structural pattern extraction for code
- Sibling tool `embed-text` — semantic clustering of non-code corpora
- `git-ops` — for blame and first-seen lookup
- `internal/tracing/` and the `decision-journal-kg` knowledge graph —
  to look for any explicit prior justification
- An LLM judge to write a one-sentence "what does this incantation
  appear to do" summary per pattern

## Side effects

Read-only against the corpus. Optionally inserts rows into the
`cargo-cult-registry` knowledge base when run in `--register` mode.

## Failure modes

- Corpus too large for one pass → streamed in chunks; partial result
  preserved if interrupted
- AST parse fails for a file → that file is skipped, not an error
- Pattern recurs but each instance has been independently justified in
  the decision journal → not flagged (the justifications are the proof)
- Embedding clustering produces unstable groupings → re-run with a
  different seed; the tool reports cluster stability as a confidence
  damper

## Why it's a good demo

Three reasons:

1. **It only works because Railyard records justifications.** A platform
   without a `decision-journal-kg` and trace-level provenance can't
   distinguish "we know why this is here" from "no one remembers." The
   detector's existence is an argument for the platform.
2. **It composes with the anti-cargo-cult pipeline.** Pairs with the
   `cargo-cult-registry` knowledge base (where findings live), the
   `anti-cargo-cult` workflow (which periodically asks "still
   justified?"), the `pattern-archaeologist` agent (which excavates
   commit history for original intent), and the `pre-mortem-required`
   governor (so new copies must come with their justification or be
   rejected).
3. **It changes the meaning of "old code."** Today, age in a codebase
   is read as stability. After this tool runs, age without a
   justification trail is read as risk. That single shift is worth more
   than any individual finding.

## Sample interaction

> corpus: governor-rules
> scope: tenants/finops/*
> min_age_days: 365

→ patterns:
  1. **`(retract ?f)` immediately after `(assert ?f)`** — appears in 7
     rules, last justified never. Representative: `tenants/finops/budget-guard.clp:42`.
     Likely originated as a workaround for a CLIPS quirk that was fixed
     in 2023; one rule still depends on the side effect.
  2. **`(printout t "DEBUG ...")` on the success path** — 14 rules.
     Origin: an early-stage debugging session in 2024. Output is
     consumed by no downstream parser. Confidence: 0.94.

→ proposed action: file these into `cargo-cult-registry` with a 30-day
re-justify TTL. The `anti-cargo-cult` workflow takes over from there.
