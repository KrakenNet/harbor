# Harbor Demos

Each demo is a single-file design doc (`<demo>/<demo>.md`) describing a real
workflow that exercises Harbor's runtime. Read in order, they walk from a
single store + skill all the way up to the full stack.

## Learning path

| # | Demo | Difficulty | Hero capability |
|---|------|------------|------------------|
| 1 | [`internal-docs-qa/`](internal-docs-qa/internal-docs-qa.md) | easy | Mandatory provenance + lineage audit CI gate |
| 2 | [`code-graph/`](code-graph/code-graph.md) | easy | Stateful agent graph over a real codebase |
| 3 | [`pr-review/`](pr-review/pr-review.md) | easy → medium | Drives on `code-graph` + replay for dispute |
| 4 | [`atr/`](atr/atr-graph.md) | medium | Threat-response workflow (legacy, see `soc-triage`) |
| 5 | [`soc-triage/`](soc-triage/soc-triage.md) | medium | Bosun-signed governance + counterfactual replay |
| 6 | [`regwatch/`](regwatch/regwatch.md) | medium | Cron trigger + air-gap deployment variant |
| 7 | [`support-veto/`](support-veto/support-veto.md) | medium → hard | Fathom interrupt mid-run + signed-pack hot-swap |
| 8 | [`pv-case-manager/`](pv-case-manager/pv-case-manager.md) | hard | Master-of-all (19 capabilities, regulated industry) |
| 9 | [`cve_remediation/`](cve_remediation/README.md) | hard | Production showcase — every node kind, action, store, trigger; 10 IRs, 174 tests |

## How to read a demo doc

Every doc has the same shape:

1. **Pitch** — one-paragraph use case + audience.
2. **Flow diagram** — ASCII graph from trigger → action → audit.
3. **Why it lands** — the sales/adoption argument.
4. **Harbor capabilities exercised** — the explicit feature checklist.
5. **Demo footprint** — concrete `demos/<name>/` directory layout + `Makefile` targets ready to implement.

The footprint section is what to hand to a spec executor when promoting a demo
from design to running code.

## Suggested adoption order

- **For docs/marketing**, lead with `internal-docs-qa` and `pv-case-manager` —
  one shows the bar is low, the other shows the ceiling.
- **For developer evangelism**, lead with `code-graph` + `pr-review` as a
  paired narrative ("build the map / drive on the map").
- **For enterprise sales**, lead with `soc-triage` and `support-veto` — both
  exercise governance + replay, which is what closes regulated-industry deals.
- **For vertical-specific outreach**, `pv-case-manager` re-skins to
  clinical-trial pharmacy, medical-device complaints, CFPB adverse-action,
  defense incident triage, or financial trade-surveillance review with no
  architectural change.

## Feature coverage matrix

| Capability | docs-qa | code-graph | pr-review | soc-triage | regwatch | support-veto | pv-cm | cve-rem |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| DocStore | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VectorStore | ✓ |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| GraphStore |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FactStore |   |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |
| MemoryStore |   |   |   | ✓ |   | ✓ | ✓ | ✓ |
| RAG / autoresearch | ✓ |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| RetrievalNode (RRF) | ✓ |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MLNode + sha256 weights |   |   |   | ✓ |   |   | ✓ | ✓ |
| DSPy adapter | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MCP adapter |   |   |   |   |   |   | ✓ | ✓ |
| Fathom + harbor_action |   |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Bosun signed packs |   |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| InterruptAction (HITL) |   |   |   | ✓ |   | ✓ | ✓ | ✓ |
| Cron trigger |   |   |   |   | ✓ |   | ✓ | ✓ |
| Webhook trigger |   |   | ✓ | ✓ |   |   | ✓ | ✓ |
| Provenance bundle | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BLAKE3 artifacts | ✓ |   |   | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ed25519 audit | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Checkpoint (sqlite/pg) |   | ✓ |   | ✓ |   | ✓ | ✓ | ✓ |
| Counterfactual replay |   | ✓ | ✓ | ✓ |   | ✓ | ✓ | ✓ |
| Air-gap variant |   |   |   |   | ✓ |   | ✓ | ✓ |
| harbor.serve API |   |   |   | ✓ |   | ✓ | ✓ | ✓ |
| mTLS + capabilities |   |   |   | ✓ |   | ✓ | ✓ | ✓ |
| KG promotion (memory) |   |   |   |   |   |   | ✓ | ✓ |
| Cypher subset linter |   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lineage audit CI | ✓ |   |   | ✓ | ✓ |   | ✓ | ✓ |
| Multi-runtime sandbox |   |   |   |   |   |   |   | ✓ |
| Progressive rollout (canary→fleet) |   |   |   |   |   |   |   | ✓ |
| Triggered safety graphs (5×) |   |   |   |   |   |   |   | ✓ |
| Audit-chain anchor (JWS) |   |   |   |   |   |   |   | ✓ |
| GEPA + Shamir ship ceremony |   |   |   |   |   |   |   | ✓ |
