import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listProjectTasks } from "../api/client";

// Task list with filtering
// Returns filtered tasks and filter controls
// Automatically refreshes when projectId changes

export function useProjectTasks(projectId: string) {
  const [filter, setFilter] = useState<string>("all");

  const { data: tasks, isLoading, error } = useQuery({
    queryKey: ["tasks", projectId],
    queryFn: () => listProjectTasks(projectId),
    enabled: !!projectId,
  });

  const filteredTasks = tasks?.filter((task) => {
    if (filter === "all") return true;
    if (filter === "active") return !task.completed_at;
    if (filter === "completed") return !!task.completed_at;
    if (filter === "failed") return task.state === "failed";
    return true;
  }) || [];

  return {
    tasks: filteredTasks,
    isLoading,
    error,
    filter,
    setFilter,
  };
}
