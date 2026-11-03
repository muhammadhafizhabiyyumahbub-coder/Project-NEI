import { useParams, Link } from "react-router-dom";
import { useProjectTasks } from "../hooks/useProjectTasks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createTask } from "../api/client";

export function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const { tasks, isLoading, error } = useProjectTasks(projectId);

  const { mutate: create, isPending } = useMutation({
    mutationFn: ({ user_request, task_type }: { user_request: string; task_type?: string }) =>
      createTask(projectId!, { user_request, task_type: task_type || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks", projectId] });
    },
  });

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Project {projectId}</h2>
      <div className="mb-4">
        <form onSubmit={(e) => { e.preventDefault(); const fd = new FormData(e.currentTarget); create({ user_request: fd.get("user_request") as string, task_type: fd.get("task_type") as string | null || undefined }); }}>
          <div className="mb-2">
            <input name="user_request" placeholder="What should the task do?" required />
          </div>
          <button type="submit" disabled={isPending}>Create Task</button>
        </form>
      </div>
      <div>
        <h3 className="font-medium mb-2">Tasks</h3>
        {isLoading ? <p>Loading...</p> : error ? <p className="text-error">Error: {error.message}</p> : (
          <ul className="space-y-2">
            {tasks.map((t) => (
              <li key={t.id} className="flex justify-between items-center p-3 border rounded">
                <Link to={`/projects/${projectId}/tasks/${t.id}`} className="font-medium hover:underline">{t.user_request}</Link>
                <span className="text-sm text-gray-500">{t.state}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}