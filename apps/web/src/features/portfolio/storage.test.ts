import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { usePortfolio } from "./storage";

const key = "rt:portfolio";

beforeEach(() => localStorage.clear());
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("portfolio persistence", () => {
  it("keeps valid stored rows and warns without rewriting invalid rows on load", () => {
    localStorage.setItem(key, JSON.stringify({
      updatedAt: "2026-10-17T10:00:00Z",
      holdings: [
        { id: "good", instrument_id: "binance:spot:BTCUSDT", amount: "1.2", avg_cost: "0" },
        { id: "bad", instrument_id: "binance:spot:SOLUSDT", amount: "1", avg_cost: "2" },
      ],
    }));
    const setItem = vi.spyOn(Storage.prototype, "setItem");

    const { result } = renderHook(() => usePortfolio());

    expect(result.current.state.holdings).toEqual([
      { id: "good", instrument_id: "binance:spot:BTCUSDT", amount: "1.2", avg_cost: "0" },
    ]);
    expect(result.current.storageWarning).toMatch(/bỏ qua 1 holding/);
    expect(setItem).not.toHaveBeenCalled();
  });

  it("preserves malformed storage until the user makes a valid change", () => {
    localStorage.setItem(key, "{");
    const { result } = renderHook(() => usePortfolio());
    expect(result.current.storageWarning).toMatch(/dữ liệu gốc/);
    expect(localStorage.getItem(key)).toBe("{");

    act(() => {
      result.current.addMany([
        { instrument_id: "binance:spot:BTCUSDT", amount: "1", avg_cost: "2" },
      ]);
    });

    expect(result.current.state.holdings).toHaveLength(1);
    expect(result.current.storageWarning).toBeNull();
    expect(JSON.parse(localStorage.getItem(key) ?? "{}").holdings).toHaveLength(1);
  });

  it("keeps session changes and reports storage write failures", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("quota exceeded", "QuotaExceededError");
    });
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      result.current.addMany([
        { instrument_id: "binance:spot:ETHUSDT", amount: "0.5", avg_cost: "3000" },
      ]);
    });

    expect(result.current.state.holdings).toHaveLength(1);
    expect(result.current.storageWarning).toMatch(/Không lưu được/);
  });

  it("rejects an invalid batch atomically", () => {
    const { result } = renderHook(() => usePortfolio());

    act(() => {
      expect(result.current.addMany([
        { instrument_id: "binance:spot:BTCUSDT", amount: "1", avg_cost: "2" },
        { instrument_id: "binance:spot:ETHUSDT", amount: "12abc", avg_cost: "2" },
      ])).toBe(false);
    });

    expect(result.current.state.holdings).toHaveLength(0);
    expect(result.current.validationError).toMatch(/Số lượng/);
  });
});
