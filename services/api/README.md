# Research Terminal fixture API

Scaffold read-only, chưa có auth/account, business API, database hay kết nối live. Dữ liệu chỉ đọc từ `data/fixtures/`; không cần secret, không load `.env.local`. API trả 503 nếu fixture thiếu, sai schema hoặc không synthetic.

Python 3.11–3.13; lock được resolve bằng uv 0.11.28. Từ repository root:

```powershell
$env:UV_CACHE_DIR = "$PWD/.cache/uv"
$env:UV_PROJECT_ENVIRONMENT = "$PWD/services/api/.venv-reset"
uv sync --project services/api --frozen --extra dev
uv run --project services/api --frozen uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000
```

Verify và export (terminal khác, cùng hai biến environment):

```powershell
uv run --project services/api --frozen --extra dev pytest services/api/tests
uv run --project services/api --frozen python services/api/scripts/export_openapi.py
```

Routes chỉ đọc: `GET /api/v1/health`, `GET /api/v1/market/instruments`, `GET /api/v1/market/candles?instrument_id=…&interval=…`, `GET /api/v1/news/articles?instrument_id=…` và `GET /api/v1/portfolio/holdings`. Danh mục server trả mảng rỗng vì holdings hiện lưu cục bộ trong trình duyệt. Schema ở `/openapi.json`, interactive docs ở `/docs`. Success envelope `{data, meta: {is_synthetic: true}}`; errors `{error: {code, message}, meta: {is_synthetic: true}}`. Health không chứng minh data source sẵn sàng.

Frontend gọi cùng origin qua Go Gateway/Vite proxy; API không bật cross-origin cookie/CORS. Bind loopback là mặc định local; deployment và provider selection thuộc phase sau.
