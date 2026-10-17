import { useState } from "react";
import Container from "../../components/layout/Container";
import { RefreshingIndicator } from "../../components/ui/RefreshingIndicator";
import { StaleBadge } from "../../components/ui/StaleBadge";
import { useArticles, type Article } from "./api";
import { isDataOlderThan } from "../../lib/dataAge";

const FILTERS = [
  { id: null, label: "Tất cả" },
  { id: "binance:spot:BTCUSDT", label: "BTC" },
  { id: "binance:spot:ETHUSDT", label: "ETH" },
] as const;

function instrumentLabel(id: string): string {
  if (id === "binance:spot:BTCUSDT") return "BTC/USDT";
  if (id === "binance:spot:ETHUSDT") return "ETH/USDT";
  return id;
}

function formatVi(dateStr: string): string {
  return new Date(dateStr).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
}

function LoadingSkeleton() {
  return (
    <div className="grid gap-4">
      {[0, 1].map((i) => (
        <div key={i} className="panel animate-pulse">
          <div className="h-3 w-20 rounded bg-muted" />
          <div className="mt-3 h-5 w-3/4 rounded bg-muted" />
          <div className="mt-3 h-3 w-1/2 rounded bg-muted" />
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

function ArticleCard({ article }: { article: Article }) {
  return (
    <article className="panel">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full border border-border px-2 py-0.5 font-mono text-muted-foreground">
          FIXTURE
        </span>
        {article.instrument_ids.map((id) => (
          <span
            key={id}
            className="rounded-full bg-secondary px-2 py-0.5 text-muted-foreground"
          >
            {instrumentLabel(id)}
          </span>
        ))}
        <span className="text-muted-foreground">{article.language.toUpperCase()}</span>
      </div>
      <h3 className="mt-3 font-semibold">{article.title}</h3>
      <dl className="mt-3 grid gap-1 text-xs text-muted-foreground">
        <div className="flex gap-2">
          <dt className="font-medium">Xuất bản:</dt>
          <dd>{formatVi(article.published_at)}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="font-medium">First seen:</dt>
          <dd>{formatVi(article.first_seen_at)}</dd>
        </div>
        {article.url && (
          <div className="flex gap-2">
            <dt className="font-medium">Nguồn:</dt>
            <dd>
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline"
              >
                {article.url}
              </a>
            </dd>
          </div>
        )}
      </dl>
    </article>
  );
}

export function NewsPage() {
  const [filter, setFilter] = useState<string | null>(null);
  const articlesQuery = useArticles(filter);
  const newestFirstSeen = articlesQuery.data
    ?.map((article) => article.first_seen_at)
    .filter((timestamp) => Number.isFinite(Date.parse(timestamp)))
    .sort((a, b) => Date.parse(b) - Date.parse(a))[0] ?? null;
  const isNewsOld = isDataOlderThan(newestFirstSeen, 24 * 60 * 60_000);

  return (
    <Container className="py-8 sm:py-12">
      <RefreshingIndicator visible={articlesQuery.data !== undefined && articlesQuery.isFetching} />
      <h1 className="text-2xl font-semibold tracking-tight">Tin tức</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        News-first · dữ liệu tổng hợp (fixture)
      </p>
      {newestFirstSeen && (
        <p className="mt-2 text-xs text-muted-foreground">Tin được thấy gần nhất: {formatVi(newestFirstSeen)}</p>
      )}
      {isNewsOld && newestFirstSeen && <div className="mt-2"><StaleBadge since={formatVi(newestFirstSeen)} /></div>}

      <div className="mt-6 flex flex-wrap gap-2" role="tablist" aria-label="Lọc theo tài sản">
        {FILTERS.map((f) => (
          <button
            key={f.label}
            type="button"
            role="tab"
            aria-selected={filter === f.id}
            onClick={() => setFilter(f.id)}
            className={`rounded-lg border px-3 py-1.5 text-sm ${
              filter === f.id
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-foreground hover:bg-secondary"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <section aria-labelledby="articles-heading" className="mt-6">
        <h2 id="articles-heading" className="sr-only">
          Danh sách bài tin
        </h2>
        {articlesQuery.isError && articlesQuery.data !== undefined && (
          <div role="alert" className="mb-3 flex items-center gap-3 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm">
            <span>Không làm mới được tin; đang giữ danh sách đã tải.</span>
            <button type="button" onClick={() => articlesQuery.refetch()} className="underline">Thử lại</button>
          </div>
        )}
        {articlesQuery.isLoading ? (
          <LoadingSkeleton />
        ) : articlesQuery.data === undefined && articlesQuery.isError ? (
          <ErrorState
            message="Không tải được bài tin."
            onRetry={() => articlesQuery.refetch()}
          />
        ) : !articlesQuery.data || articlesQuery.data.length === 0 ? (
          <EmptyState message="Chưa có bài tin cho lựa chọn này." />
        ) : (
          <div className="grid gap-4">
            {articlesQuery.data.map((a: Article) => (
              <ArticleCard key={a.id} article={a} />
            ))}
          </div>
        )}
      </section>
    </Container>
  );
}
