/**
 * Worker adapter interface for Model Lab.
 * Actual Web Worker + Pyodide integration is deferred (needs browser feasibility).
 * This adapter defines the contract and a no-op fallback.
 */

export interface WorkerMessage {
  type: "run" | "cancel" | "progress" | "result" | "error";
  run_id: string;
  payload?: unknown;
}

export interface WorkerAdapter {
  run(config: unknown): Promise<unknown>;
  cancel(runId: string): void;
  terminate(): void;
}

/**
 * Placeholder adapter used until the worker runtime is implemented.
 * Returned metrics are fixed mock values and do not depend on the config.
 */
export function createNoopAdapter(): WorkerAdapter {
  return {
    async run(config: unknown) {
      void config;
      const runId = `run-${Date.now()}`;
      await new Promise((r) => setTimeout(r, 300));
      return {
        run_id: runId,
        status: "simulated",
        source: "mock",
        out_of_sample_windows: 5,
        baseline: 0.52,
        net_cost: 0.001,
        max_drawdown: 0.08,
      };
    },
    cancel() {
      // no-op
    },
    terminate() {
      // no-op
    },
  };
}
