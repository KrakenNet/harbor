# Tool · `notifiers` (`slack-post` / `discord-post` / `email-send`)

Outbound notification tools sharing one interface. Pick a channel
(slack/discord/email), pass a message, get back a delivery receipt.

## Purpose

Agents need to talk to humans. Most ops, support, and approval flows
end with "tell someone." Rather than three near-identical tools, the
group exposes a single envelope per channel with channel-specific
options.

## Inputs

Common envelope, channel-specific options under `channel_opts`:

| Field         | Type    | Required | Notes |
|---------------|---------|----------|-------|
| `channel`     | enum    | yes      | slack / discord / email |
| `to`          | string \| []string | yes | channel id, user id, or email |
| `subject`     | string  | conditional | required for email |
| `body`        | string  | yes      | markdown for slack/discord, html-or-text for email |
| `attachments` | []FileRef | no     | size capped per channel |
| `channel_opts`| object  | no       | thread_ts (slack), embeds (discord), reply_to (email) |

## Outputs

| Field        | Type    | Notes |
|--------------|---------|-------|
| `message_id` | string  | per-channel id (slack ts, discord id, email message-id) |
| `delivered`  | bool    | accepted by upstream, not "read" |
| `latency_ms` | int     |       |
| `channel`    | string  | echo |

## Implementation kind

Python tools. Three sibling implementations behind one tool group: Slack
Web API, Discord webhooks/REST, and SMTP/SES for email.

## Dependencies

- `slack_sdk` — Slack Web API
- `httpx` — Discord REST + webhook posts
- `aiosmtplib` or `boto3` — email delivery
- `internal/credential/` — per-channel credentials

## Side effects

External message delivery. Each call is one outbound network round-trip
and produces a real message a human will see. No retries by default for
chat (to avoid duplicate posts); email retries follow SMTP conventions.

## Failure modes

- Credential missing or revoked → `error_kind="auth"`
- Recipient not found → `error_kind="recipient"`
- Rate-limited by upstream → `error_kind="rate_limit"` with retry-after
- Attachment too large → rejected pre-send, `error_kind="too_large"`
- Channel-specific format error (e.g. invalid Slack mrkdwn) → `error_kind="format"`

## Why it's a good demo

It's the canonical "agent affects the outside world" tool family and the
one most likely to need a `hitl-trigger` or `business-hours-only`
governor in front of it. Pairs with `incident-response`,
`customer-churn-outreach`, and `daily-digest` workflows, and with the
`decision-diary` creative tool when notifications are themselves
decisions worth recording.
