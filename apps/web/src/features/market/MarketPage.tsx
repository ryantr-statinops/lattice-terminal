import { useState } from "react";
import Container from "../../components/layout/Container";
import { RefreshingIndicator } from "../../components/ui/RefreshingIndicator";
import { StaleBadge } from "../../components/ui/StaleBadge";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { useInstruments, useCandles, type Instrument, type Candle } from "./api";
import { useWatchlist } from "./watchlist";
import { useBinanceStream } from "./stream";
import { CandleChart } from "./CandleChart";
import { isDataOlderThan } from "../../lib/dataAge";

const INTERVALS = ["15m", "1h", "1d"] as const;
type Interval = (typeof INTERVALS)[number];

function LoadingSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {[0, 1].map((i) => (
        <div key={i} className="panel animate-pulse">
          <div className="h-4 w-24 rounded bg-muted" />
          <div className="mt-4 h-8 w-32 rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="panel text-center">
      <p className="text-muted-foreground">{message}</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="panel text-center">
      <p className="text-destructive">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-3 rounded-lg border border-border px-3 py-2 text-sm text-foreground hover:bg-secondary"
      >
        Thử lại
      </button>
    </div>
  );
}

function latestClosedCandleTime(candles: Candle[] | undefined): string | null {
  return candles
    ?.filter((candle) => candle.is_closed && Number.isFinite(Date.parse(candle.close_time)))
    .reduce<string | null>((latest, candle) => {
      if (latest === null || Date.parse(candle.close_time) > Date.parse(latest)) return candle.close_time;
      return latest;
    }, null) ?? null;
}

function formatVi(dateStr: string): string {
  return new Date(dateStr).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
}

function CandleTable({ candles }: { candles: Candle[] }) {
  if (candles.length === 0) {
    return <EmptyState message="Không có nến cho khoảng thời gian này." />;
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <caption className="sr-only">Bảng nến OHLCV</caption>
        <thead className="bg-secondary text-left text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Mở</th>
            <th className="px-3 py-2">Cao</th>
            <th className="px-3 py-2">Thấp</th>
            <th className="px-3 py-2">Đóng</th>
            <th className="px-3 py-2">Khối lượng</th>
            <th className="px-3 py-2">Bắt đầu</th>
          </tr>
        </thead>
        <tbody>
          {candles.map((c) => (
            <tr key={c.open_time} className="border-t border-border">
              <td className="px-3 py-2 font-mono">{c.open}</td>
              <td className="px-3 py-2 font-mono text-primary">{c.high}</td>
              <td className="px-3 py-2 font-mono text-destructive">{c.low}</td>
              <td className="px-3 py-2 font-mono font-semibold">{c.close}</td>
              <td className="px-3 py-2 font-mono">{c.volume}</td>
              <td className="px-3 py-2 text-xs text-muted-foreground">
                {new Date(c.open_time).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function MarketPage() {
  const instrumentsQuery = useInstruments();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [interval, setInterval] = useState<Interval>("1h");
  const [watchlistOnly, setWatchlistOnly] = useState(false);
  const [streamEnabled, setStreamEnabled] = useState(false);
  const watchlist = useWatchlist();

  const effectiveId = selectedId ?? instrumentsQuery.data?.[0]?.instrument_id ?? null;
  const candlesQuery = useCandles(effectiveId, interval);
  const streamSymbol = effectiveId === "binance:spot:ETHUSDT" ? "ETHUSDT" : "BTCUSDT";
  const stream = useBinanceStream(streamSymbol, interval, streamEnabled);

  const instruments = watchlistOnly
    ? (instrumentsQuery.data ?? []).filter((i) => watchlist.has(i.instrument_id))
    : (instrumentsQuery.data ?? []);

  const isRefreshing =
    (instrumentsQuery.data !== undefined && instrumentsQuery.isFetching) ||
    (candlesQuery.data !== undefined && candlesQuery.isFetching);
  const candleTime = latestClosedCandleTime(candlesQuery.data);
  const candleAgeLimit = { "15m": 30, "1h": 120, "1d": 2880 }[interval] * 60_000;
  const isCandleOld = isDataOlderThan(candleTime, candleAgeLimit);

  return (
    <Container className="py-8 sm:py-12">
      <RefreshingIndicator visible={isRefreshing} />
      <h1 className="text-2xl font-semibold tracking-tight">Thị trường</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Binance Spot · dữ liệu tổng hợp (fixture)
      </p>
      {isCandleOld && candleTime && <div className="mt-2"><StaleBadge since={formatVi(candleTime)} /></div>}
      {instrumentsQuery.isError && instrumentsQuery.data !== undefined && (
        <div role="alert" className="mt-3 flex items-center gap-3 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm">
          <span>Không làm mới được danh sách tài sản; đang giữ dữ liệu đã tải.</span>
          <button type="button" onClick={() => instrumentsQuery.refetch()} className="underline">Thử lại</button>
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3 rounded-lg border border-border bg-secondary/50 p-3 text-sm">
        <span className="font-medium">Kiểm tra kết nối stream:</span>
        <StatusBadge
          tone={
            stream.state.status === "live"
              ? "success"
              : stream.state.status === "connecting" || stream.state.status === "reconnecting"
                ? "warning"
                : stream.state.status === "stale" || stream.state.status === "unavailable"
                  ? "danger"
                  : "neutral"
          }
        >
          {stream.state.status}
        </StatusBadge>
        {stream.state.reconnectAttempts > 0 && (
          <span className="text-xs text-muted-foreground">
            attempts: {stream.state.reconnectAttempts}
          </span>
        )}
        <button
          type="button"
          onClick={() => setStreamEnabled((v) => !v)}
          className="ml-auto rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-secondary"
        >
          {streamEnabled ? "Dừng stream" : "Kết nối stream"}
        </button>
        <p className="w-full text-xs text-muted-foreground">
          {streamSymbol} · {interval} · Chart và danh mục vẫn dùng fixture.
        </p>
      </div>

      <section aria-labelledby="instruments-heading" className="mt-6">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 id="instruments-heading" className="text-lg font-semibold">Tài sản</h2>
          <button
            type="button"
            aria-pressed={watchlistOnly}
            onClick={() => setWatchlistOnly((v) => !v)}
            className={`rounded-lg border px-3 py-1.5 text-sm ${
              watchlistOnly
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-foreground hover:bg-secondary"
            }`}
          >
            {watchlistOnly ? "Watchlist ✓" : "Tất cả"}
          </button>
        </div>
        {instrumentsQuery.isLoading ? (
          <LoadingSkeleton />
        ) : instrumentsQuery.data === undefined && instrumentsQuery.isError ? (
          <ErrorState
            message="Không tải được danh sách tài sản."
            onRetry={() => instrumentsQuery.refetch()}
          />
        ) : instruments.length === 0 ? (
          <EmptyState message="Chưa có tài sản nào trong watchlist." />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {instruments.map((inst: Instrument) => {
              const isSelected = inst.instrument_id === effectiveId;
              const isWatched = watchlist.has(inst.instrument_id);
              return (
                <div
                  key={inst.instrument_id}
                  className={`panel text-left transition-colors ${
                    isSelected ? "border-primary ring-1 ring-primary" : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedId(inst.instrument_id)}
                      className="flex-1 text-left"
                    >
                      <p className="text-xs text-muted-foreground">
                        {inst.base_asset}/{inst.quote_asset}
                      </p>
                      <h3 className="mt-1 text-lg font-semibold">{inst.display_symbol}</h3>
                      <p className="mt-2 text-xs text-muted-foreground">
                        {inst.instrument_id}
                      </p>
                    </button>
                    <button
                      type="button"
                      aria-label={isWatched ? "Bỏ khỏi watchlist" : "Thêm vào watchlist"}
                      aria-pressed={isWatched}
                      onClick={() => watchlist.toggle(inst.instrument_id)}
                      className={`rounded-lg border px-2 py-1 text-xs ${
                        isWatched
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border text-foreground hover:bg-secondary"
                      }`}
                    >
                      {isWatched ? "★" : "☆"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section aria-labelledby="candles-heading" className="mt-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="candles-heading" className="text-lg font-semibold">Nến</h2>
          <div className="flex gap-2" role="tablist" aria-label="Khoảng thời gian">
            {INTERVALS.map((iv) => (
              <button
                key={iv}
                type="button"
                role="tab"
                aria-selected={interval === iv}
                onClick={() => setInterval(iv)}
                className={`rounded-lg border px-3 py-1.5 text-sm ${
                  interval === iv
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border text-foreground hover:bg-secondary"
                }`}
              >
                {iv}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4 space-y-4">
          <p className="text-xs text-muted-foreground">
            Nến đã đóng mới nhất: {candleTime ? formatVi(candleTime) : "chưa có"} · fixture
          </p>
          {candlesQuery.isError && candlesQuery.data !== undefined && (
            <div role="alert" className="flex items-center gap-3 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm">
              <span>Không làm mới được nến; đang giữ dữ liệu đã tải.</span>
              <button type="button" onClick={() => candlesQuery.refetch()} className="underline">Thử lại</button>
            </div>
          )}
          {!candlesQuery.isLoading && candlesQuery.data && candlesQuery.data.length > 0 && (
            <CandleChart candles={candlesQuery.data} />
          )}
          {candlesQuery.isLoading ? (
            <div className="panel animate-pulse">
              <div className="h-4 w-full rounded bg-muted" />
              <div className="mt-2 h-4 w-full rounded bg-muted" />
              <div className="mt-2 h-4 w-3/4 rounded bg-muted" />
            </div>
          ) : candlesQuery.data === undefined && candlesQuery.isError ? (
            <ErrorState
              message="Không tải được dữ liệu nến."
              onRetry={() => candlesQuery.refetch()}
            />
          ) : (
            <CandleTable candles={candlesQuery.data ?? []} />
          )}
        </div>
      </section>
    </Container>
  );
}
