# Demo Catalog

A backlog of demos to build across Railyard's primitive types. Each subfolder
has its own focused catalog (`agents/CATALOG.md`, `tools/CATALOG.md`, etc.);
this file is the master index.

- **Generic** entries are broadly reusable, off-the-shelf primitives — the
  kind every Railyard deployment will want available.
- **Creative** entries are distinctive showcase pieces designed to highlight
  what Railyard's primitives (governors, traces, memory, KGs) make possible
  that other platforms don't.

Each item is intentionally one line: name + hook. They become design docs
when promoted into their own folder.

---

## Tools — see [`tools/CATALOG.md`](tools/CATALOG.md)

### Generic
- `http-fetch` — typed HTTP client with retry/backoff
- `shell-exec` — sandboxed shell command runner
- `sql-query` — read-only Postgres/SQLite query
- `vector-search` — pgvector similarity search
- `embed-text` — single-text embedding helper
- `web-scrape` — readability-mode page → markdown
- `pdf-extract` — PDF → text + tables
- `ocr` — image → text
- `csv-read` / `csv-write`
- `json-jq` — jq-style query over JSON
- `regex-match`
- `git-ops` — clone/diff/blame/log
- `slack-post` / `discord-post` / `email-send`
- `dns-lookup`, `whois`, `tls-cert-info`
- `markdown-html` (both directions)
- `token-count` (model-aware)
- `code-format` (prettier/black/gofmt)
- `lint-run` / `test-run`
- `aws-cli`, `gcloud`, `kubectl` thin wrappers

### Creative
- `provenance-tracer` — given a claim, walks the trace tree back to its source span
- `confidence-bettor` — asks the LLM to "bet" on its answer, returns calibrated probability
- `counterfactual-mutator` — minimally perturbs an input until the verdict flips
- `cargo-cult-detector` — finds copy-pasted patterns whose original justification is gone
- `embedding-cartographer` — clusters a corpus, auto-names regions, returns a 2D map
- `time-travel-replayer` — re-runs a span tree with one node swapped (model, prompt, tool)
- `chaos-payload` — fuzzes a tool's inputs to find brittle assumptions
- `schema-migration-synthesizer` — diffs two schemas and emits a safe migration
- `five-whys` — recursive "why?" until first-principles bedrock is hit
- `decision-diary` — writes an immutable rationale row before any irreversible verb fires

---

## Agents — see [`agents/CATALOG.md`](agents/CATALOG.md)

### Generic
- `researcher` — query → cited brief
- `summarizer` — long doc → tiered bullets
- `classifier` — label-set → label
- `extractor` — text → typed fields
- `translator`
- `code-reviewer`
- `sql-writer`
- `email-drafter`
- `meeting-notes` — transcript → action items
- `triage` — inbound → category + priority
- `support-agent` — RAG over KB
- `faq-answerer`
- `pr-describer`
- `changelog-writer`
- `test-case-writer`
- `bug-reproducer`
- `onboarding-guide`
- `form-filler`
- `api-explorer`
- `runbook-runner`

### Creative
- `devils-advocate` — always argues against the current plan, never agrees
- `socratic-tutor` — only asks questions, never answers
- `steel-manner` — rebuilds the opposing view as strongly as it can before refuting
- `panel-of-five` — one prompt → five archetypal critiques (PM, SRE, Sec, IC, exec)
- `kintsugi` — finds load-bearing legacy code and writes appreciation/care notes for it
- `naive-newcomer` — asks "why?" until first principles
- `time-bomb-scout` — finds tech debt with expiry dates (deprecation calendars)
- `pattern-archaeologist` — excavates dead idioms from commit history
- `constraint-surfacer` — turns implicit team assumptions into explicit specs
- `dialect-translator` — rewrites text in different team idioms (eng↔sales↔legal)

---

## Governors — see [`governors/CATALOG.md`](governors/CATALOG.md)

