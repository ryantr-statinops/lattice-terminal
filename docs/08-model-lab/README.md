# Model Lab — Nghiên Cứu Mô Hình Định Lượng

**Trạng thái:** ngoài MVP đầu tiên; chỉ xem xét ở phase sau, chưa cam kết lịch V2.
Tài liệu kiến trúc cũ thiết kế cho nền tảng hosted multi-tenant đã được lưu trữ tại [`docs/_archive/model-lab-legacy/experiment-lifecycle.md`](../_archive/model-lab-legacy/experiment-lifecycle.md).

---

## 1. Định Hướng Hoãn Ngoài Phạm Vi V1 (Scope Decision)

Trong giai đoạn V1, mục tiêu cốt lõi của **Kestrel Terminal** là hoàn thiện một **Local Bloomberg Terminal** chuẩn xác cho TTCK Việt Nam, tập trung vào:
- Market/history/live data trong đúng SSI entitlement và approved field/feed scope; sổ lệnh/depth không được coi là đã cấp quyền hoặc đã triển khai.
- Biểu đồ kỹ thuật nến và khối lượng.
- Sổ cái quản lý danh mục (Portfolio Ledger).
- Portfolio backtest và paper simulator theo bộ quy tắc có ngày hiệu lực; settlement T+2 và thời điểm khả dụng được phân biệt trong [market rules](../07-portfolio/vn-market-rules.md).

Các tính năng huấn luyện mô hình học máy phức tạp, tự động tối ưu hóa tham số (Hyperparameter optimization), WebAssembly/Python in-browser training, và quản lý thử nghiệm quy mô lớn thuộc phân hệ **Model Lab** được **tạm hoãn và sẽ xem xét trong phiên bản V2** sau khi hệ thống market data và backtest V1 đã hoạt động ổn định.
