// Renders one chapter: loads its rows and the foreign-key option lists, shows
// the toolbar (search, import, export, add), the sortable data grid, and hosts
// the create / edit / duplicate form and the CSV-import dialog.

import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { getChapter } from "../chapters";
import type { Row } from "../types";
import CsvImportModal from "./CsvImportModal";
import DataGrid from "./DataGrid";
import RecordForm from "./RecordForm";

interface Props {
  chapterKey: string;
  projectId: number | null;
  /** Called after any create / update / delete so the app can refresh. */
  onDataChanged: () => void;
}

export default function ChapterView({ chapterKey, projectId, onDataChanged }: Props) {
  const chapter = getChapter(chapterKey);

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
    if (!window.confirm(`Delete this ${chapter.title} record (ID ${r.id})?`)) {
      return;
    }
    try {
      await api.remove(chapter.key, r.id);
      await loadRows();
      onDataChanged();
    } catch (e: any) {
      setError(e?.message ?? String(e));
    }
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
    </div>
  );
}
