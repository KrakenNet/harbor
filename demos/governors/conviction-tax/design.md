# Governor · `conviction-tax`

A levy on certainty without evidence. High-confidence claims must come
attached to citations, traceable spans, or memory references. The more
absolute the claim, the higher the tax — at some point, conviction
without provenance is simply rejected.

The name is the mechanism. The agent gets to assert anything it wants,
but assertions cost more when they don't show their work, and
unsupported absolutes cost more than they're worth.

## Purpose

LLMs are fluent and confident in equal measure, and the two compound.
"It is well-established that..." with no source is the failure mode.
Hedge-vs-cite is the lever this governor pulls: write less assertively,
or back it up.

The mechanism is intentionally not a binary block. It's a graded
penalty: low-confidence claims pass freely, mid-confidence claims need
something attached, and "definitely / always / never / proven" claims
without citations get rewritten or rejected.

## Trigger event

`post_response`.

## Facts asserted

```clips
(deftemplate claim
  (slot trace_id)
  (slot agent)
  (slot claim_id)
  (slot conviction_score)  ; 0..1, derived from modal verbs and absolutes
  (slot citation_count)
  (slot memory_refs)       ; count of decision-journal-kg / kb hits
  (slot domain))           ; medical | legal | finance | general

(deftemplate decision
  (slot trace_id)
  (slot verdict))           ; allow | rewrite | halt
```

## Rules

```clips
(defrule absolute-without-citation
  (claim (trace_id ?t) (conviction_score ?c) (citation_count 0) (memory_refs 0))
  (test (>= ?c 0.9))
  =>
  (emit-output "halt:absolute_without_citation")
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule strong-needs-evidence
  (claim (trace_id ?t) (conviction_score ?c) (citation_count 0) (memory_refs 0))
  (test (and (>= ?c 0.7) (< ?c 0.9)))
  =>
  (emit-output (str-cat "rewrite:hedge:" ?c))
  (assert (decision (trace_id ?t) (verdict rewrite))))

(defrule regulated-domain-strict
  (claim (trace_id ?t) (domain ?d) (citation_count 0) (conviction_score ?c))
  (test (and (member ?d (create$ medical legal finance)) (>= ?c 0.5)))
  =>
  (emit-output (str-cat "halt:regulated_no_citation:" ?d))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule allow-cited-or-hedged
  (claim (trace_id ?t) (conviction_score ?c) (citation_count ?n))
  (test (or (< ?c 0.7) (> ?n 0)))
  =>
  (emit-output "allow:cited_or_hedged"))
```

## Streams

- `claim.extractor` — sentence-level extractor that emits per-claim
  conviction scores and counts of citations / memory hits
- `kb.lookup` — verifies citation IDs actually exist
- `agent.registry` — domain tag

## Routes

| Verdict | Route                                                              |
|---------|--------------------------------------------------------------------|
| halt    | reject the response, surface a "needs evidence" envelope           |
| rewrite | run a "hedge-or-cite" pass that softens absolutes and inserts citations from working memory if any are nearby |
| allow   | pass through; per-claim conviction + provenance attached to span   |

## Sample violation → decision

Response from a finance agent: *"This stock is guaranteed to outperform
the market over the next decade."*

Extractor emits:
```
(claim
  (claim_id c-71)
  (conviction_score 0.97)   ; "guaranteed", "outperform", "decade"
  (citation_count 0)
  (memory_refs 0)
  (domain finance))
```

Output:
```
halt:absolute_without_citation
halt:regulated_no_citation:finance
```

The response never reaches the user. The trace records both the rejected
claim and the conviction extractor's reasoning.

## Why it's a good demo

1. **It is policy as a price, not a wall.** Most safety governors are
   binary — pass or fail. `conviction-tax` is a graded scheme where the
   cost of an assertion scales with its absoluteness. That's a different
   conceptual primitive than most safety stacks expose.

2. **It connects three Railyard capabilities at once.** It needs the
   per-claim extractor (an agent or tool), the citation graph (the KB +
   `provenance-graph`), and the rule layer (CLIPS). The composition is
   the demo: no single primitive does this, but together they do.

3. **It pairs with `show-your-work` and `anti-sycophancy` for an
   epistemic bundle:** don't agree reflexively, don't be confidently
   vague, and when you do commit, show the receipts. Try removing this
   governor on a finance demo for one minute — the difference is
   immediate.
