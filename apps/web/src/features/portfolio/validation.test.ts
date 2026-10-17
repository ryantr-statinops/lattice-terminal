import { describe, expect, it } from "vitest";
import { parseFiniteDecimal, validateHoldingDraft } from "./validation";

const btcHolding = {
  instrument_id: "binance:spot:BTCUSDT",
  amount: "0.125",
  avg_cost: "65000.50",
};

describe("portfolio input validation", () => {
  it.each(["", " ", "0", "-1", "+1", "1e2", "12abc", "NaN", "Infinity", "1,5", "9".repeat(400)])(
    "rejects invalid positive decimals: %s",
    (amount) => {
      expect(validateHoldingDraft({ ...btcHolding, amount }).valid).toBe(false);
    },
  );

  it.each(["0", "0.00", ".5", "12.50", "01"])("accepts finite decimal %s", (value) => {
    expect(parseFiniteDecimal(value)).not.toBeNull();
  });

  it("rejects unsupported assets and negative or malformed cost basis", () => {
    expect(validateHoldingDraft({ ...btcHolding, instrument_id: "solana:spot:SOLUSDT" }).valid).toBe(false);
    expect(validateHoldingDraft({ ...btcHolding, avg_cost: "-1" }).valid).toBe(false);
    expect(validateHoldingDraft({ ...btcHolding, avg_cost: "1.2oops" }).valid).toBe(false);
  });

  it("trims valid decimal strings without changing their precision", () => {
    expect(validateHoldingDraft({ ...btcHolding, amount: " 0.00100 " })).toEqual({
      valid: true,
      holding: { ...btcHolding, amount: "0.00100" },
    });
  });
});
