import { useEffect, useRef, useState } from "react";
import { getTask } from "../api/client";
import { sseUrl } from "../api/client";
import type { Task, TaskEvent } from "../api/client";

// Live task events via SSE with exponential-backoff reconnect.
// Also refetches the task record when a state event arrives.

export function useSse(taskId: string | undefined) {
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!taskId) return;
    setEvents([]);
    setTask(null);
    setError(null);

    let retryDelay = 1000;
    let active = true;

    const connect = () => {
      const es = new EventSource(sseUrl(taskId));
      esRef.current = es;

      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          setEvents((prev) => [...prev, data]);
          if (data.event === "snapshot") {
            setTask(data.data);
          }
          // Any state change triggers a task refresh
          if (data.event === "state") {
            getTask(taskId).then(setTask).catch(() => {});
          }
        } catch (err) {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      };

      es.onerror = () => {
        es.close();
        if (active) {
          setTimeout(connect, retryDelay);
          retryDelay = Math.min(retryDelay * 2, 30000);
        }
      };
    };

    connect();

    return () => {
      active = false;
      esRef.current?.close();
    };
  }, [taskId]);

  return { events, task, error };
}
