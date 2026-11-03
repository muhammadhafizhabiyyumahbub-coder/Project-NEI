import { useTask } from "../hooks/useTask";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cancelTask } from "../api/client";
import { useParams } from "react-router-dom";

export function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>();
  const queryClient = useQueryClient();
  const { task, isLoading, error, events } = useTask(taskId);

  const { mutate: cancel, isPending: isCancelling } = useMutation({
    mutationFn: cancelTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
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
          <div>
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
