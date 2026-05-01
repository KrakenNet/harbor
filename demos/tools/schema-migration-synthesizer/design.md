# Tool · `schema-migration-synthesizer`

Diff two database schemas — current and target — and emit a migration
that gets you from one to the other safely. "Safely" means: ordered
correctly for FK dependencies, online-DDL where possible, with a
reversible down-migration, with a per-step risk annotation, and with
the breaking changes called out in writing.

LLMs can write migrations. LLMs cannot, by themselves, be trusted to
order them, to know which `ALTER TABLE`s lock for hours on Postgres
versions older than 12, or to remember that adding a NOT NULL column
without a default to a 200M-row table is a Tuesday-morning incident.
This tool is the structured pipeline that wraps the LLM with the
checks it doesn't know to do.

## Purpose

Make schema evolution something an agent can propose and a human can
approve in minutes. The output is a migration *plus* a written change
narrative *plus* a risk score *plus* the questions that should be
answered before running it.

## Inputs

| Field            | Type    | Required | Notes |
|------------------|---------|----------|-------|
| `current_schema` | string  | yes      | DDL dump or live introspection ref |
| `target_schema`  | string  | yes      | DDL dump or design-doc ref |
| `dialect`        | enum    | yes      | postgres / mysql / sqlite |
| `live_table_stats`| object | no       | row counts, index sizes; sharpens risk scoring |
| `policy`         | enum    | no       | online-only / allow-locking (default online-only) |
| `target_version` | string  | no       | e.g. "postgres-15" — gates use of online DDL features |

## Outputs

| Field             | Type             | Notes |
|-------------------|------------------|-------|
| `up_sql`          | []Statement      | ordered, FK-safe |
| `down_sql`        | []Statement      | reversal, marked irreversible where lossy |
| `narrative`       | string           | "what changes and why" in prose |
| `risk_score`      | float [0..1]     | 0 = trivial; 1 = "do not run during business hours" |
| `risk_breakdown`  | []RiskNote       | per-statement, with tag (lock / data-loss / fk-cascade / etc.) |
| `open_questions`  | []string         | things the synthesizer cannot answer alone |
| `breaking_changes`| []string         | renames, drops, type narrowings |

## Implementation kind

DSPy tool. The diff is deterministic AST work; the *narrative* and the
*open questions* and the *risk reasoning* are LLM steps with a DSPy
signature. The signature is what gets you from "ChatGPT wrote a
migration" to "the migration includes the question 'do you want to
backfill in batches or accept the lock?'"

## Dependencies

- `sqlglot` — SQL AST parsing & dialect-aware diffing
- LLM judge for narrative + risk reasoning + open-question generation
- Sibling tool `sql-query` — for live introspection mode
- `internal/tracing/` — the synthesis itself becomes a trace, so
  reviewers can see what reasoning produced which risk note
- Optional: `git-ops` to write the migration file into a checkout

## Side effects

The tool does not run the migration. Output is text + structured
metadata. Optional file write to a checkout directory. The migration
runs in a separate, governed step that an operator approves.

## Failure modes

- Schemas in different dialects → rejected, `error_kind="dialect_mismatch"`
- Diff requires an action the dialect can't express online → emitted
  with risk-tag `requires_lock` and surfaced in `open_questions`
- Lossy down migration → `down_sql` includes a stub statement and a
  warning that the down direction will lose data
- LLM produces SQL that doesn't parse → re-prompted once with the
  parser error; persistent failure surfaces as `error_kind="invalid_sql"`
- Target schema implies a rename but the diff sees drop+add → asked
  in `open_questions` so a human can confirm rename vs. drop

## Why it's a good demo

Three reasons:

1. **It's the cleanest example of "LLM + structure beats LLM alone."**
   The deterministic AST pass, the typed risk taxonomy, the explicit
   open-questions output, and the trace-linked reasoning — none of
   these come from the model. They come from the platform around the
   model. That's the whole sales pitch in one tool.
2. **It composes with the approval pillar.** Pairs with the
   `hitl-trigger`, `pre-mortem-required`, and `approval-policy`
   governors (a high-risk migration *must* go to a human; a
   `pre-mortem-required` governor demands a written failure-modes
   section before the migration can run), and with the `decision-diary`
   tool (which records the human's approval and reasoning before any
   irreversible verb).
3. **It produces an artifact that's good even when no one runs it.**
   The narrative + open-questions + risk breakdown is itself a design
   review document. Teams that adopt this end up with a richer change
   log and an `adr-archive` that fills itself.

## Sample interaction

> current_schema: live introspection of `staging-db`
> target_schema: `docs/schema/v17-target.sql`
> dialect: postgres
> live_table_stats: { events: 412M rows; users: 8.4M rows }

→ up_sql:
  1. `CREATE INDEX CONCURRENTLY idx_events_user_id ON events(user_id);`
  2. `ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}'::jsonb NOT NULL;` (risk: `requires_full_table_rewrite` for 8.4M rows; estimated 6-12 min lock on PG 11; safe online on PG 12+)
  3. `ALTER TABLE events ADD CONSTRAINT events_user_fk FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID;`
  4. `ALTER TABLE events VALIDATE CONSTRAINT events_user_fk;` (risk: long-running scan; recommended off-peak)
→ risk_score: 0.62
→ open_questions:
  - "Step 2 implies the new column is required for all existing users. Backfill strategy: app default at insert time, or batched UPDATE? The app-default path lets us drop the rewrite, but assumes no consumer reads `preferences` from older rows during the gap."
  - "Step 4 will scan ~412M rows. Run this off-peak, or split into a separate change?"
→ breaking_changes: none
→ down_sql: included; lossy on step 2 (column drop discards data)

The narrative + open-questions get filed into the `adr-archive`. The
`pre-mortem-required` governor blocks execution until the open
questions are answered.
