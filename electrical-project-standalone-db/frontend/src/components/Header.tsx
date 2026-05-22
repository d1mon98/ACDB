// Top banner: the application name, the active-database indicator, and the
// project selector.  Class B chapters are scoped to the selected project;
// Class A chapters ignore it.

import type { ConnectionStatus, Row } from "../types";

interface Props {
  projects: Row[];
  selectedProjectId: number | null;
  onSelectProject: (id: number | null) => void;
  dbStatus: ConnectionStatus;
}

export default function Header({
  projects,
  selectedProjectId,
  onSelectProject,
  dbStatus,
}: Props) {
  return (
    <header className="header">
      <div className="brand">
        <span className="brand-mark">EPDB</span>
        <span className="brand-name">Electrical Project Standalone DB</span>
      </div>

      <div className="header-right">
        <div className="db-status">
          <span
            className={
              "db-dot " + (dbStatus.connected ? "db-dot-on" : "db-dot-off")
            }
          />
          {dbStatus.connected ? (
            <span>
              Database: <strong>{dbStatus.current}</strong>
            </span>
          ) : (
            <span>No database connected</span>
          )}
        </div>

        <div className="project-picker">
          <label htmlFor="project-select">Active project:</label>
          <select
            id="project-select"
            value={selectedProjectId ?? ""}
            disabled={!dbStatus.connected}
            onChange={(e) =>
              onSelectProject(e.target.value ? Number(e.target.value) : null)
            }
          >
            {projects.length === 0 && (
              <option value="">
                {dbStatus.connected ? "No projects yet" : "—"}
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
