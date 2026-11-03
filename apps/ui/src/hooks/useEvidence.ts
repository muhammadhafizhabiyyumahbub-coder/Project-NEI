import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listEvidenceSources,
  searchEvidence,
  listFormulas,
  runCalculation,
} from "../api/client";

export function useEvidenceSources() {
  return useQuery({
    queryKey: ["evidence-sources"],
    queryFn: listEvidenceSources,
  });
}

export function useEvidenceSearch(query: string | null, sourceId?: string) {
  return useQuery({
    queryKey: ["evidence-search", query, sourceId],
    queryFn: () => searchEvidence(query!, sourceId),
    enabled: !!query && query.trim().length > 0,
  });
}

export function useFormulas(domain?: string, status?: string) {
  return useQuery({
    queryKey: ["formulas", domain, status],
    queryFn: () => listFormulas(domain, status),
  });
}

export function useRunCalculation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: runCalculation,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["calc-runs"] }),
  });
}
