// Application shell: holds the database connection state, the selected project
// and the active chapter, and wires the header, sidebar and content together.

import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import ChapterView from "./components/ChapterView";
import Dashboard from "./components/Dashboard";
import DatabaseBrowser from "./components/DatabaseBrowser";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import type { ConnectionStatus, Row } from "./types";

export default function App() {
  const [dbStatus, setDbStatus] = useState<ConnectionStatus>({
    connected: false,
    current: null,
    path: null,
  });
  const [projects, setProjects] = useState<Row[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [active, setActive] = useState<string>("database");
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    const res = await api.list("projects", { limit: 500 });
    setProjects(res.items);
    setSelectedProjectId((prev) => {
      if (prev && res.items.some((p) => p.id === prev)) return prev;
      return res.items.length ? (res.items[0].id as number) : null;
    });
  }, []);

  // Refresh the connection status, and the project list when connected.
  const refreshConnection = useCallback(async () => {
    try {
      const status = await api.databases.status();
      setDbStatus(status);
      if (status.connected) {
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

    // Every other view needs a connected database.
    if (!dbStatus.connected) {
      return (
        <div className="empty">
          <p>No database is connected.</p>
          <button
            className="btn btn-primary"
            onClick={() => setActive("database")}
          >
            Open Database Browser
          </button>
        </div>
      );
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

    return (
      <ChapterView
        // Remount when the chapter, project or database changes.
        key={`${active}:${selectedProjectId ?? "none"}:${dbStatus.current ?? "none"}`}
        chapterKey={active}
        projectId={selectedProjectId}
        onDataChanged={loadProjects}
      />
    );
  }

  return (
    <div className="app">
      <Header
        projects={projects}
        selectedProjectId={selectedProjectId}
        onSelectProject={setSelectedProjectId}
        dbStatus={dbStatus}
      />
      <div className="body">
        <Sidebar active={active} onSelect={setActive} />
        <main className="content">{renderContent()}</main>
      </div>
    </div>
  );
}
