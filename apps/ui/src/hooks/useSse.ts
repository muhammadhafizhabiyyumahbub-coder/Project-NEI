import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTaskEvents } from "../api/client";

// SSE subscription with reconnect
// Returns events as they arrive
// Automatically reconnects with exponential backoff
// Returns null when taskId changes

export function useSse(taskId: string): {
  events: TaskEvent[];
  error: Error | null;
} {
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!taskId) return;

    let retryDelay = 1000;
    let eventSource: EventSource | null = null;
    let isActive = true;

    const connect = () => {
      eventSource = new EventSource(sseUrl(taskId));
      retryDelay = 1000;

      eventSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          setEvents((prev) => [...prev, data]);
        } catch (err) {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      };

      eventSource.onerror = () => {
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        if (isActive) {
          setTimeout(connect, retryDelay);
          retryDelay = Math.min(retryDelay * 2, 30000);
        }
      };
    };

    connect();

    return () => {
      isActive = false;
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [taskId]);

  return { events, error };
}
