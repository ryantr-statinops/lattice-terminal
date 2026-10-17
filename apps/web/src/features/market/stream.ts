import { useCallback, useEffect, useRef, useState } from "react";

export type StreamStatus = "idle" | "connecting" | "live" | "reconnecting" | "stale" | "unavailable";

export interface StreamState {
  status: StreamStatus;
  lastMessageAt: number | null;
  reconnectAttempts: number;
  error: string | null;
}

const INITIAL: StreamState = {
  status: "idle",
  lastMessageAt: null,
  reconnectAttempts: 0,
  error: null,
};
const STALE_AFTER_MS = 60_000;

function isKlineMessage(data: unknown): boolean {
  if (!data || typeof data !== "object") return false;
  const kline = (data as { k?: unknown }).k;
  if (!kline || typeof kline !== "object") return false;
  const candle = kline as { t?: unknown; c?: unknown; x?: unknown };
  return typeof candle.t === "number" && typeof candle.c === "string" && typeof candle.x === "boolean";
}

export function useBinanceStream(symbol: string, interval: string, enabled: boolean) {
  const [state, setState] = useState<StreamState>(INITIAL);
  const [visible, setVisible] = useState(() => !document.hidden);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const staleTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const attemptsRef = useRef(0);
  const activeRef = useRef(false);
  const connectedAtRef = useRef<number | null>(null);
  const lastMessageAtRef = useRef<number | null>(null);

  const active = enabled && visible;

  const cleanup = useCallback(() => {
    if (reconnectTimer.current !== null) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (staleTimer.current !== null) {
      clearInterval(staleTimer.current);
      staleTimer.current = null;
    }
    connectedAtRef.current = null;
    lastMessageAtRef.current = null;
    const socket = wsRef.current;
    wsRef.current = null;
    if (socket) {
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;
      try {
        socket.close();
      } catch {
        // Ignore an already closed socket.
      }
    }
  }, []);

  const connect = useCallback(() => {
    if (!activeRef.current || wsRef.current) return;
    if (reconnectTimer.current !== null) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    setState((previous) => ({ ...previous, status: "connecting", lastMessageAt: null, error: null }));
    let socket: WebSocket;
    try {
      socket = new WebSocket(
        `wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}@kline_${interval}`,
      );
    } catch (error) {
      setState((previous) => ({ ...previous, status: "unavailable", error: String(error) }));
      return;
    }

    wsRef.current = socket;
    socket.onopen = () => {
      if (wsRef.current !== socket) return;
      connectedAtRef.current = Date.now();
      lastMessageAtRef.current = null;
      setState((previous) => ({ ...previous, status: "connecting", lastMessageAt: null, error: null }));
    };
    socket.onmessage = (event) => {
      if (wsRef.current !== socket) return;
      try {
        if (!isKlineMessage(JSON.parse(String(event.data)))) return;
        const receivedAt = Date.now();
        lastMessageAtRef.current = receivedAt;
        attemptsRef.current = 0;
        setState((previous) => ({ ...previous, status: "live", lastMessageAt: receivedAt, reconnectAttempts: 0, error: null }));
      } catch {
        // Ignore malformed stream messages.
      }
    };
    socket.onerror = () => {
      if (wsRef.current === socket) {
        setState((previous) => ({ ...previous, status: "reconnecting", error: "WebSocket error" }));
      }
    };
    socket.onclose = () => {
      if (wsRef.current !== socket) return;
      wsRef.current = null;
      connectedAtRef.current = null;
      lastMessageAtRef.current = null;
      if (!activeRef.current) {
        setState(INITIAL);
        return;
      }

      const attempts = attemptsRef.current + 1;
      attemptsRef.current = attempts;
      const delay = Math.min(1000 * 2 ** (attempts - 1), 30_000);
      setState((previous) => ({ ...previous, status: "reconnecting", reconnectAttempts: attempts }));
      reconnectTimer.current = setTimeout(() => {
        reconnectTimer.current = null;
        connect();
      }, delay);
    };
  }, [interval, symbol]);

  const reconnect = useCallback(() => {
    if (!activeRef.current) return;
    cleanup();
    attemptsRef.current = 0;
    setState({ ...INITIAL, status: "connecting" });
    connect();
  }, [cleanup, connect]);

  useEffect(() => {
    const onVisibilityChange = () => setVisible(!document.hidden);
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, []);

  useEffect(() => {
    activeRef.current = active;
    if (!active) {
      cleanup();
      attemptsRef.current = 0;
      setState(INITIAL);
      return;
    }

    attemptsRef.current = 0;
    setState({ ...INITIAL, status: "connecting" });
    connect();
    staleTimer.current = setInterval(() => {
      const referenceTime = lastMessageAtRef.current ?? connectedAtRef.current;
      if (!wsRef.current || referenceTime === null || Date.now() - referenceTime <= STALE_AFTER_MS) return;
      setState((previous) => (previous.status === "stale" ? previous : { ...previous, status: "stale" }));
    }, 15_000);

    return () => {
      activeRef.current = false;
      cleanup();
    };
  }, [active, connect, cleanup]);

  return { state, reconnect };
}
