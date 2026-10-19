# News intelligence và corrections

**Trạng thái:** mục tiêu, chưa có model chất lượng đã được đo.

## Deduplication

Giữ source article riêng và nhóm vào story cluster; không xóa provenance khi hai báo đưa cùng sự kiện. Exact dedup theo source/native ID hoặc canonical URL; content hash chỉ so sánh fields được phép lưu. Near-duplicate dùng normalized title/body được phép, time window và entity overlap; ghi algorithm version/confidence. Chưa dùng similarity threshold production khi chưa gắn nhãn và đánh giá.

Story cluster có earliest observed evidence, member revisions và merge/split history. Một bài được syndicate nhiều lần không là nhiều nguồn độc lập; novelty/count features phải phân biệt article count và independent-source count. Không tự nhận diện độc lập từ domain khác nhau.

## Asset/entity/event mapping

Map tên doanh nghiệp, instrument và tổ chức theo context; ambiguous names/tickers vào unresolved thay vì đoán. Candidate event taxonomy gồm regulatory, corporate action, earnings, market infrastructure, macro và other; chốt taxonomy theo use case và labeled evidence. Entity link, event type và sentiment nếu có đều giữ extractor version, evidence reference khi được phép và confidence.

Event time được nguồn nói đến, article publication time và system availability là ba trường khác nhau. Sentiment của bài không đồng nghĩa expected return; không hiển thị như recommendation mua/bán. Human-labeled audit set phải có positive/negative/ambiguous cases và nguồn đa dạng; metrics cần per-class/entity reports.

## Corrections và serving

Tin thay title/body/time tạo ArticleRevision mới. Serving mặc định hiển thị bản hiện hành và nhãn cập nhật/rút; experiment snapshot giữ revision cụ thể và availability cutoff. Mapping sửa sau không được lén sửa feature quá khứ như đã biết từ trước; dataset version mới phản ánh thay đổi.

News cards có source, published time khi biết, first_seen/update indicator và link gốc. Không có quyền excerpt thì chỉ fields được phép; unknown timestamp/coverage phải hiện rõ. Summary hoặc translation do model là derivative processing cần source-policy approval, không mặc định được cấp bởi quyền RSS.

Acceptance scenarios: cùng URL sửa nội dung; hai nguồn syndicate; ambiguous company/instrument name; published_at thiếu timezone; source rút tin; entity mapping đổi sau snapshot; correction đến trễ; near-duplicate merge nhầm. Đo precision/recall trên tập nhãn phù hợp trước khi phục vụ research feature hoặc tích hợp terminal.
