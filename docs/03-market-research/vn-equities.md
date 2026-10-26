# Thị trường Việt Nam và SSI FastConnect Data

**Review:** 2026-10-26; official-documentation review only. No account, endpoint test, entitlement or storage/display right has been verified.

## Quyết định sản phẩm

SSI is one candidate in the Vietnamese multi-provider plan. Research FastConnect Data separately from FastConnect Trading. Product scope permits only read-only account queries; no order, transfer or other state-changing Trading operation may be integrated. Official documentation does not establish the user's account entitlement or local-use rights.

## Khả năng SSI công bố

Tài liệu [FastConnect Data API list](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/danh-sach-cac-api) mô tả các API REST sau:

| Nhóm | API được tài liệu liệt kê | Năng lực được mô tả | Cần xác minh trước khi dùng |
|---|---|---|---|
| Token | `AccessToken` | Lấy token từ ConsumerID/ConsumerSecret | TTL, refresh, rotation và scope trong entitlement thực tế |
| Instrument/reference | `Securities`, `SecuritiesDetails` | Danh mục chứng khoán và chi tiết mã | Thị trường/asset class, field set, lịch cập nhật |
| Index/reference | `IndexList`, `IndexComponents` | Danh sách chỉ số và thành phần | Coverage từng chỉ số và lịch sử constituent |
| Historical daily | `DailyOhlc` | OHLCV/Value theo mã, khoảng ngày và pagination | History depth, adjusted/raw semantics, corrections, quota |
| Historical intraday | `IntradayOhlc` | OHLCV/Value theo mã, ngày và pagination; tài liệu mô tả resolution mặc định một phút | Intraday retention, resolution được cấp, phiên/auction handling, quota |
| Index history | `DailyIndex` | Thống kê chỉ số theo ngày, gồm breadth/volume/value fields | Lịch sử, field semantics và market coverage |
| Daily snapshot | `DailyStockPrice` | Snapshot giá/đổi giá, ceiling/floor/reference, adjusted close, matched/deal volume/value, foreign buy/sell/room và trade counts | Quy tắc điều chỉnh, timestamp/availability và quyền lưu từng field |

