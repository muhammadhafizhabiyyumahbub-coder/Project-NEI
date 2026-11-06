// NEI frontend API client.
//
// Types are hand-written minimal interfaces here. When OpenAPI generation is
// wired (see repo root: curl /openapi.json + npx openapi-typescript), replace
// these with generated types in src/api/types.ts.

const BASE = import.meta.env.VITE_NEI_API ?? "http://localhost:8000/api/v1";

// ── Types ──────────────────────────────────────────────────────────────────
export type Project = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  path_root: string;
};

export type ProjectCreate = { name: string; description?: string | null };

export type Task = {
  id: string;
  project_id: string;
  parent_task_id: string | null;
  user_request: string;
  task_type: string;
  domain: string;
  risk_level: string;
  state: string;
  plan_json: string | null;
  verification_json: string | null;
  errors_json: string | null;
  calc_run_ids: string | null;
  hull_design_json: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type TaskCreate = {
  user_request: string;
  task_type?: string;
  domain?: string;
  risk_level?: string;
  hull_design?: {
    vessel_type: string;
    loa: number;
    beam: number;
    depth: number;
    draft: number;
    speed: number;
    block_coefficient?: number;
  };
};

export type TaskEvent = {
  from_state: string | null;
  to_state: string;
  event: string;
  metadata: unknown;
  timestamp: string;
};

export type Connector = { id: string; name: string; transport: string; status?: string | null };

export type ConnectorCapability = {
  name: string;
  status: "SUPPORTED" | "UNSUPPORTED" | "UNKNOWN" | "UNAVAILABLE";
  version_tested: string | null;
  notes: string | null;
  evidence?: { count: number; last_verified_at: string | null };
};

export type ProbeResult = {
  connector_id: string;
  detected: string | null;
  version: string | null;
  bitness: string | null;
  probe_ts: string;
  note: string;
};

export type EvidenceSource = {
  id: string;
  title: string;
  source_type: string;
  authority_level: string;
  local_file_path: string;
  checksum_sha256: string;
  ingested_at: string;
  verification_status: string;
};

export type EvidenceSearchResult = {
  chunk_id: string;
  page: number | null;
  section: string | null;
  clause: string | null;
  equation_no: string | null;
  text: string;
  source_id: string;
  source_title: string;
  verification_status: string;
  citation?: string;
};

export type Formula = {
  id: string;
  name: string;
  domain: string;
  equation_text: string;
  review_status: string;
  version: number;
  created_at: string;
  variables?: Array<Record<string, unknown>>;
  canonical_units?: string;
};

export type CalcRun = {
  id: string;
  formula_id: string;
  formula_name: string;
  inputs: Record<string, unknown>;
  result: unknown;
  evidence_status: string;
  formula_review_status?: string;
  deterministic_hash?: string;
  run_id: string;
  created_at: string;
};

// ── http helper ─────────────────────────────────────────────────────────────
async function http<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...opts?.headers },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.text();
    let detail = body;
    try {
      const j = JSON.parse(body);
      detail = j.detail ?? j.message ?? body;
    } catch { /* keep raw */ }
    throw new Error(`HTTP ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ── health ─────────────────────────────────────────────────────────────────
export async function getHealth(): Promise<{ status: string; db: boolean; timestamp: string }> {
  return http("/health");
}

// ── projects ───────────────────────────────────────────────────────────────
export type Capability = { name: string; status: string; connector_id?: string; version_tested?: string | null; notes?: string | null };

export async function listCapabilities(): Promise<{ capabilities: Capability[] }> {
  return http("/capabilities");
}

export async function listProjects(): Promise<Project[]> {
  return http("/projects");
}

export async function createProject(payload: ProjectCreate): Promise<Project> {
  return http("/projects", { method: "POST", body: JSON.stringify(payload) });
}

// ── tasks ──────────────────────────────────────────────────────────────────
export async function createTask(projectId: string, payload: TaskCreate): Promise<Task> {
  return http(`/projects/${projectId}/tasks`, { method: "POST", body: JSON.stringify(payload) });
}

export async function listProjectTasks(projectId: string): Promise<Task[]> {
  return http(`/projects/${projectId}/tasks`);
}

export async function getTask(taskId: string): Promise<Task> {
  return http(`/tasks/${taskId}`);
}

export type CalculationRun = {
  id: string;
  task_id: string;
  formula_id: string;
  inputs: Record<string, unknown>;
  result: Record<string, unknown>;
  status: string;
  trace: Record<string, unknown>;
  created_at: string;
};

export async function getCalculationRun(runId: string): Promise<CalculationRun> {
  return http(`/calculations/${runId}`);
}

export async function cancelTask(taskId: string): Promise<Task> {
  return http(`/tasks/${taskId}/cancel`, { method: "POST" });
}

export async function executeTask(
  taskId: string,
  body: { action: string; params?: Record<string, unknown> },
): Promise<{ success: boolean; object_ids: string[]; data: Record<string, unknown>; error: string | null }> {
  return http(`/tasks/${taskId}/execute`, { method: "POST", body: JSON.stringify(body) });
}

export async function verifyTask(
  taskId: string,
  body: {
    connector_result?: Record<string, unknown>;
    software_version?: string;
    length?: number;
    width?: number;
    height?: number;
  },
): Promise<Task> {
  return http(`/tasks/${taskId}/verify`, { method: "POST", body: JSON.stringify(body) });
}

export async function runTask(
  taskId: string,
): Promise<Task> {
  return http(`/tasks/${taskId}/run`, { method: "POST" });
}

export async function getTaskEvents(taskId: string): Promise<TaskEvent[]> {
  return http(`/tasks/${taskId}/events_raw`);
}

export type TaskEvidence = {
  id: string;
  connector_id: string;
  capability_name: string;
  evidence_type: string;
  artifact_path: string | null;
  artifact_sha256: string | null;
  metadata: Record<string, unknown> | null;
  verified_at: string;
  verified_by: string;
  notes: string | null;
};

export async function getTaskEvidence(taskId: string): Promise<TaskEvidence[]> {
  return http(`/tasks/${taskId}/evidence`);
}

export type TaskArtifact = { filename: string; path: string; sha256: string; size_bytes: number; created_at: string };

export async function getTaskArtifacts(taskId: string): Promise<TaskArtifact[]> {
  return http(`/tasks/${taskId}/artifacts`);
}

export type EngineeringApproval = { id: string; task_id: string; artifact_sha256: string | null; status: string; reviewed_by: string | null; reason: string; created_at: string; reviewed_at: string | null };

export async function getTaskApproval(taskId: string): Promise<EngineeringApproval[]> {
  return http(`/tasks/${taskId}/approval`);
}

export async function createTaskApproval(taskId: string, body: { status: string; reviewed_by?: string; reason?: string; artifact_sha256?: string }): Promise<EngineeringApproval> {
  return http(`/tasks/${taskId}/approval`, { method: "POST", body: JSON.stringify(body) });
}

export type VerificationSummary = { task_id: string; artifact_integrity: boolean | string; volume_consistency: string; verification_status: string; reopen_verified: boolean; hydrostatics_status: string; stability_status: string; metacentric_height_m: number | null; loading_conditions: Array<{ id: string; gm_m: number | null; status: string }>; loading_status: string; mass_status: string; longitudinal_status: string; fairness_status: string; engineering_approval: string; approval_artifact_sha256: string | null; overall_status: string };

export async function getVerificationSummary(taskId: string): Promise<VerificationSummary> {
  return http(`/tasks/${taskId}/verification-summary`);
}

export function artifactDownloadUrl(taskId: string, filename: string): string {
  return `${BASE}/tasks/${taskId}/artifacts/${encodeURIComponent(filename)}`;
}

// ── connectors ──────────────────────────────────────────────────────────────
export async function listConnectors(): Promise<Connector[]> {
  return http("/connectors");
}

export async function probeConnector(id: string): Promise<ProbeResult> {
  return http(`/connectors/${id}/probe`, { method: "POST" });
}

export async function getConnectorCapabilities(id: string): Promise<{ connector_id: string; capabilities: ConnectorCapability[] }> {
  return http(`/connectors/${id}/capabilities`);
}

// ── evidence (Phase 4) ──────────────────────────────────────────────────────
export async function listEvidenceSources(): Promise<EvidenceSource[]> {
  return http("/evidence/sources");
}

export async function getEvidenceSource(id: string): Promise<EvidenceSource> {
  return http(`/evidence/sources/${id}`);
}

export async function getConnectorEvidence(connectorId: string, capability?: string): Promise<{ connector_id: string; evidence: { id: string; capability_name: string; evidence_type: string; artifact_path: string | null; artifact_sha256: string | null; metadata: Record<string, unknown> | null; verified_at: string; verified_by: string; notes: string | null }[] }> {
  const url = capability
    ? `/connectors/${connectorId}/evidence?capability=${encodeURIComponent(capability)}`
    : `/connectors/${connectorId}/evidence`;
  return http(url);
}

export async function searchEvidence(query: string, sourceId?: string, limit = 20) {
  return http<EvidenceSearchResult[]>("/evidence/search", {
    method: "POST",
    body: JSON.stringify({ query, source_id: sourceId ?? null, limit }),
  });
}

// ── formulas + calculations (Phase 5) ─────────────────────────────────────
export async function listFormulas(domain?: string, status?: string): Promise<Formula[]> {
  const q = new URLSearchParams();
  if (domain) q.set("domain", domain);
  if (status) q.set("status", status);
  const qs = q.toString();
  return http(`/formulas${qs ? `?${qs}` : ""}`);
}

export async function getFormula(id: string): Promise<Formula & Record<string, unknown>> {
  return http(`/formulas/${id}`);
}

export async function runCalculation(body: {
  formula_id: string;
  inputs: Record<string, unknown>;
  task_id?: string | null;
  research?: boolean;
}): Promise<CalcRun> {
  return http("/calculations", { method: "POST", body: JSON.stringify(body) });
}

// ── SSE helper ───────────────────────────────────────────────────────────────
export function sseUrl(taskId: string): string {
  return `${BASE}/tasks/${taskId}/events`;
}

export function sseTaskEvents(taskId: string): string {
  return `${BASE}/events?task_id=${encodeURIComponent(taskId)}`;
}
