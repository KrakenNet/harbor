# IR and Schema

Harbor's intermediate representation (IR) is a portable, JSON-Schema-typed description of an agent graph: nodes, edges, state shape, and policy bindings. The IR is the unit of replay — given the same IR, the same plugin versions, and the same inputs, Harbor reproduces a run bit-for-bit.

## Why an IR

- **Portability.** The IR is the contract between authoring tools and the runtime.
- **Determinism.** Every transition in a trace points back to an IR node.
- **Auditability.** Reviewers diff IRs, not Python.

## Nautilus prototype gaps

_None recorded yet. This section is updated when the IR-vs-Nautilus prototype (Phase 1 task 1.18 risk mitigation) surfaces a portable-subset gap. Each entry will state the gap, the remediation (lift into IR vs. document as out-of-scope), and the resolving task ID._

> TODO: link to the JSON Schema reference once `reference/ir-schema.md` is filled in.
