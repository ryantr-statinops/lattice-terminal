export type Interval = "15m" | "1h" | "1d";

export interface ExperimentConfig {
  instrument_id: string;
  interval: Interval;
  features: string[];
  target: string;
  horizon: number;
  model: "ridge" | "logistic";
  split: number; // train fraction 0..1
  costs_bps: number;
}

export interface ExperimentResult {
  run_id: string;
  status: "simulated";
  source: "mock";
  out_of_sample_windows: number;
  baseline: number | null;
  net_cost: number | null;
  max_drawdown: number | null;
  error?: string;
}

export const DEFAULT_CONFIG: ExperimentConfig = {
  instrument_id: "binance:spot:BTCUSDT",
  interval: "1h",
  features: ["returns_1", "returns_5"],
  target: "direction",
  horizon: 1,
  model: "ridge",
  split: 0.8,
  costs_bps: 5,
};
