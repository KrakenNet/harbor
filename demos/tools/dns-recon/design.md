# Tool · `dns-recon` (`dns-lookup` / `whois` / `tls-cert-info`)

Three small network-introspection tools under one folder. Take a domain
or hostname, return DNS records, registration info, or TLS certificate
chain details.

## Purpose

Security, ops, and incident-response agents constantly need basic facts
about a domain: where does it resolve, who owns it, is the cert valid,
what's the SAN list. Bundling these as a tool group makes the most
common recon flow first-class.

## Inputs

Dispatched on `op`:

| Field        | Type    | Required | Notes |
|--------------|---------|----------|-------|
| `op`         | enum    | yes      | dns / whois / tls |
| `target`     | string  | yes      | hostname (dns/tls) or domain (whois) |
| `record_types`| []string | no      | dns op only; default A, AAAA, MX, TXT, NS |
| `port`       | int     | no, 443  | tls op only |
| `resolver`   | string  | no       | optional override DNS server |
| `timeout_ms` | int     | no, 5000 |       |

## Outputs

| Field         | Type             | Notes |
|---------------|------------------|-------|
| `op`          | string           | echo |
| `dns`         | map[string][]string | dns op only; type → values |
| `whois`       | WhoisRecord      | whois op only; registrar, creation, expiry |
| `tls`         | TLSChain         | tls op only; cert chain + SAN + dates |
| `duration_ms` | int              |       |

## Implementation kind

Python tools. `dnspython` for DNS, `python-whois` for WHOIS, raw
`ssl`+`socket` for TLS chain extraction.

## Dependencies

- `dnspython` — DNS resolver
- `python-whois` — WHOIS client
- Standard `ssl` / `socket` — for TLS handshake + cert capture

## Side effects

Outbound network: DNS queries to the resolver, TCP/53 to WHOIS servers,
TCP+TLS handshake to the target host. No filesystem, no state.

## Failure modes

- NXDOMAIN → returned as empty record set, `nxdomain=true`, not an error
- WHOIS server refuses (rate limit, blocked country) → `error_kind="whois_blocked"`
- TLS handshake fails before cert exchange → `error_kind="tls_handshake"`
- Resolver timeout → `error_kind="timeout"`

## Why it's a good demo

It shows three small useful tools sharing a single tool group instead of
three near-duplicate registrations. Pairs with `http-fetch` (often you
want both a resolution and a fetch), with the `threat-intel-feed`
knowledge base, and with security-incident workflows.
