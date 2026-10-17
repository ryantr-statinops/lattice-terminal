import { useMemo } from "react";
import Container from "../../components/layout/Container";
import { PartialBadge } from "../../components/ui/PartialBadge";
import { RefreshingIndicator } from "../../components/ui/RefreshingIndicator";
import { StaleBadge } from "../../components/ui/StaleBadge";
import { usePortfolio } from "./storage";
import { ManualEntryForm } from "./ManualEntryForm";
import { CsvImport } from "./CsvImport";
import { useCandles } from "../market/api";
import { calculatePortfolioValuation, latestClosedQuote } from "./valuation";
import { isDataOlderThan } from "../../lib/dataAge";

function instrumentLabel(id: string): string {
  if (id === "binance:spot:BTCUSDT") return "BTC/USDT";
  if (id === "binance:spot:ETHUSDT") return "ETH/USDT";
  return id;
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="panel text-center">
      <p className="text-muted-foreground">{message}</p>
    </div>
  );
}

export function PortfolioPage() {
  const { state, add, addMany, remove, clear, storageWarning, validationError } = usePortfolio();
  const btcCandles = useCandles("binance:spot:BTCUSDT", "1h");
  const ethCandles = useCandles("binance:spot:ETHUSDT", "1h");

  const prices: Record<string, ReturnType<typeof latestClosedQuote>> = {
    "binance:spot:BTCUSDT": latestClosedQuote(btcCandles.data),
    "binance:spot:ETHUSDT": latestClosedQuote(ethCandles.data),
  };

  const valuation = useMemo(
    () => calculatePortfolioValuation(state.holdings, prices),
    [state.holdings, btcCandles.data, ethCandles.data],
  );
  const rows = valuation.rows;
  const hasBtc = state.holdings.some((holding) => holding.instrument_id === "binance:spot:BTCUSDT");
  const hasEth = state.holdings.some((holding) => holding.instrument_id === "binance:spot:ETHUSDT");
  const isRefreshing =
    (hasBtc && btcCandles.data !== undefined && btcCandles.isFetching) ||
    (hasEth && ethCandles.data !== undefined && ethCandles.isFetching);
  const isLoadingPrices =
    (hasBtc && btcCandles.isLoading) || (hasEth && ethCandles.isLoading);
  const valuationTime = state.holdings
    .map((holding) => prices[holding.instrument_id as keyof typeof prices]?.time)
    .filter((time): time is string => time !== undefined)
    .sort((a, b) => Date.parse(a) - Date.parse(b))[0] ?? null;
  const isStale = isDataOlderThan(valuationTime, 2 * 60 * 60_000);

  return (
    <Container className="py-8 sm:py-12">
      <RefreshingIndicator visible={isRefreshing} />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Danh mục</h1>
        {state.holdings.length > 0 && (
          <button
            type="button"
            onClick={clear}
            className="rounded-lg border border-border px-3 py-1.5 text-sm text-foreground hover:bg-secondary"
          >
            Xóa tất cả
          </button>
        )}
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        Spot long/cash · base USDT · dữ liệu giá từ fixture
      </p>
      {(storageWarning || validationError) && (
        <p role="alert" className="mt-3 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm text-warning">
          {validationError ?? storageWarning}
        </p>
      )}

      <section className="mt-6">
        <ManualEntryForm onAdd={add} />
      </section>

      <section className="mt-6">
        <h2 className="mb-3 text-lg font-semibold">Nhập CSV</h2>
        <p className="mb-2 text-xs text-muted-foreground">
          Header: <code className="font-mono">instrument_id,amount,avg_cost</code>
        </p>
        <CsvImport onImport={addMany} />
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Holdings</h2>
        {state.holdings.length === 0 ? (
          <EmptyState message="Chưa có holding nào. Thêm thủ công hoặc import CSV." />
        ) : (
          <>
            {isLoadingPrices && (
              <p role="status" className="mb-3 text-sm text-muted-foreground">Đang tải giá fixture…</p>
            )}
            {((hasBtc && btcCandles.isError) || (hasEth && ethCandles.isError)) && (
              <div role="alert" className="mb-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">
                <p className="text-destructive">
                  {((hasBtc && btcCandles.data !== undefined) || (hasEth && ethCandles.data !== undefined))
                    ? "Không làm mới được giá; đang giữ dữ liệu đã tải."
                    : "Không tải được giá fixture cho một hoặc nhiều tài sản."}
                </p>
                <div className="mt-2 flex gap-2">
                  {hasBtc && btcCandles.isError && (
                    <button type="button" onClick={() => btcCandles.refetch()} className="underline">Thử lại BTC</button>
                  )}
                  {hasEth && ethCandles.isError && (
                    <button type="button" onClick={() => ethCandles.refetch()} className="underline">Thử lại ETH</button>
                  )}
                </div>
              </div>
            )}
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <caption className="sr-only">Bảng holdings và P&amp;L</caption>
                <thead className="bg-secondary text-left text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2">Tài sản</th>
                    <th className="px-3 py-2">Số lượng</th>
                    <th className="px-3 py-2">Giá vốn</th>
                    <th className="px-3 py-2">Giá hiện tại</th>
                    <th className="px-3 py-2">Giá trị</th>
                    <th className="px-3 py-2">P&L</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.holding.id} className="border-t border-border">
                      <td className="px-3 py-2 font-medium">{instrumentLabel(r.holding.instrument_id)}</td>
                      <td className="px-3 py-2 font-mono">{r.holding.amount}</td>
                      <td className="px-3 py-2 font-mono">{r.holding.avg_cost}</td>
                      <td className="px-3 py-2 font-mono">
                        {r.price !== null ? r.price.toFixed(2) : "—"}
                      </td>
                      <td className="px-3 py-2 font-mono">
                        {r.value !== null ? r.value.toFixed(2) : "—"}
                      </td>
                      <td
                        className={`px-3 py-2 font-mono ${
                          r.pnl === null
                            ? "text-muted-foreground"
                            : r.pnl >= 0
                              ? "text-primary"
                              : "text-destructive"
                        }`}
                      >
                        {r.pnl !== null
                          ? `${r.pnl >= 0 ? "+" : ""}${r.pnl.toFixed(2)} (${r.pnlPct !== null ? `${r.pnlPct.toFixed(2)}%` : "—"})`
                          : "—"}
                      </td>
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => remove(r.holding.id)}
                          className="text-xs text-muted-foreground hover:text-destructive"
                        >
                          Xóa
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 grid gap-2 rounded-lg border border-border bg-secondary/50 p-4 text-sm sm:grid-cols-4">
              <div>
                <p className="text-xs text-muted-foreground">Tổng giá vốn</p>
                <p className="font-mono font-semibold">{valuation.cost.toFixed(2)} USDT</p>
              </div>
              <div>
                  <p className="flex items-center gap-2 text-xs text-muted-foreground">
                    Tổng giá trị
                    {!valuation.isComplete && <PartialBadge reason="Thiếu giá cho một hoặc nhiều holdings." />}
                  </p>
                <p className="font-mono font-semibold">
                  {valuation.value !== null ? `${valuation.value.toFixed(2)} USDT` : "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">P&L</p>
                <p
                  className={`font-mono font-semibold ${
                    valuation.pnl === null
                      ? "text-muted-foreground"
                      : valuation.pnl >= 0
                        ? "text-primary"
                        : "text-destructive"
                  }`}
                >
                  {valuation.pnl !== null
                    ? `${valuation.pnl >= 0 ? "+" : ""}${valuation.pnl.toFixed(2)} (${valuation.pnlPct !== null ? `${valuation.pnlPct.toFixed(2)}%` : "—"})`
                    : "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Valuation time</p>
                <p className="font-mono text-xs">
                  {valuationTime
                    ? new Date(valuationTime).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })
                    : "—"}
                </p>
                {isStale && <div className="mt-1"><StaleBadge since={null} /></div>}
              </div>
            </div>

            <p className="mt-2 text-xs text-muted-foreground">
              P&L là client-computed từ nến đã đóng trong fixture, không phải giá live. Cashflow không được coi là trading profit.
            </p>
          </>
        )}
      </section>
    </Container>
  );
}
