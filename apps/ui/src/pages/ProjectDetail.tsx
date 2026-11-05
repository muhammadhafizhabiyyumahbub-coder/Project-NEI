import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { createTask, listProjects } from "../api/client";
import { useProjectTasks } from "../hooks/useProjectTasks";

export function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: listProjects });
  const [taskType, setTaskType] = useState("geometry");
  const project = projects?.find((item) => item.id === projectId);
  const { tasks, isLoading, error, filter, setFilter } = useProjectTasks(projectId ?? "");
  const { mutate: create, isPending } = useMutation({
    mutationFn: ({ user_request, task_type, hull_design }: { user_request: string; task_type?: string; hull_design?: { vessel_type: string; loa: number; beam: number; depth: number; draft: number; speed: number } }) => createTask(projectId!, { user_request, task_type: task_type || undefined, hull_design }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });

  return (
    <div className="dashboard-page project-detail-page">
      <Link to="/projects" className="back-link">← Projects</Link>
      <header className="dashboard-heading">
        <div><p className="eyebrow">Project workspace</p><h2>{project?.name ?? projectId}</h2><p className="lede">{project?.description || "Local workspace for tasks, evidence, and generated artifacts."}</p></div>
      </header>
      <section className="workspace-panel task-create-panel">
        <div className="panel-heading"><div><p className="eyebrow">Next operation</p><h3>Create task</h3></div></div>
        <div className="form-body"><p className="field-note">Describe desired work. NEI creates a pending task; open it to run full planning, connector execution, and verification. Hull design is currently a schema preview; no connector is claimed until capability is tested.</p>
          <form onSubmit={(e) => { e.preventDefault(); const fd = new FormData(e.currentTarget); const request = taskType === "hull_design" ? `Design ${fd.get("vessel_type")} hull: LOA ${fd.get("loa")} m, beam ${fd.get("beam")} m, depth ${fd.get("depth")} m, draft ${fd.get("draft")} m, speed ${fd.get("speed")} kn.` : String(fd.get("user_request")); create({ user_request: request, task_type: taskType, hull_design: taskType === "hull_design" ? { vessel_type: String(fd.get("vessel_type")), loa: Number(fd.get("loa")), beam: Number(fd.get("beam")), depth: Number(fd.get("depth")), draft: Number(fd.get("draft")), speed: Number(fd.get("speed")) } : undefined }); }}>
            {taskType === "hull_design" ? <div className="hull-input-grid"><label>Vessel type<select name="vessel_type"><option>Patrol boat</option><option>Tugboat</option><option>Ferry</option><option>Fishing vessel</option><option>General cargo</option></select></label><label>LOA (m)<input name="loa" type="number" min="0.01" step="any" required /></label><label>Beam (m)<input name="beam" type="number" min="0.01" step="any" required /></label><label>Depth (m)<input name="depth" type="number" min="0.01" step="any" required /></label><label>Draft (m)<input name="draft" type="number" min="0.01" step="any" required /></label><label>Speed (kn)<input name="speed" type="number" min="0" step="any" required /></label></div> : <input className="task-request-input" name="user_request" placeholder="Example: inspect active SOLIDWORKS document metadata" required />}
            <div className="task-form-row"><select aria-label="Task type" value={taskType} onChange={(e) => setTaskType(e.target.value)}><option value="geometry">Geometry / inspection</option><option value="calculation">Engineering calculation</option><option value="hull_design">Hull design (schema preview)</option></select><button type="submit" className="primary-action" disabled={isPending}>{isPending ? "Creating..." : "Create task"}</button></div>
          </form>
        </div>
      </section>
      <section className="workspace-panel project-tasks-panel">
        <div className="panel-heading"><div><p className="eyebrow">Execution queue</p><h3>Tasks</h3></div><select aria-label="Filter tasks" value={filter} onChange={(e) => setFilter(e.target.value)}><option value="all">All tasks</option><option value="active">Active</option><option value="completed">Completed</option><option value="failed">Failed</option></select></div>
        {isLoading ? <div className="state-panel">Loading tasks...</div> : error ? <div className="state-panel error-state">Could not load tasks: {error.message}</div> : tasks.length ? <div className="task-list">{tasks.map((task) => <Link className="task-row" key={task.id} to={`/projects/${projectId}/tasks/${task.id}`}><span><strong>{task.user_request}</strong><small>{task.task_type} · {task.risk_level} risk</small></span><em className={`task-state state-${task.state}`}>{task.state}</em></Link>)}</div> : <div className="state-panel"><strong>No tasks match filter.</strong><span>Create task above or choose All tasks.</span></div>}
      </section>
    </div>
  );
}
