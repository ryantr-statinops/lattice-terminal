import { Link, Outlet } from "react-router-dom";
import Container from "./Container";
import { useTheme } from "../../lib/theme";

const NAV = [
  { to: "/terminal/market", label: "Thị trường" },
  { to: "/terminal/news", label: "Tin tức" },
  { to: "/terminal/portfolio", label: "Danh mục" },
  { to: "/terminal/model-lab", label: "Model Lab" },
  { to: "/terminal/account", label: "Tài khoản" },
];

export function AppLayout() {
  const { theme, toggle } = useTheme();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <a className="skip-link" href="#main">
        Đi đến nội dung
      </a>
      <header className="border-b border-border bg-background">
        <Container className="flex flex-wrap items-center justify-between gap-4 py-4">
          <Link to="/terminal/news" className="font-semibold tracking-tight">
            Kestrel Terminal
          </Link>
          <nav className="flex flex-wrap items-center gap-2" aria-label="Chính">
            {NAV.map((n) => (
              <Link
                key={n.to}
                to={n.to}
                className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <span className="fixture-badge">SYNTHETIC · FIXTURE ONLY</span>
            <button
              type="button"
              onClick={toggle}
              aria-label="Chuyển theme"
              className="rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-secondary"
            >
              {theme === "dark" ? "🌙" : "☀️"}
            </button>
          </div>
        </Container>
      </header>
      <main id="main">
        <Outlet />
      </main>
      <footer className="border-t border-border">
        <Container className="py-6 text-sm text-muted-foreground">
          Kestrel Terminal · Dữ liệu tổng hợp phục vụ phát triển giao diện.
        </Container>
      </footer>
    </div>
  );
}
