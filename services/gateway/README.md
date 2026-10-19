# Go Gateway scaffold

Trạng thái P01: HTTP proxy local, chưa có auth, database hoặc exchange integration. P02 sẽ bổ sung các boundary đã mô tả trong docs.

Yêu cầu Go 1.27.2. Từ repository root:

```powershell
go -C services/gateway run ./cmd/gateway
go -C services/gateway test ./...
```

Mặc định lắng nghe `127.0.0.1:8080`; `KESTREL_GATEWAY_ADDR` đổi bind address, `KESTREL_API_BASE_URL` đổi API origin (mặc định `http://127.0.0.1:8000`). Không đặt credentials/query/path trong API origin.

`GET /healthz` trả JSON `status=ok`, `service=gateway`, `mode=scaffold`. `/api/*` giữ nguyên path/query/body khi chuyển tới FastAPI. Các path khác trả 404. Giới hạn body 1 MiB, request upstream 10 giây; upstream lỗi trả 502 an toàn. Request ID hợp lệ được giữ, giá trị khác được thay bằng ID mới. Health chỉ phản ánh process gateway, không xác nhận upstream sẵn sàng.

Vite dev proxy chuyển `/api` tới gateway; không cần wildcard CORS. Không public scaffold trước khi hoàn thiện auth/rate limits P02.
