import { useState } from "react";
import { Link } from "react-router-dom";
import news from "../../../data/fixtures/news.json";
import market from "../../../data/fixtures/market.json";
import Container from "./components/layout/Container";
import { Button } from "./components/ui/button";
import {
  Dialog, DialogTrigger, DialogPortal, DialogBackdrop,
  DialogContent, DialogClose, DialogTitle, DialogDescription,
} from "./components/ui/dialog";

export function App() {
  const [health, setHealth] = useState("Chưa kiểm tra kết nối API");
  const [pending, setPending] = useState(false);

  async function checkHealth() {
    setPending(true);
    try {
      const base = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
      const response = await fetch(`${base}/api/v1/health`, { signal: AbortSignal.timeout(5000) });
      if (!response.ok) throw new Error("API unavailable");
      const result = await response.json();
      if (result.data?.status !== "ok" || result.data?.mode !== "fixture" ||
          result.data?.service !== "kestrel-terminal-api" || result.meta?.is_synthetic !== true) {
        throw new Error("Unexpected health response");
      }
      setHealth("API đã kết nối · chế độ fixture");
    } catch {
      setHealth("API chưa sẵn sàng. Bạn vẫn có thể xem dữ liệu mẫu bên dưới.");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <a className="skip-link" href="#main">Đi đến nội dung</a>
      <header className="border-b border-border bg-background">
        <Container className="flex flex-wrap items-center justify-between gap-4 py-5">
          <Link to="/terminal/news" className="font-semibold tracking-tight">Kestrel Terminal</Link>
          <span className="fixture-badge">SYNTHETIC · FIXTURE ONLY</span>
        </Container>
      </header>
      <main id="main">
        <Container className="py-12 sm:py-16">
          <p className="mb-3 text-sm font-medium text-primary">P01 / Chuẩn bị nền tảng</p>
          <h1 className="max-w-3xl text-3xl font-semibold tracking-tight sm:text-4xl">Không gian nghiên cứu thị trường đang được xây dựng</h1>
          <p className="mt-5 max-w-2xl leading-7 text-muted-foreground">Đây là khung giao diện để chuẩn bị Kestrel Terminal. Toàn bộ tin và giá hiển thị là dữ liệu tổng hợp, không phản ánh thị trường thực tế.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button onClick={checkHealth} disabled={pending}>{pending ? "Đang kiểm tra…" : "Kiểm tra API local"}</Button>
            <Dialog>
              <DialogTrigger render={<Button variant="outline" />}>Phạm vi bản chuẩn bị</DialogTrigger>
              <DialogPortal>
                <DialogBackdrop />
                <DialogContent className="max-w-[calc(100%-2rem)] border border-border bg-background text-foreground sm:max-w-lg">
                  <DialogTitle className="text-foreground">Khung thử nghiệm bằng fixture</DialogTitle>
                  <DialogDescription className="mt-4 text-sm leading-6 text-muted-foreground">Hiện có giao diện React, routing và dữ liệu mẫu dùng chung trong repository. Tài khoản, live feed, portfolio và Model Lab sẽ được triển khai trong các giai đoạn tiếp theo.</DialogDescription>
                  <DialogClose className="static mt-6 rounded-lg border border-border px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-primary">Đóng</DialogClose>
                </DialogContent>
              </DialogPortal>
            </Dialog>
          </div>
          <p role="status" aria-live="polite" className="mt-3 min-h-6 text-sm text-muted-foreground">{health}</p>

          <section aria-labelledby="market-heading" className="mt-12">
            <div className="section-title"><h2 id="market-heading">Danh sách tài sản mẫu</h2><span>Giá tổng hợp · USDT</span></div>
            <div className="grid gap-4 sm:grid-cols-2">
              {market.instruments.map((instrument) => {
                const candle = market.candles.find((item) => item.instrument_id === instrument.instrument_id);
                return <article className="panel" key={instrument.instrument_id}>
                  <p className="text-sm text-muted-foreground">Binance Spot · fixture</p>
                  <h3 className="mt-2 text-lg font-semibold">{instrument.display_symbol}</h3>
                  <p className="mt-4 font-mono text-2xl">{candle?.close ?? "—"} <span className="text-sm text-muted-foreground">USDT</span></p>
                  <p className="mt-2 text-xs text-muted-foreground">Nến 1h mẫu · không phải giá live</p>
                </article>;
              })}
            </div>
          </section>
          <section aria-labelledby="news-heading" className="mt-10">
            <div className="section-title"><h2 id="news-heading">Bản tin mẫu</h2><span>Chưa kết nối nguồn tin thật</span></div>
            <div className="grid gap-4">
              {news.articles.map((article) => <article key={article.id} className="panel">
                <p className="text-xs font-medium text-primary">FIXTURE · {article.instrument_ids.map((id) => market.instruments.find((item) => item.instrument_id === id)?.display_symbol ?? id).join(", ")}</p>
                <h3 className="mt-2 font-semibold">{article.title}</h3>
                <p className="mt-3 text-sm text-muted-foreground">Thời điểm mẫu: <time dateTime={article.published_at}>{new Date(article.published_at).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })} (UTC+7)</time></p>
              </article>)}
            </div>
          </section>
        </Container>
      </main>
      <footer className="border-t border-border"><Container className="py-6 text-sm text-muted-foreground">Kestrel Terminal · Dữ liệu tổng hợp phục vụ phát triển giao diện.</Container></footer>
    </>
  );
}

