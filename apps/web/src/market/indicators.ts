import type {Candle} from '../api';

export function calculateSMA(candles: Candle[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  let sum = 0;
  for (let i = 0; i < candles.length; i++) {
    const val = Number(candles[i].close);
    sum += val;
    if (i >= period) {
      sum -= Number(candles[i - period].close);
    }
    if (i >= period - 1) {
      result.push(Number((sum / period).toFixed(2)));
    } else {
      result.push(null);
    }
  }
  return result;
}

export type IndicatorConfig = {
  ma20: boolean;
  ma50: boolean;
  volume: boolean;
};
