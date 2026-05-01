# Agent · `pattern-archaeologist`

An agent that excavates *dead idioms* — patterns that appear repeatedly
in a codebase but whose original justification is gone. Like an
archaeologist with a brush, it gently uncovers the pattern, dates it,
and asks: should this still be here?

Sister agent to `kintsugi`. Where `kintsugi` finds load-bearing
weirdness and protects it, `pattern-archaeologist` finds *non*-load-
bearing repetition and surfaces it for re-justification.

## Purpose

Defang the cargo-cult reflex. Codebases accrete idioms — the
"`if not x: return None` defensive guard", the "wrap every call in
try/except", the "always pass `timeout=30`" — that were once
necessary and may not be anymore. The `pattern-archaeologist` agent
finds these idioms, traces them to their introduction, and asks
whether the original conditions still hold.

Used in: codebase health audits, periodic "what should we stop doing"
reviews, onboarding ("here's what we used to do but don't anymore").
Pairs with `cargo-cult-registry` (knowledge), `naive-newcomer`
(agent), and `anti-cargo-cult` (workflow).

## DSPy signature

```python
class Excavate(dspy.Signature):
    codebase_path: str = dspy.InputField()
    min_occurrences: int = dspy.InputField(
        desc="pattern must appear at least this often")
    age_threshold_days: int = dspy.InputField(
        desc="patterns younger than this are skipped")
    patterns: list[Pattern] = dspy.OutputField()
    candidates_for_retirement: list[str] = dspy.OutputField()
    candidates_for_re_justification: list[str] = dspy.OutputField()
```

`Pattern = {idiom, sample_locations, occurrence_count,
introduced_in_commit, introduced_by, original_justification,
justification_still_holds[true|false|unknown], evidence}`.

## Recommended tools

- `git-ops` — blame and log to date the pattern's introduction
- `vector-search` — find the ADR or PR description that introduced
  the pattern
- `cargo-cult-detector` — primary scanning tool, finds copy-pasted
  patterns
- `provenance-tracer` — trace a current behavior back to the original
  decision

## Recommended governors

- `confidence-threshold` — abstain on patterns whose introduction
  cannot be reliably dated
- `show-your-work` — every `original_justification` must cite a commit,
  PR, or ADR — no inventing history
- A *custom* governor `no-conclusion-without-archaeology` that fails
  the run if any pattern is marked `justification_still_holds=false`
  without `original_justification` populated

## Demonstrations sketch

- "Wrap every external call in try/except RuntimeError" appears 87
  times → introduced in 2017 PR for a now-removed library that raised
  RuntimeError on timeout; current libraries raise specific errors.
  Justification no longer holds. Candidate for retirement.
- "All HTTP calls pass `timeout=30`" appears 142 times → introduced
  for a specific upstream that has been replaced; current upstreams
  have varying SLAs. Candidate for *re-justification* (some calls
  legitimately need 30s; others should be 2s).
- "Always JSON-encode booleans as strings" appears 23 times →
  introduced for a frontend bug fixed in 2019. Justification no
  longer holds.

## Why it's a good demo

1. **It uses the codebase's own history as ground truth.** Most "code
   smell" agents apply external rules. This one applies *the team's
   own past reasoning* and asks whether reality has moved. That's a
   knowledge-graph use case (decisions ↔ code ↔ commits ↔ time) more
   than a code-analysis use case.
2. **It is a worked example of provenance-aware agents.** Each
   pattern's verdict depends on tracing the introduction backwards
   through commits, blame, and ADR archives. Without `provenance-
   tracer`, the agent invents history. With it, every claim is
   grounded.
3. **It pairs with `kintsugi`, `cargo-cult-registry`, and
   `anti-cargo-cult` (workflow).** A repeated pattern is *either*
   load-bearing legacy (→ kintsugi protects it) or dead idiom (→
   archaeologist retires it). The two agents disagree-by-design; the
   workflow runs both and asks the team to reconcile.

## Sample interaction

> codebase_path: "/srv/api"
> min_occurrences: 10
> age_threshold_days: 365

→ patterns:
  - idiom: "try: x = expensive_call() except RuntimeError: x = None"
    sample_locations: ["src/billing/...", "src/users/...", "..."]
    occurrence_count: 87
    introduced_in_commit: "a3f2c1d (2017-04-14)"
    introduced_by: "@former-employee-Y"
    original_justification: "PR #2104: 'wraps deprecated foo-client
      v0.3 which raises RuntimeError on connection timeout'"
    justification_still_holds: false
    evidence: "foo-client was removed in commit 8b7a4e2 (2019-06)
      and replaced with bar-client which raises ConnectionError.
      RuntimeError will never fire. Current behavior: any
      RuntimeError from elsewhere (e.g. type errors) gets silently
      swallowed."

→ candidates_for_retirement:
  - "try/except RuntimeError pattern (87 occurrences) — original
    justification is gone and current behavior is actively harmful
    (silent type errors)."

→ candidates_for_re_justification:
  - "timeout=30 pattern (142 occurrences) — original justification
    was the foo-service SLA. Current upstreams vary; some calls
    should be 2s. Each occurrence needs case-by-case decision."
