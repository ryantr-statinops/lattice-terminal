# Thị trường Việt Nam và SSI FastConnect Data

**Review:** 2026-10-18; official-documentation review only. No account, endpoint test, entitlement or storage/display right has been verified.

## Quyết định sản phẩm

Thị trường Việt Nam và SSI FastConnect Data là hướng market-data đầu tiên. Chỉ bật endpoint/feed phù hợp sau khi xác minh entitlement, điều khoản dịch vụ, quota, coverage, schema và quyền xử lý/lưu local. Không tích hợp FastConnect Trading. Endpoint được tài liệu hóa không đồng nghĩa tài khoản có quyền truy cập hoặc project có quyền sử dụng theo mọi cách.

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

[Hướng dẫn đăng ký dịch vụ SSI](https://guide.ssi.com.vn/ssi-products/service-registration) cho biết khách hàng cần đăng ký FastConnect, có tài khoản SSI và được chấp thuận; quy trình hướng dẫn tạo API key tại iBoard. ConsumerID/ConsumerSecret là thông tin bí mật; chỉ nhập vào local secret/config flow đã được triển khai, tuyệt đối không đưa lên chat, commit, log hoặc frontend bundle. FastConnect Data token endpoint tài liệu hóa ConsumerID/ConsumerSecret; không lấy nhầm credentials hoặc phạm vi của FastConnect Trading.

[General Information](https://guide.ssi.com.vn/ssi-products/general-information) mô tả giới hạn API theo từng API và connection key, nhưng không công bố số quota áp dụng cho tài khoản cụ thể; SSI có thể xác nhận/nâng giới hạn. Streaming được khuyến nghị cho dữ liệu realtime thay cho polling dày. Hướng dẫn đăng ký mô tả thời hạn dịch vụ một năm và cần gia hạn. Tài liệu có nhắc lựa chọn fixed IP trong quy trình đăng ký; chưa xác minh đây là yêu cầu bắt buộc với entitlement cụ thể của người dùng.

Chưa có account/entitlement của người dùng để xác minh giá, phí, endpoint access, số kết nối đồng thời, request/subscription limits, rate reset, history depth, retention hoặc vùng/địa chỉ IP được phép. Không yêu cầu người dùng gửi secret để hoàn thành docs.

## Rights và trạng thái nguồn

Official docs describe capabilities and registration flow; they do not grant project-wide rights or prove a user's account entitlement. Review service terms and separately verify local access, caching/retention, export, research/backtest, derived metrics, display/audience, attribution, deletion and commercial status. A user-provided key does not imply redistribution rights.

Source register keeps SSI REST and streaming separate. Both currently have `documented=true`, `access-tested=false`, `rights-confirmed=false`, `approved=false`. Until the gates are evidenced, implementation preparation is fixture-only: do not call endpoints or persist real market responses.

## Yêu cầu market contract cần chốt

- Canonical instrument identity phải giữ venue, board/market type, native symbol, instrument class và lifecycle dates; không dùng ticker đơn lẻ làm identity.
- Giữ payload timestamp, timezone, resolution, observation/received time và publication/availability time riêng. Chuẩn hóa UTC nhưng lưu unit/original value theo policy.
- Tách regular board, auction/session, odd lot, derivative và bond nếu SSI feed trả về chúng; không nhập chung candle series trước khi semantics được hiểu.
- Giữ raw revisions, corrected/adjusted status và source version nếu được phép; backtest chỉ dùng dữ liệu khả dụng tại thời điểm tương ứng.
- Missing ranges/unsupported fields là partial/unavailable; không nội suy hoặc gán zero.
- Quote/trade stream không thay thế historical feed. Historical REST và live stream phải reconcile với rule về overlap, revisions, closed bars và reconnect gaps.

## Các nguồn khác

DNSE, news RSS/disclosures và Vnstock vẫn là nguồn khảo sát, không thuộc V1 market adapter đã chọn. News engine là workstream riêng; xem [News ingestion](../05-news-ingestion/README.md). Không dùng SDK license để suy ra quyền upstream data.
