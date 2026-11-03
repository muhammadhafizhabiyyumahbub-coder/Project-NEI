import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../api/client";

export function Dashboard() {
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Dashboard</h2>
      {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : (
        <div>
          <h3 className="font-medium mb-2">Projects</h3>
          {projects && projects.length > 0 ? (
            <ul className="space-y-2">
              {projects.map((p) => (
                <li key={p.id} className="p-3 border rounded">
                  <Link to={`/projects/${p.id}`} className="font-medium hover:underline">{p.name}</Link>
                  {p.description && <div className="text-sm text-gray-500">{p.description}</div>}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No projects yet. <Link to="/projects" className="underline">Create one.</Link></p>
          )}
        </div>
      )}
    </div>
  );
}
