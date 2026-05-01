# Workflows — Demo Catalog

Multi-step orchestration demos. Each entry will graduate into its own folder
with a pipeline graph (in the style of `cve-remediation/pipeline-graph.md`),
the workflow JSON, and a sample run.

Existing demos: [`code-graph/`](code-graph/), [`atr/`](atr/),
[`cve-remediation/`](cve-remediation/).

## Generic

- `support-triage` — inbound ticket → category + owner + draft reply
- `doc-ingest-rag` — file drop → chunked + embedded + indexed
- `lead-enrichment` — name/email → enriched profile + score
- `invoice-extract-approve` — PDF → fields → approval → ERP
- `outreach-sequencer`
- `pr-review`
- `incident-response`
- `daily-digest`
- `inventory-reconcile`
- `kb-sync` — code/docs ↔ KB articles
- `data-quality-sweep`
- `stale-record-cleanup`
- `backup-verify`
- `license-expiry-watch`
- `api-contract-diff-alert`
- `employee-onboarding`
- `customer-churn-outreach`
- `expense-policy-check`
- `meeting-prep` — calendar + CRM + email recap
- `weekly-roll-up`

## Creative

- `counterfactual-replay` — re-runs past decisions on alt paths and grades each
- `trial-and-retro` — every decision auto-spawns a 7-day post-mortem with outcome
- `pre-mortem-first` — workflow spends N% of budget hunting failure modes before any action
- `devils-pair` — runs primary + opposing strategy in parallel, picks winner on evidence
- `forecast-then-score` — workflow predicts its own outcome up front, logs delta after
- `auto-hypothesis` — scans logs for surprises, proposes & queues experiments
- `inverse-onboarding` — produces a "what would I forget if I left tomorrow" doc
- `knowledge-half-life-sweep` — surfaces KB articles whose source code drifted
- `decision-journal-loop` — every multi-step plan gets an immutable rationale + outcome row
- `anti-cargo-cult` — periodically re-justifies any rule older than X or removes it
