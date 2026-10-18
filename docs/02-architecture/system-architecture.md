# System architecture

**Trạng thái:** target local-first được chốt ở cấp product; process boundaries, local persistence và password protection vẫn đang thiết kế. Current fixture stack: React/Vite, Go Gateway, FastAPI và CLI.

| Thành phần | Trách nhiệm mục tiêu |
|---|---|
| React/Vite web | UI tại localhost, market/portfolio/research screens; không giữ SSI secret |
| Local API process | Chỉ loopback; cấp normalized local data và portfolio/simulation operations |
| SSI FC Data adapter | Dùng ConsumerID/Secret từ local secret boundary; REST history/reference và streaming theo entitlement. Không gọi FastConnect Trading |
| Local data store | Snapshot/config/portfolio/backtest/paper history trên máy người dùng, với version/provenance và recovery policy |
| Simulator | Backtest trên historical data và paper live trên reconciled live feed; không có broker order route |
| Separate news engine | Nguồn quốc tế + Việt Nam, xây độc lập rồi mới tích hợp vào app |

## Luồng mục tiêu

~~~text
User starts local project
Browser (localhost) -> loopback API -> local normalized snapshots / portfolio / simulator
                                      -> SSI FastConnect Data (only after access + rights gates)
                                      -> local stream reconciliation -> paper-trading simulator
Separate news engine -> later, reviewed integration boundary
~~~

Các process chỉ bind vào loopback trừ khi có ADR và bảo vệ phù hợp. Browser không nhận ConsumerID/ConsumerSecret và không tự kết nối SSI upstream. Local API chỉ expose fields cần cho app; log không chứa secret hoặc raw payload không được phép lưu.

## Ranh giới và failure

- SSI REST/historical là nguồn lịch sử; stream dùng để cập nhật realtime/reconcile. Disconnect không xóa history, và stream không là nguồn duy nhất.
- Rights/entitlement/access/quality gate riêng theo endpoint/feed. Không thay SSI bằng source khác âm thầm; không phát hành data fixture như data thật.
- Provider auth error, policy/terms block, quota, session/market closure, stale feed và partial history có state riêng. Dừng request boundedly, không retry vô hạn.
- Local storage corruption, interrupted write hoặc invalid secret không làm publish partial snapshot; cần recovery/export/delete contract.
- Backtest chỉ nhận closed bars theo explicit availability rules. Paper live đánh dấu simulated fills; quote/trade stream không chứng minh fill thật.
- Không có cloud sync/remote user account. Password-only local login là requested UX; threat model, encryption-at-rest, account recovery và whether lock is per profile or per app instance vẫn cần quyết định.
- News engine không chặn market MVP và không được dùng content/fields ngoài rights của từng source.

## Implementation status

SSI API/streaming, local secret store, local persistent store, password login, market-data serving, backtest, paper simulator và news integration chưa có. Detailed cloud/multi-account/Binance designs elsewhere describe earlier direction and are superseded until individually revised.
