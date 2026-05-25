// Generic data grid for one chapter with resizable columns.
//
// Column widths are dragged via a handle on the right edge of each header.
// Widths are persisted in localStorage keyed by chapter so they survive
// page reloads and navigation.

import React, { useEffect, useRef, useState } from "react";
import type { ChapterDef, Row } from "../types";
import { getChapter } from "../chapters";

interface Props {
  chapter: ChapterDef;
  rows: Row[];
  fkOptions: Record<string, Row[]>;
  sort: string | null;
  order: "asc" | "desc";
  onSort: (field: string) => void;
  onEdit: (row: Row) => void;
  onDuplicate: (row: Row) => void;
  onDelete: (row: Row) => void;
  /** Optional extra buttons rendered before Edit in each row's action cell. */
  extraActions?: (row: Row) => React.ReactNode;
  /** Multi-select state owned by the parent. */
  selectedIds?: Set<number>;
  onSelectionChange?: (ids: Set<number>) => void;
}

// Column keys including the fixed id and actions sentinel.
const ID_KEY      = "__id__";
const ACTIONS_KEY = "__actions__";

const DEFAULT_WIDTHS: Record<string, number> = {
  [ID_KEY]:      64,
  [ACTIONS_KEY]: 170,
};
const DEFAULT_COL_W = 200;
const MIN_COL_W     = 50;

function storageKey(chapterKey: string) {
  return `grid-col-widths:${chapterKey}`;
}

function loadWidths(chapterKey: string): Record<string, number> {
  try {
    const raw = localStorage.getItem(storageKey(chapterKey));
    if (raw) return { ...DEFAULT_WIDTHS, ...JSON.parse(raw) };
  } catch { /* ignore */ }
  return { ...DEFAULT_WIDTHS };
}

function saveWidths(chapterKey: string, widths: Record<string, number>) {
  try {
    // only persist non-default values
    const delta: Record<string, number> = {};
    for (const [k, v] of Object.entries(widths)) {
      if (v !== DEFAULT_WIDTHS[k]) delta[k] = v;
    }
    localStorage.setItem(storageKey(chapterKey), JSON.stringify(delta));
  } catch { /* ignore */ }
}

// ---------------------------------------------------------------------------
// FK / cell helpers
// ---------------------------------------------------------------------------

