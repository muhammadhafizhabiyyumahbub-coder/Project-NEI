// NEI frontend API client — all types come from openapi-generated src/api/types.ts.
//
// Regenerate types (run from repo root):
//   1. start uvicorn on :8000
//   2. curl -s http://localhost:8000/openapi.json > apps/ui/openapi.json
//   3. cd apps/ui && npx openapi-typescript openapi.json src/api/types.ts

import type {
  components,
} from "./types";

export type Project = components["schemas"]["Project"];
export type Task = components["schemas"]["Task"];
export type TaskCreate = components["schemas"]["TaskCreate"];
export type ProjectCreate = components["schemas"]["ProjectCreate"];
export type TaskEvent = {
  from_state: string | null;
  to_state: string;
  event: string;
  metadata: unknown;
  timestamp: string;
};

const BASE = import.meta.env.VITE_NEI_API ?? "http://localhost:8000/api/v1";

async function http<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...opts?.headers },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`HTTP ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ── health ─────────────────────────────────────────────────────────────────
export async function getHealth(): Promise<{ status: string; db: boolean; timestamp: string }> {
  return http("/health");
}

// ── projects ───────────────────────────────────────────────────────────────
export async function listProjects(): Promise<Project[]> {
  return http("/projects");
}

export async function createProject(payload: ProjectCreate): Promise<Project> {
  return http("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── tasks ────────────────────────────────────────────────────────────────────
export async function createTask(projectId: string, payload: TaskCreate): Promise<Task> {
  return http(`/projects/${projectId}/tasks`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listProjectTasks(projectId: string): Promise<Task[]> {
  return http(`/projects/${projectId}/tasks`);
}

export async function getTask(taskId: string): Promise<Task> {
  return http(`/tasks/${taskId}`);
}

export async function cancelTask(taskId: string): Promise<Task> {
  return http(`/tasks/${taskId}/cancel`, { method: "POST" });
}

export async function getTaskEvents(taskId: string): Promise<TaskEvent[]> {
  return http(`/tasks/${taskId}/events_raw`);
}

// ── connectors ───────────────────────────────────────────────────────────────
export type Connector = {
  id: string;
  name: string;
  transport: string;
};

export type ProbeResult = {
  connector_id: string;
  detected: string | null;
  version: string | null;
  bitness: string | null;
  probe_ts: string;
  note: string;
};

export async function listConnectors(): Promise<Connector[]> {
  return http("/connectors");
}

export async function probeConnector(id: string): Promise<ProbeResult> {
  return http(`/connectors/${id}/probe`, { method: "POST" });
}

// ── SSE helper ───────────────────────────────────────────────────────────────
export function sseUrl(taskId: string): string {
  return `${BASE}/tasks/${taskId}/events`;
}
