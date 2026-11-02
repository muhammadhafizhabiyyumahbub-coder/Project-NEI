import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listConnectors, probeConnector } from "../api/client";

// Connector health with probe capability
// Returns connector list and probe function
// Automatically refreshes connector list

export function useConnectors() {
  const { data: connectors, isLoading, error } = useQuery({
    queryKey: ["connectors"],
    queryFn: listConnectors,
  });

  const { mutate: probe, isPending: isProbing } = useMutation({
    mutationFn: probeConnector,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connectors"] });
    },
  });

  return {
    connectors: connectors || [],
    isLoading,
    error,
    probe,
    isProbing,
  };
}