### Generic
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
- `compliance-scan` — HIPAA/PCI/SOC2 keyword catch
- `jailbreak-detector`
- `business-hours-only`
- `geo-fence`
- `tenant-quota`
- `approval-policy`
- `output-length-cap`
- `redaction-on-egress`

### Creative
- `are-you-sure` — forces a self-doubt pass before any irreversible verb
- `echo-chamber-breaker` — rejects outputs too similar to recent ones (anti-rut)
- `conviction-tax` — penalizes high-confidence claims with no citations
- `anti-sycophancy` — blocks "great question!" / agreement-spirals
- `drift-detector` — flags when agent strays from system prompt embedding
- `tone-calibrator` — blocks tone mismatches for the channel
- `fact-half-life` — refuses use of facts older than X for class Y
- `show-your-work` — math/finance/legal answers must include reasoning chain
- `escalation-ladder` — auto-promotes to bigger model only after N small-model retries
- `pre-mortem-required` — no high-stakes plan executes without a written failure-modes section

---

## Workflows — see [`flows/CATALOG.md`](flows/CATALOG.md)

Existing flow demos: `code-graph/`, `atr/`, `cve-remediation/`.

### Generic
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

### Creative
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

---

## Machine Learning — see [`machine-learning/CATALOG.md`](machine-learning/CATALOG.md)

### Generic
- `sentiment` — pos/neg/neutral
- `intent-classifier`
- `ner` — named-entity recognition
- `topic-model`
- `embedding-encoder`
- `toxicity-classifier`
- `timeseries-forecast`
- `anomaly-detector`
- `image-classifier`
- `object-detector`
- `ocr-model`
- `language-id`
- `spam-filter`
- `churn-predictor`
- `doc-classifier`
- `outlier-detector`
- `risk-scorer`
- `recommender`
- `clustering`
- `summarization-extractive`

### Creative (platform-aware)
- `trace-shape-anomaly` — learns "normal" span trees, flags weird ones
- `prompt-drift-classifier` — detects when an agent silently veers off-policy
- `cost-spike-forecaster` — predicts $$ blowups N minutes ahead
- `hallucination-scorer` — per-claim grounding confidence
- `tool-choice-predictor` — recommends which tool the agent *should* have called
- `workflow-eta-predictor` — time-to-finish from intermediate state
- `operator-fatigue` — HITL reviewer quality decline detector
- `governor-rule-miner` — induces CLIPS rules from past escalation patterns
- `question-difficulty-router` — easy → small model, hard → big model
- `memory-utility-scorer` — predicts which memories are worth keeping past decay

---

## Knowledge — see [`knowledge/CATALOG.md`](knowledge/CATALOG.md)

### Generic
- `hr-policy-kb`
- `product-docs-kb`
- `api-reference-kb`
- `runbooks-kb`
- `customer-faq-kb`
- `sales-playbook-kb`
- `adr-archive` — engineering decisions
- `compliance-kb`
- `org-chart-kg`
- `cmdb-asset-kg`
- `code-dependency-kg`
- `customer-account-kg`
- `threat-intel-feed` — NVD/OSV/KEV
- `codebase-semantic-index`
- `meeting-transcript-memory`
- `user-preference-memory`
- `past-decision-memory` — with outcomes
- `conversation-history-memory`
- `vendor-contracts-kg`
- `feature-flag-registry`

### Creative
- `half-life-kb` — every fact has decay date + source-trust score
- `decision-journal-kg` — decisions ↔ rationales ↔ outcomes ↔ learnings
- `counterfactual-memory` — what we *almost* did, with reasons we didn't
- `disagreement-archive` — unresolved internal debates, kept open on purpose
- `anti-pattern-kb` — mistakes we made + how we noticed + what tipped us off
- `open-questions-kb` — questions without answers, indexed by domain
- `cargo-cult-registry` — patterns we use whose origin is lost; flagged for re-justification
- `folklore-kb` — oral-tradition ops knowledge captured before the carrier leaves
- `intentional-non-features-kb` — "why X isn't here," to stop re-litigation
- `provenance-graph` — every fact ↔ its source ↔ trust path
