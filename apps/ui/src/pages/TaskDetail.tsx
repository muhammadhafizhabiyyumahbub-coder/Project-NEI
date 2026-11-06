import { useTask } from "../hooks/useTask";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cancelTask, executeTask, verifyTask, runTask, getCalculationRun, getTaskEvidence, getTaskArtifacts, getTaskApproval, getVerificationSummary, type CalculationRun } from "../api/client";
import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";

export function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>();
  const queryClient = useQueryClient();
  const { task, isLoading, error, events } = useTask(taskId);
  const { data: evidence = [] } = useQuery({
    queryKey: ["task-evidence", taskId],
    queryFn: () => getTaskEvidence(taskId!),
    enabled: !!taskId,
  });
  const { data: artifacts = [] } = useQuery({
    queryKey: ["task-artifacts", taskId],
    queryFn: () => getTaskArtifacts(taskId!),
    enabled: !!taskId,
  });
  const { data: approvals = [] } = useQuery({
    queryKey: ["task-approval", taskId],
    queryFn: () => getTaskApproval(taskId!),
    enabled: !!taskId,
  });
  const { data: summary } = useQuery({
    queryKey: ["verification-summary", taskId],
    queryFn: () => getVerificationSummary(taskId!),
    enabled: !!taskId,
  });
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);
  const [calcRun, setCalcRun] = useState<CalculationRun | null>(null);

  useEffect(() => {
    if (!task?.calc_run_ids) return;
    try {
      const ids = JSON.parse(task.calc_run_ids) as string[];
      if (ids[0]) getCalculationRun(ids[0]).then(setCalcRun).catch(() => setCalcRun(null));
    } catch { setCalcRun(null); }
  }, [task?.calc_run_ids]);

  const { mutate: cancel, isPending: isCancelling } = useMutation({
    mutationFn: cancelTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  const { mutate: runTaskFull, isPending: isRunningFull } = useMutation({
    mutationFn: () => runTask(taskId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  const { mutate: runAction, isPending: isRunning } = useMutation({
    mutationFn: ({ action, params }: { action: string; params?: Record<string, unknown> }) =>
      executeTask(taskId!, { action, params }),
    onSuccess: (data) => {
      setLastResult(data as unknown as Record<string, unknown>);
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });

  const { mutate: runVerify, isPending: isVerifying } = useMutation({
    mutationFn: (body: { connector_result?: Record<string, unknown>; software_version?: string; length?: number; width?: number; height?: number }) =>
      verifyTask(taskId!, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Task {taskId}</h2>
      {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : task && (
        <div>
          <div className="mb-4 p-4 border rounded">
            <div className="flex justify-between items-center mb-2">
              <span className="font-medium">{task.user_request}</span>
              <button onClick={() => cancel(taskId!)} disabled={isCancelling} className="text-error">Cancel</button>
            </div>
            <div className="text-sm flex gap-4">
              <div><span>State:</span> <span className="ml-2 font-mono">{task.state}</span></div>
              <div><span>Domain:</span> <span className="ml-2">{task.domain}</span></div>
              <div><span>Risk:</span> <span className="ml-2">{task.risk_level}</span></div>
            </div>
          </div>

          <div className="mb-4 p-4 border rounded">
            <h3 className="font-medium mb-2">Workflow controls</h3>
            <p className="text-sm text-gray-500 mb-3">Run Full Flow executes planning, connector action, and verification for this pending task. Other buttons run one connector operation only; they do not complete the full task flow.</p>
            <div className="workflow-steps" aria-label="Task workflow"><span className={task.state === "pending" ? "active" : ""}>1. Pending</span><span className={task.state === "planning" ? "active" : ""}>2. Planning</span><span className={task.state === "running" ? "active" : ""}>3. Running</span><span className={task.state === "verifying" ? "active" : ""}>4. Verifying</span><span className={task.state === "completed" ? "active" : ""}>5. Completed</span></div>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => runTaskFull()}
                disabled={isRunningFull || task.state !== "pending"}
                className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm font-medium"
                title="Drive pending task through plan → execute → verify (PENDING only)"
              >
                Run Full Flow
              </button>
              <button onClick={() => runAction({ action: "rhino.get_document_info" })} disabled={isRunning} className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm">
                Get Document Info
              </button>
              <button onClick={() => runAction({ action: "rhino.create_box_test", params: { length: 10, width: 3, height: 1 } })} disabled={isRunning} className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm">
                Create Box 10×3×1
              </button>
              <button onClick={() => runAction({ action: "rhino.inspect_objects", params: {} })} disabled={isRunning} className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm">
                Inspect Objects
              </button>
              <button
                onClick={() => runVerify({
                  connector_result: (lastResult?.data as Record<string, unknown>) ?? {},
                  software_version: "Rhino 6",
                  length: 10, width: 3, height: 1,
                })}
                disabled={isVerifying}
                className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm"
              >
                Verify
              </button>
            </div>
            {isRunningFull && <p className="mt-2 text-sm text-gray-400">Running full flow…</p>}
            {isRunning && <p className="mt-2 text-sm text-gray-400">Running…</p>}
            {lastResult && (
              <pre className="mt-2 text-xs bg-black/30 p-2 rounded overflow-auto max-h-60">{JSON.stringify(lastResult, null, 2)}</pre>
            )}
          </div>

          <div className="task-output-grid">
            <section className="output-panel"><h3>Hull Preview</h3>{task.task_type === "hull_design" ? <pre>{calcRun ? JSON.stringify({ status: calcRun.status, inputs: calcRun.inputs, result: calcRun.result }, null, 2) : task.plan_json ? (() => { try { const plan = JSON.parse(task.plan_json); return plan.notes || "Hull calculation pending"; } catch { return "Hull data parsing error"; } })() : "No hull data."}</pre> : <span className="quiet-text">Not a hull design task.</span>}</section>
            <section className="output-panel"><h3>Plan</h3><pre>{task.plan_json ? (() => { try { return JSON.stringify(JSON.parse(task.plan_json), null, 2); } catch { return task.plan_json; } })() : "No plan recorded yet."}</pre></section>
            <section className="output-panel"><h3>Errors</h3><pre>{task.errors_json ? (() => { try { return JSON.stringify(JSON.parse(task.errors_json), null, 2); } catch { return task.errors_json; } })() : "No errors recorded."}</pre></section>
          </div>
          <div>
            <h3 className="font-medium mb-2">Task Evidence</h3>
             {summary && <div className="mb-2 text-xs text-gray-500">Readiness: {summary.overall_status} · Verification: {summary.verification_status} · Hydrostatics: {summary.hydrostatics_status} · Stability: {summary.stability_status}{summary.approval_artifact_sha256 ? ` · Approval SHA-256: ${summary.approval_artifact_sha256.slice(0, 12)}…` : ""}</div>}
             {approvals.length > 0 && <div className="mb-2 text-xs text-gray-500">Engineering approval: {approvals[0].status}{approvals[0].reason ? ` — ${approvals[0].reason}` : ""}</div>}
             {artifacts.length > 0 && <div className="mb-2 text-xs text-gray-500">Artifacts: {artifacts.map((a) => `${a.filename} (${a.sha256.slice(0, 12)}…)`).join(", ")}</div>}
             {evidence.length === 0 ? <p className="text-gray-500">No evidence linked.</p> : <ul className="space-y-2">{evidence.map((item) => <li key={item.id} className="text-sm p-2 border rounded"><div className="flex justify-between"><span className="font-medium">{item.capability_name}</span><span className="text-gray-500">{item.evidence_type}</span></div>{item.artifact_path && <div className="text-xs text-gray-500 break-all">{item.artifact_path}</div>}{item.artifact_sha256 && <div className="text-xs font-mono text-gray-400 break-all">SHA-256: {item.artifact_sha256}</div>}{item.notes && <div className="text-xs text-gray-500">{item.notes}</div>}</li>)}</ul>}
             <h3 className="font-medium mb-2">Events</h3>
            {events.length === 0 ? <p className="text-gray-500">No events.</p> : (
              <ul className="space-y-2">
                {events.map((e, i) => (
                  <li key={i} className="text-sm p-2 border rounded">
                    <span className="font-mono">{e.event}</span>
                    <span className="ml-2 text-gray-500">{e.from_state ?? "null"} → {e.to_state}</span>
                    <span className="ml-2 text-gray-400">{e.timestamp}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
