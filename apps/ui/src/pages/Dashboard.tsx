import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../api/client";
import { CapabilityStatus } from "../components/CapabilityStatus";

const SketchLine = ({ className = "" }: { className?: string }) => (
  <span aria-hidden="true" className={`sketch-line ${className}`} />
);

export function Dashboard() {
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  return (
    <div className="dashboard-page">
      <header className="dashboard-heading">
        <div>
          <p className="eyebrow">Engineering workspace</p>
          <h2>Workspace overview</h2>
          <p className="lede">Projects, evidence, and connector readiness in one working view.</p>
        </div>
        <Link className="primary-action" to="/projects">Open projects</Link>
      </header>

      <section className="signal-strip" aria-label="Workspace signals">
        <div><span className="signal-label">Mode</span><strong>Local first</strong></div>
        <div><span className="signal-label">Evidence</span><strong>Traceable</strong></div>
        <div><span className="signal-label">Connectors</span><strong>Read only</strong></div>
      </section>

      <section className="workspace-panel" aria-labelledby="capability-heading">
        <div className="panel-heading"><div><p className="eyebrow">Connector readiness</p><h3 id="capability-heading">Hull capabilities</h3></div></div>
        <CapabilityStatus />
      </section>

      <section className="workspace-panel" aria-labelledby="projects-heading">
        <div className="panel-heading">
          <div><p className="eyebrow">Current work</p><h3 id="projects-heading">Projects</h3></div>
          {projects && <span className="quiet-count">{projects.length} loaded</span>}
        </div>
        {isLoading ? (
          <div className="project-list" aria-label="Loading projects">
            {[1, 2, 3].map((item) => <div className="project-row sketch-loading" key={item}><SketchLine className="wide" /><SketchLine /><SketchLine className="short" /></div>)}
          </div>
        ) : error ? (
          <div className="state-panel error-state"><strong>Projects could not load.</strong><span>{error.message}</span></div>
        ) : projects && projects.length > 0 ? (
          <div className="project-list">
            {projects.map((project) => (
              <Link className="project-row" key={project.id} to={`/projects/${project.id}`}>
                <span className="project-mark" aria-hidden="true" />
                <span className="project-copy"><strong>{project.name}</strong>{project.description && <span>{project.description}</span>}</span>
                <span className="row-arrow" aria-hidden="true">View</span>
              </Link>
            ))}
          </div>
        ) : (
          <div className="state-panel"><strong>No projects yet.</strong><Link to="/projects">Create first project</Link></div>
        )}
      </section>
    </div>
  );
}
