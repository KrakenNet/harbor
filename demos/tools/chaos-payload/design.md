# Tool · `chaos-payload`

Aim a fuzzer at any registered tool. Generate boundary-case, malformed,
encoded, oversize, and adversarial inputs against the tool's declared
schema and watch what breaks. Returns a list of brittle assumptions
ranked by how badly they fail.

Most tools have a happy path that's been tested with three obvious
inputs. The actual world hands them empty strings, NUL bytes, recursive
JSON, RTL-override Unicode, and 12MB payloads. `chaos-payload` is the
unit test you wish you'd written.

## Purpose

Find tool brittleness before users (or a hostile prompt) do. Especially
useful before promoting a tool to production scope, before granting it
to a wider set of agents, and as a periodic health check on
long-installed tools whose downstream callers have changed.

## Inputs

| Field           | Type    | Required | Notes |
|-----------------|---------|----------|-------|
| `target_tool`   | string  | yes      | registered tool id |
| `iterations`    | int     | no, 200  | total payloads to try |
| `categories`    | []enum  | no       | empty / oversize / unicode / encoding / type-mismatch / injection / nesting |
| `seed`          | int     | no       | for reproducibility |
| `cost_cap`      | int     | no, 200  | abort if cumulative tool cost exceeds N units |
| `dry_run`       | bool    | no, false| true → generate payloads but don't invoke the tool |

## Outputs

| Field             | Type             | Notes |
|-------------------|------------------|-------|
| `findings`        | []ChaosFinding   | one per failure cluster |
| `payload_corpus`  | []Payload        | full set, with category tags |
| `coverage`        | CoverageReport   | per-input-field, per-category |
| `tool_panic_rate` | float [0..1]     | uncaught-error rate |
| `recommendations` | []string         | LLM-summarized fixes per finding |

`ChaosFinding` carries: `category`, `representative_payload`,
`failure_kind` (panic / wrong-shape / silently-truncated / hang / leak),
`severity`, and a `repro_url` to a saved trace.

## Implementation kind

DSPy tool. Payload generation is a mix of deterministic generators
(boundary values, encoding tricks) and LLM-driven adversarial
construction (which is what makes it DSPy — getting a model to produce
inputs that look plausible but break implicit assumptions is a prompt
problem, not a fuzzer problem).

## Dependencies

- `hypothesis` — property-based payload generation
- LLM judge for adversarial-payload synthesis and finding clustering
- `internal/agent/tool_executor.go` — the tool invocation path
- `internal/tracing/` — every probe is a span, so failures are debuggable
- Sibling tool `counterfactual-mutator` — once a failing payload is
  found, the mutator can minimize it to a smallest-failing-input

## Side effects

Many invocations of the target tool. If the tool itself has side effects
(writes a file, sends a message), so will the fuzzer. The
recommended pattern is to run `chaos-payload` against tools registered
in a sandboxed tenant first; the tool refuses to run against tools
flagged as `production_irreversible=true` unless explicitly overridden.

## Failure modes

- Target tool unregistered → rejected, `error_kind="no_tool"`
- Cost cap hit → halts with partial findings preserved
- All probes pass → returns empty `findings`, sets `tool_panic_rate=0.0`
  (this is itself a useful artifact for promotion gates)
- LLM-generated payloads consistently invalid against the tool schema
  → reports `error_kind="schema_mismatch"` so the schema can be tightened

## Why it's a good demo

Three reasons:

1. **The platform makes "invoke any tool 200 times with structured
   inputs" trivial.** Every tool has a typed contract, every invocation
   is a span, every failure is reproducible from the trace. On a
   platform without those properties, building this fuzzer is a
   week-long project; here it's a tool.
2. **It composes with the platform's safety story.** Pairs with the
   `tool-allowlist` and `pre-mortem-required` governors (a tool with
   open chaos-payload findings can be auto-demoted from the allowlist),
   the `decision-journal-kg` (each promotion records the chaos pass
   that justified it), and the `anti-pattern-kb` knowledge base (which
   collects every category of failure ever found).
3. **It changes what "tool ready" means.** Today a tool is "ready" when
   someone says it is. After this demo, "ready" means "passed N
   chaos-payload runs at coverage X" — a property the platform can
   compute and a governor can enforce.

## Sample interaction

> target_tool: csv-write
> iterations: 200

→ findings:
  1. **NUL bytes in cells** silently truncate the row. severity: HIGH.
     repro: payload #47.
  2. **Header row containing the configured delimiter** produces
     malformed output. severity: HIGH. repro: #112.
  3. **Empty `rows` array** writes a header-only file but reports
     `row_count=0`; correct, but downstream `csv-read` then errors with
     `error_kind="ragged"` on re-read. severity: MED. repro: #180.
→ tool_panic_rate: 0.015
→ recommendations: tighten input schema to forbid NUL in cells; quote
  header values containing the delimiter; add an empty-rows fast-path.

Each finding files into `anti-pattern-kb` with its repro trace, and the
tool's `production_ready` flag is held until the HIGH-severity ones
are closed.
