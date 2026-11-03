import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../api/client";

export function useHealth() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30000,
  });
  return { health: data, isLoading, error, refetch };
}
