import { createContext, useContext, useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  getHealth,
  listProjects,
  createProject,
  listProjectTasks,
  createTask,
  getTask,
  cancelTask,
  getTaskEvents,
  listConnectors,
  probeConnector,
  sseUrl,
  listEvidenceSources,
  searchEvidence,
  listFormulas,
  runCalculation,
} from "../api/client";
import type {
  Project,
  Connector,
  EvidenceSource,
  EvidenceSearchResult,
  Formula,
  CalcRun,
} from "../api/client";

// Global state
const AppContext = createContext<{
  health: {
    status: string;
    db: boolean;
    timestamp: string;
  } | null;
  projects: Project[];
  connectors: Connector[];
  evidenceSources: EvidenceSource[];
  formulas: Formula[];
  refreshHealth: () => void;
  refreshProjects: () => void;
  refreshConnectors: () => void;
  refreshEvidenceSources: () => void;
  refreshFormulas: () => void;
}>(null!);


export function AppProvider({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<{
    status: string;
    db: boolean;
    timestamp: string;
  } | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [evidenceSources, setEvidenceSources] = useState<EvidenceSource[]>([]);
  const [formulas, setFormulas] = useState<Formula[]>([]);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Health
  const { refetch: refreshHealth } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30000,
    onSuccess: (data) => setHealth(data),
  });

  // Projects
  const { refetch: refreshProjects } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    onSuccess: (data) => setProjects(data),
  });

  // Connectors
  const { refetch: refreshConnectors } = useQuery({
    queryKey: ["connectors"],
    queryFn: listConnectors,
    onSuccess: (data) => setConnectors(data),
  });

  // Evidence sources
  const { refetch: refreshEvidenceSources } = useQuery({
    queryKey: ["evidence-sources"],
    queryFn: listEvidenceSources,
    onSuccess: (data) => setEvidenceSources(data),
  });

  // Formulas
  const { refetch: refreshFormulas } = useQuery({
    queryKey: ["formulas"],
    queryFn: listFormulas,
    onSuccess: (data) => setFormulas(data),
  });

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      refreshProjects();
      navigate("/projects");
    },
  });

  // Create task mutation
  const createTaskMutation = useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: TaskCreate }) =>
      createTask(projectId, payload),
    onSuccess: (task) => {
      queryClient.invalidateQueries({ queryKey: ["tasks", task.project_id] });
      navigate(`/projects/${task.project_id}/tasks/${task.id}`);
    },
  });

  // Cancel task mutation
  const cancelTaskMutation = useMutation({
    mutationFn: cancelTask,
    onSuccess: (task) => {
      queryClient.invalidateQueries({ queryKey: ["tasks", task.project_id] });
      queryClient.invalidateQueries({ queryKey: ["task", task.id] });
    },
  });

  // Probe connector mutation
  const probeConnectorMutation = useMutation({
    mutationFn: probeConnector,
    onSuccess: () => refreshConnectors(),
  });

  // Search evidence mutation
  const searchEvidenceMutation = useMutation({
    mutationFn: ({ query, sourceId }: { query: string; sourceId?: string }) =>
      searchEvidence(query, sourceId),
  });

  // Run calculation mutation
  const runCalculationMutation = useMutation({
    mutationFn: runCalculation,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["calc-runs"] }),
  });

  return (
    <AppContext.Provider
      value={{ health, projects, connectors, evidenceSources, formulas, refreshHealth, refreshProjects, refreshConnectors, refreshEvidenceSources, refreshFormulas }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
