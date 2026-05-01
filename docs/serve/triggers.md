# Triggers

Triggers are the inbound dispatch boundary: they accept a request from
the outside (cron, webhook, idempotency-keyed POST) and convert it into
a `PendingRun` entry on the scheduler queue. The scheduler then drives
the actual `GraphRun` startup.

Trigger sources are tagged on the `runs_history.trigger_source` column
(`http`, `webhook`, `cron`, `cli`) so operators can audit how a run was
born.

## Topics

- TODO: cron schedule format + reconciliation loop.
- TODO: webhook signature verification (HMAC + replay-window).
- TODO: idempotency-key handling + `pending_runs` table semantics.
- TODO: trigger-side capability check.
- TODO: per-trigger rate-limiting.
