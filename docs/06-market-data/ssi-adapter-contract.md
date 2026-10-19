# SSI FastConnect Data — adapter preparation contract

**Trạng thái:** implementation preparation only. SSI production capabilities remain blocked (`access-tested=false`, `rights-confirmed=false`, `approved=false`). Current mode is fixture-only; a separately authorized bounded probe may precede production approval under the [probe policy](../03-market-research/source-register.md#access-probes-and-operating-states). No probe is authorized by this document.

## Boundary mục tiêu

- React UI communicates only with a local loopback API.
- A local adapter owns SSI authentication, bounded requests, quota handling, normalization and stream lifecycle.
- Credentials and provider tokens stay outside browser storage, URLs, logs, fixtures and Git.
- Product development/serving uses synthetic fixtures until production approval; probe outputs are not product datasets or reusable fixtures.
- FastConnect Trading and real order routing are excluded.

The specific local process, secret store, database and transport between UI and local service are not yet selected. See [architecture decisions](../02-architecture/decisions.md).

## Capability inventory from SSI documentation

Official SSI documents describe the following capabilities. This list is not proof of account entitlement, exact schema, history depth or permitted use.

| Product area | Documented API/feed examples | Verification still required |
|---|---|---|
| Authentication | Access-token API using ConsumerID/ConsumerSecret | Current request/response schema, token lifetime, refresh, entitlement and secure local handling |
| Reference data | Securities, security details, index list/components | Supported markets/classes, field meaning, updates and corrections |
| Historical data | Daily OHLC, intraday OHLC, daily index and daily stock snapshot | Actual schema, timestamp/value units, resolution/history depth, pagination and quota |
| Streaming | Documented groups include F, X/X-Quote, B, R, MI and OL | Exact protocol, message schema, subscription limits, coverage, replay/reconnect and retention rights |

See the [SSI capability review](../03-market-research/vn-equities.md) and [source register](../03-market-research/source-register.md) for evidence status and source URLs. Recheck provider documentation before implementation because API details can change.

## Normalization requirements to design after schema verification

- Preserve source identifier, endpoint/feed, provider timestamp and unit, local receive time and parser version.
- Normalize instants to UTC only after endpoint-specific timezone/precision semantics are established; retain original value/unit when policy allows.
- Identify instruments with venue, board/market type, instrument class, native symbol and lifecycle; symbol alone is insufficient.
- Represent unknown, missing, stale, partial, provisional and closed states explicitly. Never convert unknown values to zero or invent bars.
- Keep revisions and adjustment semantics traceable where source terms permit storage.
- Reconcile history and live stream with documented overlap, gap, duplicate and correction behavior before serving paper sessions.

## Failure and quota behavior

- Bound request ranges, concurrency, timeouts, retries and subscription counts according to the verified account plan.
- Stop on authentication, terms/policy denial, hard quota response or repeated schema errors; do not retry indefinitely or use undocumented fallback sources.
- Expose safe local status for connected, reconnecting, stale, partial, unavailable and stopped states without returning credentials/tokens.
- On disconnect, do not infer unseen ticks or fills. Recovery/backfill behavior remains a design decision until provider replay/history support is verified.

## Approval gate before live adapter work

For each REST API and stream group, record entitlement, reviewed access evidence, rights for the exact local access/storage/export/research/display use, fields, retention/deletion, attribution, terms version, review expiry and disable procedure. Only the source register owner may approve that production purpose. Offline work remains the default; scoped access tests require separate probe authorization and must not feed production serving.
