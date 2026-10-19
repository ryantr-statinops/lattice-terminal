# Fixture API contracts

`openapi.json` được sinh từ FastAPI scaffold, chỉ mô tả API fixture read-only. Đây chưa phải API nghiệp vụ Kestrel Terminal, auth hoặc provider contract.

Nguồn schema: `services/api/app/schemas.py`. Dữ liệu authoritative: `data/fixtures/news.json` và `market.json`; mọi response thành công có `meta.is_synthetic=true`. API từ chối fixture thiếu, sai schema hoặc không synthetic với 503, không fallback sang dữ liệu thật.

Sinh lại từ repository root:

```powershell
$env:UV_CACHE_DIR = "$PWD/.cache/uv"
$env:UV_PROJECT_ENVIRONMENT = "$PWD/services/api/.venv-reset"
uv run --project services/api --frozen python services/api/scripts/export_openapi.py
git diff --exit-code -- packages/contracts/openapi.json
```

Frontend gọi cùng origin qua Gateway/proxy. Không có wildcard CORS với cookie hoặc kết nối cloud trong scaffold.
