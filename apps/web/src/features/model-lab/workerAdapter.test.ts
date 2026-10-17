import { describe, expect, it } from "vitest";
import { createNoopAdapter } from "./workerAdapter";

describe("placeholder experiment adapter", () => {
  it("returns mock metrics independent of the submitted config", async () => {
    const adapter = createNoopAdapter();
    const result = await adapter.run({ instrument_id: "binance:spot:ETHUSDT", costs_bps: 999 }) as {
      status: string;
      source: string;
      baseline: number;
      max_drawdown: number;
      client_computed?: boolean;
      config?: unknown;
    };

    expect(result.status).toBe("simulated");
    expect(result.source).toBe("mock");
    expect(result.baseline).toBe(0.52);
    expect(result.max_drawdown).toBe(0.08);
    expect(result.client_computed).toBeUndefined();
    expect(result.config).toBeUndefined();
  });
});
