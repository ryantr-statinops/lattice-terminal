# Vision và phạm vi

**Trạng thái:** product target; prototype hiện có giao diện fixture, chưa có data production.

Research Terminal giúp retail trader người Việt đọc tin theo tài sản, đối chiếu phần động giá, theo dõi danh mục và kiểm tra giả thuyết bằng model đơn giản. Giá trị chính là research workflow có evidence, không phải lời hứa lợi nhuận hay tín hiệu giao dịch.

## Người dùng

- Retail trader intraday cần biết sự kiện mới, thời điểm nhận và bối cảnh giá/volume.
- Người giữ lệnh với ngày/tuần cần theo dõi exposure và news liên quan danh mục.
- Người học/nghiên cứu cần dùng baseline có thể tái lập, hiểu leakage và chi phí.

## MVP

Binance Spot BTCUSDT/ETHUSDT; candles 15m/1h/1d; UI tiếng Việt. News có provenance và event mapping; nguồn chỉ được dùng trong phạm vi quyền. Có account/workspace private, watchlist, live theo tab, portfolio manual/CSV và browser Model Lab. Base portfolio là USDT, không giữ USD/VND ngang giá.

## Ngoài MVP

Không real-order execution, không khóa sản, không margin/short/leverage/liquidation. Funding/OI là dữ liệu mở rộng, chưa là mục tiêu. Không arbitrary Python, training server, deep learning hay tuning không giới hạn. US equities, FX và VN equities giữ trong khảo sát, chưa hỗ trợ sản phẩm.

## Current versus target

Prototype hiện có market/news fixture views, watchlist, chart, portfolio localStorage/CSV và form Model Lab mock trên React/Vite + FastAPI + Go Gateway. Binance WebSocket là opt-in và chỉ báo kết nối; không cập nhật chart. Feed/ingestion thật, auth, server-backed portfolio và Model Lab runtime chưa triển khai. Không lấy dataset cũ hay credential cũ làm bằng chứng cho sản phẩm mới. Public demo là workspace mẫu riêng, không công khai danh mục/experiment người dùng.
