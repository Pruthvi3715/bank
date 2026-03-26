import { useEffect, useRef, useState, useCallback } from "react";
import { AgentActivityStep } from "@/types/api";

const WS_BASE =
  (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000")
    .replace(/^http/, "ws");

export interface UsePipelineWebSocketOptions {
  onActivity?: (step: AgentActivityStep) => void;
}

export function usePipelineWebSocket({
  onActivity,
}: UsePipelineWebSocketOptions = {}) {
  const [connected, setConnected] = useState(false);
  const [steps, setSteps] = useState<AgentActivityStep[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE}/ws/pipeline`);

    ws.onopen = () => setConnected(true);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as AgentActivityStep;
        setSteps((prev) => [...prev, data]);
        onActivity?.(data);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [onActivity]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  const clearSteps = useCallback(() => {
    setSteps([]);
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { connected, steps, clearSteps, disconnect };
}
