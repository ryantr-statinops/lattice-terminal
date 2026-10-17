import { StrictMode, type PropsWithChildren } from "react";
import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useBinanceStream } from "./stream";

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  readyState = FakeWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  close = vi.fn(() => {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.({} as CloseEvent);
  });

  constructor(readonly url: string) {
    FakeWebSocket.instances.push(this);
  }

  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.({} as Event);
  }

  message(data: string) {
    this.onmessage?.({ data } as MessageEvent);
  }

  serverClose() {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.({} as CloseEvent);
  }
}

const strictWrapper = ({ children }: PropsWithChildren) => <StrictMode>{children}</StrictMode>;
const validKline = JSON.stringify({ k: { t: 1_797_000_000_000, c: "100", x: false } });
const hiddenDescriptor = Object.getOwnPropertyDescriptor(document, "hidden");

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-10-17T10:00:00Z"));
  FakeWebSocket.instances = [];
  vi.stubGlobal("WebSocket", FakeWebSocket);
  Object.defineProperty(document, "hidden", { configurable: true, value: false });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  if (hiddenDescriptor) Object.defineProperty(document, "hidden", hiddenDescriptor);
  else Reflect.deleteProperty(document, "hidden");
});

describe("Binance stream lifecycle", () => {
  it("subscribes to the selected symbol and interval and waits for a valid kline", () => {
    const { result } = renderHook(() => useBinanceStream("ETHUSDT", "15m", true));
    const socket = FakeWebSocket.instances[0];

    expect(socket.url).toBe("wss://stream.binance.com:9443/ws/ethusdt@kline_15m");
    expect(result.current.state.status).toBe("connecting");
    act(() => {
      socket.open();
      socket.message("not json");
    });
    expect(result.current.state.status).toBe("connecting");
    expect(result.current.state.lastMessageAt).toBeNull();

    act(() => socket.message(validKline));
    expect(result.current.state.status).toBe("live");
    expect(result.current.state.lastMessageAt).toBe(Date.now());
  });

  it("marks an open stream stale if it never receives a valid message", () => {
    const { result } = renderHook(() => useBinanceStream("BTCUSDT", "1h", true));
    act(() => FakeWebSocket.instances[0].open());

    act(() => vi.advanceTimersByTime(75_000));

    expect(result.current.state.status).toBe("stale");
    expect(result.current.state.lastMessageAt).toBeNull();
  });

  it("uses exponential reconnect delay and clears attempts after valid data", () => {
    const { result } = renderHook(() => useBinanceStream("BTCUSDT", "1h", true));
    act(() => FakeWebSocket.instances[0].serverClose());
    expect(result.current.state.reconnectAttempts).toBe(1);

    act(() => vi.advanceTimersByTime(999));
    expect(FakeWebSocket.instances).toHaveLength(1);
    act(() => vi.advanceTimersByTime(1));
    expect(FakeWebSocket.instances).toHaveLength(2);
    act(() => FakeWebSocket.instances[1].message(validKline));
    expect(result.current.state.reconnectAttempts).toBe(0);
  });

  it("pauses while the document is hidden and resumes when visible", () => {
    const { result } = renderHook(() => useBinanceStream("BTCUSDT", "1h", true));
    const firstSocket = FakeWebSocket.instances[0];

    act(() => {
      Object.defineProperty(document, "hidden", { configurable: true, value: true });
      document.dispatchEvent(new Event("visibilitychange"));
    });
    expect(firstSocket.close).toHaveBeenCalledOnce();
    expect(result.current.state.status).toBe("idle");

    act(() => {
      Object.defineProperty(document, "hidden", { configurable: true, value: false });
      document.dispatchEvent(new Event("visibilitychange"));
    });
    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it("keeps one active connection under StrictMode and fully cleans up on disable or unmount", () => {
    const { result, rerender, unmount } = renderHook(
      ({ enabled }: { enabled: boolean }) => useBinanceStream("BTCUSDT", "1h", enabled),
      { initialProps: { enabled: true }, wrapper: strictWrapper },
    );
    expect(FakeWebSocket.instances.filter((socket) => socket.readyState !== FakeWebSocket.CLOSED)).toHaveLength(1);

    rerender({ enabled: false });
    expect(result.current.state.status).toBe("idle");
    expect(vi.getTimerCount()).toBe(0);
    const countAfterDisable = FakeWebSocket.instances.length;
    unmount();
    act(() => vi.advanceTimersByTime(60_000));
    expect(FakeWebSocket.instances).toHaveLength(countAfterDisable);
  });

  it("replaces the subscription and cancels the prior socket and timers", () => {
    const { rerender } = renderHook(
      ({ symbol, interval }: { symbol: string; interval: string }) => useBinanceStream(symbol, interval, true),
      { initialProps: { symbol: "BTCUSDT", interval: "1h" } },
    );
    const prior = FakeWebSocket.instances[0];

    rerender({ symbol: "ETHUSDT", interval: "15m" });

    expect(prior.close).toHaveBeenCalledOnce();
    expect(FakeWebSocket.instances.at(-1)?.url).toContain("ethusdt@kline_15m");
    expect(FakeWebSocket.instances.filter((socket) => socket.readyState !== FakeWebSocket.CLOSED)).toHaveLength(1);
  });
});