function fkLabel(fkChapterKey: string, id: unknown, fkOptions: Record<string, Row[]>): string {
  if (id === null || id === undefined) return "—";
  const target = fkOptions[fkChapterKey] ?? [];
  const match = target.find((r) => r.id === id);
  if (!match) return `#${id}`;
  const labelField = getChapter(fkChapterKey).fkLabelField;
  return String(match[labelField] ?? `#${id}`);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const CB_KEY = "__cb__";

export default function DataGrid({
  chapter, rows, fkOptions,
  sort, order, onSort,
  onEdit, onDuplicate, onDelete,
  extraActions,
  selectedIds = new Set(),
  onSelectionChange,
}: Props) {
  const [colWidths, setColWidths] = useState<Record<string, number>>(
    () => loadWidths(chapter.key),
  );

  // Reset widths when the chapter changes.
  useEffect(() => {
    setColWidths(loadWidths(chapter.key));
  }, [chapter.key]);

  // Ref so resize handlers always see fresh widths without stale closure.
  const widthsRef = useRef(colWidths);
  useEffect(() => { widthsRef.current = colWidths; }, [colWidths]);

  function getWidth(key: string): number {
    return colWidths[key] ?? DEFAULT_COL_W;
  }

  // Ordered list of all column keys, used to find the next sibling column.
  const allColKeys = [CB_KEY, ID_KEY, ...chapter.gridFields, ACTIONS_KEY];

  // ---- selection helpers ----------------------------------------------------

  function toggleRow(id: number) {
    if (!onSelectionChange) return;
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id); else next.add(id);
    onSelectionChange(next);
  }

  function toggleAll() {
    if (!onSelectionChange) return;
    const allIds = rows.map((r) => r.id as number);
    const allSelected = allIds.every((id) => selectedIds.has(id));
    onSelectionChange(allSelected ? new Set() : new Set(allIds));
  }

  const allSelected = rows.length > 0 && rows.every((r) => selectedIds.has(r.id as number));
  const someSelected = !allSelected && rows.some((r) => selectedIds.has(r.id as number));

  function startResize(
    e: React.MouseEvent,
    colKey: string,
    thEl: HTMLTableCellElement,
  ) {
    e.preventDefault();
    e.stopPropagation();

    const startX   = e.clientX;
    const startW   = thEl.getBoundingClientRect().width;

    // Find the next column key and its starting rendered width.
    const idx = allColKeys.indexOf(colKey);
    const nextKey = idx >= 0 && idx < allColKeys.length - 1 ? allColKeys[idx + 1] : null;
    const nextThEl = nextKey
      ? (thEl.nextElementSibling as HTMLTableCellElement | null)
      : null;
    const nextStartW = nextThEl ? nextThEl.getBoundingClientRect().width : 0;

    function onMove(ev: MouseEvent) {
      const raw = ev.clientX - startX;

      if (nextKey && nextStartW > 0) {
        // Clamp delta so neither column goes below MIN_COL_W.
        const delta = Math.max(
          -(startW   - MIN_COL_W),   // current column can't shrink past min
          Math.min(
            nextStartW - MIN_COL_W,  // next column can't shrink past min
            raw,
          ),
        );
        setColWidths((prev) => ({
          ...prev,
          [colKey]:  startW   + delta,
          [nextKey]: nextStartW - delta,
        }));
      } else {
        // Last column — just grow/shrink it alone.
        setColWidths((prev) => ({
          ...prev,
          [colKey]: Math.max(MIN_COL_W, startW + raw),
        }));
      }
    }

    function onUp() {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      saveWidths(chapter.key, widthsRef.current);
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  // ---- header label / sort --------------------------------------------------

  function headerLabel(gridField: string): string {
    if (gridField === "__source__") return "Catalog / Custom";
    const field = chapter.fields.find((f) => f.name === gridField);
    return field ? field.label : gridField;
  }

  function sortIndicator(gridField: string): string {
    if (sort !== gridField) return "";
    return order === "asc" ? " ▲" : " ▼";
  }

  // ---- cell renderer --------------------------------------------------------

  function renderCell(row: Row, gridField: string) {
    if (gridField === "__source__" && chapter.merge) {
      if (row.is_custom) {
        const localVal = row[chapter.merge.primaryLocalField];
        return (
          <span>
            <span className="badge badge-custom">Custom</span> {localVal ?? "—"}
          </span>
        );
      }
      const catalog: Row | null = row.catalog ?? null;
      const label = catalog
        ? chapter.merge.catalogLabelFields
            .map((f) => catalog[f])
            .filter(Boolean)
            .join(" / ")
        : "—";
      return (
        <span>
          <span className="badge badge-catalog">Catalog</span> {label}
        </span>
      );
    }

    const field = chapter.fields.find((f) => f.name === gridField);
    const value = row[gridField];

    if (field?.type === "fk" && field.fkChapter) return fkLabel(field.fkChapter, value, fkOptions);
    if (field?.type === "bool") return value ? "Yes" : "No";
    if (value === null || value === undefined || value === "") return "—";
    return String(value);
  }

  // ---- resize handle --------------------------------------------------------

  function ResizeHandle({ colKey }: { colKey: string }) {
    return (
      <div
        className="col-resize-handle"
        onMouseDown={(e) => {
          const th = e.currentTarget.closest("th") as HTMLTableCellElement;
          startResize(e, colKey, th);
        }}
        onClick={(e) => e.stopPropagation()}
      />
    );
  }

  // ---- render ---------------------------------------------------------------

  if (rows.length === 0) {
    return <div className="empty">No records. Use "+ Add" or "Import CSV" to create some.</div>;
  }

  return (
    <div className="grid-wrap">
      <table
        className="grid"
        style={{ tableLayout: "fixed", width: "100%" }}
      >
        <colgroup>
          <col style={{ width: 36 }} />
          <col style={{ width: getWidth(ID_KEY) }} />
          {chapter.gridFields.map((gf) => (
            <col key={gf} style={{ width: getWidth(gf) }} />
          ))}
          <col style={{ width: getWidth(ACTIONS_KEY) }} />
        </colgroup>

        <thead>
          <tr>
            <th className="col-cb">
              <input
                type="checkbox"
                checked={allSelected}
                ref={(el) => { if (el) el.indeterminate = someSelected; }}
                onChange={toggleAll}
                title="Select all"
              />
            </th>
            <th className="col-id resizable-col sortable" onClick={() => onSort("id")}>
              ID{sortIndicator("id")}
              <ResizeHandle colKey={ID_KEY} />
            </th>
            {chapter.gridFields.map((gf) =>
              gf === "__source__" ? (
                <th key={gf} className="resizable-col">
                  {headerLabel(gf)}
                  <ResizeHandle colKey={gf} />
                </th>
              ) : (
                <th key={gf} className="resizable-col sortable" onClick={() => onSort(gf)}>
                  {headerLabel(gf)}{sortIndicator(gf)}
                  <ResizeHandle colKey={gf} />
                </th>
              ),
            )}
            <th className="col-actions resizable-col">
              Actions
              <ResizeHandle colKey={ACTIONS_KEY} />
            </th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className={selectedIds.has(row.id as number) ? "row-selected" : ""}>
              <td className="col-cb">
                <input
                  type="checkbox"
                  checked={selectedIds.has(row.id as number)}
                  onChange={() => toggleRow(row.id as number)}
                />
              </td>
              <td className="col-id">{row.id}</td>
              {chapter.gridFields.map((gf) => (
                <td key={gf} className="cell-clip">{renderCell(row, gf)}</td>
              ))}
              <td className="col-actions">
                {extraActions?.(row)}
                <button className="btn btn-sm" onClick={() => onEdit(row)}>Edit</button>
                <button className="btn btn-sm" onClick={() => onDuplicate(row)}>Duplicate</button>
                <button className="btn btn-sm btn-danger" onClick={() => onDelete(row)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
