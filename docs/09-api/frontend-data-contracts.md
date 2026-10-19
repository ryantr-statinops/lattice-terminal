# Frontend data contracts — prototype

**Trạng thái:** mô tả fixture API hiện có, không phải contract V1. V1 local API schema chưa được khóa; portfolio hiện là browser-side placeholder và news không thuộc MVP terminal đầu tiên.

## API client (`apps/web/src/lib/api.ts`)

- `apiFetch<T>(path, init?)`: fetch wrapper, returns `body.data` as T.
- Base URL from `VITE_API_BASE_URL` (empty → relative `/api` via Vite proxy → Go Gateway → FastAPI).
- Error handling: throw `Error` with server `error.message` if present, else `HTTP {status}`.
- Content-Type: `application/json`.

## Endpoints (OpenAPI 3.1.0, `packages/contracts/openapi.json`)

| Method | Path | Response | Notes |
|--------|------|----------|-------|
| GET | `/api/v1/health` | `HealthResponse` | service/mode synthetic marker |
| GET | `/api/v1/market/instruments` | `InstrumentsResponse` | list of Instrument |
| GET | `/api/v1/market/candles?instrument_id=&interval=` | `CandlesResponse` | filtered by instrument + interval; 404 if instrument unknown |
| GET | `/api/v1/news/articles?instrument_id=` | `ArticlesResponse` | synthetic fixture; news API V1 chưa định nghĩa |
| GET | `/api/v1/portfolio/holdings` | `HoldingsResponse` | empty placeholder; V1 portfolio API chưa định nghĩa |

## Envelope

Success: `{ data, meta: { is_synthetic: true } }`
Error: `{ error: { code, message }, meta: { is_synthetic: true } }`

## Loading states (TanStack Query)

| Query state | UI treatment |
|-------------|--------------|
| `isLoading` (no cached data) | Skeleton placeholders matching final layout |
| `isFetching` (background refetch) | Keep existing data; show subtle refresh hint |
| `isError` | Error summary + retry button; keep last good data if available |
| Empty `data` (array length 0) | Empty state with explanation + CTA |
| Stale (custom flag) | Muted styling + stale badge with valuation time |

## Error handling rules

- Never show raw server errors to users; map to friendly messages.
- Retry button calls `refetch()`.
- Network errors → "Không tải được dữ liệu. Thử lại."
- 404 → "Không tìm thấy."
- 422 → "Yêu cầu không hợp lệ."

## Synthetic marker

All fixture responses include `meta.is_synthetic: true`. UI must label fixture data as synthetic (badge "SYNTHETIC · FIXTURE ONLY"). Never present fixture data as current market.

## CSV import contract (client-side)

Header: `instrument_id,amount,avg_cost`. Validation:
- `instrument_id`: required, non-empty
- `amount`: positive number
- `avg_cost`: non-negative number

Preview table shows per-row OK/error. Confirm disabled if any row has error.
