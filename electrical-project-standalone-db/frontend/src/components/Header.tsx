// Top banner: app name, both database indicators (catalog + project), and the
// project selector.  Class B chapters are scoped to the selected project;
// Class A chapters ignore it.

import type { ConnectionStatus, Row } from "../types";

interface Props {
  projects: Row[];
  selectedProjectId: number | null;
  onSelectProject: (id: number | null) => void;
  catalogStatus: ConnectionStatus;
  projectStatus: ConnectionStatus;
}

function StatusDot({ label, status }: { label: string; status: ConnectionStatus }) {
  return (
    <div className="db-status" title={status.path ?? "Not connected"}>
      <span className={"db-dot " + (status.connected ? "db-dot-on" : "db-dot-off")} />
      {status.connected ? (
        <span>
          {label}: <strong>{status.current}</strong>
        </span>
      ) : (
        <span>{label}: <em>not connected</em></span>
      )}
    </div>
  );
}

export default function Header({
  projects,
  selectedProjectId,
  onSelectProject,
  catalogStatus,
  projectStatus,
}: Props) {
  return (
    <header className="header">
      <div className="brand">
        <span className="brand-mark">EPDB</span>
        <span className="brand-name">Electrical Project Standalone DB</span>
      </div>

      <div className="header-right">
        <StatusDot label="Catalog" status={catalogStatus} />
        <StatusDot label="Project" status={projectStatus} />

        <div className="project-picker">
          <label htmlFor="project-select">Active project:</label>
          <select
            id="project-select"
            value={selectedProjectId ?? ""}
            disabled={!projectStatus.connected}
            onChange={(e) =>
              onSelectProject(e.target.value ? Number(e.target.value) : null)
            }
          >
            {projects.length === 0 && (
              <option value="">
                {projectStatus.connected ? "No projects yet" : "—"}
              </option>
            )}
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.project_number} — {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}
