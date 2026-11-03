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
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Projects</h2>
      <div className="mb-4 p-4 border rounded">
        <h3 className="font-medium mb-2">Create Project</h3>
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
      <h3 className="font-medium mb-2">Projects</h3>
      {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : (
        <ul className="space-y-2">
          {projects?.map((p) => (
            <li key={p.id} className="flex justify-between items-center p-3 border rounded">
              <Link to={`/projects/${p.id}`} className="font-medium hover:underline">{p.name}</Link>
              <span className="text-sm text-gray-500">{p.created_at}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
