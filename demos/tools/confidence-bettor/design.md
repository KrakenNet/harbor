# Tool · `confidence-bettor`

Asks the LLM to put money on its answer. Returns a calibrated probability
that's been pressure-tested by forcing the model to commit to a stake,
not just guess a number. The output is a probability you can actually
threshold against.

Self-reported confidence from LLMs is famously bad — they say "0.9" when
they mean "this sounds plausible." This tool reframes the question as a
betting problem ("how much of $100 would you wager?") and the answers
come out far better calibrated. Then it logs the bet and the eventual
outcome so calibration can be tracked over time.

## Purpose

Make uncertainty a first-class signal in agent execution. Once you have
a reliable per-claim probability, you can route low-confidence answers
to escalation, gate irreversible verbs behind a confidence floor, and
identify systematic over- or under-confidence per agent and per topic.

## Inputs

| Field           | Type    | Required | Notes |
|-----------------|---------|----------|-------|
| `claim`         | string  | yes      | the assertion to bet on |
| `context`       | string  | no       | what the model can see while betting |
| `model`         | string  | no       | defaults to a small dedicated bettor model |
| `mode`          | enum    | no       | wager / probability / brier (default wager) |
| `record`        | bool    | no, true | log the bet for later resolution |

## Outputs

| Field          | Type             | Notes |
|----------------|------------------|-------|
| `probability`  | float [0..1]     | resolved from whichever mode was used |
| `wager`        | int (0..100)     | dollars staked in `wager` mode |
| `rationale`    | string           | model's brief justification |
| `bet_id`       | uuid             | for outcome reconciliation |
| `model`        | string           | resolved model |

## Implementation kind

DSPy tool. The signatures (wager-mode in particular) are prompt-shaped
to elicit calibrated rather than fluent answers, and that's what makes
this a DSPy tool rather than a hand-rolled prompt.

## Dependencies

- LLM-model registry — pick a small bettor model
- `internal/tracing/` — bet attestations land in a span on the run
- A dedicated `bets` table — open bets keyed by `bet_id`, resolved later
- Sibling tool `decision-diary` — bet rows are decision rows for
  irreversible-verb cases

## Side effects

One LLM call. One row inserted into the bets table when `record=true`.
Eventually a resolution row is written by whatever process closes the
loop — usually a workflow that grades outcomes against bets.

## Failure modes

- Model returns malformed wager (non-numeric, > 100) → re-prompted once,
  then `error_kind="malformed"`
- Bet logging fails (DB unavailable) → bet is still returned but
  `recorded=false` is set so the caller knows calibration tracking
  missed this round
- Repeated 0/100 wagers → flagged in the bet record so reviewers can spot
  miscalibrated agents

## Why it's a good demo

Three reasons:

1. **Most platforms have no concept of agent uncertainty.** Confidence
   is either absent or a hard-coded "score" stamped on outputs. Railyard
   makes it a tool, a span, and a row — i.e. something governors can
   read, traces can show, and dashboards can chart over months.
2. **It composes with the trust pillar.** Pairs directly with the
   `conviction-tax` governor (penalize high-confidence claims with no
   citations), `confidence-threshold` (block low-confidence verbs), and
   `provenance-tracer` (when confidence is low, show *why* by walking
   the chain). One demo, one calibration story.
3. **Calibration becomes a property of the platform, not the agent.**
   Because every bet lands in a span and a row, you can compute Brier
   scores per agent / per tenant / per topic and use them to drive the
   `escalation-ladder` governor and the `question-difficulty-router`
   ML primitive.

## Sample interaction

> claim: "Postgres `ON CONFLICT DO UPDATE` does not fire AFTER UPDATE triggers."
> context: (blank — testing memorized knowledge)
> mode: wager

→ wager: 35
→ probability: 0.35
→ rationale: "I recall ON CONFLICT having unusual trigger semantics but
  am not certain whether AFTER UPDATE specifically fires. The
  asymmetric phrasing suggests caution."
→ bet_id: 4f9c…

Two days later a workflow checks the actual answer (it does fire AFTER
UPDATE in the upsert path) and resolves the bet to outcome=false with
Brier delta 0.42. That delta feeds the calibration table the
`question-difficulty-router` uses to decide which questions deserve
the bigger model.
