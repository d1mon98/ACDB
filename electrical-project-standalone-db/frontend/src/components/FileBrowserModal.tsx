// File picker dialog -- browse the filesystem and open a database file.
//
// The browser cannot read the OS filesystem directly, so navigation goes
// through the backend's /api/fs/browse endpoint.  Only directories and
// database files (*.db / *.sqlite) are shown.

import { useEffect, useState } from "react";
import { api } from "../api";
import type { FsListing } from "../types";

interface Props {
  onClose: () => void;
  onOpened: () => void;
}

function formatSize(bytes?: number | null): string {
  if (bytes == null) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function FileBrowserModal({ onClose, onOpened }: Props) {
  const [listing, setListing] = useState<FsListing | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [opening, setOpening] = useState(false);

  async function browse(path?: string) {
    setLoading(true);
    setError(null);
    setSelected(null);
    try {
      setListing(await api.fs.browse(path));
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  // Start at the user's home folder.
  useEffect(() => {
    browse();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function openFile(path: string) {
    setOpening(true);
    setError(null);
    try {
      await api.databases.open(path);
      onOpened();
    } catch (e: any) {
      setError(e?.message ?? String(e));
      setOpening(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={() => !opening && onClose()}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Open Database File</h3>
          <button className="btn-icon" onClick={() => !opening && onClose()}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          {listing && listing.drives.length > 1 && (
            <div className="fb-drives">
              {listing.drives.map((d) => (
                <button key={d} className="btn btn-sm" onClick={() => browse(d)}>
                  {d}
                </button>
              ))}
            </div>
          )}

          <div className="fb-path" title={listing?.path}>
            {listing?.path ?? "…"}
          </div>

          {error && <div className="form-error">{error}</div>}
          {loading && <div className="empty">Loading…</div>}

          {!loading && listing && (
            <div className="fb-list">
              {listing.parent && (
                <div
                  className="fb-row fb-row-dir"
                  onClick={() => browse(listing.parent!)}
                >
                  <span className="fb-icon">📁</span> ..
                </div>
              )}
              {listing.directories.map((d) => (
                <div
                  key={d.path}
                  className="fb-row fb-row-dir"
                  onClick={() => browse(d.path)}
                >
                  <span className="fb-icon">📁</span> {d.name}
                </div>
              ))}
              {listing.files.map((f) => (
                <div
                  key={f.path}
                  className={
                    "fb-row fb-row-file" +
                    (selected === f.path ? " fb-selected" : "")
                  }
                  onClick={() => setSelected(f.path)}
                  onDoubleClick={() => !opening && openFile(f.path)}
                >
                  <span className="fb-icon">🗄</span>
                  <span className="fb-name">{f.name}</span>
                  <span className="fb-size">{formatSize(f.size_bytes)}</span>
                </div>
              ))}
              {listing.directories.length === 0 &&
                listing.files.length === 0 && (
                  <div className="empty">This folder has no databases.</div>
                )}
            </div>
          )}

          <div className="field-hint">
            Showing folders and database files (.db, .sqlite). Double-click a
            file to open it.
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn" onClick={onClose} disabled={opening}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={() => selected && openFile(selected)}
            disabled={!selected || opening}
          >
            {opening ? "Opening…" : "Open"}
          </button>
        </div>
      </div>
    </div>
  );
}
