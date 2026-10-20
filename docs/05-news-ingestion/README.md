# News engine

**Trạng thái:** workstream độc lập trong định hướng sản phẩm, dành cho tin tức quốc tế và Việt Nam. Engine chưa được triển khai; news fixture prototype cũ đã bị thay thế, hiện không có route news. Nó không thuộc market/portfolio MVP và chỉ tích hợp vào Kestrel Terminal ở phase sau.

Engine dự kiến khám phá, chuẩn hóa, khử trùng lặp, theo dõi corrections và liên kết evidence được phép với instruments/events Việt Nam. Trước implementation cần chốt source inventory, rights gates, operating model, retention, fetch constraints và output contract riêng. Không suy ra quyền lưu full text, dịch, xử lý bằng ML hoặc phân phối lại chỉ vì trang/feed truy cập được.

Current design references:

1. [Adapters and ingestion lifecycle](adapters-and-jobs.md).
2. [Deduplication, entities, events and corrections](intelligence-and-corrections.md).

Các trang sau là design proposal cho workstream độc lập, không phải implementation instructions đã duyệt. Engine phải giữ provenance, publication/first-seen/correction times, source policy và partial/unavailable status. Contract tích hợp tương lai không được làm mất các trường này. See [source register](../03-market-research/source-register.md).
