import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listConnectors, probeConnector, listProjectTasks, getTask, cancelTask } from "../api/client";
import type { Connector } from "../api/client";

export function useConnectors() {
  const { data: connectors, isLoading, error, refetch } = useQuery({
    queryKey: ["connectors"],
    queryFn: listConnectors,
  });

  const qc = useQueryClient();
  const { mutate: probe, isPending: isProbing } = useMutation({
    mutationFn: probeConnector,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["connectors"] }),
  });

  return {
    connectors: (connectors as Connector[] | undefined) ?? [],
    isLoading,
    error,
    refetch,
    probe,
    isProbing,
  };
}

export function useProjectTasks(projectId: string | undefined) {
  return useQuery({
    queryKey: ["tasks", projectId],
    queryFn: () => listProjectTasks(projectId!),
    enabled: !!projectId,
  });
}

export function useTask(taskId: string | undefined) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => getTask(taskId!),
    enabled: !!taskId,
  });
}

export function useCancelTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: cancelTask,
    onSuccess: (_, taskId) => {
      qc.invalidateQueries({ queryKey: ["task", taskId] });
      qc.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
