// Application shell: holds the database connection state, the selected project
// and the active chapter, and wires the header, sidebar and content together.

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import ChapterView from "./components/ChapterView";
import CatalogTableView from "./components/CatalogTableView";
import Dashboard from "./components/Dashboard";
import DatabaseBrowser from "./components/DatabaseBrowser";
import ERDCanvas from "./components/ERDCanvas";
import Header from "./components/Header";
import LocationPresets from "./components/LocationPresets";
import Sidebar from "./components/Sidebar";
import type { ConnectionStatus, Row } from "./types";

const SIDEBAR_MIN = 140;
const SIDEBAR_MAX = 520;

const EMPTY_STATUS: ConnectionStatus = {
  role: "",
  connected: false,
  current: null,
  path: null,
};

export default function App() {
  const [catalogStatus, setCatalogStatus] = useState<ConnectionStatus>(EMPTY_STATUS);
  const [projectStatus, setProjectStatus] = useState<ConnectionStatus>(EMPTY_STATUS);
  const [projects, setProjects] = useState<Row[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [active, setActive] = useState<string>("database");
  const [loadError, setLoadError] = useState<string | null>(null);

  const [sidebarWidth, setSidebarWidth] = useState<number>(() => {
    const saved = localStorage.getItem("sidebarWidth");
    return saved ? Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, parseInt(saved, 10))) : 220;
  });
  const [resizing, setResizing] = useState(false);
  const sidebarWidthRef = useRef(sidebarWidth);
  useEffect(() => { sidebarWidthRef.current = sidebarWidth; }, [sidebarWidth]);

  function handleResizerMouseDown(e: React.MouseEvent) {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = sidebarWidthRef.current;
    setResizing(true);

    function onMouseMove(ev: MouseEvent) {
      const next = Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, startWidth + ev.clientX - startX));
      setSidebarWidth(next);
    }
    function onMouseUp() {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      localStorage.setItem("sidebarWidth", String(sidebarWidthRef.current));
      setResizing(false);
    }
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  }

  const loadProjects = useCallback(async () => {
    const res = await api.list("projects", { limit: 500 });
    setProjects(res.items);
    setSelectedProjectId((prev) => {
      if (prev && res.items.some((p) => p.id === prev)) return prev;
      return res.items.length ? (res.items[0].id as number) : null;
    });
  }, []);

  // Refresh both catalog + project connection statuses, and reload the project
  // list when the project DB is connected.
  const refreshConnection = useCallback(async () => {
    try {
      const combined = await api.dbStatus();
      setCatalogStatus(combined.catalog);
      setProjectStatus(combined.project);
      if (combined.project.connected) {
        await loadProjects();
      } else {
        setProjects([]);
        setSelectedProjectId(null);
      }
      setLoadError(null);
    } catch (e: any) {
      setLoadError(
        "Could not reach the backend API. Is the FastAPI server running on " +
          "port 8000?  (" + (e?.message ?? String(e)) + ")",
      );
    }
  }, [loadProjects]);

  useEffect(() => {
    refreshConnection();
  }, [refreshConnection]);

  function renderContent() {
    if (loadError) {
      return <div className="form-error">{loadError}</div>;
    }

    // The Database Browser works whether or not a database is connected.
    if (active === "database") {
      return <DatabaseBrowser onConnectionChanged={refreshConnection} />;
    }

    // Every other view needs at least one connected database (catalog views
    // need catalog; project views need project; the per-endpoint check happens
    // server-side, returning 409 when the required DB is missing).
    if (!catalogStatus.connected && !projectStatus.connected) {
      return (
        <div className="empty">
          <p>No databases are connected.</p>
          <button
            className="btn btn-primary"
            onClick={() => setActive("database")}
          >
            Open Database Browser
          </button>
        </div>
      );
    }

    if (active === "erd") {
      return <ERDCanvas />;
    }

    if (active.startsWith("group:")) {
      const groupId = parseInt(active.slice(6), 10);
      return <CatalogTableView key={groupId} groupId={groupId} />;
    }

    if (active === "dashboard") {
      if (!selectedProjectId) {
        return (
          <div className="empty">
            No project selected. Open the “Projects” chapter to create one.
          </div>
        );
      }
      return <Dashboard projectId={selectedProjectId} onNavigate={setActive} />;
    }

    const projectsExtraActions =
      active === "projects"
        ? (row: import("./types").Row) => {
            const isActive = projectStatus.current === row.project_number + ".db";
            return (
              <button
                className={"btn btn-sm" + (isActive ? " btn-primary" : "")}
                title={isActive ? "This project's database is currently active" : "Connect this project's database"}
                onClick={async () => {
                  try {
                    await api.activateProject(row.id);
                    await refreshConnection();
                  } catch (e: any) {
                    alert(e?.message ?? String(e));
                  }
                }}
              >
                {isActive ? "Active" : "Activate"}
              </button>
            );
          }
        : undefined;

    const locationHeaderExtra =
      active === "project-locations" && selectedProjectId
        ? (reload: () => void) => (
            <LocationPresets
              projectId={selectedProjectId}
              onAdded={reload}
            />
          )
        : undefined;

    return (
      <ChapterView
        // Remount when the chapter, project or database changes.
        key={`${active}:${selectedProjectId ?? "none"}:${catalogStatus.current ?? "-"}:${projectStatus.current ?? "-"}`}
        chapterKey={active}
        projectId={selectedProjectId}
        onDataChanged={loadProjects}
        extraActions={projectsExtraActions}
        headerExtra={locationHeaderExtra}
      />
    );
  }

  return (
    <div className="app">
      <Header
        projects={projects}
        selectedProjectId={selectedProjectId}
        onSelectProject={setSelectedProjectId}
        catalogStatus={catalogStatus}
        projectStatus={projectStatus}
      />
      <div className={"body" + (resizing ? " body--resizing" : "")}>
        <Sidebar active={active} onSelect={setActive} width={sidebarWidth} />
        <div
          className="sidebar-resizer"
          onMouseDown={handleResizerMouseDown}
          title="Drag to resize"
        />
        <main className="content">{renderContent()}</main>
      </div>
    </div>
  );
}
