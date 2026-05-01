# Agent · `time-bomb-scout`

An agent that hunts for tech debt with *expiry dates* — code that
references deprecated APIs, libraries past EOL, certs that will expire,
laws that take effect on a date, model versions being retired. It
turns "tech debt" from a vibe into a calendar.

## Purpose

Defang the "we'll get to it" reflex. Tech debt without a date is
infinite-horizon; tech debt with a date is a project. The
`time-bomb-scout` agent reads a codebase and produces a deprecation
calendar: every fuse, what blows when it triggers, and how much
runway remains.

Used in: quarterly tech-debt review, pre-launch readiness, vendor-
contract renewal cycles, model-deprecation audits (Claude Opus 4.5 →
4.7 migration is the canonical example). Pairs with `license-expiry-
watch` and `api-contract-diff-alert` (workflows), and `threat-intel-
feed` (knowledge).

## DSPy signature

```python
class FindTimeBombs(dspy.Signature):
    codebase_path: str = dspy.InputField()
    today: str = dspy.InputField(desc="ISO date for runway calculation")
    feeds: list[str] = dspy.InputField(
        desc="deprecation calendars to consult (e.g. endoflife.date,
              cloud provider deprecation pages)")
    bombs: list[TimeBomb] = dspy.OutputField()
    timeline: list[TimelineEntry] = dspy.OutputField(
        desc="bombs grouped and sorted by trigger date")
    immediate_risks: list[str] = dspy.OutputField(
        desc="bombs <30 days from trigger")
```

`TimeBomb = {file, line, what, trigger_date, days_remaining,
blast_radius[1..5], replacement_path, evidence_url}`.
`TimelineEntry = {month, bombs}`.

## Recommended tools

- `git-ops` — search for known-deprecated symbols in code
- `http-fetch` — pull deprecation calendars (cloud SDKs, language
  versions, framework EOL)
- `regex-match` — match deprecated import paths, model names, API
  versions
- `tls-cert-info` — surface cert-expiry as a time bomb
- `vector-search` — retrieve prior deprecation incidents

## Recommended governors

- `schema-validator` — every bomb must have a `trigger_date` (no
  date = not a bomb, just debt)
- `confidence-threshold` — low confidence on `trigger_date` →
  abstain (do not invent dates)
- `fact-half-life` — refuse deprecation feeds older than 30 days
- `cost-ceiling` — codebase-wide scans can fan out; cap

## Demonstrations sketch

- A repo using `boto3` calls deprecated in the next AWS SDK release →
  3 bombs, 90-day runway, blast=3
- A frontend using a React API removed in v19 → bomb dated to
  upgrade, blast=4 (full app affected)
- A Claude Opus 4.5 model reference in code, with 4.7 migration
  deadline → bomb dated to deprecation, blast=5 (every agent affected)
- TLS certs expiring in 14 days → immediate_risks entry

## Why it's a good demo

1. **It turns vibes into a Gantt chart.** Most "tech debt finder"
   demos produce a list of vague concerns. This one produces a dated
   timeline, which is the only thing that gets prioritized in a
   sprint review. The output is *budgetable*.
2. **It is a worked example of `fact-half-life` as a governor.**
   Deprecation feeds rot; a 90-day-old "this API is deprecated" feed
   may already be wrong. The governor refuses stale feeds, which is
   exactly the behavior that makes the agent's outputs trustworthy.
3. **It pairs with `decision-journal-kg`, `forecast-then-score`
   (workflow), and `pre-mortem-first` (workflow).** The journal logs
   each bomb defused; `forecast-then-score` predicts how long
   defusal will take and scores the prediction afterward; pre-mortem
   asks "what if we miss this one?" Together: a deprecation discipline
   no other platform composes end-to-end.

## Sample interaction

> codebase_path: "/srv/api"
> today: "2026-04-30"
> feeds: ["https://endoflife.date/python", "https://aws.amazon.com/sdk-deprecation"]

→ bombs:
  - file: "requirements.txt", line: 12, what: "Python 3.9 (EOL)",
    trigger_date: "2025-10-31", days_remaining: -181, blast_radius: 5,
    replacement_path: "Python 3.12", evidence_url: "endoflife.date/python"
    [NOTE: already past trigger; promoted to immediate_risks]
  - file: "src/agents/researcher.py", line: 7, what: "claude-opus-4-5
    model name", trigger_date: "2026-08-15", days_remaining: 107,
    blast_radius: 4, replacement_path: "claude-opus-4-7",
    evidence_url: "anthropic.com/model-deprecation"
  - file: "src/billing/invoicing.py", line: 88, what: "boto3.client('s3').list_objects",
    trigger_date: "2026-09-01", days_remaining: 124, blast_radius: 2,
    replacement_path: "list_objects_v2", evidence_url: "aws.amazon.com/sdk-deprecation"

→ timeline:
  - 2025-10 (PAST): 1 bomb [Python 3.9 EOL]
  - 2026-08: 1 bomb [Claude Opus 4.5]
  - 2026-09: 1 bomb [boto3 list_objects]

→ immediate_risks:
  - "Python 3.9 is past EOL by 181 days. Security patches no longer
     issued. Promote to S1."
