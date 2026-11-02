import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../hooks/useApp";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../api/client";

// Health check with manual refresh
// Returns health status and a refresh function
// Automatically refreshes every 30 seconds

export function useHealth() {
  const { health, refreshHealth } = useApp();
  const navigate = useNavigate();

  const { isLoading, error } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30000,
    onSuccess: (data) => {
      if (data.status !== "ok") {
        navigate("/offline");
      }
    },
  });

  return {
    health,
    isLoading,
    error,
    refresh: refreshHealth,
  };
}
