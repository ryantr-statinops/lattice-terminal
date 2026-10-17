import type { Holding } from "./types";

export type HoldingDraft = Omit<Holding, "id">;

const SUPPORTED_INSTRUMENTS = new Set([
  "binance:spot:BTCUSDT",
  "binance:spot:ETHUSDT",
]);
const DECIMAL_PATTERN = /^(?:\d+(?:\.\d+)?|\.\d+)$/;

export function parseFiniteDecimal(value: string): number | null {
  const normalized = value.trim();
  if (!DECIMAL_PATTERN.test(normalized)) return null;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

export function validateHoldingDraft(value: unknown):
  | { valid: true; holding: HoldingDraft }
  | { valid: false; error: string } {
  if (!value || typeof value !== "object") {
    return { valid: false, error: "Dữ liệu holding không hợp lệ" };
  }

  const row = value as Record<string, unknown>;
  if (typeof row.instrument_id !== "string" || !SUPPORTED_INSTRUMENTS.has(row.instrument_id)) {
    return { valid: false, error: "Tài sản chỉ hỗ trợ BTC/USDT hoặc ETH/USDT" };
  }
  if (typeof row.amount !== "string") {
    return { valid: false, error: "Số lượng không hợp lệ" };
  }
  const amount = parseFiniteDecimal(row.amount);
  if (amount === null || amount <= 0) {
    return { valid: false, error: "Số lượng phải là số thập phân dương hữu hạn" };
  }
  if (typeof row.avg_cost !== "string") {
    return { valid: false, error: "Giá vốn không hợp lệ" };
  }
  const avgCost = parseFiniteDecimal(row.avg_cost);
  if (avgCost === null || avgCost < 0) {
    return { valid: false, error: "Giá vốn phải là số thập phân không âm hữu hạn" };
  }

  return {
    valid: true,
    holding: {
      instrument_id: row.instrument_id,
      amount: row.amount.trim(),
      avg_cost: row.avg_cost.trim(),
    },
  };
}

export function validateStoredHolding(value: unknown):
  | { valid: true; holding: Holding }
  | { valid: false } {
  if (!value || typeof value !== "object") return { valid: false };
  const row = value as Record<string, unknown>;
  if (typeof row.id !== "string" || row.id.trim() === "") return { valid: false };
  const draft = validateHoldingDraft(row);
  return draft.valid ? { valid: true, holding: { id: row.id, ...draft.holding } } : { valid: false };
}
