import type { Candle } from "../market/api";
import type { Holding } from "./types";

export interface PriceQuote {
  price: number;
  time: string;
}

export interface ValuedHolding {
  holding: Holding;
  price: number | null;
  value: number | null;
  cost: number;
  pnl: number | null;
  pnlPct: number | null;
}

export interface PortfolioValuation {
  rows: ValuedHolding[];
  cost: number;
  value: number | null;
  pnl: number | null;
  pnlPct: number | null;
  isComplete: boolean;
}

export function latestClosedQuote(candles: readonly Candle[] | undefined): PriceQuote | null {
  if (!candles) return null;

  const latest = candles
    .filter((candle) => candle.is_closed && Number.isFinite(Date.parse(candle.close_time)))
    .map((candle) => ({
      price: Number(candle.close),
      time: candle.close_time,
      timestamp: Date.parse(candle.close_time),
    }))
    .filter((quote) => Number.isFinite(quote.price))
    .sort((a, b) => a.timestamp - b.timestamp)
    .at(-1);

  return latest ? { price: latest.price, time: latest.time } : null;
}

export function calculatePortfolioValuation(
  holdings: readonly Holding[],
  prices: Readonly<Record<string, PriceQuote | null>>,
): PortfolioValuation {
  const rows = holdings.map((holding): ValuedHolding => {
    const amount = Number(holding.amount);
    const averageCost = Number(holding.avg_cost);
    const hasValidCost = Number.isFinite(amount) && amount >= 0 && Number.isFinite(averageCost) && averageCost >= 0;
    const cost = hasValidCost ? amount * averageCost : 0;
    const quote = prices[holding.instrument_id] ?? null;
    const price = quote?.price ?? null;
    const value = price !== null && Number.isFinite(amount) ? amount * price : null;
    const pnl = value !== null ? value - cost : null;
    const pnlPct = cost > 0 && pnl !== null ? (pnl / cost) * 100 : null;
    return { holding, price, value, cost, pnl, pnlPct };
  });

  const cost = rows.reduce((sum, row) => sum + row.cost, 0);
  const isComplete = rows.every(
    (row) => row.price !== null && row.value !== null && Number.isFinite(row.value),
  );
  const value = isComplete ? rows.reduce((sum, row) => sum + (row.value ?? 0), 0) : null;
  const pnl = value !== null ? value - cost : null;
  const pnlPct = cost > 0 && pnl !== null ? (pnl / cost) * 100 : null;

  return { rows, cost, value, pnl, pnlPct, isComplete };
}
