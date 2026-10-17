import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NewsPage } from "./NewsPage";
import type { Article } from "./api";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0, gcTime: Infinity } },
  });
}

function makeArticle(id: string, firstSeenAt: string): Article {
  return {
    id,
    title: `Fixture story ${id}`,
    instrument_ids: ["binance:spot:BTCUSDT"],
    published_at: firstSeenAt,
    first_seen_at: firstSeenAt,
    language: "en",
    url: null,
  };
}

function renderNews(client: QueryClient) {
  return render(
    <QueryClientProvider client={client}>
      <NewsPage />
    </QueryClientProvider>,
  );
}

describe("news refresh and data age", () => {
  it("uses the initial loading state without showing a refresh indicator", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    renderNews(makeQueryClient());

    expect(screen.getByRole("heading", { name: "Tin tức" })).toBeTruthy();
    expect(screen.queryByLabelText("Đang làm mới dữ liệu")).toBeNull();
  });

  it("keeps cached news visible during a successful refresh", async () => {
    const client = makeQueryClient();
    const recent = makeArticle("old", new Date(Date.now() - 5_000).toISOString());
    client.setQueryData(["news", "articles", null], [recent]);
    let resolveFetch: ((response: unknown) => void) | undefined;
    const fetchMock = vi.fn(() => new Promise((resolve) => { resolveFetch = resolve; }));
    vi.stubGlobal("fetch", fetchMock);

    renderNews(client);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    expect(screen.getByText("Fixture story old")).toBeTruthy();
    expect(screen.getByLabelText("Đang làm mới dữ liệu")).toBeTruthy();

    const fresh = makeArticle("fresh", new Date().toISOString());
    await act(async () => {
      resolveFetch?.({
        ok: true,
        json: async () => ({ data: [fresh], meta: { is_synthetic: true } }),
      });
    });

    expect(await screen.findByText("Fixture story fresh")).toBeTruthy();
    expect(screen.queryByText("Fixture story old")).toBeNull();
    expect(screen.queryByLabelText("Đang làm mới dữ liệu")).toBeNull();
  });

  it("keeps cached articles after refresh failure and warns only when source data is old", async () => {
    const client = makeQueryClient();
    const old = makeArticle("old", new Date(Date.now() - 48 * 60 * 60_000).toISOString());
    client.setQueryData(["news", "articles", null], [old]);
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("offline"));
    vi.stubGlobal("fetch", fetchMock);

    renderNews(client);

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("Fixture story old")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Thử lại" })).toBeTruthy();
    expect(screen.getByText(/Có thể đã cũ/)).toBeTruthy();
  });

  it("does not mark a fresh article stale just because its cache is refetching", async () => {
    const client = makeQueryClient();
    const recent = makeArticle("recent", new Date(Date.now() - 5_000).toISOString());
    client.setQueryData(["news", "articles", null], [recent]);
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));

    renderNews(client);

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("Fixture story recent")).toBeTruthy();
    expect(screen.queryByText(/Có thể đã cũ/)).toBeNull();
  });
});
