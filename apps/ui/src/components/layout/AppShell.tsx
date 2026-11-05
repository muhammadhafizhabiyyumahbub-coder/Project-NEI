import { Link, Outlet, useLocation } from "react-router-dom";
import { useState } from "react";
import { useHealth } from "../../hooks/useHealth";
import { useConnectors } from "../../hooks/useConnectors";
import { LayoutDashboard, Folder, Plug, Settings, BookOpen, Calculator } from "lucide-react";

// Sidebar navigation items
const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/projects", icon: Folder, label: "Projects" },
  { to: "/connectors", icon: Plug, label: "Connectors" },
  { to: "/evidence", icon: BookOpen, label: "Evidence" },
  { to: "/calculations", icon: Calculator, label: "Calculations" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function AppShell() {
  const { health } = useHealth();
  const { connectors } = useConnectors();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className={`flex flex-col h-full border-r border-border transition-all duration-300 ${collapsed ? "w-16" : "w-64"}`}>
        <div className="flex items-center justify-between p-4 border-b border-border">
          {!collapsed && (
            <h1 className="text-lg font-bold">NEI</h1>
          )}
          <button
            type="button"
            aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
            onClick={() => setCollapsed(!collapsed)}
            className="shell-toggle"
          >
            {collapsed ? "→" : "←"}
          </button>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 p-2 rounded-md transition-colors ${location.pathname === item.to ? "bg-accent text-accent-foreground" : "hover:bg-accent/50"}`}
            >
              <item.icon className="w-5 h-5" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            {health && <span className={`text-sm font-medium ${health.status === "healthy" ? "text-success" : "text-error"}`}>{health.status}</span>}
            {connectors.map((c) => (
              <div
                key={c.id}
                className={`w-3 h-3 rounded-full ${c.status === "DETECTED" ? "bg-success" : "bg-error"}`}
                title={`${c.name}: ${c.status ?? "unknown"}`}
              />
            ))}
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
