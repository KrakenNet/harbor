# Knowledge · `folklore-kb`

A knowledge base of oral-tradition operational knowledge — the "you
have to know to know" stuff that lives in one engineer's head, gets
shared at 2am during incidents, and disappears the day they leave.
Captured on purpose, before the carrier walks out the door.

Documentation captures what the team has decided to write down. The
`folklore-kb` captures what the team has *not* written down — the
heuristics, the workarounds, the "always check the third graph
first" tricks — and the reason it hasn't been written is rarely that
it's unimportant. Usually it's that nobody asked.

## Purpose

Two specific failure modes this KB addresses:

1. The senior engineer who's been on-call for the legacy mainframe for
   nine years and is going on sabbatical. Nobody knows what they know.
2. The "tribal Slack thread from 2022" — institutional knowledge whose
   only retrieval path is "ask whoever was around then."

The load-bearing innovations:

1. **Folklore is solicited, not waited for.** The
   `inverse-onboarding` workflow drives interviews with carriers to
   extract their heuristics on a schedule, not in a panic.
2. **Each entry is attributed to a *carrier*** (the person whose head
   it lives in) and rated by *fragility* — how many other people on
   the team also know this. Single-carrier folklore is high-priority
   for capture and corroboration.
3. **Entries link to the *triggering observable*** — not the action,
   the cue. Folklore is "when X happens, do Y." The Y is easy. The
   X — the cue you learn to recognize — is the load-bearing part, and
   the part most documentation skips.

## Type

Knowledge Base (markdown documents) with chunked embeddings;
append-only, with corroboration sub-records adding carriers over time.

## Schema

Each folklore entry carries frontmatter:

```yaml
---
folklore_id: <uuid>
title: <the heuristic, in the carrier's words>
domain: <area>
captured_at: <date>
captured_from: <person>
captured_via: <interview|incident-followup|chat-mining|self-filed>
carriers: [<person>]                    // others who confirmed they also know this
fragility: <single-carrier|few-carriers|widespread>
trigger_observable: <prose, the cue>
action: <prose, what to do>
why_it_works: <prose, may be "unknown" — that's an honest answer>
related_runbooks: [<doc-id>]            // if any; often there are none, that's why it's folklore
last_used: <date-or-null>
---
```

Body sections: **The cue** · **The action** · **What I think is going
on** · **War stories where this saved us**.

## Ingest source

- The `inverse-onboarding` workflow ("what would I forget if I left
  tomorrow?") — primary source
- Post-incident follow-ups: when an SRE pulls a save out of nowhere,
  the `meeting-notes` agent flags it for folklore capture
- Chat-mining of `conversation-history-memory` — when senior engineers
  hand off knowledge in DMs, those threads are surfaced for folklore
  candidates with the carrier's consent
- Self-filing — engineers who realize they've been holding something in
  their head can submit directly

## Retrieval query example

> A junior on-call gets paged at 3am for a slow-query alert on the
  legacy reporting database:

→ semantic search over `title + trigger_observable` for "slow query
  reporting db"
→ retrieves `folklore_id=fk_037`: "the reporting DB's plan cache goes
  cold around UTC 02:00 because of the nightly stats refresh; if you
  see a slow query in the first 30 minutes after that, don't roll the
  service — wait 5 minutes."
→ carrier: Marcus (going on sabbatical Q3). Fragility:
  `single-carrier`. Action shown verbatim. The junior on-call doesn't
  page Marcus at 3am — and doesn't roll the service unnecessarily.

## ACLs

- **Read**: workspace-wide for ops and engineering folklore; sensitive
  HR / customer / sales folklore tagged for restricted readership
- **Write**: append-only — entries can gain corroborating carriers but
  the original capture text stays intact (the carrier's voice is part
  of the value)
- **Carrier consent**: required at capture time; carriers can request
  their attribution be anonymized after departure
- **Public/customer access**: never

## Why it's a good demo

1. **It captures the most-asked-for and least-shipped intervention in
   ops orgs.** "Capture tribal knowledge before they leave" is on every
   leadership wishlist; nobody has a primitive for it. Making it a
   structured KB with a *workflow* (`inverse-onboarding`) that drives
   the capture is the difference between an aspirational ask and a
   running system.

2. **The `trigger_observable` field is the distinctive thing.** Most
   "tips and tricks" docs explain the action. Folklore's value is in
   the *recognition* — the cue you learn to see after enough
   incidents. Forcing the capture to include the cue, separately from
   the action, is what makes the entry usable by someone who hasn't
   already developed the carrier's intuition.

3. **It composes with `inverse-onboarding`,
   `meeting-transcript-memory`, and `governor-rule-miner` to form a
   capture pipeline.** Carriers get interviewed; transcripts get
   mined; the rule-miner promotes recurring folklore patterns into
   formal governor rules; the folklore that *can't* be formalized
   stays as folklore. The pipeline triages knowledge by how
   structurable it is, instead of forcing everything into the same
   shape.

## Sample read

> The `inverse-onboarding` workflow runs against Marcus, the carrier
  for the legacy reporting database, two weeks before sabbatical:

→ workflow surfaces six candidate folklore entries by mining Marcus's
  on-call action history and chat DMs
→ Marcus reviews, edits, confirms five, rejects one ("that one was a
  one-off, don't put it in the KB")
→ each confirmed entry asks: "anyone else on the team know this?"
  Three engineers raise their hands; their names get added as
  corroborating `carriers`, dropping the fragility from
  `single-carrier` to `few-carriers` for those entries.
→ two entries remain `single-carrier` — Marcus is the only person who
  recognizes those specific cues. The team now *knows* it has two
  carrier-fragile bus-factors, and can prioritize: write more
  detailed runbooks, or accept the risk for the sabbatical period.
→ none of this would have happened in a normal "before you go please
  document things" email.
