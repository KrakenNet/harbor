# Harbor

Orchestration framework for LLMs, ML models, tools, and CLIPS rules.

> **Status:** v0.1.0 (foundation phase). Public API is unstable until v1.0.

Harbor composes LLMs, classical ML models, tools, and deterministic logic
into auditable, replayable graphs whose transitions are decided by
CLIPS-based rules over provenance-typed facts.

## Install

```bash
uv add harbor
```

Requires Python 3.12+.

## Documentation

Architecture, ADRs, and API contracts live under [`design-docs/`](./design-docs/).

## License

Apache-2.0. See [LICENSE](./LICENSE).