Tài liệu [streaming](https://guide.ssi.com.vn/ssi-products/tieng-viet/fastconnect-data/du-lieu-streaming) mô tả các nhóm subscription:

| Mã/nhóm | Capability được mô tả | Vai trò tiềm năng trong local research |
|---|---|---|
| `F` | Trạng thái chứng khoán/phiên giao dịch | Session state và kiểm soát thời gian có thể giao dịch |
| `X` | Summary; `X-Quote` gồm bid/ask depth và trades/quotes | Quote/trade tape và thanh khoản hiển thị |
| `B` | Realtime OHLCV; tài liệu ghi `Value` hiện bằng 0 | Nến live/provisional; phải reconcile với REST/historical |
| `R` | Foreign room/foreign flows | Room và giao dịch khối ngoại |
| `MI` | Index data với breadth, OHLC-like values, bid/ask/status | Chỉ số và market breadth |
| `OL` | Odd-lot trades | Giao dịch lô lẻ, phải tách khỏi regular-board candle/trade totals |

Tài liệu dịch vụ có nhắc market codes `HOSE`, `HNX`, `UPCOM`, `DER`, `BOND`. Đây là capability evidence ở mức tài liệu; chưa xác minh mỗi API/feed có cùng coverage, và chưa chốt V1 có phái sinh/trái phiếu hay chỉ cổ phiếu cơ sở. “Dùng hết” trong product direction có nghĩa không bỏ qua nhóm SSI phù hợp; không có nghĩa bật mọi field/feed trước khi entitlement và ý nghĩa dữ liệu được kiểm tra.

## Đăng ký, credentials và quota

[Hướng dẫn đăng ký dịch vụ SSI](https://guide.ssi.com.vn/ssi-products/service-registration) yêu cầu tài khoản SSI và đăng ký được chấp thuận trước khi tạo API key tại iBoard. Hướng dẫn cũng yêu cầu đăng ký fixed IP; cần xác nhận điều kiện áp dụng cho tài khoản cụ thể. General Information liệt kê ConsumerID, ConsumerSecret và PrivateKey cho FastConnect API; mỗi service/capability chỉ nhận thông tin cần thiết cho thao tác được phép. Secrets không đưa vào chat, commit, log hay frontend bundle.

[General Information](https://guide.ssi.com.vn/ssi-products/general-information) mô tả quota theo API và connection key, nhưng không công bố mức cụ thể cho tài khoản. Streaming được khuyến nghị thay cho polling dày; dịch vụ có thời hạn một năm và cần gia hạn. Fixed IP được nêu trong hướng dẫn đăng ký. Xác nhận quota, phí, IP và renewal của tài khoản trước khi bật kết nối.

Chưa có account/entitlement của người dùng để xác minh giá, phí, endpoint access, số kết nối đồng thời, request/subscription limits, rate reset, history depth, retention hoặc vùng/địa chỉ IP được phép. Không yêu cầu người dùng gửi secret để hoàn thành docs.

## Broker account read-only

[FastConnect API overview](https://guide.ssi.com.vn/ssi-products) phân biệt FC Data và FC Trading. Trading API bao gồm cả truy vấn thông tin tài khoản lẫn thao tác đặt/sửa/hủy lệnh; dự án chỉ nghiên cứu các query đọc cần thiết như balances, holdings/portfolio và lịch sử hoạt động. Phải lập allowlist theo từng method/endpoint; không dùng nguyên SDK Trading với các thao tác ghi bị để sẵn.

[Trading connection guide](https://guide.ssi.com.vn/ssi-products/fastconnect-trading/connection-guide) mô tả access token tối đa 8 giờ; account query cần token. OTP/auth code có thể là PIN, SMS, email hoặc SmartOTP theo cách đăng ký. Không lưu OTP như secret dài hạn. Phải xác minh account read entitlement riêng với market-data entitlement; account snapshots chỉ hiển thị riêng và không ghi vào fund ledger local.

## Rights và trạng thái nguồn

Official docs describe capabilities and registration flow; they do not grant project-wide rights or prove a user's account entitlement. Review service terms and separately verify local access, caching/retention, export, research/backtest, derived metrics, display/audience, attribution, deletion and commercial status. A user-provided key does not imply redistribution rights.

Source register keeps SSI REST and streaming separate. Both currently have `documented=true`, `access-tested=false`, `rights-confirmed=false`, `approved=false`. Default preparation is fixture-only. A bounded access test requires separate authorization under the [probe policy](source-register.md#access-probes-and-operating-states); its success does not grant production/storage rights.

## Yêu cầu market contract cần chốt

- Tài liệu API và stream nêu các mã thị trường gồm HOSE, HNX, UPCOM, DER và BOND; streaming còn nêu HNXBOND. Đây là market code evidence, chưa chứng minh các market code xuất hiện trong mọi endpoint hoặc entitlement. Tài liệu streaming mô tả cash và derivatives; khả năng dữ liệu trái phiếu cần đối chiếu từng endpoint.
- Canonical instrument identity phải giữ venue, board/market type, native symbol, instrument class và lifecycle dates; không dùng ticker đơn lẻ làm identity.
- Giữ payload timestamp, timezone, resolution, observation/received time và publication/availability time riêng. Chuẩn hóa UTC nhưng lưu unit/original value theo policy.
- Tách regular board, auction/session, odd lot, derivative và bond nếu SSI feed trả về chúng; không nhập chung candle series trước khi semantics được hiểu.
- Giữ raw revisions, corrected/adjusted status và source version nếu được phép; backtest chỉ dùng dữ liệu khả dụng tại thời điểm tương ứng.
- Missing ranges/unsupported fields là partial/unavailable; không nội suy hoặc gán zero.
- Quote/trade stream không thay thế historical feed. Historical REST và live stream phải reconcile với rule về overlap, revisions, closed bars và reconnect gaps.

## Các nguồn khác

SSI FastConnect Data documents daily/reference APIs and realtime stream groups `F`, `X`/`X-Quote`/`X-Trade`, `B`, `R` and `MI`; market-specific quote depth differs. The docs include derivatives/bond market codes in some places, which does not prove every API/feed supports each market. API examples may use zero for absent quote levels; map those values using feed semantics rather than treating them as zero-priced levels. Source approval remains independently split for REST, streaming and account-read capabilities.

News engine is an independent workstream; see [News ingestion](../05-news-ingestion/README.md). Do not infer upstream rights from an SDK license.
