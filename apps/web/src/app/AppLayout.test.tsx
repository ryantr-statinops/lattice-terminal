import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import marketFixture from "../../../../data/fixtures/market.json";
import newsFixture from "../../../../data/fixtures/news.json";
import { AppLayout } from "../components/layout/AppLayout";
import { AccountPage } from "../features/account/AccountPage";
import { NewsPage } from "../features/news/NewsPage";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});

function renderAtNewsRoute() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/terminal/news"]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/terminal/news" element={<NewsPage />} />
            <Route path="/terminal/account" element={<AccountPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("terminal shell", () => {
  it("loads synthetic fixture news and navigates between routes", async () => {
    expect(marketFixture.is_synthetic).toBe(true);
    expect(newsFixture.is_synthetic).toBe(true);

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        data: newsFixture.articles,
        meta: { is_synthetic: true },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAtNewsRoute();

    expect(await screen.findByRole("heading", { name: "Tin tức" })).toBeTruthy();
    expect(
      await screen.findByText("Bản tin mẫu BTC — chỉ dùng để kiểm tra giao diện"),
    ).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/news/articles",
      expect.objectContaining({
        headers: expect.objectContaining({ "Content-Type": "application/json" }),
      }),
    );

    await userEvent.click(screen.getByRole("link", { name: "Tài khoản" }));
    expect(await screen.findByRole("heading", { name: "Tài khoản" })).toBeTruthy();
  });
});
