import { useState } from "react";
import type { Holding } from "./types";
import { validateHoldingDraft } from "./validation";

const INSTRUMENTS = [
  { id: "binance:spot:BTCUSDT", label: "BTC/USDT" },
  { id: "binance:spot:ETHUSDT", label: "ETH/USDT" },
];

interface Props {
  onAdd: (holding: Omit<Holding, "id">) => void;
}

export function ManualEntryForm({ onAdd }: Props) {
  const [instrumentId, setInstrumentId] = useState(INSTRUMENTS[0].id);
  const [amount, setAmount] = useState("");
  const [avgCost, setAvgCost] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const result = validateHoldingDraft({ instrument_id: instrumentId, amount, avg_cost: avgCost });
    if (!result.valid) {
      setError(result.error);
      return;
    }
    setError(null);
    onAdd(result.holding);
    setAmount("");
    setAvgCost("");
  }

  return (
    <form onSubmit={handleSubmit} className="panel grid gap-3 sm:grid-cols-4">
      <label className="grid gap-1 text-sm">
        <span className="text-muted-foreground">Tài sản</span>
        <select
          value={instrumentId}
          onChange={(e) => setInstrumentId(e.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-2"
        >
          {INSTRUMENTS.map((i) => (
            <option key={i.id} value={i.id}>
              {i.label}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-1 text-sm">
        <span className="text-muted-foreground">Số lượng</span>
        <input
          type="text"
          inputMode="decimal"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.00"
          className="rounded-lg border border-border bg-background px-3 py-2 font-mono"
        />
      </label>
      <label className="grid gap-1 text-sm">
        <span className="text-muted-foreground">Giá vốn (USDT)</span>
        <input
          type="text"
          inputMode="decimal"
          value={avgCost}
          onChange={(e) => setAvgCost(e.target.value)}
          placeholder="0.00"
          className="rounded-lg border border-border bg-background px-3 py-2 font-mono"
        />
      </label>
      <div className="flex items-end">
        <button
          type="submit"
          className="w-full rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground"
        >
          Thêm
        </button>
      </div>
      {error && <p className="sm:col-span-4 text-sm text-destructive">{error}</p>}
    </form>
  );
}
