import { describe, expect, it } from "vitest";
import type { Candle } from "../market/api";
import { calculatePortfolioValuation, latestClosedQuote } from "./valuation";
import type { Holding } from "./types";

const holdings: Holding[] = [
  { id: "btc", instrument_id: "btc", amount: "2", avg_cost: "100" },
  { id: "eth", instrument_id: "eth", amount: "3", avg_cost: "50" },
];

describe("portfolio valuation", () => {
  it("calculates complete totals and row P&L", () => {
    const result = calculatePortfolioValuation(holdings, {
      btc: { price: 120, time: "2026-10-17T10:00:00Z" },
      eth: { price: 40, time: "2026-10-17T09:00:00Z" },
    });

    expect(result.cost).toBe(350);
    expect(result.value).toBe(360);
    expect(result.pnl).toBe(10);
    expect(result.pnlPct).toBeCloseTo((10 / 350) * 100);
    expect(result.rows.map((row) => row.pnl)).toEqual([40, -30]);
    expect(result.isComplete).toBe(true);
  });

  it("keeps invested cost but hides totals when any holding lacks a price", () => {
    const result = calculatePortfolioValuation(holdings, {
      btc: { price: 120, time: "2026-10-17T10:00:00Z" },
      eth: null,
    });

    expect(result.cost).toBe(350);
    expect(result.rows[0].pnl).toBe(40);
    expect(result.rows[1].value).toBeNull();
    expect(result.value).toBeNull();
    expect(result.pnl).toBeNull();
    expect(result.pnlPct).toBeNull();
    expect(result.isComplete).toBe(false);
  });

  it("hides all portfolio value totals when no price is available", () => {
    const result = calculatePortfolioValuation(holdings, { btc: null, eth: null });

    expect(result.cost).toBe(350);
    expect(result.rows.map((row) => row.pnl)).toEqual([null, null]);
    expect(result.value).toBeNull();
    expect(result.pnl).toBeNull();
    expect(result.isComplete).toBe(false);
  });

  it("returns zero totals for an empty portfolio", () => {
    expect(calculatePortfolioValuation([], {}).value).toBe(0);
    expect(calculatePortfolioValuation([], {}).pnl).toBe(0);
    expect(calculatePortfolioValuation([], {}).isComplete).toBe(true);
  });

  it("leaves return percentage blank when cost basis is zero", () => {
    const result = calculatePortfolioValuation(
      [{ id: "cash", instrument_id: "btc", amount: "1", avg_cost: "0" }],
      { btc: { price: 10, time: "2026-10-17T10:00:00Z" } },
    );

    expect(result.rows[0].pnl).toBe(10);
    expect(result.rows[0].pnlPct).toBeNull();
    expect(result.pnlPct).toBeNull();
  });
});

describe("latest closed quote", () => {
  const candle = (open_time: string, close_time: string, close: string, is_closed = true): Candle => ({
    instrument_id: "btc",
    interval: "1h",
    open_time,
    close_time,
    is_closed,
    open: close,
    high: close,
    low: close,
    close,
    volume: "1",
  });

  it("selects the newest closed candle by timestamp, independent of array order", () => {
    expect(
      latestClosedQuote([
        candle("2026-10-17T10:00:00Z", "2026-10-17T10:59:00Z", "10"),
        candle("2026-10-17T08:00:00Z", "2026-10-17T08:59:00Z", "8"),
        candle("2026-10-17T11:00:00Z", "2026-10-17T11:59:00Z", "99", false),
      ]),
    ).toEqual({ price: 10, time: "2026-10-17T10:59:00Z" });
  });

  it("returns no quote when candles are absent, open, or invalid", () => {
    expect(latestClosedQuote(undefined)).toBeNull();
    expect(latestClosedQuote([candle("now", "now", "10")])).toBeNull();
    expect(latestClosedQuote([candle("2026-10-17T09:00:00Z", "2026-10-17T09:59:00Z", "bad")])).toBeNull();
  });
});
