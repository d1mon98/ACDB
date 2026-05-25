// Renders one chapter: loads its rows and the foreign-key option lists, shows
// the toolbar (search, import, export, add), the sortable data grid, and hosts
// the create / edit / duplicate form and the CSV-import dialog.

import React, { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { getChapter } from "../chapters";
import type { ChapterDef, Row, UsageResult } from "../types";
import CsvImportModal from "./CsvImportModal";
import DataGrid from "./DataGrid";
import RecordForm from "./RecordForm";

interface Props {
  chapterKey: string;
  projectId: number | null;
  /** Called after any create / update / delete so the app can refresh. */
  onDataChanged: () => void;
  /** Optional override chapter — field labels/required merged from catalog_column_defs. */
  chapterOverride?: ChapterDef;
  /** Optional extra action buttons rendered per row (before Edit). */
  extraActions?: (row: Row) => React.ReactNode;
  /** Optional content rendered between the chapter heading and the toolbar.
   *  Receives a callback to reload the grid rows so it can trigger a refresh. */
  headerExtra?: (reload: () => void) => React.ReactNode;
}

export default function ChapterView({ chapterKey, projectId, onDataChanged, chapterOverride, extraActions, headerExtra }: Props) {
  const chapter = chapterOverride ?? getChapter(chapterKey);

  const [rows, setRows] = useState<Row[]>([]);
  const [fkOptions, setFkOptions] = useState<Record<string, Row[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<string | null>(null);
  const [order, setOrder] = useState<"asc" | "desc">("asc");

  const [formOpen, setFormOpen] = useState(false);
  const [formRow, setFormRow] = useState<Row | null>(null);
  const [formDuplicate, setFormDuplicate] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);

  // Usage-check dialog state (catalog tables only)
  const [deleteCandidate, setDeleteCandidate] = useState<Row | null>(null);
  const [deleteUsage, setDeleteUsage] = useState<UsageResult | null>(null);
  const [deleteChecking, setDeleteChecking] = useState(false);

  const needsProject = chapter.projectScoped && !projectId;

  // Debounce the search box so we do not fetch on every keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Foreign-key option lists -- loaded once per chapter / project.
  const loadFkOptions = useCallback(async () => {
    if (needsProject) {
      setFkOptions({});
      return;
    }
    const fkKeys = new Set<string>();
    for (const f of chapter.fields) {
      if (f.type === "fk" && f.fkChapter) fkKeys.add(f.fkChapter);
    }
    if (chapter.merge) fkKeys.add(chapter.merge.catalogChapter);
    try {
      const entries = await Promise.all(
        [...fkKeys].map(async (key) => {
          const target = getChapter(key);
          const params: Record<string, unknown> = { limit: 1000 };
          if (target.projectScoped) params.project_id = projectId;
          const res = await api.list(key, params);
          return [key, res.items] as const;
        }),
      );
      setFkOptions(Object.fromEntries(entries));
    } catch (e: any) {
      setError(e?.message ?? String(e));
    }
  }, [chapter, projectId, needsProject]);

  // Row data -- reloaded whenever the search term or sort changes.
  const loadRows = useCallback(async () => {
    if (needsProject) {
      setRows([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = { limit: 1000 };
      if (chapter.projectScoped) params.project_id = projectId;
      if (search) params.search = search;
      if (sort) {
        params.sort = sort;
        params.order = order;
      }
      const data = chapter.merge
        ? await api.listMerged(chapter.key, params)
        : await api.list(chapter.key, params);
      setRows(data.items);
      setSelectedIds(new Set()); // clear selection on any reload
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }, [chapter, projectId, needsProject, search, sort, order]);

  useEffect(() => {
    loadFkOptions();
  }, [loadFkOptions]);

  useEffect(() => {
    loadRows();
  }, [loadRows]);

  function handleSort(field: string) {
    if (sort === field) {
      setOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSort(field);
      setOrder("asc");
    }
  }

  function handleAdd() {
    setFormRow(null);
    setFormDuplicate(false);
    setFormOpen(true);
  }

  function handleEdit(r: Row) {
    setFormRow(r);
    setFormDuplicate(false);
    setFormOpen(true);
  }

  function handleDuplicate(r: Row) {
    setFormRow(r);
    setFormDuplicate(true);
    setFormOpen(true);
  }

  async function handleDelete(r: Row) {
    // For catalog tables: check usage before showing the confirm dialog.
    if (chapter.group === "catalog") {
      setDeleteCandidate(r);
      setDeleteUsage(null);
      setDeleteChecking(true);
      try {
        const tableName = chapter.key.replace(/-/g, "_");
        const usage = await api.checkUsage(tableName, r.id);
        setDeleteUsage(usage);
      } catch {
        setDeleteUsage({ table: "", id: r.id, references: [], total: 0 });
      } finally {
        setDeleteChecking(false);
      }
      return; // dialog handles the actual delete
    }
    // Project tables: simple confirm.
    if (!window.confirm(`Delete this ${chapter.title} record (ID ${r.id})?`)) return;
    try {
      await api.remove(chapter.key, r.id);
      await loadRows();
      onDataChanged();
    } catch (e: any) {
      setError(e?.message ?? String(e));
    }
  }

  async function confirmDelete() {
    if (!deleteCandidate) return;
    try {
      await api.remove(chapter.key, deleteCandidate.id);
      setDeleteCandidate(null);
      setDeleteUsage(null);
      await loadRows();
      onDataChanged();
    } catch (e: any) {
      setDeleteCandidate(null);
      setDeleteUsage(null);
      setError(e?.message ?? String(e));
    }
  }

  async function handleBulkDelete() {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Delete ${selectedIds.size} selected record(s)? This cannot be undone.`)) return;
    setBulkDeleting(true);
    setError(null);
    const failures: string[] = [];
    for (const id of selectedIds) {
      try {
        await api.remove(chapter.key, id);
      } catch (e: any) {
        failures.push(`ID ${id}: ${e?.message ?? String(e)}`);
      }
    }
    setBulkDeleting(false);
    if (failures.length) setError(`Some deletions failed:\n${failures.join("\n")}`);
    await loadRows();
    onDataChanged();
  }

  async function handleSaved() {
    setFormOpen(false);
    await loadRows();
    await loadFkOptions();
    onDataChanged();
  }

  async function handleExport() {
    try {
      const params: Record<string, unknown> = {};
      if (chapter.projectScoped) params.project_id = projectId;
      if (search) params.search = search;
      const csv = await api.exportCsv(chapter.key, params);
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${chapter.key}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    }
  }

  async function handleImported() {
    setImportOpen(false);
    await loadRows();
    onDataChanged();
  }

  return (
    <div className="chapter">
      <div className="chapter-head">
        <div>
          <h2>{chapter.title}</h2>
          <div className="chapter-sub">
            {chapter.group === "catalog"
              ? "General Catalog · Class A"
              : "Project Table · Class B"}
            {!needsProject && !loading && ` · ${rows.length} record(s)`}
          </div>
        </div>
      </div>

      {headerExtra?.(loadRows)}

      {needsProject && (
        <div className="empty">
          Select a project from the header to view this project table.
        </div>
      )}

      {!needsProject && (
        <div className="toolbar">
          <input
            className="input toolbar-search"
            placeholder="Search…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <div className="toolbar-actions">
            {selectedIds.size > 0 && (
              <button className="btn btn-danger" onClick={handleBulkDelete} disabled={bulkDeleting}>
                {bulkDeleting ? "Deleting…" : `Delete ${selectedIds.size} selected`}
              </button>
            )}
            <button className="btn" onClick={() => setImportOpen(true)}>
              Import CSV
            </button>
            <button className="btn" onClick={handleExport}>
              Export CSV
            </button>
            <button className="btn btn-primary" onClick={handleAdd}>
              + Add
            </button>
          </div>
        </div>
      )}

      {error && <div className="form-error">{error}</div>}
      {loading && <div className="empty">Loading…</div>}
      {!loading && !needsProject && !error && (
        <DataGrid
          chapter={chapter}
          rows={rows}
          fkOptions={fkOptions}
          sort={sort}
          order={order}
          onSort={handleSort}
          onEdit={handleEdit}
          onDuplicate={handleDuplicate}
          onDelete={handleDelete}
          extraActions={extraActions}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
        />
      )}

      {formOpen && (
        <RecordForm
          chapter={chapter}
          row={formRow}
          isDuplicate={formDuplicate}
          fkOptions={fkOptions}
          projectId={projectId}
          onClose={() => setFormOpen(false)}
          onSaved={handleSaved}
        />
      )}

      {importOpen && (
        <CsvImportModal
          chapter={chapter}
          projectId={projectId}
          onClose={() => setImportOpen(false)}
          onImported={handleImported}
        />
      )}

      {/* Usage-check dialog for catalog table deletions */}
      {deleteCandidate && (
        <div className="modal-overlay">
          <div className="modal usage-dialog">
            <div className="modal-header">
              <h3>Delete {chapter.title} record</h3>
            </div>
            <div className="modal-body">
              {deleteChecking ? (
                <p className="usage-dialog__checking">Checking references…</p>
              ) : deleteUsage && deleteUsage.total > 0 ? (
                <>
                  <div className="usage-dialog__blocked">
                    <span className="usage-dialog__icon">🔒</span>
                    <strong>Cannot delete — this record is referenced in {deleteUsage.total} place{deleteUsage.total !== 1 ? "s" : ""}.</strong>
                  </div>
                  <p style={{ color: "var(--muted)", fontSize: 13, margin: "8px 0" }}>
                    Remove or reassign these references first:
                  </p>
                  <table className="usage-dialog__table">
                    <thead>
                      <tr><th>Table</th><th>Column</th><th>Rows</th></tr>
                    </thead>
                    <tbody>
                      {deleteUsage.references.map((r, i) => (
                        <tr key={i}>
                          <td><code>{r.table}</code></td>
                          <td><code>{r.column}</code></td>
                          <td>{r.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : (
                <div className="usage-dialog__safe">
                  <span className="usage-dialog__icon">✓</span>
                  <span>This record is not referenced anywhere. Safe to delete.</span>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button
                className="btn"
                onClick={() => { setDeleteCandidate(null); setDeleteUsage(null); }}
              >
                Cancel
              </button>
              {!deleteChecking && deleteUsage && deleteUsage.total === 0 && (
                <button className="btn btn-danger" onClick={confirmDelete}>
                  Delete
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
