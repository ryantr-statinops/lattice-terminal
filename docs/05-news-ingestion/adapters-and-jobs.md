# Source adapters và jobs

**Trạng thái:** design proposal cho news engine độc lập; chưa có nguồn được phê duyệt hay crawl production.

## Source discovery

Chọn một nhóm nhỏ nguồn quốc tế và Việt Nam theo use case rõ ràng. Mỗi candidate cần owner, URL/docs/terms, permitted fields, access method, stable IDs, timestamps, pagination/update semantics, rate evidence, retention và approved purpose. Nguồn chưa được duyệt không được tính là coverage sản phẩm; danh sách candidate không đại diện toàn thị trường.

Ưu tiên API/RSS do nguồn công bố. Không dùng login cá nhân để scrape, không vượt paywall/CAPTCHA/region và không xoay IP để tránh giới hạn. robots.txt là thông tin vận hành bổ sung, không thay quyền nội dung. Nếu chỉ metadata được phép, adapter không fetch full article text hoặc images.

## Adapter contract

Input: source config version, permitted scope, cursor/checkpoint, optional time range và deadline. Output: source_item_id/canonical URL, observed_at UTC, published_at/source_updated_at nullable, allowed fields, raw hash/ref when retention permits, parse status, next cursor, rate/deletion hints. Jobs phải phân biệt fetch success và parse completeness; raw text không được lưu nếu policy chưa cho phép.

URL canonicalization chỉ bỏ tracking parameters đã biết; không xóa mọi query vì có thể làm mất identity. Redirect URL và original URL lưu riêng khi allowed. HTML sanitize trước display; fetched URLs phải allowlist và tránh SSRF/internal IP. Không log auth headers hoặc signed URLs.

## Job lifecycle

Trigger → source-policy check → fetch theo quota → persist only allowed evidence → parse/version → dedup/map → quality gate → publish permitted output → checkpoint. Checkpoint chỉ tiến sau durable write; replay không tạo article trùng. Job có source-level lock và timeout để ngăn overlap. Scheduler/host placement remains open until the standalone engine's operating model is decided.

Respect response rate hints; retry lỗi tạm với bounded backoff. 401/403/terms change disable source and surface status; không retry vô hạn. 404/rút tin không tự xóa research history: tạo trạng thái theo source policy. Numeric poll interval/quota/batch size chỉ chốt bằng evidence, không suy từ RSS tồn tại.

Backfill và incremental là hai mode riêng. Backfill giữ first_seen là lúc thu thực tế và research eligibility riêng; không tự biến published_at thành available_at. Trong outage, ghi gap window; lần chạy sau reconcile overlap để nhận tin sửa/rút.

Exit gate: source policy approved theo fields/purpose, adapter fixtures, bounded access test ở runner region, replay/cursor scenarios, revision handling và coverage report. Chưa đạt thì chỉ dùng synthetic/demo source có nhãn.
