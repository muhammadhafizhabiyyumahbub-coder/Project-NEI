import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { Projects } from "./pages/Projects";
import { ProjectDetail } from "./pages/ProjectDetail";
import { TaskDetail } from "./pages/TaskDetail";
import { Connectors } from "./pages/Connectors";
import { Settings } from "./pages/Settings";
import { Evidence } from "./pages/Evidence";
import { Calculations } from "./pages/Calculations";

const queryClient = new QueryClient();

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "projects", element: <Projects /> },
      { path: "projects/:projectId", element: <ProjectDetail /> },
      { path: "projects/:projectId/tasks/:taskId", element: <TaskDetail /> },
      { path: "connectors", element: <Connectors /> },
      { path: "settings", element: <Settings /> },
      { path: "evidence", element: <Evidence /> },
      { path: "calculations", element: <Calculations /> },
    ],
  },
]);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

export default App;
