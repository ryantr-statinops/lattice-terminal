import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Candle, Instrument } from "./api";
import { MarketPage } from "./MarketPage";

vi.mock("./CandleChart", () => ({
  CandleChart: ({ candles }: { candles: Candle[] }) => <div data-testid="candle-chart">{candles.length} candles</div>,
}));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("market refresh and source age", () => {
  it("keeps cached candles on refresh failure and bases stale status on candle time", async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: 0, gcTime: Infinity } },
    });
    const instruments: Instrument[] = [
      { instrument_id: "binance:spot:BTCUSDT", display_symbol: "BTC/USDT", base_asset: "BTC", quote_asset: "USDT" },
      { instrument_id: "binance:spot:ETHUSDT", display_symbol: "ETH/USDT", base_asset: "ETH", quote_asset: "USDT" },
    ];
    const candle: Candle = {
      instrument_id: "binance:spot:BTCUSDT",
      interval: "1h",
      open_time: "2026-10-15T00:00:00Z",
      close_time: "2026-10-15T01:00:00Z",
      is_closed: true,
      open: "100",
      high: "102",
      low: "99",
      close: "101",
      volume: "5",
    };
    client.setQueryData(["market", "instruments"], instruments);
    client.setQueryData(["market", "candles", "binance:spot:BTCUSDT", "1h"], [candle]);
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));

    render(
      <QueryClientProvider client={client}>
        <MarketPage />
      </QueryClientProvider>,
    );

    expect(await screen.findAllByRole("alert")).toHaveLength(2);
    expect(screen.getAllByText("BTC/USDT").length).toBeGreaterThan(0);
    expect(screen.getByTestId("candle-chart").textContent).toContain("1 candles");
    expect(screen.getByText(/Nến đã đóng mới nhất:/)).toBeTruthy();
    expect(screen.getByText(/Có thể đã cũ/)).toBeTruthy();
  });
});
