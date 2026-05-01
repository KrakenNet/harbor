# Machine Learning — Demo Catalog

ML model primitives served via gomlx / onnxrt. Each entry will graduate into
its own folder with a model card, training/inference config, sample data,
and a smoke-test inference call.

## Generic

- `sentiment` — pos / neg / neutral
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

## Creative (platform-aware)

These models train on Railyard's own telemetry — span trees, governor
decisions, memories, traces — so they only work where a platform like this
exists.

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
