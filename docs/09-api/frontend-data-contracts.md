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

## Error handling (current prototype)

- `apiFetch` throws an `Error` containing the server's `error.message`, or `HTTP {status}` when the response has no message.
- The current pages render generic feature-specific text rather than mapping HTTP status codes: market instruments → "Không tải được danh sách tài sản."; candles → "Không tải được dữ liệu nến."; news → "Không tải được bài tin.".
- Retry buttons call TanStack Query `refetch()`.
- There is no implemented network/404/422-specific localized mapping. A V1 error taxonomy and user-facing status mapping remain to be specified; the wrapper's exception text is not itself that UX contract.

## Synthetic marker

All fixture responses include `meta.is_synthetic: true`. UI must label fixture data as synthetic (badge "SYNTHETIC · FIXTURE ONLY"). Never present fixture data as current market.

## CSV import contract (client-side)

Required header names: `instrument_id`, `amount`, `avg_cost`. Current parser behavior:
- Header names are case-insensitive and may be in any order. Duplicate names are rejected. Other columns are allowed, but every non-empty data row must have the same number of fields as the header.
- Quoted CSV fields and CRLF line endings are handled; a leading UTF-8 BOM and empty rows are ignored.
- The three required values must be strings. Numeric fields are trimmed unsigned decimal strings: digits with an optional fractional part, or a leading decimal point followed by digits. Exponent notation, decimal commas, signs, empty values and non-finite values are rejected. `amount` must be greater than zero; `avg_cost` may be zero.
- `instrument_id` must match one of the two hard-coded fixture identifiers accepted by the current validator. This prototype allowlist does not establish support for arbitrary instruments or Vietnamese-market imports.
- Preview shows row-level errors. Import is disabled if parsing failed, if any row has an error, or if there are no valid rows.

These restrictions document current browser-side prototype behavior; they do not define a V1 portfolio import contract.
