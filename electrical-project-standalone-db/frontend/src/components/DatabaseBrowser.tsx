// Database Browser -- manage database files and the active connection.
//
// Databases in the managed project folder can be created, renamed, deleted and
// connected.  A database file anywhere on disk can be opened with the file
// picker, and recently opened databases are listed for quick reconnection.

import { useEffect, useState } from "react";
import { api } from "../api";
import type { DatabaseInfo, RecentDatabase } from "../types";
import FileBrowserModal from "./FileBrowserModal";

interface Props {
  /** Called after any operation so the app can refresh its connection state. */
  onConnectionChanged: () => void;
}

interface NameModalState {
  mode: "create" | "rename";
  target?: string; // existing filename, for rename
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export default function DatabaseBrowser({ onConnectionChanged }: Props) {
  const [items, setItems] = useState<DatabaseInfo[]>([]);
  const [recent, setRecent] = useState<RecentDatabase[]>([]);
  const [currentPath, setCurrentPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [modal, setModal] = useState<NameModalState | null>(null);
  const [nameInput, setNameInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [fileBrowserOpen, setFileBrowserOpen] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.databases.list();
      setItems(data.items);
      setRecent(data.recent);
      setCurrentPath(data.path);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // Run an operation, then refresh this view and notify the app.
  async function run(op: () => Promise<unknown>) {
    setError(null);
    try {
      await op();
      await load();
      onConnectionChanged();
    } catch (e: any) {
      setError(e?.message ?? String(e));
    }
  }

  function handleConnect(name: string) {
    run(() => api.databases.connect(name));
  }

  function handleDisconnect() {
    run(() => api.databases.disconnect());
  }

  function handleOpenPath(path: string) {
    run(() => api.databases.open(path));
  }

  function handleDelete(name: string) {
    if (
      window.confirm(
        `Delete database "${name}"?\n\nThis permanently removes the file and ` +
          `all data in it. This cannot be undone.`,
      )
    ) {
      run(() => api.databases.remove(name));
    }
  }

  function openCreate() {
    setNameInput("");
    setError(null);
    setModal({ mode: "create" });
  }

  function openRename(name: string) {
    setNameInput(name.replace(/\.db$/i, ""));
    setError(null);
    setModal({ mode: "rename", target: name });
  }

  async function submitModal() {
    if (!modal) return;
    setBusy(true);
    setError(null);
    try {
      if (modal.mode === "create") {
        await api.databases.create(nameInput);
      } else {
        await api.databases.rename(modal.target!, nameInput);
      }
      setModal(null);
      await load();
      onConnectionChanged();
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleFileOpened() {
    setFileBrowserOpen(false);
    await load();
    onConnectionChanged();
  }

  return (
    <div className="chapter">
      <div className="chapter-head">
        <div>
          <h2>Database Browser</h2>
          <div className="chapter-sub">
            Connect, create, open, rename and delete project databases
          </div>
        </div>
        <div className="toolbar-actions">
          <button className="btn" onClick={() => setFileBrowserOpen(true)}>
            Open from File System…
          </button>
          <button className="btn btn-primary" onClick={openCreate}>
            + Create Database
          </button>
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}

      {currentPath ? (
        <div className="connected-banner">
          <span>
            <span className="badge badge-connected">Connected</span>{" "}
            <strong>{currentPath}</strong>
          </span>
          <button className="btn btn-sm" onClick={handleDisconnect}>
            Disconnect
          </button>
        </div>
      ) : (
        <div className="connected-banner connected-banner-off">
          No database connected.
        </div>
      )}

      {loading && <div className="empty">Loading…</div>}

      {/* --- managed project-folder databases --- */}
      {!loading && (
        <>
          <div className="section-label">Databases in the project folder</div>
          {items.length === 0 ? (
            <div className="empty">
              No databases in the project folder. Use “+ Create Database”.
            </div>
          ) : (
            <div className="grid-wrap">
              <table className="grid">
                <thead>
                  <tr>
                    <th>Database</th>
                    <th>Size</th>
                    <th>Last Modified</th>
                    <th>Status</th>
                    <th className="col-actions">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((db) => (
                    <tr key={db.path}>
                      <td>
                        <strong>{db.name}</strong>
                      </td>
                      <td>{formatSize(db.size_bytes)}</td>
                      <td>{formatDate(db.modified)}</td>
                      <td>
                        {db.connected ? (
                          <span className="badge badge-connected">
                            Connected
                          </span>
                        ) : (
                          <span className="muted">Not connected</span>
                        )}
                      </td>
                      <td className="col-actions">
                        {db.connected ? (
                          <button
                            className="btn btn-sm"
                            onClick={handleDisconnect}
                          >
                            Disconnect
                          </button>
                        ) : (
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => handleConnect(db.name)}
                          >
                            Connect
                          </button>
                        )}
                        <button
                          className="btn btn-sm"
                          onClick={() => openRename(db.name)}
                        >
                          Rename
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDelete(db.name)}
                          disabled={db.connected}
                          title={
                            db.connected
                              ? "Disconnect before deleting"
                              : "Delete this database"
                          }
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* --- recently opened databases (incl. external files) --- */}
          {recent.length > 0 && (
            <>
              <div className="section-label">Recent databases</div>
              <div className="grid-wrap">
                <table className="grid">
                  <tbody>
                    {recent.map((r) => (
                      <tr key={r.path}>
                        <td>
                          <strong>{r.name}</strong>
                        </td>
                        <td className="recent-path" title={r.path}>
                          {r.path}
                        </td>
                        <td className="col-actions">
                          {r.path === currentPath ? (
                            <span className="badge badge-connected">
                              Connected
                            </span>
                          ) : r.exists ? (
                            <button
                              className="btn btn-sm btn-primary"
                              onClick={() => handleOpenPath(r.path)}
                            >
                              Open
                            </button>
                          ) : (
                            <span className="muted">Missing</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}

      {modal && (
        <div className="modal-overlay" onClick={() => !busy && setModal(null)}>
          <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {modal.mode === "create"
                  ? "Create Database"
                  : `Rename “${modal.target}”`}
              </h3>
              <button
                className="btn-icon"
                onClick={() => !busy && setModal(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              <div className="field">
                <label>
                  Database name<span className="req">*</span>
                </label>
                <input
                  className="input"
                  autoFocus
                  value={nameInput}
                  placeholder="e.g. flat-creek-wrf"
                  onChange={(e) => setNameInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !busy) submitModal();
                  }}
                />
                <div className="field-hint">
                  Letters, numbers, spaces, hyphens and underscores. The “.db”
                  extension is added automatically. New databases are created in
                  the project folder.
                </div>
              </div>
              {error && <div className="form-error">{error}</div>}
            </div>
            <div className="modal-footer">
              <button
                className="btn"
                onClick={() => setModal(null)}
                disabled={busy}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={submitModal}
                disabled={busy}
              >
                {busy
                  ? "Working…"
                  : modal.mode === "create"
                    ? "Create"
                    : "Rename"}
              </button>
            </div>
          </div>
        </div>
      )}

      {fileBrowserOpen && (
        <FileBrowserModal
          onClose={() => setFileBrowserOpen(false)}
          onOpened={handleFileOpened}
        />
      )}
    </div>
  );
}
