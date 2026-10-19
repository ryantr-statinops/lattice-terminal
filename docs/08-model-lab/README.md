# Model Lab — Nghiên Cứu Mô Hình Định Lượng

**Trạng thái:** Hoãn lại ngoài phạm vi V1 (Deferred to V2).  
Tài liệu kiến trúc cũ thiết kế cho nền tảng hosted multi-tenant đã được lưu trữ tại [`docs/_archive/model-lab-legacy/experiment-lifecycle.md`](../_archive/model-lab-legacy/experiment-lifecycle.md).

---

## 1. Định Hướng Hoãn Ngoài Phạm Vi V1 (Scope Decision)

Trong giai đoạn V1, mục tiêu cốt lõi của **Research Terminal** là hoàn thiện một **Local Bloomberg Terminal** chuẩn xác cho TTCK Việt Nam, tập trung vào:
- Bảng giá & sổ lệnh thời gian thực từ SSI FastConnect Data.
- Biểu đồ kỹ thuật nến và khối lượng.
- Sổ cái quản lý danh mục (Portfolio Ledger).
- Động cơ kiểm thử chiến lược giao dịch (Backtest Engine) và Giả lập giao dịch thời gian thực (Paper Trading Simulator) bám sát các quy tắc thị trường Việt Nam (ATO/ATC, T+2.5, bước giá, thuế phí).

Các tính năng huấn luyện mô hình học máy phức tạp, tự động tối ưu hóa tham số (Hyperparameter optimization), WebAssembly/Python in-browser training, và quản lý thử nghiệm quy mô lớn thuộc phân hệ **Model Lab** được **tạm hoãn và sẽ xem xét trong phiên bản V2** sau khi hệ thống market data và backtest V1 đã hoạt động ổn định.
