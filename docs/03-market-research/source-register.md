# Source register và approval gates

**Ngày review:** 2026-10-19. SSI FastConnect Data là market-data direction của V1; chưa có account access test hoặc quyền lưu/hiển thị/research được xác nhận. News sources dưới đây là candidates cần review riêng, không phải nguồn đã bật.

## Evidence flags

- `documented`: có primary documentation cho capability cụ thể.
- `access-tested`: bounded test ghi rõ ngày, region/runner, endpoint/schema và quota.
- `rights-confirmed`: evidence bao phủ exact fields, purpose, audience, geography, storage/retention và derived use.
- `approved`: owner chấp nhận source/purpose sau khi các evidence phù hợp được review.

Các flags độc lập. `false` nghĩa là chưa có evidence trong register, không kết luận provider từ chối khả năng/quyền. Ghi nguồn, phiên bản/ngày, owner, expiry/review date và disable procedure cho mỗi approval. Không ghi credentials hoặc account identifiers vào tài liệu này.

## Market data — SSI FastConnect Data

| Source ID | Capability direction | Documented | Access tested | Rights confirmed | Approved |
|---|---|---:|---:|---:|---:|
| `SSI-FC-DATA-REST` | Token, reference, historical/reference market APIs | true | false | false | false |
| `SSI-FC-DATA-STREAM` | Realtime market-data stream groups | true | false | false | false |

Official capability references: [REST API list](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/danh-sach-cac-api), [streaming data](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/du-lieu-streaming), [service registration](https://guide.ssi.com.vn/ssi-products/service-registration), [general information](https://guide.ssi.com.vn/ssi-products/general-information). These links establish documentation references only. User entitlement, fees, coverage, quota, exact schema, geography and local-use rights remain unverified.

**Gate decision:** BLOCKED for live calls and persistence of real market payload. Safe preparation is limited to synthetic fixtures, offline parsers/normalizers and local security design. To open a gate, record account-specific access evidence and written/contractual rights for local access, storage, export, research/backtest, display, attribution, retention/deletion and permitted audience. Approve REST APIs and stream groups separately where their terms/capabilities differ.

## News source candidates — independent engine

Candidates require a fresh, source-specific review before fetching or storing content. RSS/page reachability does not establish full-text, translation, model processing, image, retention or redistribution rights.

| Candidate | Region/type | Candidate evidence/reference | Gate state |
|---|---|---|---|
| SEC releases / EDGAR | International regulator and filings | [SEC press releases](https://www.sec.gov/newsroom/press-releases), [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Not reviewed for engine use |
| CFTC releases | International regulator | [CFTC RSS](https://www.cftc.gov/RSS/index.htm) | Not reviewed for engine use |
| HNX disclosures | Vietnam market disclosures | [HNX disclosure information](https://www.hnx.vn/en-gb/thong-tin-cong-bo-up-hnx.html) | Not reviewed for engine use |
| CafeF RSS | Vietnam financial news | [CafeF RSS](https://cafef.vn/index.rss) | Candidate; terms/fields unreviewed |
| Vietstock RSS | Vietnam financial news | [Vietstock RSS directory](https://vietstock.vn/rss) | Candidate; access/terms/fields unreviewed |
| VnEconomy RSS | Vietnam financial news | [VnEconomy RSS candidate](https://vneconomy.vn/rss.htm) | Candidate; access and terms unverified |

News engine owner must record allowed metadata/content fields, fetch method, audience, processing/derived use, retention/deletion, attribution, rate limits, source corrections and review expiry. Keep news source approval separate from market-data approval.

## Approval record

For each approved source and purpose record: source ID, owner, exact fields, audience/geography, allowed transformations and research use, storage/retention/deletion, attribution, quota evidence, terms version/hash, review date/expiry and disable action. If terms or entitlement change, stop the affected use, mark impacted local records restricted and apply the documented review/delete process. No silent provider fallback.
