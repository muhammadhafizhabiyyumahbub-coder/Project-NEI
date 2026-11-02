import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTask, getTaskEvents } from "../api/client";
import { useSse } from "./useSse";

// Task detail with SSE updates
// Returns task data and live events
// Automatically refreshes when taskId changes

export function useTask(taskId: string) {
  const { data: task, isLoading, error } = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => getTask(taskId),
    enabled: !!taskId,
  });

  const { events: sseEvents, error: sseError } = useSse(taskId);

  const { data: rawEvents } = useQuery({
    queryKey: ["taskEvents", taskId],
    queryFn: () => getTaskEvents(taskId),
    enabled: !!taskId,
  });

  const allEvents = [...(rawEvents || []), ...sseEvents];

  return {
    task,
    isLoading,
    error,
    events: allEvents,
    sseError,
  };
}
