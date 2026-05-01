# Governors — Demo Catalog

CLIPS-based policy primitives. Each entry will graduate into its own folder
with rules / facts / streams / routes, plus a sample violation and the
expected `(emit-output ...)` decision.

## Generic

- `pii-redactor`
- `profanity-filter`
- `cost-ceiling` — hard $$ cap per request/tenant
- `token-budget`
- `rate-limit`
- `schema-validator` — output must conform
- `latency-sla`
- `tool-allowlist`
- `role-gate` — RBAC over verbs
- `hitl-trigger` — high-risk verbs need human
- `confidence-threshold`
- `loop-breaker` — same action N times = stop
- `compliance-scan` — HIPAA / PCI / SOC2 keyword catch
- `jailbreak-detector`
- `business-hours-only`
- `geo-fence`
- `tenant-quota`
- `approval-policy`
- `output-length-cap`
- `redaction-on-egress`

## Creative

- `are-you-sure` — forces a self-doubt pass before any irreversible verb
- `echo-chamber-breaker` — rejects outputs too similar to recent ones (anti-rut)
- `conviction-tax` — penalizes high-confidence claims with no citations
- `anti-sycophancy` — blocks "great question!" / agreement-spirals
- `drift-detector` — flags when agent strays from system prompt embedding
- `tone-calibrator` — blocks tone mismatches for the channel
- `fact-half-life` — refuses use of facts older than X for class Y
- `show-your-work` — math / finance / legal answers must include reasoning chain
- `escalation-ladder` — auto-promotes to bigger model only after N small-model retries
- `pre-mortem-required` — no high-stakes plan executes without a written failure-modes section
