import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, Link } from "react-router-dom";
import { listProjects, createProject } from "../api/client";

export function Projects() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: projects, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  const { mutate: create, isPending } = useMutation({
    mutationFn: createProject,
    onSuccess: (p) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      navigate(`/projects/${p.id}`);
    },
  });

  return (
    <div className="dashboard-page projects-page">
      <header className="dashboard-heading">
        <div><p className="eyebrow">Engineering workspace</p><h2>Projects</h2><p className="lede">Create project container, then describe work as task for planning, connector execution, and verification.</p></div>
      </header>
      <div className="workspace-panel project-create-panel">
        <div className="panel-heading"><div><p className="eyebrow">Project setup</p><h3>Create project</h3></div></div>
        <div className="form-body"><p className="field-note">Project stores tasks, evidence, and generated artifacts in its local workspace. It does not open or modify original CAD files.</p>
        <form onSubmit={(e) => { e.preventDefault(); const fd = new FormData(e.currentTarget); create({ name: fd.get("name") as string, description: fd.get("description") as string || null }); }}>
          <div className="mb-2">
            <label className="block text-sm font-medium mb-1">Name</label>
            <input name="name" className="w-full p-2 border rounded" required />
          </div>
          <div className="mb-2">
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea name="description" className="w-full p-2 border rounded" />
          </div>
          <button type="submit" disabled={isPending} className="px-4 py-2 bg-primary text-primary-foreground rounded">
            {isPending ? "Creating..." : "Create"}
          </button>
        </form>
        </div>
      </div>
      <section className="workspace-panel project-list-panel">
        <div className="panel-heading"><div><p className="eyebrow">Local workspaces</p><h3>Projects</h3></div>{projects && <span className="quiet-count">{projects.length} loaded</span>}</div>
      {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : (
        <ul className="space-y-2">
          {projects?.map((p) => (
            <li key={p.id} className="project-card">
              <div className="project-card-copy"><Link to={`/projects/${p.id}`} className="font-medium hover:underline">{p.name}</Link><span>{p.description || "No description yet."}</span><small>Created {new Date(p.created_at).toLocaleString()}</small></div>
              <Link className="row-arrow" to={`/projects/${p.id}`}>Open workspace</Link>
            </li>
          ))}
        </ul>
      )}
      </section>
    </div>
  );
}
